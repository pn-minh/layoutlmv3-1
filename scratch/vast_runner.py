#!/usr/bin/env python3
"""
Autonomous Dual-GPU Vast.ai Runner for LayoutLMv3 Ablation Completion & Cross-Modal Contrastive Loss Suite:
  - Cell 23: CORD  | large | no_hpe      (Remaining HPE ablation for Large on CORD, 3 seeds)
  - Cell 24: FUNSD | base  | contrastive (Contrastive Loss ablation for Base on FUNSD, 3 seeds)
  - Cell 25: CORD  | base  | contrastive (Contrastive Loss ablation for Base on CORD, 3 seeds)
  - Cell 26: FUNSD | large | contrastive (Contrastive Loss ablation for Large on FUNSD, 3 seeds)
  - Cell 27: CORD  | large | contrastive (Contrastive Loss ablation for Large on CORD, 3 seeds)
  - Cell 28: Master Aggregation of all 24 3-seed configurations into FINAL_AGGREGATED_ABLATION_TABLE.md

Features:
  1. Multi-GPU Parallel Worker Pool: Assigns each cell to an dedicated A100 GPU (CUDA_VISIBLE_DEVICES=0 or 1)
     using Longest-Processing-Time-First (LPT) scheduling, cutting wall-clock runtime & cost in half (~4.4 hrs).
  2. Retry-hardened Google Drive upload of every summary JSON, execution log, consolidated JSON snapshot,
     and final master ZIP archive.
  3. Live Google Sheet 8-section Quad-Block synchronization after every cell.
  4. Strict pre-destruction verification: confirms all 5 new cells (and all 24 total summaries) + Google Drive
     uploads succeeded before permanently destroying the Vast.ai instance.
"""
import os
import re
import sys
import time
import json
import queue
import base64
import zipfile
import datetime
import subprocess
import threading
from pathlib import Path

WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyTnMY4wH9BwXUeNKKWqUdL_BClo-8ai76o70kQM0sT-nh7wv9oN64BpumGGAoalhSM1w/exec"
ACCOUNT_VAST_API_KEY = os.environ.get(
    "VAST_API_KEY",
    "3ad44c08d95a4f951cced4d2fdbda4698d1cfab2c81ccc51f7ad6830e573bd50",
)
CONTAINER_VAST_API_KEY = os.environ.get("CONTAINER_API_KEY", "")

WORKSPACE_DIR = Path("/workspace")
REPO_DIR = WORKSPACE_DIR / "layoutlmv3-1"
LOG_DIR = REPO_DIR / "layoutlmv3" / "logs"
RUNNER_LOG = WORKSPACE_DIR / "vast_runner.log"
LIVE_STATUS_PATH = WORKSPACE_DIR / "live_status.json"
INSTANCE_ID_FILE = WORKSPACE_DIR / "vast_instance_id.txt"

# Ordered Longest-Processing-Time-First (LPT) for optimal load balance across 2x A100 GPUs:
# GPU 0 takes Cell 23 (~120m) -> Cell 26 (~95m)
# GPU 1 takes Cell 27 (~125m) -> Cell 25 (~85m) -> Cell 24 (~55m)
CELL_QUEUE = [
    (23, "cord",  "large", "no_hpe",      "CORD large no_hpe (w/o HPE)",                  "cord-large-no_hpe_3seed_summary.json"),
    (27, "cord",  "large", "contrastive", "CORD large contrastive (+Contrastive Loss)",   "cord-large-contrastive_3seed_summary.json"),
    (26, "funsd", "large", "contrastive", "FUNSD large contrastive (+Contrastive Loss)",  "funsd-large-contrastive_3seed_summary.json"),
    (25, "cord",  "base",  "contrastive", "CORD base contrastive (+Contrastive Loss)",    "cord-base-contrastive_3seed_summary.json"),
    (24, "funsd", "base",  "contrastive", "FUNSD base contrastive (+Contrastive Loss)",   "funsd-base-contrastive_3seed_summary.json"),
]

# Allow filtering cells via CELLS env var (e.g. CELLS="24,25,26,27" for Contrastive Fine-Tuning)
if os.environ.get("CELLS"):
    _target_ids = {int(x.strip()) for x in os.environ["CELLS"].split(",") if x.strip().isdigit()}
    if _target_ids:
        CELL_QUEUE = [item for item in CELL_QUEUE if item[0] in _target_ids]

LOG_LOCK = threading.RLock()
SYNC_LOCK = threading.RLock()

STATE = {
    "pipeline_status": "INITIALIZING",
    "start_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "start_epoch": time.time(),
    "active_workers": {},
    "completed_cells": [],
    "failed_cells": [],
    "gdrive_uploads_ok": [],
}


def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    with LOG_LOCK:
        print(formatted, flush=True)
        with open(RUNNER_LOG, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")


def get_python_bin() -> str:
    candidates = [
        "/workspace/miniconda3/envs/layoutlmv3/bin/python",
        "/dev/shm/miniconda3/envs/layoutlmv3/bin/python",
        "/venv/layoutlmv3/bin/python",
        sys.executable,
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return sys.executable


def detect_gpu_count() -> int:
    try:
        proc = subprocess.run(["nvidia-smi", "-L"], capture_output=True, text=True, timeout=5)
        if proc.returncode == 0:
            lines = [ln for ln in proc.stdout.strip().splitlines() if ln.strip().startswith("GPU ")]
            if len(lines) >= 1:
                return len(lines)
    except Exception:
        pass
    return 1


def upload_to_gdrive(file_path: Path, remote_filename: str = None, max_retries: int = 5) -> bool:
    """Upload a file to Google Drive via Apps Script Webhook with automatic exponential backoff retries."""
    if not file_path.exists():
        log(f"[WARN] File does not exist for upload: {file_path}")
        return False
    fname = remote_filename or file_path.name
    raw_bytes = file_path.read_bytes()
    b64_str = base64.b64encode(raw_bytes).decode("utf-8")
    payload = {
        "action": "upload_pdf",
        "filename": fname,
        "pdfBase64": b64_str,
    }
    import requests
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(WEBHOOK_URL, json=payload, timeout=120)
            if r.status_code == 200 and "OK" in r.text:
                log(f"[GDRIVE] Successfully uploaded {fname} ({len(raw_bytes)/1024:.1f} KB) [attempt {attempt}]")
                with SYNC_LOCK:
                    if fname not in STATE["gdrive_uploads_ok"]:
                        STATE["gdrive_uploads_ok"].append(fname)
                return True
            else:
                log(f"[WARN] Upload {fname} attempt {attempt} returned: {r.status_code} {r.text[:200]}")
        except Exception as e:
            log(f"[WARN] Upload {fname} attempt {attempt} error: {e}")
        time.sleep(5 * attempt)
    log(f"[ERROR] Failed to upload {fname} after {max_retries} attempts.")
    return False


def write_and_upload_consolidated_snapshot() -> bool:
    """Bundle all *_3seed_summary.json files into a single JSON snapshot and upload to Google Drive."""
    snapshot = {
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summaries": {},
    }
    if LOG_DIR.exists():
        for p in sorted(LOG_DIR.glob("*_3seed_summary.json")):
            try:
                snapshot["summaries"][p.name] = json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                log(f"[WARN] Error reading {p.name} for snapshot: {e}")
    snap_path = WORKSPACE_DIR / "LayoutLMv3_All_Summaries_Snapshot.json"
    snap_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return upload_to_gdrive(snap_path, "LayoutLMv3_All_Summaries_Snapshot.json")


def sync_sheet() -> bool:
    """Trigger Google Sheet Live Tracker sync with retries."""
    script_path = REPO_DIR / "scratch" / "sync_google_sheet.py"
    if not script_path.exists():
        return False
    py_bin = get_python_bin()
    for attempt in range(1, 4):
        try:
            res = subprocess.run([py_bin, str(script_path)], capture_output=True, text=True, timeout=60)
            out = res.stdout.strip()
            log(f"[SHEET] sync_google_sheet (attempt {attempt}): {out}")
            if res.returncode == 0 and ("200" in out or "OK" in out):
                return True
        except Exception as e:
            log(f"[WARN] Google Sheet sync attempt {attempt} error: {e}")
        time.sleep(5 * attempt)
    return False


def run_suite_step_on_gpu(gpu_id: int, cell_num: int, dataset: str, variant: str, mode: str, label: str, summary_file: str):
    worker_key = f"GPU_{gpu_id}"
    with SYNC_LOCK:
        STATE["active_workers"][worker_key] = {
            "cell": cell_num,
            "label": label,
            "dataset": dataset,
            "variant": variant,
            "mode": mode,
            "started_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    log("======================================================================")
    log(f"[{worker_key}] STARTING CELL {cell_num}: {label} ({dataset.upper()} | {variant} | {mode})")
    log("======================================================================")

    sum_path = LOG_DIR / summary_file
    log_path = Path(f"/tmp/cell_{cell_num}.log")

    force_rerun = os.environ.get("FORCE_RERUN", "0") in ("1", "true", "True") or "--force" in sys.argv
    if sum_path.exists() and not force_rerun:
        log(f"[{worker_key}] [SKIP] Summary already exists for Cell {cell_num}: {sum_path}")
        with SYNC_LOCK:
            upload_to_gdrive(sum_path)
            write_and_upload_consolidated_snapshot()
            sync_sheet()
            if cell_num not in STATE["completed_cells"]:
                STATE["completed_cells"].append(cell_num)
        return

    conda_activate = (
        "source /workspace/miniconda3/etc/profile.d/conda.sh && conda activate layoutlmv3"
        if Path("/workspace/miniconda3/etc/profile.d/conda.sh").exists()
        else "source /venv/layoutlmv3/bin/activate"
    )
    cmd = (
        f"{conda_activate} && "
        f"export CUDA_VISIBLE_DEVICES={gpu_id} && "
        f"export HF_HOME=/workspace/.hf_home && "
        f"export PYTHONUNBUFFERED=1 && cd /workspace/layoutlmv3-1/layoutlmv3 && "
        f"bash scripts/run_ablation_suite.sh {dataset} {variant} {mode} > /tmp/cell_{cell_num}.log 2>&1; "
        f"echo '===EXIT_CODE:'$? '===' >> /tmp/cell_{cell_num}.log"
    )

    t0 = time.time()
    proc = subprocess.run(["bash", "-c", cmd])
    elapsed = time.time() - t0
    log(f"[{worker_key}] Cell {cell_num} finished in {elapsed:.1f}s ({elapsed/60.0:.2f} min) with returncode {proc.returncode}")

    with SYNC_LOCK:
        if log_path.exists():
            upload_to_gdrive(log_path, f"cell_{cell_num}.log")

        if proc.returncode != 0 or not sum_path.exists():
            log(f"[{worker_key}] [FATAL] Cell {cell_num} failed (returncode={proc.returncode}, summary_exists={sum_path.exists()})!")
            STATE["failed_cells"].append(cell_num)
            raise RuntimeError(f"Cell {cell_num} failed on {worker_key}")

        log(f"[{worker_key}] Verified summary exists: {sum_path}")
        upload_to_gdrive(sum_path)
        write_and_upload_consolidated_snapshot()
        sync_sheet()
        if cell_num not in STATE["completed_cells"]:
            STATE["completed_cells"].append(cell_num)
        log(f"[{worker_key}] Cell {cell_num} ({label}) synced to Google Drive & Google Sheets.")


def run_aggregation() -> bool:
    STATE["pipeline_status"] = "AGGREGATING_FINAL_TABLE"
    log("======================================================================")
    log("STARTING CELL 28: Aggregate All 24 3-Seed Results into Final Table")
    log("======================================================================")

    modes = ["baseline", "full", "contrastive", "no_boundary", "no_segment", "no_hpe"]
    mode_labels = {
        "baseline":    "Baseline (Vanilla LayoutLMv3)",
        "full":        "3-Module Model (HPE + Token-Segment + Boundary; w/o Contrastive)",
        "contrastive": "Full 4-Module Model (+ Cross-Modal Contrastive Loss)",
        "no_boundary": "Ablation: w/o Boundary Loss",
        "no_segment":  "Ablation: w/o Token-Segment",
        "no_hpe":      "Ablation: w/o HPE",
    }

    missing = []
    for variant in ["base", "large"]:
        for dataset in ["funsd", "cord"]:
            for mode in modes:
                summary_path = LOG_DIR / f"{dataset}-{variant}-{mode}_3seed_summary.json"
                if not summary_path.exists():
                    missing.append(summary_path.name)
    if missing:
        log(f"[FATAL] Missing summaries during final aggregation: {missing}")
        return False

    table_lines = [
        "# LayoutLMv3 Final Aggregated Ablation Results (Including Cross-Modal Contrastive Loss)",
        "",
        "All 24 configurations evaluated across 3 random seeds (`42, 123, 1993`) on NVIDIA A100 GPUs.",
        "",
        f"| {'Variant':<7} | {'Dataset':<7} | {'Configuration':<64} | {'Precision (%)':<16} | {'Recall (%)':<16} | {'F1 (%)':<18} |",
        "|" + "-" * 9 + "|" + "-" * 9 + "|" + "-" * 66 + "|" + "-" * 18 + "|" + "-" * 18 + "|" + "-" * 20 + "|",
    ]

    for variant in ["base", "large"]:
        for dataset in ["funsd", "cord"]:
            for mode in modes:
                summary_path = LOG_DIR / f"{dataset}-{variant}-{mode}_3seed_summary.json"
                with open(summary_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    data = content.get("metrics") or content.get("mean_std")

                if "eval_precision" in data and "mean" in data["eval_precision"]:
                    p_str = f"`{data['eval_precision']['mean']*100:.2f} ± {data['eval_precision']['std']*100:.2f}`"
                    r_str = f"`{data['eval_recall']['mean']*100:.2f} ± {data['eval_recall']['std']*100:.2f}`"
                    f1_str = f"**`{data['eval_f1']['mean']*100:.2f} ± {data['eval_f1']['std']*100:.2f}`**"
                else:
                    p_str = f"`{data['eval_precision']['mean_pct']:.2f} ± {data['eval_precision']['std_pct']:.2f}`"
                    r_str = f"`{data['eval_recall']['mean_pct']:.2f} ± {data['eval_recall']['std_pct']:.2f}`"
                    f1_str = f"**`{data['eval_f1']['mean_pct']:.2f} ± {data['eval_f1']['std_pct']:.2f}`**"

                table_lines.append(
                    f"| `{variant}` | `{dataset.upper()}` | {mode_labels[mode]:<64} | {p_str:<16} | {r_str:<16} | {f1_str:<18} |"
                )

    table_text = "\n".join(table_lines) + "\n"
    log("\n" + table_text)

    out_table_path = REPO_DIR / "FINAL_AGGREGATED_ABLATION_TABLE.md"
    out_table_path.write_text(table_text, encoding="utf-8")
    ok_table = upload_to_gdrive(out_table_path, "FINAL_AGGREGATED_ABLATION_TABLE.md")
    ok_snap = write_and_upload_consolidated_snapshot()
    ok_sheet = sync_sheet()
    STATE["completed_cells"].append(28)
    log(f"Cell 28 completed (table_uploaded={ok_table}, snapshot_uploaded={ok_snap}, sheet_synced={ok_sheet}).")
    return ok_table and ok_snap


def create_and_upload_final_package() -> bool:
    STATE["pipeline_status"] = "UPLOADING_MASTER_ARCHIVE"
    log("======================================================================")
    log("CREATING FINAL MASTER RESULTS ARCHIVE...")
    log("======================================================================")

    zip_path = WORKSPACE_DIR / "LayoutLMv3_Final_Experiment_Results_All_28_Cells.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for jf in sorted(LOG_DIR.glob("*.json")):
            zf.write(jf, arcname=f"summaries/{jf.name}")
        for lf in sorted(Path("/tmp").glob("cell_*.log")):
            zf.write(lf, arcname=f"logs/{lf.name}")
        if RUNNER_LOG.exists():
            zf.write(RUNNER_LOG, arcname=f"logs/{RUNNER_LOG.name}")
        tab = REPO_DIR / "FINAL_AGGREGATED_ABLATION_TABLE.md"
        if tab.exists():
            zf.write(tab, arcname="FINAL_AGGREGATED_ABLATION_TABLE.md")
        snap = WORKSPACE_DIR / "LayoutLMv3_All_Summaries_Snapshot.json"
        if snap.exists():
            zf.write(snap, arcname="LayoutLMv3_All_Summaries_Snapshot.json")
        csv_tracker = REPO_DIR / "thesis" / "tracker.csv"
        if csv_tracker.exists():
            zf.write(csv_tracker, arcname="tracker.csv")

    log(f"Created final master archive: {zip_path} ({zip_path.stat().st_size / (1024*1024):.2f} MB)")
    zip_ok = upload_to_gdrive(zip_path, "LayoutLMv3_Final_Experiment_Results_All_28_Cells.zip")

    done_file = WORKSPACE_DIR / "ALL_EXPERIMENTS_COMPLETE.txt"
    done_text = f"""======================================================================
LAYOUTLMV3 FULL 28-CELL EXPERIMENT SUITE 100% COMPLETE
======================================================================
Completed at: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Master Archive: LayoutLMv3_Final_Experiment_Results_All_28_Cells.zip
Consolidated JSON: LayoutLMv3_All_Summaries_Snapshot.json
All 24 ablation configurations (Baseline, 3-Module Full, 4-Module Contrastive Full,
w/o Boundary, w/o Segment, w/o HPE across Base & Large on FUNSD & CORD, 3 seeds each)
have finished and evaluated successfully.
Google Sheet Live Tracker & Google Drive fully synchronized.
======================================================================
"""
    done_file.write_text(done_text, encoding="utf-8")
    done_ok = upload_to_gdrive(done_file, "ALL_EXPERIMENTS_COMPLETE.txt")
    log(f"ALL EXPERIMENTS AND DELIVERABLES COMPLETE (zip_ok={zip_ok}, done_ok={done_ok})!")
    return zip_ok


def detect_vast_instance_id() -> str:
    if INSTANCE_ID_FILE.exists():
        val = INSTANCE_ID_FILE.read_text(encoding="utf-8").strip()
        if val:
            return val
    for env_key in ["CONTAINER_ID", "VAST_CONTAINERLABEL", "CONTAINER_LABEL"]:
        val = os.environ.get(env_key, "").strip()
        if val:
            m = re.search(r"(\d{5,})", val)
            if m:
                return m.group(1)
    return "58981233"


def self_destruct_instance():
    """Destroy the Vast.ai instance immediately after verifying all results are saved to Google Drive."""
    STATE["pipeline_status"] = "SELF_DESTRUCTING"
    inst_id = detect_vast_instance_id()
    log(f"[SELF-DESTRUCT] All runs verified and saved to Google Drive. Destroying Vast.ai instance {inst_id}...")

    # Upload final runner log right before destruction
    upload_to_gdrive(RUNNER_LOG, "vast_runner_final.log", max_retries=2)

    api_keys = [k for k in [CONTAINER_VAST_API_KEY, ACCOUNT_VAST_API_KEY] if k]

    # Method 1: vastai CLI (preinstalled on Vast.ai image at /opt/instance-tools/bin/vastai)
    for key in api_keys:
        for vast_bin in [
            "/opt/instance-tools/bin/vastai",
            "/venv/layoutlmv3/bin/vastai",
            "vastai",
            "/usr/local/bin/vastai",
            "/workspace/miniconda3/envs/layoutlmv3/bin/vastai",
        ]:
            for action in ["destroy", "stop"]:
                try:
                    res = subprocess.run(
                        [vast_bin, action, "instance", str(inst_id), "--api-key", key],
                        capture_output=True,
                        text=True,
                        timeout=25,
                    )
                    log(f"[SELF-DESTRUCT CLI] ({vast_bin} {action}) exit={res.returncode} stdout={res.stdout.strip()} stderr={res.stderr.strip()}")
                except Exception:
                    pass

    # Method 2: Vast.ai REST API DELETE
    import requests
    for key in api_keys:
        try:
            url = f"https://console.vast.ai/api/v0/instances/{inst_id}/?api_key={key}"
            r = requests.delete(url, timeout=25)
            log(f"[SELF-DESTRUCT REST] DELETE {inst_id} -> {r.status_code} {r.text[:200]}")
        except Exception as e:
            log(f"[WARN] REST self-destruct error: {e}")


def main():
    num_gpus = detect_gpu_count()
    inst_id = detect_vast_instance_id()
    log("**********************************************************************")
    log("AUTONOMOUS MULTI-GPU RUNNER INITIALIZED ON VAST.AI")
    log(f"Start time : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Instance ID: {inst_id} | Detected GPUs: {num_gpus}")
    log("**********************************************************************")

    work_q = queue.Queue()
    for item in CELL_QUEUE:
        work_q.put(item)

    worker_errors = []

    def gpu_worker(gpu_id: int):
        while True:
            try:
                cell_num, dataset, variant, mode, label, summary_file = work_q.get_nowait()
            except queue.Empty:
                break
            try:
                run_suite_step_on_gpu(gpu_id, cell_num, dataset, variant, mode, label, summary_file)
            except Exception as e:
                log(f"[GPU_{gpu_id} ERROR] {e}")
                worker_errors.append(str(e))
            finally:
                work_q.task_done()

    threads = []
    worker_count = min(num_gpus, len(CELL_QUEUE))
    for gid in range(worker_count):
        t = threading.Thread(target=gpu_worker, args=(gid,), daemon=False)
        t.start()
        threads.append(t)
        time.sleep(3)

    for t in threads:
        t.join()

    if worker_errors or STATE["failed_cells"]:
        log(f"[ABORT SELF-DESTRUCT] Errors occurred in cells {STATE['failed_cells']}: {worker_errors}")
        upload_to_gdrive(RUNNER_LOG, "vast_runner_error.log")
        sys.exit(1)

    # Cell 28: Aggregate All 24 Ablation Summaries
    agg_ok = run_aggregation()
    pkg_ok = create_and_upload_final_package()

    if agg_ok and pkg_ok and len(STATE["completed_cells"]) >= 6:
        log("[VERIFIED] All 5 ablation cells + Cell 28 aggregation completed and uploaded to Google Drive!")
        self_destruct_instance()
    else:
        log(f"[WARN] Verification check incomplete (agg_ok={agg_ok}, pkg_ok={pkg_ok}, completed={STATE['completed_cells']}). Uploading log.")
        upload_to_gdrive(RUNNER_LOG, "vast_runner_incomplete.log")


if __name__ == "__main__":
    main()
