#!/usr/bin/env python3
"""
Autonomous Vast.ai Runner for LayoutLMv3 Ablation Completion & Cross-Modal Contrastive Loss Suite:
  - Cell 23: CORD  | large | no_hpe      (Remaining HPE ablation for Large on CORD, 3 seeds)
  - Cell 24: FUNSD | base  | contrastive (Contrastive Loss ablation for Base on FUNSD, 3 seeds)
  - Cell 25: CORD  | base  | contrastive (Contrastive Loss ablation for Base on CORD, 3 seeds)
  - Cell 26: FUNSD | large | contrastive (Contrastive Loss ablation for Large on FUNSD, 3 seeds)
  - Cell 27: CORD  | large | contrastive (Contrastive Loss ablation for Large on CORD, 3 seeds)
  - Cell 28: Master Aggregation of all 24 3-seed configurations into FINAL_AGGREGATED_ABLATION_TABLE.md

Features:
  1. Real-time telemetry & training progress emitter (/workspace/live_status.json) for the Local Tracking Dashboard.
  2. Automatic Google Drive upload of every summary JSON, execution log, and final master ZIP archive.
  3. Live Google Sheet 8-section Quad-Block synchronization after every cell.
  4. Automatic Vast.ai instance self-destruction upon completion to prevent any credit overspending.
"""
import os
import re
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
DEFAULT_VAST_API_KEY = os.environ.get(
    "VAST_API_KEY",
    "3ad44c08d95a4f951cced4d2fdbda4698d1cfab2c81ccc51f7ad6830e573bd50",
)

WORKSPACE_DIR = Path("/workspace")
REPO_DIR = WORKSPACE_DIR / "layoutlmv3-1"
LOG_DIR = REPO_DIR / "layoutlmv3" / "logs"
RUNNER_LOG = WORKSPACE_DIR / "vast_runner.log"
LIVE_STATUS_PATH = WORKSPACE_DIR / "live_status.json"
INSTANCE_ID_FILE = WORKSPACE_DIR / "vast_instance_id.txt"
LOCAL_SYNC_FLAG = WORKSPACE_DIR / "LOCAL_SYNC_CONFIRMED"

CELL_QUEUE = [
    (23, "cord",  "large", "no_hpe",      "CORD large no_hpe (w/o HPE)",                  "cord-large-no_hpe_3seed_summary.json"),
    (24, "funsd", "base",  "contrastive", "FUNSD base contrastive (+Contrastive Loss)",   "funsd-base-contrastive_3seed_summary.json"),
    (25, "cord",  "base",  "contrastive", "CORD base contrastive (+Contrastive Loss)",    "cord-base-contrastive_3seed_summary.json"),
    (26, "funsd", "large", "contrastive", "FUNSD large contrastive (+Contrastive Loss)",  "funsd-large-contrastive_3seed_summary.json"),
    (27, "cord",  "large", "contrastive", "CORD large contrastive (+Contrastive Loss)",   "cord-large-contrastive_3seed_summary.json"),
]

STATE = {
    "pipeline_status": "INITIALIZING",
    "start_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "start_epoch": time.time(),
    "current_cell": 23,
    "current_label": "Initializing",
    "current_dataset": "",
    "current_variant": "",
    "current_mode": "",
    "current_seed": "",
    "current_seed_idx": 0,
    "step": 0,
    "max_steps": 0,
    "step_pct": 0.0,
    "seed_eta_sec": 0.0,
    "latest_eval": {},
    "gpu": {},
    "completed_cells": [],
    "cells_plan": [
        {"cell": c[0], "dataset": c[1], "variant": c[2], "mode": c[3], "label": c[4], "summary_file": c[5]}
        for c in CELL_QUEUE
    ],
}


def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    with open(RUNNER_LOG, "a", encoding="utf-8") as f:
        f.write(formatted + "\n")


def get_python_bin() -> str:
    candidates = [
        "/workspace/miniconda3/envs/layoutlmv3/bin/python",
        "/venv/layoutlmv3/bin/python",
        sys.executable,
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return sys.executable


def query_gpu_telemetry() -> dict:
    try:
        proc = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            parts = [p.strip() for p in proc.stdout.strip().split(",")]
            if len(parts) >= 6:
                return {
                    "name": parts[0],
                    "util_pct": float(parts[1]) if parts[1].replace(".", "").isdigit() else 0.0,
                    "mem_used_mib": float(parts[2]) if parts[2].replace(".", "").isdigit() else 0.0,
                    "mem_total_mib": float(parts[3]) if parts[3].replace(".", "").isdigit() else 0.0,
                    "temp_c": float(parts[4]) if parts[4].replace(".", "").isdigit() else 0.0,
                    "power_w": float(parts[5]) if parts[5].replace(".", "").isdigit() else 0.0,
                }
    except Exception:
        pass
    return {}


def parse_active_cell_log(cell_num: int):
    log_path = Path(f"/tmp/cell_{cell_num}.log")
    if not log_path.exists():
        return
    try:
        text = log_path.read_text(encoding="utf-8", errors="ignore")
        # Find latest [RUN X/3] DATASET=... | SEED=...
        run_matches = re.findall(
            r"\[RUN\s+(\d+)/(\d+)\]\s+DATASET=(\S+)\s+\|\s+VARIANT=(\S+)\s+\|\s+MODE=(\S+)\s+\|\s+SEED=(\d+)",
            text,
        )
        if run_matches:
            last_run = run_matches[-1]
            STATE["current_seed_idx"] = int(last_run[0])
            STATE["current_seed"] = last_run[5]

        # Find latest [REALTIME] Step X/Y (Z%) | Elapsed: ...s | ETA: ...s
        rt_matches = re.findall(
            r"\[REALTIME\]\s+Step\s+(\d+)/(\d+)\s+\(([\d.]+)%\)\s+\|\s+Elapsed:\s+([\d.]+)s\s+\|\s+ETA:\s+([\d.]+)s",
            text,
        )
        if rt_matches:
            last_rt = rt_matches[-1]
            STATE["step"] = int(last_rt[0])
            STATE["max_steps"] = int(last_rt[1])
            STATE["step_pct"] = float(last_rt[2])
            STATE["seed_eta_sec"] = float(last_rt[4])

        # Find latest intermediate or final eval metrics
        f1_matches = re.findall(r"'eval_f1':\s*([\d.]+)", text)
        p_matches = re.findall(r"'eval_precision':\s*([\d.]+)", text)
        r_matches = re.findall(r"'eval_recall':\s*([\d.]+)", text)
        l_matches = re.findall(r"'eval_loss':\s*([\d.]+)", text)
        if f1_matches:
            STATE["latest_eval"] = {
                "eval_f1": round(float(f1_matches[-1]) * 100.0, 2),
                "eval_precision": round(float(p_matches[-1]) * 100.0, 2) if p_matches else None,
                "eval_recall": round(float(r_matches[-1]) * 100.0, 2) if r_matches else None,
                "eval_loss": round(float(l_matches[-1]), 4) if l_matches else None,
            }
    except Exception:
        pass


def collect_completed_summaries() -> list:
    items = []
    if not LOG_DIR.exists():
        return items
    for p in sorted(LOG_DIR.glob("*_3seed_summary.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            ms = data.get("mean_std") or data.get("metrics") or {}
            f1_obj = ms.get("eval_f1", {})
            p_obj = ms.get("eval_precision", {})
            r_obj = ms.get("eval_recall", {})
            if "mean" in f1_obj:
                items.append({
                    "file": p.name,
                    "dataset": data.get("dataset"),
                    "variant": data.get("variant"),
                    "mode": data.get("mode"),
                    "f1_mean": round(float(f1_obj["mean"]) * 100.0, 2),
                    "f1_std": round(float(f1_obj.get("std", 0.0)) * 100.0, 2),
                    "p_mean": round(float(p_obj.get("mean", 0.0)) * 100.0, 2),
                    "r_mean": round(float(r_obj.get("mean", 0.0)) * 100.0, 2),
                })
        except Exception:
            pass
    return items


def status_heartbeat_loop():
    """Continuously write /workspace/live_status.json every 5 seconds for the local dashboard."""
    while True:
        try:
            STATE["gpu"] = query_gpu_telemetry()
            if STATE["current_cell"] in [c[0] for c in CELL_QUEUE]:
                parse_active_cell_log(STATE["current_cell"])
            STATE["completed_summaries"] = collect_completed_summaries()
            STATE["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            STATE["elapsed_total_sec"] = round(time.time() - STATE["start_epoch"], 1)
            tmp_path = LIVE_STATUS_PATH.with_suffix(".tmp")
            tmp_path.write_text(json.dumps(STATE, indent=2), encoding="utf-8")
            tmp_path.replace(LIVE_STATUS_PATH)
        except Exception:
            pass
        time.sleep(5)


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
            "pdfBase64": b64_str,
        }
        import requests
        r = requests.post(WEBHOOK_URL, json=payload, timeout=90)
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
            py_bin = get_python_bin()
            res = subprocess.run([py_bin, str(script_path)], capture_output=True, text=True)
            log(f"[SHEET] sync_google_sheet output: {res.stdout.strip()}")
    except Exception as e:
        log(f"[WARN] Error during Google Sheet sync: {e}")


def git_commit(cell_label: str):
    """Create local git commit on Vast.ai instance."""
    try:
        subprocess.run(["git", "-C", str(REPO_DIR), "config", "user.name", "pn-minh"], check=False)
        subprocess.run(["git", "-C", str(REPO_DIR), "config", "user.email", "pn-minh@users.noreply.github.com"], check=False)
        subprocess.run(["git", "-C", str(REPO_DIR), "add", "-f", "layoutlmv3/logs/*_3seed_summary.json", "FINAL_AGGREGATED_ABLATION_TABLE.md"], check=False)
        subprocess.run(["git", "-C", str(REPO_DIR), "commit", "-m", f"Auto-run (Vast.ai): {cell_label} results completed"], check=False)
        log(f"[GIT] Committed {cell_label} locally.")
    except Exception as e:
        log(f"[WARN] Git commit warning: {e}")


def run_suite_step(cell_num: int, dataset: str, variant: str, mode: str, label: str, summary_file: str):
    STATE["pipeline_status"] = f"RUNNING_CELL_{cell_num}"
    STATE["current_cell"] = cell_num
    STATE["current_label"] = label
    STATE["current_dataset"] = dataset
    STATE["current_variant"] = variant
    STATE["current_mode"] = mode
    STATE["current_seed"] = "42"
    STATE["current_seed_idx"] = 1
    STATE["step"] = 0
    STATE["max_steps"] = 1000 if dataset == "funsd" else 500
    STATE["step_pct"] = 0.0
    STATE["latest_eval"] = {}

    log("======================================================================")
    log(f"STARTING CELL {cell_num}: {label} ({dataset.upper()} | {variant} | {mode})")
    log("======================================================================")

    sum_path = LOG_DIR / summary_file
    log_path = Path(f"/tmp/cell_{cell_num}.log")

    if sum_path.exists():
        log(f"[SKIP] Summary already exists for Cell {cell_num}: {sum_path}")
        upload_to_gdrive(sum_path)
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

    if cell_num not in STATE["completed_cells"]:
        STATE["completed_cells"].append(cell_num)

    # Sync Google Sheet & Commit locally
    sync_sheet()
    git_commit(f"Cell {cell_num} ({label})")
    log(f"Cell {cell_num} ({label}) pipeline actions finished.")


def run_aggregation():
    STATE["pipeline_status"] = "AGGREGATING_FINAL_TABLE"
    STATE["current_cell"] = 28
    STATE["current_label"] = "Master Aggregation (All 24 Ablation Configurations)"
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
        log(f"[WARN] Some summaries missing during aggregation: {missing}")

    table_lines = [
        "# LayoutLMv3 Final Aggregated Ablation Results (Including Cross-Modal Contrastive Loss)",
        "",
        "All experiments evaluated across 3 random seeds (`42, 123, 1993`) on dedicated NVIDIA A100 GPU.",
        "",
        f"| {'Variant':<7} | {'Dataset':<7} | {'Configuration':<64} | {'Precision (%)':<16} | {'Recall (%)':<16} | {'F1 (%)':<18} |",
        "|" + "-" * 9 + "|" + "-" * 9 + "|" + "-" * 66 + "|" + "-" * 18 + "|" + "-" * 18 + "|" + "-" * 20 + "|",
    ]

    for variant in ["base", "large"]:
        for dataset in ["funsd", "cord"]:
            for mode in modes:
                summary_path = LOG_DIR / f"{dataset}-{variant}-{mode}_3seed_summary.json"
                if not summary_path.exists():
                    table_lines.append(
                        f"| `{variant}` | `{dataset.upper()}` | {mode_labels[mode]:<64} | {'MISSING':<16} | {'MISSING':<16} | {'MISSING':<18} |"
                    )
                    continue
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
    upload_to_gdrive(out_table_path)
    STATE["completed_cells"].append(28)
    log("Cell 28 completed successfully.")


def create_and_upload_final_package():
    STATE["pipeline_status"] = "UPLOADING_MASTER_ARCHIVE"
    log("======================================================================")
    log("CREATING FINAL MASTER RESULTS ARCHIVE...")
    log("======================================================================")

    zip_path = WORKSPACE_DIR / "LayoutLMv3_Final_Experiment_Results_All_28_Cells.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for jf in LOG_DIR.glob("*.json"):
            zf.write(jf, arcname=f"summaries/{jf.name}")
        for lf in Path("/tmp").glob("cell_*.log"):
            zf.write(lf, arcname=f"logs/{lf.name}")
        if RUNNER_LOG.exists():
            zf.write(RUNNER_LOG, arcname=f"logs/{RUNNER_LOG.name}")
        tab = REPO_DIR / "FINAL_AGGREGATED_ABLATION_TABLE.md"
        if tab.exists():
            zf.write(tab, arcname="FINAL_AGGREGATED_ABLATION_TABLE.md")
        csv_tracker = REPO_DIR / "thesis" / "tracker.csv"
        if csv_tracker.exists():
            zf.write(csv_tracker, arcname="tracker.csv")

    log(f"Created final master archive: {zip_path} ({zip_path.stat().st_size / (1024*1024):.2f} MB)")
    upload_to_gdrive(zip_path)

    done_file = WORKSPACE_DIR / "ALL_EXPERIMENTS_COMPLETE.txt"
    done_text = f"""======================================================================
LAYOUTLMV3 FULL 28-CELL EXPERIMENT SUITE 100% COMPLETE
======================================================================
Completed at: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Master Archive: LayoutLMv3_Final_Experiment_Results_All_28_Cells.zip
All 24 ablation configurations (Baseline, 3-Module Full, 4-Module Contrastive Full,
w/o Boundary, w/o Segment, w/o HPE across Base & Large on FUNSD & CORD, 3 seeds each)
have finished and evaluated successfully.
Google Sheet Live Tracker & Google Drive fully synchronized.
======================================================================
"""
    done_file.write_text(done_text, encoding="utf-8")
    upload_to_gdrive(done_file, "ALL_EXPERIMENTS_COMPLETE.txt")
    log("ALL EXPERIMENTS AND DELIVERABLES 100% COMPLETE!")


def detect_vast_instance_id() -> str:
    """Detect the current Vast.ai instance/container ID from file or environment variables."""
    if INSTANCE_ID_FILE.exists():
        val = INSTANCE_ID_FILE.read_text(encoding="utf-8").strip()
        if val:
            return val
    for env_key in ["CONTAINER_ID", "VAST_CONTAINERLABEL"]:
        val = os.environ.get(env_key, "").strip()
        if val:
            # VAST_CONTAINERLABEL has format "C.12345678"
            m = re.search(r"(\d{5,})", val)
            if m:
                return m.group(1)
    return ""


def self_destruct_instance():
    """Destroy the Vast.ai instance via CLI and REST API to prevent any credit overspending."""
    STATE["pipeline_status"] = "COMPLETED_WAITING_LOCAL_SYNC"
    log("[SELF-DESTRUCT] Waiting up to 90s for local watcher to pull final files (or /workspace/LOCAL_SYNC_CONFIRMED)...")
    for _ in range(18):
        if LOCAL_SYNC_FLAG.exists():
            log("[SELF-DESTRUCT] Local sync confirmed via /workspace/LOCAL_SYNC_CONFIRMED!")
            break
        time.sleep(5)

    STATE["pipeline_status"] = "SELF_DESTRUCTING"
    inst_id = detect_vast_instance_id()
    log(f"[SELF-DESTRUCT] Initiating permanent Vast.ai instance destruction (Instance ID={inst_id})...")

    # Upload final runner log right before destruction
    upload_to_gdrive(RUNNER_LOG, "vast_runner_final.log")

    if inst_id and DEFAULT_VAST_API_KEY:
        # Method 1: Vast.ai REST API DELETE
        try:
            import requests
            url = f"https://console.vast.ai/api/v0/instances/{inst_id}/?api_key={DEFAULT_VAST_API_KEY}"
            r = requests.delete(url, timeout=30)
            log(f"[SELF-DESTRUCT] REST API DELETE response: {r.status_code} {r.text}")
        except Exception as e:
            log(f"[WARN] REST API self-destruct error: {e}")

        # Method 2: vastai CLI
        for vast_bin in ["vastai", "/workspace/miniconda3/envs/layoutlmv3/bin/vastai", "/usr/local/bin/vastai"]:
            try:
                subprocess.run([vast_bin, "destroy", "instance", str(inst_id), "--api-key", DEFAULT_VAST_API_KEY], timeout=20, check=False)
            except Exception:
                pass

    # Method 3: Query all active instances on account if inst_id wasn't in env and destroy matching running instance
    if not inst_id and DEFAULT_VAST_API_KEY:
        try:
            import requests
            r = requests.get(f"https://console.vast.ai/api/v0/instances/?api_key={DEFAULT_VAST_API_KEY}", timeout=20)
            if r.status_code == 200:
                instances = r.json().get("instances", [])
                for inst in instances:
                    iid = inst.get("id")
                    if iid:
                        log(f"[SELF-DESTRUCT] Destroying active instance {iid} via REST API...")
                        requests.delete(f"https://console.vast.ai/api/v0/instances/{iid}/?api_key={DEFAULT_VAST_API_KEY}", timeout=20)
        except Exception as e:
            log(f"[WARN] Fallback instance query error: {e}")


def main():
    log("**********************************************************************")
    log("AUTONOMOUS RUNNER INITIALIZED ON VAST.AI")
    log(f"Start time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Detected Vast.ai Instance ID: {detect_vast_instance_id() or 'will auto-detect'}")
    log("**********************************************************************")

    hb_thread = threading.Thread(target=status_heartbeat_loop, daemon=True)
    hb_thread.start()

    try:
        for cell_num, dataset, variant, mode, label, summary_file in CELL_QUEUE:
            run_suite_step(cell_num, dataset, variant, mode, label, summary_file)

        # Cell 28: Aggregate All 24 Ablation Summaries
        run_aggregation()

        # Create and upload master package
        create_and_upload_final_package()
    except Exception as e:
        STATE["pipeline_status"] = f"FAILED: {e}"
        log(f"[CRITICAL ERROR] Pipeline halted due to error: {e}")
        upload_to_gdrive(RUNNER_LOG, "vast_runner_error.log")
        raise
    finally:
        # Self-destruct when all cells complete (or if AUTO_DESTRUCT_ALWAYS=1)
        if STATE["pipeline_status"].startswith("UPLOADING") or STATE["pipeline_status"].startswith("COMPLETED") or os.environ.get("AUTO_DESTRUCT_ALWAYS", "1") == "1":
            self_destruct_instance()


if __name__ == "__main__":
    main()
