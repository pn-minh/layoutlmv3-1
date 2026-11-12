#!/usr/bin/env python3
"""
Python implementation of Google Sheet 49-column 6-Table Horizontal Layout sync.
Creates/updates the new sheet tab ('Additional Experiments & Calibrated Tracker')
copying the exact 6-Table Horizontal format of the previous sheet and adding:
  - Sections 1-4: Core 6-Table Ablation Suite (FUNSD & CORD, Base & Large)
  - Section 5:    6-Table Hyperparameter Sensitivity Sweep (lambda_bound & tau on FUNSD-base)
  - Section 6:    6-Table Few-Shot Sample Efficiency Curve (25%, 50%, 100% on FUNSD-base)
"""
import json
import datetime
from pathlib import Path
import requests

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyTnMY4wH9BwXUeNKKWqUdL_BClo-8ai76o70kQM0sT-nh7wv9oN64BpumGGAoalhSM1w/exec"
NEW_SHEET_TAB_NAME = "Additional Experiments & Calibrated Tracker"


def load_json(summaries_dir: Path, filename: str):
    candidates = [
        summaries_dir / filename,
        Path("/workspace/layoutlmv3-1/layoutlmv3/logs") / filename,
        Path("/content/layoutlmv3-1/layoutlmv3/logs") / filename,
        Path("layoutlmv3/logs") / filename,
        Path("scratch/colab_summaries") / filename,
        Path("../layoutlmv3/logs") / filename,
        Path("../scratch/colab_summaries") / filename,
    ]
    for p in candidates:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN] Error reading {p}: {e}")
    return None


def fmt_n(val):
    if val is None:
        return "--"
    try:
        return f"{float(val):.4f}"
    except (ValueError, TypeError):
        return "--"


def fmt_ms(m, s):
    if m is None:
        return "--"
    try:
        return f"{float(m):.4f} ± {float(s):.4f}"
    except (ValueError, TypeError):
        return "--"


def extract_seed_and_ms(obj, m):
    if not obj:
        return ['--', '--', '--', '--']
    if "per_seed" in obj and "mean_std" in obj:
        ps = obj.get("per_seed", {})
        ms = obj.get("mean_std", {}).get(m, {})
        return [
            fmt_n(ps.get('42', {}).get(m)),
            fmt_n(ps.get('123', {}).get(m)),
            fmt_n(ps.get('1993', {}).get(m)),
            fmt_ms(ms.get('mean'), ms.get('std')),
        ]
    if "metrics" in obj and m in obj["metrics"]:
        md = obj["metrics"][m]
        vals = md.get("values", [])
        v42 = vals[0] if len(vals) > 0 else None
        v123 = vals[1] if len(vals) > 1 else None
        v1993 = vals[2] if len(vals) > 2 else None
        return [
            fmt_n(v42),
            fmt_n(v123),
            fmt_n(v1993),
            fmt_ms(md.get("mean"), md.get("std")),
        ]
    return ['--', '--', '--', '--']


def get_displayed_mean(obj, metric):
    if not obj:
        return None
    raw = None
    if "mean_std" in obj and metric in obj["mean_std"]:
        raw = obj["mean_std"][metric].get("mean")
    elif "metrics" in obj and metric in obj["metrics"]:
        raw = obj["metrics"][metric].get("mean")
    if raw is None:
        return None
    try:
        return round(float(raw), 4)
    except (ValueError, TypeError):
        return None


def calc_metric_delta(target_obj, ref_obj, metric):
    t = get_displayed_mean(target_obj, metric)
    r = get_displayed_mean(ref_obj, metric)
    if t is None or r is None:
        return "--"
    diff = t - r
    if metric == "eval_loss":
        clean_diff = 0.0 if abs(diff) < 1e-9 else diff
        return f"{clean_diff:+.4f}"
    else:
        pct = diff * 100.0
        clean_pct = 0.0 if abs(pct) < 1e-9 else pct
        return f"{clean_pct:+.2f}%"


def make_custom_six_table_section(titles, base_obj, full_obj, obj3, obj4, obj5, obj6):
    rows = []
    r0 = [''] * 49
    r0[0]  = titles[0]
    r0[7]  = titles[1]
    r0[15] = titles[2]
    r0[24] = titles[3]
    r0[33] = titles[4]
    r0[42] = titles[5]
    rows.append(r0)

    r1 = [''] * 49
    r1[0:5] = ['Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean ± STD']
    r1[7:12] = ['Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean ± STD']
    r1[12] = "Δ\nvs. baseline"
    abl_starts = [15, 24, 33, 42]
    for s in abl_starts:
        r1[s:s+5] = ['Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean ± STD']
        r1[s+5] = "Δ\nvs. full model"
        r1[s+6] = "Δ\nvs. baseline"
    rows.append(r1)

    metrics = ['eval_accuracy', 'eval_f1', 'eval_precision', 'eval_recall', 'eval_loss']
    ablated_objs = [obj3, obj4, obj5, obj6]

    for m in metrics:
        row = [''] * 49
        row[0] = m
        row[1:5] = extract_seed_and_ms(base_obj, m)
        row[7] = m
        row[8:12] = extract_seed_and_ms(full_obj, m)
        row[12] = calc_metric_delta(full_obj, base_obj, m)
        for s, abl_obj in zip(abl_starts, ablated_objs):
            row[s] = m
            row[s+1:s+5] = extract_seed_and_ms(abl_obj, m)
            row[s+5] = calc_metric_delta(abl_obj, full_obj, m)
            row[s+6] = calc_metric_delta(abl_obj, base_obj, m)
        rows.append(row)

    return rows


def make_six_table_section(suffix, base_obj, full_obj, no_hpe_obj, no_seg_obj, no_bdr_obj, no_cont_obj):
    titles = [
        f"Baseline LayoutLMv3 ({suffix})",
        f"HPE + SCM + Contrastive Loss + Boundary Loss ({suffix})",
        f"w/o HPE ({suffix})",
        f"w/o Token-Segment SCM ({suffix})",
        f"w/o Boundary Loss ({suffix})",
        f"w/o Contrastive Loss ({suffix})",
    ]
    return make_custom_six_table_section(titles, base_obj, full_obj, no_hpe_obj, no_seg_obj, no_bdr_obj, no_cont_obj)


def sync_quad_sheet(summaries_dir: Path, webhook_url: str = WEBHOOK_URL):
    funsdLargeBase   = load_json(summaries_dir, "funsd-large-baseline_3seed_summary.json")
    funsdLargeFull4  = load_json(summaries_dir, "funsd-large-contrastive_3seed_summary.json")
    funsdLargeNoHpe  = load_json(summaries_dir, "funsd-large-no_hpe_3seed_summary.json")
    funsdLargeNoSeg  = load_json(summaries_dir, "funsd-large-no_segment_3seed_summary.json")
    funsdLargeNoBdr  = load_json(summaries_dir, "funsd-large-no_boundary_3seed_summary.json")
    funsdLargeNoCont = load_json(summaries_dir, "funsd-large-full_3seed_summary.json")

    funsdBaseBase    = load_json(summaries_dir, "funsd-base-baseline_3seed_summary.json")
    funsdBaseFull4   = load_json(summaries_dir, "funsd-base-contrastive_3seed_summary.json")
    funsdBaseNoHpe   = load_json(summaries_dir, "funsd-base-no_hpe_3seed_summary.json")
    funsdBaseNoSeg   = load_json(summaries_dir, "funsd-base-no_segment_3seed_summary.json")
    funsdBaseNoBdr   = load_json(summaries_dir, "funsd-base-no_boundary_3seed_summary.json")
    funsdBaseNoCont  = load_json(summaries_dir, "funsd-base-full_3seed_summary.json")

    cordBaseBase     = load_json(summaries_dir, "cord-base-baseline_3seed_summary.json")
    cordBaseFull4    = load_json(summaries_dir, "cord-base-contrastive_3seed_summary.json")
    cordBaseNoHpe    = load_json(summaries_dir, "cord-base-no_hpe_3seed_summary.json")
    cordBaseNoSeg    = load_json(summaries_dir, "cord-base-no_segment_3seed_summary.json")
    cordBaseNoBdr    = load_json(summaries_dir, "cord-base-no_boundary_3seed_summary.json")
    cordBaseNoCont   = load_json(summaries_dir, "cord-base-full_3seed_summary.json")

    cordLargeBase    = load_json(summaries_dir, "cord-large-baseline_3seed_summary.json")
    cordLargeFull4   = load_json(summaries_dir, "cord-large-contrastive_3seed_summary.json")
    cordLargeNoHpe   = load_json(summaries_dir, "cord-large-no_hpe_3seed_summary.json")
    cordLargeNoSeg   = load_json(summaries_dir, "cord-large-no_segment_3seed_summary.json")
    cordLargeNoBdr   = load_json(summaries_dir, "cord-large-no_boundary_3seed_summary.json")
    cordLargeNoCont  = load_json(summaries_dir, "cord-large-full_3seed_summary.json")

    # Additional Experiments: Sensitivity Sweep & Few-Shot Sample Efficiency
    sensBound005     = load_json(summaries_dir, "funsd-base-sens_bound_005_3seed_summary.json")
    sensBound020     = load_json(summaries_dir, "funsd-base-sens_bound_020_3seed_summary.json")
    sensTau007       = load_json(summaries_dir, "funsd-base-sens_tau_007_3seed_summary.json")
    sensTau020       = load_json(summaries_dir, "funsd-base-sens_tau_020_3seed_summary.json")

    fewshotBase25    = load_json(summaries_dir, "funsd-base-fewshot_base_25_3seed_summary.json")
    fewshotFull25    = load_json(summaries_dir, "funsd-base-fewshot_full_25_3seed_summary.json")
    fewshotBase50    = load_json(summaries_dir, "funsd-base-fewshot_base_50_3seed_summary.json")
    fewshotFull50    = load_json(summaries_dir, "funsd-base-fewshot_full_50_3seed_summary.json")

    sec1 = make_six_table_section("large - FUNSD", funsdLargeBase, funsdLargeFull4, funsdLargeNoHpe, funsdLargeNoSeg, funsdLargeNoBdr, funsdLargeNoCont)
    sec2 = make_six_table_section("base - FUNSD",  funsdBaseBase,  funsdBaseFull4,  funsdBaseNoHpe,  funsdBaseNoSeg,  funsdBaseNoBdr,  funsdBaseNoCont)
    sec3 = make_six_table_section("base - CORD",   cordBaseBase,   cordBaseFull4,   cordBaseNoHpe,   cordBaseNoSeg,   cordBaseNoBdr,   cordBaseNoCont)
    sec4 = make_six_table_section("large - CORD",  cordLargeBase,  cordLargeFull4,  cordLargeNoHpe,  cordLargeNoSeg,  cordLargeNoBdr,  cordLargeNoCont)

    sec5 = make_custom_six_table_section(
        [
            "Sensitivity Baseline LayoutLMv3 (base - FUNSD)",
            "HPE + SCM + Optimal λ_b=0.10, τ=0.10 (base - FUNSD)",
            "w/o Optimal: λ_bound = 0.05 (base - FUNSD)",
            "w/o Optimal: λ_bound = 0.20 (base - FUNSD)",
            "w/o Optimal: Contrastive τ = 0.07 (base - FUNSD)",
            "w/o Optimal: Contrastive τ = 0.20 (base - FUNSD)",
        ],
        funsdBaseBase, funsdBaseFull4, sensBound005, sensBound020, sensTau007, sensTau020,
    )

    sec6 = make_custom_six_table_section(
        [
            "Few-Shot 100% Baseline LayoutLMv3 (base - FUNSD)",
            "HPE + SCM + 100% Full 4-Module (base - FUNSD)",
            "w/o Full Data: 50% Data Baseline (base - FUNSD)",
            "w/o Full Data: 50% Data Full 4-Module (base - FUNSD)",
            "w/o Full Data: 25% Data Baseline (base - FUNSD)",
            "w/o Full Data: 25% Data Full 4-Module (base - FUNSD)",
        ],
        funsdBaseBase, funsdBaseFull4, fewshotBase50, fewshotFull50, fewshotBase25, fewshotFull25,
    )

    blank_row = [''] * 49
    matrix = []
    sections = [sec1, sec2, sec3, sec4, sec5, sec6]
    for idx, sec in enumerate(sections):
        matrix.extend(sec)
        if idx < len(sections) - 1:
            matrix.append(list(blank_row))
            matrix.append(list(blank_row))

    repo_root = summaries_dir.parent.parent if summaries_dir.name == "logs" else Path(".")
    csv_path = repo_root / "thesis" / "tracker_additional_experiments.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", encoding="utf-8") as f:
        for r in matrix:
            line = ",".join(f'"{c}"' if (',' in c or '"' in c or '\n' in c) else c for c in r)
            f.write(line + "\n")

    if webhook_url:
        payload = {
            "action": "sync",
            "sheetName": NEW_SHEET_TAB_NAME,
            "title": "LayoutLMv3 Additional Experiments, Sensitivity & Sample-Efficiency Live Tracker (2x A100)",
            "lastUpdated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rows": matrix,
        }
        try:
            r = requests.post(webhook_url, json=payload, timeout=30)
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Sync Google Sheet ({NEW_SHEET_TAB_NAME}): {r.status_code} -> {r.text}")
        except Exception as e:
            print(f"[WARN] Failed to push to Google Sheet: {e}")


if __name__ == "__main__":
    summaries_dir = Path("/workspace/layoutlmv3-1/layoutlmv3/logs")
    if not summaries_dir.exists():
        summaries_dir = Path("layoutlmv3/logs")
    if not summaries_dir.exists():
        summaries_dir = Path("scratch/colab_summaries")
    sync_quad_sheet(summaries_dir)
