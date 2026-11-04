#!/usr/bin/env python3
"""
Python implementation of Google Sheet 45-column 6-Table Horizontal Layout sync.
Matches scratch/sync_sheet_updated.js and thesis/sync_google_sheet.ps1.
"""
import json
import datetime
from pathlib import Path
import requests

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyTnMY4wH9BwXUeNKKWqUdL_BClo-8ai76o70kQM0sT-nh7wv9oN64BpumGGAoalhSM1w/exec"

def load_json(summaries_dir: Path, filename: str):
    candidates = [
        summaries_dir / filename,
        Path("/workspace/layoutlmv3-1/layoutlmv3/logs") / filename,
        Path("/content/layoutlmv3-1/layoutlmv3/logs") / filename,
        Path("scratch/colab_summaries") / filename,
        Path("layoutlmv3/logs") / filename,
        Path("../scratch/colab_summaries") / filename,
        Path("../layoutlmv3/logs") / filename,
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

def make_six_table_section(suffix, base_obj, full_obj, no_hpe_obj, no_seg_obj, no_bdr_obj, no_cont_obj):
    rows = []
    r0 = [''] * 45
    r0[0]  = f"Baseline LayoutLMv3 ({suffix})"
    r0[7]  = f"HPE + SCM + Contrastive Loss + Boundary Loss ({suffix})"
    r0[15] = f"w/o HPE ({suffix})"
    r0[23] = f"w/o Token-Segment SCM ({suffix})"
    r0[31] = f"w/o Boundary Loss ({suffix})"
    r0[39] = f"w/o Contrastive Loss ({suffix})"
    rows.append(r0)

    r1 = [''] * 45
    r1[0:5] = ['Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean ± STD']
    for s in [7, 15, 23, 31, 39]:
        r1[s:s+6] = ['Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean ± STD', 'Delta']
    rows.append(r1)

    metrics = ['eval_accuracy', 'eval_f1', 'eval_precision', 'eval_recall', 'eval_loss']
    ablated_objs = [no_hpe_obj, no_seg_obj, no_bdr_obj, no_cont_obj]
    abl_starts = [15, 23, 31, 39]

    for m in metrics:
        row = [''] * 45
        # Table 1: Baseline
        row[0] = m
        row[1:5] = extract_seed_and_ms(base_obj, m)
        # Table 2: Full 4-Module vs Baseline
        row[7] = m
        row[8:12] = extract_seed_and_ms(full_obj, m)
        row[12] = calc_metric_delta(full_obj, base_obj, m)
        # Tables 3..6: Ablations vs Full 4-Module
        for s, abl_obj in zip(abl_starts, ablated_objs):
            row[s] = m
            row[s+1:s+5] = extract_seed_and_ms(abl_obj, m)
            row[s+5] = calc_metric_delta(abl_obj, full_obj, m)
        rows.append(row)

    return rows

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

    sec1 = make_six_table_section("large - FUNSD", funsdLargeBase, funsdLargeFull4, funsdLargeNoHpe, funsdLargeNoSeg, funsdLargeNoBdr, funsdLargeNoCont)
    sec2 = make_six_table_section("base - FUNSD",  funsdBaseBase,  funsdBaseFull4,  funsdBaseNoHpe,  funsdBaseNoSeg,  funsdBaseNoBdr,  funsdBaseNoCont)
    sec3 = make_six_table_section("base - CORD",   cordBaseBase,   cordBaseFull4,   cordBaseNoHpe,   cordBaseNoSeg,   cordBaseNoBdr,   cordBaseNoCont)
    sec4 = make_six_table_section("large - CORD",  cordLargeBase,  cordLargeFull4,  cordLargeNoHpe,  cordLargeNoSeg,  cordLargeNoBdr,  cordLargeNoCont)

    blank_row = [''] * 45
    matrix = []
    sections = [sec1, sec2, sec3, sec4]
    for idx, sec in enumerate(sections):
        matrix.extend(sec)
        if idx < len(sections) - 1:
            matrix.append(list(blank_row))
            matrix.append(list(blank_row))

    repo_root = summaries_dir.parent.parent if summaries_dir.name == "logs" else Path(".")
    csv_path = repo_root / "thesis" / "tracker.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", encoding="utf-8") as f:
        for r in matrix:
            line = ",".join(f'"{c}"' if (',' in c or '"' in c or '\n' in c) else c for c in r)
            f.write(line + "\n")

    if webhook_url:
        payload = {
            "action": "sync",
            "lastUpdated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rows": matrix
        }
        try:
            r = requests.post(webhook_url, json=payload, timeout=30)
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Sync Google Sheet: {r.status_code} -> {r.text}")
        except Exception as e:
            print(f"[WARN] Failed to push to Google Sheet: {e}")

if __name__ == "__main__":
    summaries_dir = Path("/workspace/layoutlmv3-1/layoutlmv3/logs")
    if not summaries_dir.exists():
        summaries_dir = Path("/content/layoutlmv3-1/layoutlmv3/logs")
    if not summaries_dir.exists():
        summaries_dir = Path("scratch/colab_summaries")
    sync_quad_sheet(summaries_dir)
