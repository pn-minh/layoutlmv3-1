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
        if o1 and "per_seed" in o1 and "mean_std" in o1:
            ps = o1.get("per_seed", {})
            ms = o1.get("mean_std", {}).get(m, {})
            row.extend([m, fmt_n(ps.get('42', {}).get(m)), fmt_n(ps.get('123', {}).get(m)), fmt_n(ps.get('1993', {}).get(m)), fmt_ms(ms.get('mean'), ms.get('std'))])
        else:
            row.extend([m, '--', '--', '--', '--'])
        row.append('')

        # Model 2
        if o2 and "per_seed" in o2 and "mean_std" in o2:
            ps = o2.get("per_seed", {})
            ms = o2.get("mean_std", {}).get(m, {})
            row.extend([m, fmt_n(ps.get('42', {}).get(m)), fmt_n(ps.get('123', {}).get(m)), fmt_n(ps.get('1993', {}).get(m)), fmt_ms(ms.get('mean'), ms.get('std'))])
        else:
            row.extend([m, '--', '--', '--', '--'])
        row.append(gain2 if m == 'eval_f1' else '')

        # Model 3
        if o3 and "per_seed" in o3 and "mean_std" in o3:
            ps = o3.get("per_seed", {})
            ms = o3.get("mean_std", {}).get(m, {})
            row.extend([m, fmt_n(ps.get('42', {}).get(m)), fmt_n(ps.get('123', {}).get(m)), fmt_n(ps.get('1993', {}).get(m)), fmt_ms(ms.get('mean'), ms.get('std'))])
        else:
            row.extend([m, '--', '--', '--', '--'])
        row.append(gain3 if m == 'eval_f1' else '')

        # Model 4
        if o4 and "per_seed" in o4 and "mean_std" in o4:
            ps = o4.get("per_seed", {})
            ms = o4.get("mean_std", {}).get(m, {})
            row.extend([m, fmt_n(ps.get('42', {}).get(m)), fmt_n(ps.get('123', {}).get(m)), fmt_n(ps.get('1993', {}).get(m)), fmt_ms(ms.get('mean'), ms.get('std'))])
        else:
            row.extend([m, '--', '--', '--', '--'])

        rows.append(row)
    return rows

def sync_quad_sheet(summaries_dir: Path, webhook_url: str = WEBHOOK_URL):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Building Quad-Block Per-Seed Data Structure from {summaries_dir}...")

    funsdLargeBase = load_json(summaries_dir, "funsd-large-baseline_3seed_summary.json")
    funsdLargeFull = load_json(summaries_dir, "funsd-large-full_3seed_summary.json")
    funsdLargeNoBdr = load_json(summaries_dir, "funsd-large-no_boundary_3seed_summary.json")
    funsdLargeNoHpe = load_json(summaries_dir, "funsd-large-no_hpe_3seed_summary.json")
    funsdLargeNoSeg = load_json(summaries_dir, "funsd-large-no_segment_3seed_summary.json")

    funsdBaseBase = load_json(summaries_dir, "funsd-base-baseline_3seed_summary.json")
    funsdBaseFull = load_json(summaries_dir, "funsd-base-full_3seed_summary.json")
    funsdBaseNoHpe = load_json(summaries_dir, "funsd-base-no_hpe_3seed_summary.json")
    funsdBaseNoBdr = load_json(summaries_dir, "funsd-base-no_boundary_3seed_summary.json")
    funsdBaseNoSeg = load_json(summaries_dir, "funsd-base-no_segment_3seed_summary.json")

    cordBaseBase = load_json(summaries_dir, "cord-base-baseline_3seed_summary.json")
    cordBaseFull = load_json(summaries_dir, "cord-base-full_3seed_summary.json")
    cordBaseNoHpe = load_json(summaries_dir, "cord-base-no_hpe_3seed_summary.json")
    cordBaseNoBdr = load_json(summaries_dir, "cord-base-no_boundary_3seed_summary.json")
    cordBaseNoSeg = load_json(summaries_dir, "cord-base-no_segment_3seed_summary.json")

    cordLargeBase = load_json(summaries_dir, "cord-large-baseline_3seed_summary.json")
    cordLargeFull = load_json(summaries_dir, "cord-large-full_3seed_summary.json")
    cordLargeNoBdr = load_json(summaries_dir, "cord-large-no_boundary_3seed_summary.json")
    cordLargeNoHpe = load_json(summaries_dir, "cord-large-no_hpe_3seed_summary.json")
    cordLargeNoSeg = load_json(summaries_dir, "cord-large-no_segment_3seed_summary.json")

    # Dynamic Delta F1 calculation if summaries are present
    def calc_delta(target_sum, base_sum):
        if target_sum and base_sum:
            try:
                t_f1 = target_sum.get("mean_std", {}).get("eval_f1", {}).get("mean")
                b_f1 = base_sum.get("mean_std", {}).get("eval_f1", {}).get("mean")
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

    # Section 5: Token-Segment Ablation
    g_funsd_noseg = calc_delta(funsdBaseNoSeg, funsdBaseBase)
    g_cord_noseg = calc_delta(cordBaseNoSeg, cordBaseBase)
    sec5 = make_quad_block(
        'w/o Token-Segment SCM (base - FUNSD)', funsdBaseNoSeg,
        'Reference Baseline (base - FUNSD)', funsdBaseBase,
        'w/o Token-Segment SCM (base - CORD)', cordBaseNoSeg,
        'Reference Baseline (base - CORD)', cordBaseBase,
        g_funsd_noseg, '--', g_cord_noseg
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

    # Write local CSV
    csv_path = Path("/content/layoutlmv3-1/thesis/tracker.csv")
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

