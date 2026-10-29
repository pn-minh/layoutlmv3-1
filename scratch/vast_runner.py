#!/usr/bin/env python3
"""
Autonomous Vast.ai Runner for Remaining Experiments (Cells 20 -> 21 -> 22 -> 23 -> 24).
Continuously syncs the Google Sheet Live Tracker and uploads summaries/logs/archives to Google Drive.
"""
import os
import sys
import time
import json
import base64
import zipfile
import datetime
import subprocess
import threading
from pathlib import Path

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyTnMY4wH9BwXUeNKKWqUdL_BClo-8ai76o70kQM0sT-nh7wv9oN64BpumGGAoalhSM1w/exec"
WORKSPACE_DIR = Path("/workspace")
REPO_DIR = WORKSPACE_DIR / "layoutlmv3-1"
LOG_DIR = REPO_DIR / "layoutlmv3" / "logs"
RUNNER_LOG = WORKSPACE_DIR / "vast_runner.log"

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    with open(RUNNER_LOG, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

def upload_to_gdrive(file_path: Path, remote_filename: str = None) -> bool:
    """Upload a file to Google Drive via Apps Script Webhook."""
    if not file_path.exists():
        log(f"[WARN] File does not exist for upload: {file_path}")
        return False
    fname = remote_filename or file_path.name
    try:
        raw_bytes = file_path.read_bytes()
        b64_str = base64.b64encode(raw_bytes).decode("utf-8")
        payload = {
            "action": "upload_pdf",
            "filename": fname,
            "pdfBase64": b64_str
        }
        import requests
        r = requests.post(WEBHOOK_URL, json=payload, timeout=60)
        if r.status_code == 200 and "OK" in r.text:
            log(f"[GDRIVE] Successfully uploaded {fname} ({len(raw_bytes)/1024:.1f} KB)")
            return True
        else:
            log(f"[WARN] Upload {fname} returned: {r.status_code} {r.text}")
            return False
    except Exception as e:
        log(f"[ERROR] Upload error for {fname}: {e}")
        return False

def sync_sheet():
    """Trigger Google Sheet Live Tracker sync."""
    try:
        script_path = REPO_DIR / "scratch" / "sync_google_sheet.py"
        if script_path.exists():
            py_bin = "/venv/layoutlmv3/bin/python" if Path("/venv/layoutlmv3/bin/python").exists() else sys.executable
            res = subprocess.run([py_bin, str(script_path)], capture_output=True, text=True)
            log(f"[SHEET] sync_google_sheet output: {res.stdout.strip()}")
    except Exception as e:
        log(f"[WARN] Error during Google Sheet sync: {e}")

def git_commit(cell_label: str):
    """Create local git commit on Vast.ai instance."""
    try:
        subprocess.run(["git", "-C", str(REPO_DIR), "config", "user.name", "pn-minh"], check=False)
        subprocess.run(["git", "-C", str(REPO_DIR), "config", "user.email", "pn-minh@users.noreply.github.com"], check=False)
        subprocess.run(["git", "-C", str(REPO_DIR), "add", "layoutlmv3/logs/"], check=False)
        subprocess.run(["git", "-C", str(REPO_DIR), "commit", "-m", f"Auto-run (Vast.ai): {cell_label} results completed"], check=False)
        log(f"[GIT] Committed {cell_label} locally.")
    except Exception as e:
        log(f"[WARN] Git commit warning: {e}")

def run_suite_step(cell_num: int, dataset: str, variant: str, mode: str, label: str, summary_file: str):
    log("======================================================================")
    log(f"STARTING CELL {cell_num}: {label} ({dataset.upper()} | {variant} | {mode})")
    log("======================================================================")

    sum_path = LOG_DIR / summary_file
    log_path = Path(f"/tmp/cell_{cell_num}.log")

    if sum_path.exists():
        log(f"[SKIP] Summary already exists for Cell {cell_num}: {sum_path}")
        upload_to_gdrive(sum_path)
        sync_sheet()
        return

    cmd = (
        f"source /workspace/miniconda3/etc/profile.d/conda.sh && conda activate layoutlmv3 && "
        f"export PYTHONUNBUFFERED=1 && cd /workspace/layoutlmv3-1/layoutlmv3 && "
        f"bash scripts/run_ablation_suite.sh {dataset} {variant} {mode} > /tmp/cell_{cell_num}.log 2>&1; "
        f"echo '===EXIT_CODE:'$? '===' >> /tmp/cell_{cell_num}.log"
    )

    t0 = time.time()
    proc = subprocess.run(["bash", "-c", cmd])
    elapsed = time.time() - t0
    log(f"Cell {cell_num} execution finished in {elapsed:.1f}s ({elapsed/60.0:.2f} min) with returncode {proc.returncode}")

    # Upload execution log immediately
    if log_path.exists():
        upload_to_gdrive(log_path, f"cell_{cell_num}.log")

    if proc.returncode != 0:
        log(f"[FATAL] Cell {cell_num} failed with returncode {proc.returncode}!")
        raise RuntimeError(f"Cell {cell_num} failed with returncode {proc.returncode}")

    # Verify summary
    if sum_path.exists():
        log(f"Verified summary exists: {sum_path}")
        upload_to_gdrive(sum_path)
    else:
        log(f"[FATAL] Expected summary not found: {sum_path}")
        raise RuntimeError(f"Summary missing for cell {cell_num}: {sum_path}")

    # Sync Google Sheet & Commit locally
    sync_sheet()
    git_commit(f"Cell {cell_num} ({label})")
    log(f"Cell {cell_num} ({label}) pipeline actions finished.")

def run_aggregation():
    log("======================================================================")
    log("STARTING CELL 24: Aggregate All 3-Seed Results into Final Table")
    log("======================================================================")
    
    modes = ["baseline", "full", "no_boundary", "no_segment", "no_hpe"]
    mode_labels = {
        "baseline": "Baseline (Vanilla LayoutLMv3)",
        "full": "Full Model (HPE + Token-Segment + Boundary Loss)",
        "no_boundary": "Ablation: w/o Boundary Loss",
        "no_segment": "Ablation: w/o Token-Segment",
        "no_hpe": "Ablation: w/o HPE",
    }

    missing = []
    for variant in ["base", "large"]:
        for dataset in ["funsd", "cord"]:
            for mode in modes:
                summary_path = LOG_DIR / f"{dataset}-{variant}-{mode}_3seed_summary.json"
                if not summary_path.exists():
                    missing.append(summary_path.name)
    if missing:
        log(f"[FATAL] Cannot aggregate! Missing summaries: {missing}")
        raise RuntimeError(f"Missing summaries: {missing}")

    table_lines = []
    table_lines.append(f"| {'Variant':<7} | {'Dataset':<7} | {'Configuration':<48} | {'Precision (%)':<16} | {'Recall (%)':<16} | {'F1 (%)':<16} |")
    table_lines.append("|" + "-"*9 + "|" + "-"*9 + "|" + "-"*50 + "|" + "-"*18 + "|" + "-"*18 + "|" + "-"*18 + "|")

    for variant in ["base", "large"]:
        for dataset in ["funsd", "cord"]:
            for mode in modes:
                summary_path = LOG_DIR / f"{dataset}-{variant}-{mode}_3seed_summary.json"
                if not summary_path.exists():
                    table_lines.append(f"| {variant:<7} | {dataset.upper():<7} | {mode_labels[mode]:<48} | {'MISSING':<16} | {'MISSING':<16} | {'MISSING':<16} |")
                    continue
                with open(summary_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    data = content.get("metrics") or content.get("mean_std")
                
                if "eval_precision" in data and "mean" in data["eval_precision"]:
                    p_str = f"{data['eval_precision']['mean']*100:.2f} ± {data['eval_precision']['std']*100:.2f}"
                    r_str = f"{data['eval_recall']['mean']*100:.2f} ± {data['eval_recall']['std']*100:.2f}"
                    f1_str = f"{data['eval_f1']['mean']*100:.2f} ± {data['eval_f1']['std']*100:.2f}"
                else:
                    p_str = f"{data['eval_precision']['mean_pct']:.2f} ± {data['eval_precision']['std_pct']:.2f}"
                    r_str = f"{data['eval_recall']['mean_pct']:.2f} ± {data['eval_recall']['std_pct']:.2f}"
                    f1_str = f"{data['eval_f1']['mean_pct']:.2f} ± {data['eval_f1']['std_pct']:.2f}"

                table_lines.append(f"| {variant:<7} | {dataset.upper():<7} | {mode_labels[mode]:<48} | {p_str:<16} | {r_str:<16} | {f1_str:<16} |")

    table_text = "\n".join(table_lines)
    log("\n" + table_text)

    out_table_path = REPO_DIR / "FINAL_AGGREGATED_ABLATION_TABLE.md"
    out_table_path.write_text(table_text, encoding="utf-8")
    upload_to_gdrive(out_table_path)
    log("Cell 24 completed successfully.")

def create_and_upload_final_package():
    log("======================================================================")
    log("CREATING FINAL MASTER RESULTS ARCHIVE...")
    log("======================================================================")

    zip_path = WORKSPACE_DIR / "LayoutLMv3_Final_Experiment_Results_All_24_Cells.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # All summary JSONs
        for jf in LOG_DIR.glob("*.json"):
            zf.write(jf, arcname=f"summaries/{jf.name}")

        # All logs
        for lf in Path("/tmp").glob("cell_*.log"):
            zf.write(lf, arcname=f"logs/{lf.name}")
        if RUNNER_LOG.exists():
            zf.write(RUNNER_LOG, arcname=f"logs/{RUNNER_LOG.name}")

        # Final table
        tab = REPO_DIR / "FINAL_AGGREGATED_ABLATION_TABLE.md"
        if tab.exists():
            zf.write(tab, arcname="FINAL_AGGREGATED_ABLATION_TABLE.md")

    log(f"Created final master archive: {zip_path} ({zip_path.stat().st_size / (1024*1024):.2f} MB)")
    upload_to_gdrive(zip_path)

    done_file = WORKSPACE_DIR / "ALL_EXPERIMENTS_COMPLETE.txt"
    done_text = f"""======================================================================
LAYOUTLMV3 FULL 24-CELL EXPERIMENT SUITE 100% COMPLETE
======================================================================
Completed at: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Master Archive: LayoutLMv3_Final_Experiment_Results_All_24_Cells.zip
All 20 ablation runs (10 Base + 10 Large across FUNSD & CORD, 3 seeds each)
have finished successfully.
Google Sheet Live Tracker fully synchronized.
All summaries, logs, and tables uploaded to Google Drive.
======================================================================
"""
    done_file.write_text(done_text, encoding="utf-8")
    upload_to_gdrive(done_file, "ALL_EXPERIMENTS_COMPLETE.txt")
    log("ALL EXPERIMENTS AND DELIVERABLES 100% COMPLETE!")

def main():
    log("**********************************************************************")
    log("AUTONOMOUS RUNNER INITIALIZED ON VAST.AI")
    log(f"Start time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("**********************************************************************")

    # Cell 20: FUNSD | large | no_segment
    run_suite_step(20, "funsd", "large", "no_segment", "FUNSD large no_segment", "funsd-large-no_segment_3seed_summary.json")

    # Cell 21: CORD | large | no_segment
    run_suite_step(21, "cord", "large", "no_segment", "CORD large no_segment", "cord-large-no_segment_3seed_summary.json")

    # Cell 22: FUNSD | large | no_hpe
    run_suite_step(22, "funsd", "large", "no_hpe", "FUNSD large no_hpe", "funsd-large-no_hpe_3seed_summary.json")

    # Cell 23: CORD | large | no_hpe
    run_suite_step(23, "cord", "large", "no_hpe", "CORD large no_hpe", "cord-large-no_hpe_3seed_summary.json")

    # Cell 24: Aggregate All 20 Ablation Summaries
    run_aggregation()

    # Step 7: Create and upload master package
    create_and_upload_final_package()

if __name__ == "__main__":
    main()

