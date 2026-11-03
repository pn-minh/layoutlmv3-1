#!/usr/bin/env python3
"""
Python implementation of Google Sheet 23-column Quad-Block sync.
Matches thesis/sync_google_sheet.ps1 exactly.
"""
import os
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
        return f"{float(m):.4f} +/- {float(s):.4f}"
    except (ValueError, TypeError):
        return "--"

def extract_seed_and_ms(obj, m):
    """Extract (s42, s123, s1993, mean_std_str) from either schema ('per_seed'+'mean_std' or 'metrics')."""
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

def make_quad_block(t1, o1, t2, o2, t3, o3, t4, o4, gain2, gain3, gain4):
    rows = []
    # Row 0: Titles
    r0 = [t1, '', '', '', '', '', t2, '', '', '', '', '', t3, '', '', '', '', '', t4, '', '', '', '']
    # Row 1: Headers
    r1 = [
        'Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean +/- STD', '',
        'Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean +/- STD', 'Delta F1',
        'Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean +/- STD', 'Delta F1',
        'Metric', 'Seed 42', 'Seed 123', 'Seed 1993', 'Mean +/- STD'
    ]
    rows.append(r0)
    rows.append(r1)

    metrics = ['eval_accuracy', 'eval_f1', 'eval_precision', 'eval_recall', 'eval_loss']
    for m in metrics:
        row = []
        # Model 1
        row.extend([m] + extract_seed_and_ms(o1, m))
        row.append('')

        # Model 2
        row.extend([m] + extract_seed_and_ms(o2, m))
        row.append(gain2 if m == 'eval_f1' else '')

        # Model 3
        row.extend([m] + extract_seed_and_ms(o3, m))
        row.append(gain3 if m == 'eval_f1' else '')

        # Model 4
        row.extend([m] + extract_seed_and_ms(o4, m))

        rows.append(row)
    return rows

def get_mean_f1(obj):
    if not obj:
        return None
    if "mean_std" in obj and "eval_f1" in obj["mean_std"]:
        return obj["mean_std"]["eval_f1"].get("mean")
    if "metrics" in obj and "eval_f1" in obj["metrics"]:
        return obj["metrics"]["eval_f1"].get("mean")
    return None

def sync_quad_sheet(summaries_dir: Path, webhook_url: str = WEBHOOK_URL):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Building Quad-Block Per-Seed Data Structure from {summaries_dir}...")

    funsdLargeBase = load_json(summaries_dir, "funsd-large-baseline_3seed_summary.json")
    funsdLargeFull = load_json(summaries_dir, "funsd-large-full_3seed_summary.json")
    funsdLargeCont = load_json(summaries_dir, "funsd-large-contrastive_3seed_summary.json")
    funsdLargeNoBdr = load_json(summaries_dir, "funsd-large-no_boundary_3seed_summary.json")
    funsdLargeNoHpe = load_json(summaries_dir, "funsd-large-no_hpe_3seed_summary.json")
    funsdLargeNoSeg = load_json(summaries_dir, "funsd-large-no_segment_3seed_summary.json")

    funsdBaseBase = load_json(summaries_dir, "funsd-base-baseline_3seed_summary.json")
    funsdBaseFull = load_json(summaries_dir, "funsd-base-full_3seed_summary.json")
    funsdBaseCont = load_json(summaries_dir, "funsd-base-contrastive_3seed_summary.json")
    funsdBaseNoHpe = load_json(summaries_dir, "funsd-base-no_hpe_3seed_summary.json")
    funsdBaseNoBdr = load_json(summaries_dir, "funsd-base-no_boundary_3seed_summary.json")
    funsdBaseNoSeg = load_json(summaries_dir, "funsd-base-no_segment_3seed_summary.json")

    cordBaseBase = load_json(summaries_dir, "cord-base-baseline_3seed_summary.json")
    cordBaseFull = load_json(summaries_dir, "cord-base-full_3seed_summary.json")
    cordBaseCont = load_json(summaries_dir, "cord-base-contrastive_3seed_summary.json")
    cordBaseNoHpe = load_json(summaries_dir, "cord-base-no_hpe_3seed_summary.json")
    cordBaseNoBdr = load_json(summaries_dir, "cord-base-no_boundary_3seed_summary.json")
    cordBaseNoSeg = load_json(summaries_dir, "cord-base-no_segment_3seed_summary.json")

    cordLargeBase = load_json(summaries_dir, "cord-large-baseline_3seed_summary.json")
    cordLargeFull = load_json(summaries_dir, "cord-large-full_3seed_summary.json")
    cordLargeCont = load_json(summaries_dir, "cord-large-contrastive_3seed_summary.json")
    cordLargeNoBdr = load_json(summaries_dir, "cord-large-no_boundary_3seed_summary.json")
    cordLargeNoHpe = load_json(summaries_dir, "cord-large-no_hpe_3seed_summary.json")
    cordLargeNoSeg = load_json(summaries_dir, "cord-large-no_segment_3seed_summary.json")

    # Dynamic Delta F1 calculation if summaries are present
    def calc_delta(target_sum, base_sum):
        if target_sum and base_sum:
            try:
                t_f1 = get_mean_f1(target_sum)
                b_f1 = get_mean_f1(base_sum)
                if t_f1 is not None and b_f1 is not None:
                    diff = (float(t_f1) - float(b_f1)) * 100.0
                    return f"{diff:+.2f}%"
            except Exception:
                pass
        return "--"

    g_funsd_lg_nohpe = calc_delta(funsdLargeNoHpe, funsdLargeBase)
    g_funsd_lg_full = calc_delta(funsdLargeFull, funsdLargeBase)
    g_funsd_lg_nobdr = calc_delta(funsdLargeNoBdr, funsdLargeBase)

    g_funsd_bs_nohpe = calc_delta(funsdBaseNoHpe, funsdBaseBase)
    g_funsd_bs_full = calc_delta(funsdBaseFull, funsdBaseBase)
    g_funsd_bs_nobdr = calc_delta(funsdBaseNoBdr, funsdBaseBase)

    g_cord_bs_nohpe = calc_delta(cordBaseNoHpe, cordBaseBase)
    g_cord_bs_full = calc_delta(cordBaseFull, cordBaseBase)
    g_cord_bs_nobdr = calc_delta(cordBaseNoBdr, cordBaseBase)

    g_cord_lg_nohpe = calc_delta(cordLargeNoHpe, cordLargeBase)
    g_cord_lg_full = calc_delta(cordLargeFull, cordLargeBase)
    g_cord_lg_nobdr = calc_delta(cordLargeNoBdr, cordLargeBase)

    blank_row = [''] * 23

    # Section 1: LARGE - FUNSD
    sec1 = make_quad_block(
        'Baseline LayoutLMv3 (large - FUNSD)', funsdLargeBase,
        'w/o HPE (large - FUNSD)', funsdLargeNoHpe,
        'OURS: Full Model (large - FUNSD)', funsdLargeFull,
        'w/o Boundary Loss (large - FUNSD)', funsdLargeNoBdr,
        g_funsd_lg_nohpe, g_funsd_lg_full, g_funsd_lg_nobdr
    )

    # Section 2: BASE - FUNSD
    sec2 = make_quad_block(
        'Baseline LayoutLMv3 (base - FUNSD)', funsdBaseBase,
        'w/o HPE (base - FUNSD)', funsdBaseNoHpe,
        'OURS: Full Model (base - FUNSD)', funsdBaseFull,
        'w/o Boundary Loss (base - FUNSD)', funsdBaseNoBdr,
        g_funsd_bs_nohpe, g_funsd_bs_full, g_funsd_bs_nobdr
    )

    # Section 3: BASE - CORD
    sec3 = make_quad_block(
        'Baseline LayoutLMv3 (base - CORD)', cordBaseBase,
        'w/o HPE (base - CORD)', cordBaseNoHpe,
        'OURS: Full Model (base - CORD)', cordBaseFull,
        'w/o Boundary Loss (base - CORD)', cordBaseNoBdr,
        g_cord_bs_nohpe, g_cord_bs_full, g_cord_bs_nobdr
    )

    # Section 4: LARGE - CORD
    sec4 = make_quad_block(
        'Baseline LayoutLMv3 (large - CORD)', cordLargeBase,
        'w/o HPE (large - CORD)', cordLargeNoHpe,
        'OURS: Full Model (large - CORD)', cordLargeFull,
        'w/o Boundary Loss (large - CORD)', cordLargeNoBdr,
        g_cord_lg_nohpe, g_cord_lg_full, g_cord_lg_nobdr
    )

    # Section 5: Token-Segment Ablation (base)
    g_funsd_noseg = calc_delta(funsdBaseNoSeg, funsdBaseBase)
    g_cord_noseg = calc_delta(cordBaseNoSeg, cordBaseBase)
    sec5 = make_quad_block(
        'w/o Token-Segment SCM (base - FUNSD)', funsdBaseNoSeg,
        'Reference Baseline (base - FUNSD)', funsdBaseBase,
        'w/o Token-Segment SCM (base - CORD)', cordBaseNoSeg,
        'Reference Baseline (base - CORD)', cordBaseBase,
        g_funsd_noseg, '--', g_cord_noseg
    )

    # Section 6: Token-Segment Ablation (large)
    g_funsd_lg_noseg = calc_delta(funsdLargeNoSeg, funsdLargeBase)
    g_cord_lg_noseg = calc_delta(cordLargeNoSeg, cordLargeBase)
    sec6 = make_quad_block(
        'w/o Token-Segment SCM (large - FUNSD)', funsdLargeNoSeg,
        'Reference Baseline (large - FUNSD)', funsdLargeBase,
        'w/o Token-Segment SCM (large - CORD)', cordLargeNoSeg,
        'Reference Baseline (large - CORD)', cordLargeBase,
        g_funsd_lg_noseg, '--', g_cord_lg_noseg
    )

    # Section 7: Cross-Modal Contrastive Loss Ablation (base)
    g_funsd_bs_cont = calc_delta(funsdBaseCont, funsdBaseBase)
    g_cord_bs_cont = calc_delta(cordBaseCont, cordBaseBase)
    sec7 = make_quad_block(
        'OURS + Contrastive Loss (base - FUNSD)', funsdBaseCont,
        'w/o Contrastive Loss (base - FUNSD)', funsdBaseFull,
        'OURS + Contrastive Loss (base - CORD)', cordBaseCont,
        'w/o Contrastive Loss (base - CORD)', cordBaseFull,
        g_funsd_bs_cont, g_cord_bs_cont, g_cord_bs_full
    )

    # Section 8: Cross-Modal Contrastive Loss Ablation (large)
    g_funsd_lg_cont = calc_delta(funsdLargeCont, funsdLargeBase)
    g_cord_lg_cont = calc_delta(cordLargeCont, cordLargeBase)
    sec8 = make_quad_block(
        'OURS + Contrastive Loss (large - FUNSD)', funsdLargeCont,
        'w/o Contrastive Loss (large - FUNSD)', funsdLargeFull,
        'OURS + Contrastive Loss (large - CORD)', cordLargeCont,
        'w/o Contrastive Loss (large - CORD)', cordLargeFull,
        g_funsd_lg_cont, g_cord_lg_cont, g_cord_lg_full
    )

    matrix = []
    matrix.extend(sec1)
    matrix.append(blank_row)
    matrix.extend(sec2)
    matrix.append(blank_row)
    matrix.extend(sec3)
    matrix.append(blank_row)
    matrix.extend(sec4)
    matrix.append(blank_row)
    matrix.extend(sec5)
    matrix.append(blank_row)
    matrix.extend(sec6)
    matrix.append(blank_row)
    matrix.extend(sec7)
    matrix.append(blank_row)
    matrix.extend(sec8)

    # Write local CSV
    repo_root = summaries_dir.parent.parent if summaries_dir.name == "logs" else Path(".")
    csv_path = repo_root / "thesis" / "tracker.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", encoding="utf-8") as f:
        for r in matrix:
            line = ",".join(f'"{c}"' if (',' in c or '"' in c or '\n' in c) else c for c in r)
            f.write(line + "\n")

    # Push to Google Sheet Webhook
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

