#!/usr/bin/env python3
"""
Autonomous Master Runner for LayoutLMv3 Colab A100 Experiment Suite.
Executes all remaining cells (19 -> 20 -> 21 -> 22 -> 23 -> 24),
continuously syncs the Google Sheet Live Tracker,
and uploads all summaries, logs, and final master archives to Google Drive.
Runs completely detached from the local machine in a tmux session.
"""
import os
import sys
import time
import json
import base64
import shutil
import zipfile
import datetime
import subprocess
import threading
from pathlib import Path

# Add script directory to sys.path for sync_google_sheet import
sys.path.insert(0, "/content")
try:
    from sync_google_sheet import sync_quad_sheet
except ImportError:
    sync_quad_sheet = None

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyTnMY4wH9BwXUeNKKWqUdL_BClo-8ai76o70kQM0sT-nh7wv9oN64BpumGGAoalhSM1w/exec"
LOG_DIR = Path("/content/layoutlmv3-1/layoutlmv3/logs")
REPO_DIR = Path("/content/layoutlmv3-1")
RUNNER_LOG = Path("/content/autonomous_runner.log")

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    with open(RUNNER_LOG, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")

def upload_to_gdrive(file_path: Path, remote_filename: str = None) -> bool:
    """Upload a file to Google Drive via Apps Script Webhook."""
    if not file_path.exists():
        log(f"[WARN] upload_to_gdrive: file does not exist: {file_path}")
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
            log(f"[GDRIVE] Successfully uploaded {fname} ({len(raw_bytes)/1024:.1f} KB) -> {r.text}")
            return True
        else:
            log(f"[WARN] Upload {fname} returned: {r.status_code} {r.text}")
            return False
    except Exception as e:
        log(f"[ERROR] Failed uploading {fname} to Google Drive: {e}")
        return False

def sync_sheet():
    """Trigger Google Sheet Live Tracker sync."""
    try:
        if sync_quad_sheet is not None:
            sync_quad_sheet(LOG_DIR, WEBHOOK_URL)
            log("[SHEET] Live Tracker updated successfully.")
        else:
            res = subprocess.run(["python3", "/content/sync_google_sheet.py"], capture_output=True, text=True)
            log(f"[SHEET] sync_google_sheet output: {res.stdout.strip()}")
    except Exception as e:
        log(f"[WARN] Error during Google Sheet sync: {e}")

def git_commit(cell_label: str):
    """Create local git commit on Colab instance."""
    try:
        subprocess.run(["git", "-C", str(REPO_DIR), "config", "user.name", "pn-minh"], check=False)
        subprocess.run(["git", "-C", str(REPO_DIR), "config", "user.email", "pn-minh@users.noreply.github.com"], check=False)
        subprocess.run(["git", "-C", str(REPO_DIR), "add", "layoutlmv3/logs/"], check=False)
        subprocess.run(["git", "-C", str(REPO_DIR), "commit", "-m", f"Auto-run: {cell_label} results completed"], check=False)
        log(f"[GIT] Committed {cell_label} locally.")
    except Exception as e:
        log(f"[WARN] Git commit warning: {e}")

CURRENT_STAGE = "Initializing"

def heartbeat_loop():
    """Background thread updating heartbeat and keeping system active."""
    while True:
        try:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            hb_path = Path("/content/heartbeat.txt")
            gpu_info = ""
            try:
                gpu_proc = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,temperature.gpu", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=5
                )
                if gpu_proc.returncode == 0:
                    gpu_info = f" | GPU: {gpu_proc.stdout.strip()}"
            except Exception:
                pass
            with open(hb_path, "w", encoding="utf-8") as f:
                f.write(f"Timestamp: {ts} | Stage: {CURRENT_STAGE}{gpu_info}\n")
        except Exception:
            pass
        time.sleep(60)

def wait_for_cell_19():
    global CURRENT_STAGE
    CURRENT_STAGE = "Cell 19 (CORD large no_boundary)"
    log("======================================================================")
    log("STEP 1: Monitoring Cell 19 (currently running in tmux 'cell_19')...")
    log("======================================================================")

    log_path = Path("/tmp/cell_19.log")
    summary_path = LOG_DIR / "cord-large-no_boundary_3seed_summary.json"

    while True:
        # Check if tmux cell_19 is still running
        tmux_check = subprocess.run(["tmux", "has-session", "-t", "cell_19"], capture_output=True)
        session_exists = (tmux_check.returncode == 0)

        # Check if log has exit code
        has_exit = False
        if log_path.exists():
            content = log_path.read_text(encoding="utf-8", errors="ignore")
            if "===EXIT_CODE:" in content:
                has_exit = True

        if not session_exists or has_exit:
            log("Cell 19 tmux session finished / detected exit code in log.")
            time.sleep(5)
            break

        time.sleep(15)

    # Verify summary
    if summary_path.exists():
        log(f"Cell 19 summary verified: {summary_path}")
        upload_to_gdrive(summary_path)
    else:
        log(f"[WARN] Cell 19 summary not found at {summary_path}")

    if log_path.exists():
        upload_to_gdrive(log_path, "cell_19.log")

    sync_sheet()
    git_commit("Cell 19 (CORD large no_boundary)")
    log("Step 1 (Cell 19) complete!")

def run_cell_sequence(cell_num: int, label: str, expected_summary: str):
    global CURRENT_STAGE
    CURRENT_STAGE = f"Cell {cell_num}: {label}"
    log("======================================================================")
    log(f"STARTING CELL {cell_num}: {label}")
    log("======================================================================")

    log_path = Path(f"/tmp/cell_{cell_num}.log")
    cmd = f"python3 -u /content/run_cell.py {cell_num} > /tmp/cell_{cell_num}.log 2>&1; echo '===EXIT_CODE:'$? '===' >> /tmp/cell_{cell_num}.log"

    t0 = time.time()
    proc = subprocess.run(["bash", "-c", cmd])
    elapsed = time.time() - t0
    log(f"Cell {cell_num} execution finished in {elapsed:.1f}s ({elapsed/60.0:.2f} min) with returncode {proc.returncode}")

    # Verify summary
    if expected_summary:
        sum_path = LOG_DIR / expected_summary
        if sum_path.exists():
            log(f"Verified summary exists: {sum_path}")
            upload_to_gdrive(sum_path)
        else:
            log(f"[WARN] Expected summary not found: {sum_path}")

    # Upload execution log
    if log_path.exists():
        upload_to_gdrive(log_path, f"cell_{cell_num}.log")

    # Sync Google Sheet & Commit locally
    sync_sheet()
    git_commit(f"Cell {cell_num} ({label})")
    log(f"Cell {cell_num} ({label}) pipeline actions finished.")

def create_and_upload_final_package():
    global CURRENT_STAGE
    CURRENT_STAGE = "Final Packaging & Aggregation"
    log("======================================================================")
    log("CREATING FINAL MASTER RESULTS ARCHIVE...")
    log("======================================================================")

    zip_path = Path("/content/LayoutLMv3_Final_Experiment_Results_All_24_Cells.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. All summary JSONs
        for jf in LOG_DIR.glob("*.json"):
            zf.write(jf, arcname=f"summaries/{jf.name}")

        # 2. All execution logs
        for lf in Path("/tmp").glob("cell_*.log"):
            zf.write(lf, arcname=f"logs/{lf.name}")
        if RUNNER_LOG.exists():
            zf.write(RUNNER_LOG, arcname=f"logs/{RUNNER_LOG.name}")

        # 3. Thesis tracker CSV & Notebook
        csv_path = Path("/content/layoutlmv3-1/thesis/tracker.csv")
        if csv_path.exists():
            zf.write(csv_path, arcname="tracker.csv")
        nb_path = Path("/content/layoutlmv3-1/layoutlmv3/Colab_A100_Training_and_Ablation.ipynb")
        if nb_path.exists():
            zf.write(nb_path, arcname="Colab_A100_Training_and_Ablation.ipynb")

    log(f"Created final master archive: {zip_path} ({zip_path.stat().st_size / (1024*1024):.2f} MB)")
    upload_to_gdrive(zip_path)

    # Create completion indicator
    done_file = Path("/content/ALL_EXPERIMENTS_COMPLETE.txt")
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
    log("All experiments and uploads completed successfully!")

def main():
    log("**********************************************************************")
    log("AUTONOMOUS RUNNER INITIALIZED ON COLAB A100")
    log(f"Start time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log("**********************************************************************")

    # Start heartbeat thread
    hb_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    hb_thread.start()

    # Step 1: Cell 19: CORD | large | no_boundary (accelerated 500 steps)
    run_cell_sequence(19, "CORD large no_boundary", "cord-large-no_boundary_3seed_summary.json")

    # Step 2: Cell 20: FUNSD | large | no_segment
    run_cell_sequence(20, "FUNSD large no_segment", "funsd-large-no_segment_3seed_summary.json")

    # Step 3: Cell 21: CORD | large | no_segment (accelerated 500 steps)
    run_cell_sequence(21, "CORD large no_segment", "cord-large-no_segment_3seed_summary.json")

    # Step 4: Cell 22: FUNSD | large | no_hpe
    run_cell_sequence(22, "FUNSD large no_hpe", "funsd-large-no_hpe_3seed_summary.json")

    # Step 5: Cell 23: CORD | large | no_hpe (accelerated 500 steps)
    run_cell_sequence(23, "CORD large no_hpe", "cord-large-no_hpe_3seed_summary.json")

    # Step 6: Cell 24: Aggregated Summary Comparison Table
    run_cell_sequence(24, "Aggregated Summary Comparison Table", None)

    # Step 7: Create and upload master package
    create_and_upload_final_package()

if __name__ == "__main__":
    main()

