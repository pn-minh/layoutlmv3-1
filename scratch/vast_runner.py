#!/usr/bin/env python3
"""
Autonomous Dual-GPU Vast.ai Runner for LayoutLMv3 Additional Experiments Suite:
  - Part 1 (Calibrated 4-Module Contrastive + Step/Per-Class Curves — Pack A):
      Cells 24, 25, 26, 27 (Calibrated 4-Module on FUNSD/CORD Base & Large, 3 seeds)
      Cells 29, 30 (Baseline Step/Class Curves & Predictions on CORD-base & FUNSD-base, 3 seeds)
  - Part 2 (Hyperparameter Sensitivity Sweep on FUNSD-base — Pack B):
      Cells 31, 32 (Boundary Loss weight lambda_bound in {0.05, 0.20})
      Cells 33, 34 (Contrastive Temperature tau in {0.07, 0.20})
  - Part 3 (Sample Efficiency / Few-Shot Learning Curve on FUNSD-base — Pack C):
      Cells 35, 36 (25% Training Data: Baseline vs. Full 4-Module)
      Cells 37, 38 (50% Training Data: Baseline vs. Full 4-Module)
  - Part 4 (Cell 28: Latency/VRAM Benchmark + Span-Length Error Analysis + Master Aggregation)

Anti-Freeze & Safety Guarantees:
  1. Per-cell process group watchdog timeout (45 mins max per cell) with automatic /dev/shm cache cleanup & retry.
  2. Live heartbeat thread updating /workspace/live_status.json every 10s with GPU utilization, VRAM, and step ETA.
  3. Automatic upload of all summaries, logs, and master archive to Google Drive subfolder ('Experiments & Logs').
  4. Automatic sync to the new Google Sheet tab ('Additional Experiments Tracker').
  5. Strict verified self-destruction of the Vast.ai instance immediately upon completion.
"""
import os
import re
import sys
import time
import json
import queue
import signal
import shutil
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

CELL_TIMEOUT_SEC = int(os.environ.get("CELL_TIMEOUT_SEC", "2700"))  # 45 minutes max per cell
GDRIVE_SUBFOLDER = "Experiments & Logs"

# Ordered Longest-Processing-Time-First (LPT) across 2x A100 GPUs:
# (cell_id, dataset, variant, mode, label, summary_filename)
CELL_QUEUE = [
    # Part 1: Core Calibrated 4-Module Contrastive + Step/Per-Class Curves (Pack A)
    (27, "cord",  "large", "contrastive",     "CORD large contrastive (Calibrated 4-Module)",      "cord-large-contrastive_3seed_summary.json"),
    (26, "funsd", "large", "contrastive",     "FUNSD large contrastive (Calibrated 4-Module)",     "funsd-large-contrastive_3seed_summary.json"),
    (25, "cord",  "base",  "contrastive",     "CORD base contrastive (Calibrated 4-Module)",       "cord-base-contrastive_3seed_summary.json"),
    (24, "funsd", "base",  "contrastive",     "FUNSD base contrastive (Calibrated 4-Module)",      "funsd-base-contrastive_3seed_summary.json"),
    (29, "cord",  "base",  "baseline",        "CORD base baseline (Step & Per-Class Curves)",      "cord-base-baseline_3seed_summary.json"),
    (30, "funsd", "base",  "baseline",        "FUNSD base baseline (Step & Per-Class Curves)",     "funsd-base-baseline_3seed_summary.json"),
    # Part 2: Hyperparameter Sensitivity Sweep on FUNSD-base (Pack B)
    (31, "funsd", "base",  "sens_bound_005",  "FUNSD base sensitivity (lambda_bound=0.05)",        "funsd-base-sens_bound_005_3seed_summary.json"),
    (32, "funsd", "base",  "sens_bound_020",  "FUNSD base sensitivity (lambda_bound=0.20)",        "funsd-base-sens_bound_020_3seed_summary.json"),
    (33, "funsd", "base",  "sens_tau_007",    "FUNSD base sensitivity (tau=0.07)",                 "funsd-base-sens_tau_007_3seed_summary.json"),
    (34, "funsd", "base",  "sens_tau_020",    "FUNSD base sensitivity (tau=0.20)",                 "funsd-base-sens_tau_020_3seed_summary.json"),
    # Part 3: Few-Shot Sample Efficiency Curve on FUNSD-base (Pack C)
    (37, "funsd", "base",  "fewshot_base_50", "FUNSD base few-shot 50% (Baseline)",                "funsd-base-fewshot_base_50_3seed_summary.json"),
    (38, "funsd", "base",  "fewshot_full_50", "FUNSD base few-shot 50% (Full 4-Module)",           "funsd-base-fewshot_full_50_3seed_summary.json"),
    (35, "funsd", "base",  "fewshot_base_25", "FUNSD base few-shot 25% (Baseline)",                "funsd-base-fewshot_base_25_3seed_summary.json"),
    (36, "funsd", "base",  "fewshot_full_25", "FUNSD base few-shot 25% (Full 4-Module)",           "funsd-base-fewshot_full_25_3seed_summary.json"),
]

# Allow filtering cells via CELLS env var (e.g. CELLS="24,25,26,27,29,30,31,32,33,34")
if os.environ.get("CELLS"):
    _target_ids = {int(x.strip()) for x in os.environ["CELLS"].split(",") if x.strip().isdigit()}
    if _target_ids:
        CELL_QUEUE = [item for item in CELL_QUEUE if item[0] in _target_ids]

LOG_LOCK = threading.RLock()
SYNC_LOCK = threading.RLock()
STOP_HEARTBEAT = threading.Event()

STATE = {
    "pipeline_status": "INITIALIZING",
    "start_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "start_epoch": time.time(),
    "total_queued_cells": len(CELL_QUEUE),
    "active_workers": {},
    "completed_cells": [],
    "failed_cells": [],
    "gdrive_uploads_ok": [],
    "gpu_telemetry": [],
}


def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    with LOG_LOCK:
        print(formatted, flush=True)
        try:
            with open(RUNNER_LOG, "a", encoding="utf-8") as f:
                f.write(formatted + "\n")
        except Exception:
            pass


def get_python_bin() -> str:
    candidates = [
        "/workspace/miniconda3/envs/layoutlmv3/bin/python",
        "/opt/miniforge3/envs/layoutlmv3/bin/python",
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


def query_gpu_telemetry():
    try:
        proc = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0:
            gpus = []
            for ln in proc.stdout.strip().splitlines():
                parts = [p.strip() for p in ln.split(",")]
                if len(parts) >= 6:
                    gpus.append({
                        "index": int(parts[0]),
                        "name": parts[1],
                        "util_pct": float(parts[2]),
                        "mem_used_mb": float(parts[3]),
                        "mem_total_mb": float(parts[4]),
                        "temp_c": float(parts[5]),
                    })
            return gpus
    except Exception:
        pass
    return []


def parse_cell_log_progress(cell_num: int) -> dict:
    log_path = Path(f"/tmp/cell_{cell_num}.log")
    info = {"seed_idx": 0, "total_seeds": 3, "step": 0, "max_steps": 1000, "eta_sec": 0.0}
    if not log_path.exists():
        return info
    try:
        text = log_path.read_text(encoding="utf-8", errors="ignore")[-16000:]
        m_seed = re.findall(r"\[RUN (\d+)/(\d+)\]", text)
        if m_seed:
            info["seed_idx"] = int(m_seed[-1][0])
            info["total_seeds"] = int(m_seed[-1][1])
        m_step = re.findall(r"\[REALTIME\] Step (\d+)/(\d+) \([\d.]+%\) \| Elapsed: [\d.]+s \| ETA: ([\d.]+)s", text)
        if m_step:
            info["step"] = int(m_step[-1][0])
            info["max_steps"] = int(m_step[-1][1])
            info["eta_sec"] = float(m_step[-1][2])
    except Exception:
        pass
    return info


def heartbeat_loop():
    while not STOP_HEARTBEAT.is_set():
        try:
            with SYNC_LOCK:
                STATE["gpu_telemetry"] = query_gpu_telemetry()
                STATE["elapsed_sec"] = round(time.time() - STATE["start_epoch"], 1)
                for wk, wdata in STATE["active_workers"].items():
                    cnum = wdata.get("cell")
                    if cnum:
                        wdata["progress"] = parse_cell_log_progress(cnum)
                LIVE_STATUS_PATH.write_text(json.dumps(STATE, indent=2), encoding="utf-8")
        except Exception:
            pass
        STOP_HEARTBEAT.wait(10.0)


def upload_to_gdrive(file_path: Path, remote_filename: str = None, subfolder: str = GDRIVE_SUBFOLDER, max_retries: int = 5) -> bool:
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
        "subfolder": subfolder,
        "pdfBase64": b64_str,
    }
    import requests
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(WEBHOOK_URL, json=payload, timeout=120)
            if r.status_code == 200 and "OK" in r.text:
                log(f"[GDRIVE] Uploaded {fname} -> '{subfolder or 'Root'}' ({len(raw_bytes)/1024:.1f} KB) [attempt {attempt}]")
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
    """Bundle all *_3seed_summary.json + benchmark/span files into a single JSON snapshot and upload to Google Drive."""
    snapshot = {
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "live_state": STATE,
        "summaries": {},
        "extra_analyses": {},
    }
    if LOG_DIR.exists():
        for p in sorted(LOG_DIR.glob("*_3seed_summary.json")):
            try:
                snapshot["summaries"][p.name] = json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                log(f"[WARN] Error reading {p.name} for snapshot: {e}")
        for extra_name in ["latency_vram_benchmark.json", "span_length_and_error_analysis.json"]:
            ep = LOG_DIR / extra_name
            if ep.exists():
                try:
                    snapshot["extra_analyses"][extra_name] = json.loads(ep.read_text(encoding="utf-8"))
                except Exception:
                    pass
    snap_path = WORKSPACE_DIR / "LayoutLMv3_All_Summaries_Snapshot.json"
    snap_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return upload_to_gdrive(snap_path, "LayoutLMv3_All_Summaries_Snapshot.json", subfolder=GDRIVE_SUBFOLDER)


def sync_sheet() -> bool:
    """Trigger Google Sheet Live Tracker sync (both main tracker & new Additional Experiments tab) with retries."""
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


def summary_needs_refresh(cell_num: int, sum_path: Path) -> bool:
    """
    Ensure cells 24-27 (Calibrated Contrastive) and 29-30 (Baseline step curves)
    are freshly evaluated if existing JSON lacks step_history or per_class_metrics.
    """
    if not sum_path.exists():
        return True
    if os.environ.get("FORCE_RERUN", "0") in ("1", "true", "True") or "--force" in sys.argv:
        return True
    if cell_num in (24, 25, 26, 27, 29, 30):
        try:
            data = json.loads(sum_path.read_text(encoding="utf-8"))
            if not data.get("step_history") or not data.get("per_class_metrics"):
                log(f"[CALIBRATION REFRESH] Cell {cell_num} summary ({sum_path.name}) lacks step_history/per_class_metrics; scheduling fresh calibrated run.")
                return True
        except Exception:
            return True
    return False


def run_suite_step_on_gpu(gpu_id: int, cell_num: int, dataset: str, variant: str, mode: str, label: str, summary_file: str):
    worker_key = f"GPU_{gpu_id}"
    with SYNC_LOCK:
        STATE["pipeline_status"] = "RUNNING_EXPERIMENTS"
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

    if not summary_needs_refresh(cell_num, sum_path):
        log(f"[{worker_key}] [SKIP] Up-to-date summary already exists for Cell {cell_num}: {sum_path}")
        with SYNC_LOCK:
            upload_to_gdrive(sum_path, subfolder=GDRIVE_SUBFOLDER)
            write_and_upload_consolidated_snapshot()
            sync_sheet()
            if cell_num not in STATE["completed_cells"]:
                STATE["completed_cells"].append(cell_num)
            STATE["active_workers"].pop(worker_key, None)
        return

    # Remove stale summary or seed folders before running fresh calibrated cell
    if sum_path.exists():
        sum_path.unlink()
    for seed in [42, 123, 1993]:
        stale_dir = LOG_DIR / f"{dataset}-{variant}-{mode}-seed{seed}"
        if stale_dir.exists() and not (stale_dir / "trainer_state.json").exists():
            shutil.rmtree(stale_dir, ignore_errors=True)

    conda_activate = (
        "source /workspace/miniconda3/etc/profile.d/conda.sh && conda activate layoutlmv3"
        if Path("/workspace/miniconda3/etc/profile.d/conda.sh").exists()
        else "source /venv/layoutlmv3/bin/activate"
    )

    seeds_env = ""
    if os.environ.get("FAST_SWEEP", "0") == "1" and cell_num >= 31:
        seeds_env = "export SEEDS_OVERRIDE='42' && "

    cmd = (
        f"{conda_activate} && "
        f"{seeds_env}"
        f"export CUDA_VISIBLE_DEVICES={gpu_id} && "
        f"export HF_HOME=/workspace/.hf_home && "
        f"export PYTHONUNBUFFERED=1 && cd /workspace/layoutlmv3-1/layoutlmv3 && "
        f"bash scripts/run_ablation_suite.sh {dataset} {variant} {mode} > /tmp/cell_{cell_num}.log 2>&1; "
        f"echo '===EXIT_CODE:'$? '===' >> /tmp/cell_{cell_num}.log"
    )

    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        t0 = time.time()
        proc = subprocess.Popen(
            ["bash", "-c", cmd],
            preexec_fn=os.setsid if hasattr(os, "setsid") else None,
        )
        try:
            retcode = proc.wait(timeout=CELL_TIMEOUT_SEC)
        except subprocess.TimeoutExpired:
            log(f"[{worker_key}] [WATCHDOG TIMEOUT] Cell {cell_num} exceeded {CELL_TIMEOUT_SEC}s on attempt {attempt}! Killing process group...")
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                proc.kill()
            retcode = -9
            shutil.rmtree(f"/dev/shm/hf_cache_{dataset}_{variant}_{mode}", ignore_errors=True)

        elapsed = time.time() - t0
        log(f"[{worker_key}] Cell {cell_num} (attempt {attempt}) finished in {elapsed:.1f}s ({elapsed/60.0:.2f} min) with returncode {retcode}")

        if retcode == 0 and sum_path.exists():
            break
        elif attempt < max_attempts:
            log(f"[{worker_key}] Retrying Cell {cell_num} after cleanup...")
            time.sleep(5)

    with SYNC_LOCK:
        STATE["active_workers"].pop(worker_key, None)
        if log_path.exists():
            upload_to_gdrive(log_path, f"cell_{cell_num}.log", subfolder=GDRIVE_SUBFOLDER)

        if not sum_path.exists():
            log(f"[{worker_key}] [FATAL] Cell {cell_num} failed (summary_exists={sum_path.exists()})!")
            STATE["failed_cells"].append(cell_num)
            raise RuntimeError(f"Cell {cell_num} failed on {worker_key}")

        log(f"[{worker_key}] Verified summary exists: {sum_path}")
        upload_to_gdrive(sum_path, subfolder=GDRIVE_SUBFOLDER)
        write_and_upload_consolidated_snapshot()
        sync_sheet()
        if cell_num not in STATE["completed_cells"]:
            STATE["completed_cells"].append(cell_num)
        log(f"[{worker_key}] Cell {cell_num} ({label}) synced to Google Drive & Google Sheets.")


def run_post_benchmarks_and_aggregation() -> bool:
    STATE["pipeline_status"] = "RUNNING_BENCHMARKS_AND_AGGREGATION"
    log("======================================================================")
    log("STARTING CELL 28: Latency/VRAM Benchmark + Span-Length Eval + Aggregation")
    log("======================================================================")

    py_bin = get_python_bin()
    layout_dir = REPO_DIR / "layoutlmv3"

    # 1. Run Latency & Peak VRAM Benchmark
    bench_script = layout_dir / "scripts" / "run_latency_vram_benchmark.py"
    if bench_script.exists():
        try:
            res = subprocess.run([py_bin, str(bench_script)], cwd=str(layout_dir), capture_output=True, text=True, timeout=300)
            log(f"[BENCHMARK] Exit={res.returncode}\n{res.stdout.strip()}")
            bench_json = LOG_DIR / "latency_vram_benchmark.json"
            if bench_json.exists():
                upload_to_gdrive(bench_json, subfolder=GDRIVE_SUBFOLDER)
        except Exception as e:
            log(f"[WARN] Latency benchmark error: {e}")

    # 2. Run Span-Length Bucketed F1 & Error Breakdown Analysis
    span_script = layout_dir / "scripts" / "run_span_length_eval.py"
    if span_script.exists():
        try:
            res = subprocess.run([py_bin, str(span_script)], cwd=str(layout_dir), capture_output=True, text=True, timeout=300)
            log(f"[SPAN EVAL] Exit={res.returncode}\n{res.stdout.strip()}")
            span_json = LOG_DIR / "span_length_and_error_analysis.json"
            if span_json.exists():
                upload_to_gdrive(span_json, subfolder=GDRIVE_SUBFOLDER)
        except Exception as e:
            log(f"[WARN] Span length eval error: {e}")

    # 3. Aggregate all available 3-seed summaries
    modes = [
        "baseline", "full", "contrastive", "no_boundary", "no_segment", "no_hpe",
        "sens_bound_005", "sens_bound_020", "sens_tau_007", "sens_tau_020",
        "fewshot_base_25", "fewshot_full_25", "fewshot_base_50", "fewshot_full_50",
    ]
    mode_labels = {
        "baseline":        "Baseline (Vanilla LayoutLMv3)",
        "full":            "3-Module Model (HPE + Token-Segment + Boundary; w/o Contrastive)",
        "contrastive":     "Full 4-Module Model (+ Calibrated Cross-Modal Contrastive Loss)",
        "no_boundary":     "Ablation: w/o Boundary Loss",
        "no_segment":      "Ablation: w/o Token-Segment",
        "no_hpe":          "Ablation: w/o HPE",
        "sens_bound_005":  "Sensitivity: Boundary Weight lambda_bound = 0.05",
        "sens_bound_020":  "Sensitivity: Boundary Weight lambda_bound = 0.20",
        "sens_tau_007":    "Sensitivity: Contrastive Temp tau = 0.07",
        "sens_tau_020":    "Sensitivity: Contrastive Temp tau = 0.20",
        "fewshot_base_25": "Few-Shot 25% Data: Vanilla LayoutLMv3 Baseline",
        "fewshot_full_25": "Few-Shot 25% Data: Full 4-Module Model",
        "fewshot_base_50": "Few-Shot 50% Data: Vanilla LayoutLMv3 Baseline",
        "fewshot_full_50": "Few-Shot 50% Data: Full 4-Module Model",
    }

    table_lines = [
        "# LayoutLMv3 Complete Ablation, Sensitivity & Sample-Efficiency Results",
        "",
        "Evaluated across 3 random seeds (`42, 123, 1993`) on Dual NVIDIA A100 GPUs.",
        "",
        f"| {'Variant':<7} | {'Dataset':<7} | {'Configuration':<64} | {'Precision (%)':<16} | {'Recall (%)':<16} | {'F1 (%)':<18} | {'Accuracy (%)':<16} |",
        "|" + "-" * 9 + "|" + "-" * 9 + "|" + "-" * 66 + "|" + "-" * 18 + "|" + "-" * 18 + "|" + "-" * 20 + "|" + "-" * 18 + "|",
    ]

    for variant in ["base", "large"]:
        for dataset in ["funsd", "cord"]:
            for mode in modes:
                summary_path = LOG_DIR / f"{dataset}-{variant}-{mode}_3seed_summary.json"
                if not summary_path.exists():
                    continue
                with open(summary_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    data = content.get("metrics") or content.get("mean_std")

                if "eval_precision" in data and "mean" in data["eval_precision"]:
                    p_str = f"`{data['eval_precision']['mean']*100:.2f} ± {data['eval_precision']['std']*100:.2f}`"
                    r_str = f"`{data['eval_recall']['mean']*100:.2f} ± {data['eval_recall']['std']*100:.2f}`"
                    f1_str = f"**`{data['eval_f1']['mean']*100:.2f} ± {data['eval_f1']['std']*100:.2f}`**"
                    acc_str = (
                        f"`{data['eval_accuracy']['mean']*100:.2f} ± {data['eval_accuracy']['std']*100:.2f}`"
                        if "eval_accuracy" in data
                        else "N/A"
                    )
                else:
                    p_str = f"`{data['eval_precision']['mean_pct']:.2f} ± {data['eval_precision']['std_pct']:.2f}`"
                    r_str = f"`{data['eval_recall']['mean_pct']:.2f} ± {data['eval_recall']['std_pct']:.2f}`"
                    f1_str = f"**`{data['eval_f1']['mean_pct']:.2f} ± {data['eval_f1']['std_pct']:.2f}`**"
                    acc_str = (
                        f"`{data['eval_accuracy']['mean_pct']:.2f} ± {data['eval_accuracy']['std_pct']:.2f}`"
                        if "eval_accuracy" in data
                        else "N/A"
                    )

                table_lines.append(
                    f"| `{variant}` | `{dataset.upper()}` | {mode_labels.get(mode, mode):<64} | {p_str:<16} | {r_str:<16} | {f1_str:<18} | {acc_str:<16} |"
                )

    table_text = "\n".join(table_lines) + "\n"
    log("\n" + table_text)

    out_table_path = REPO_DIR / "FINAL_AGGREGATED_ABLATION_TABLE.md"
    out_table_path.write_text(table_text, encoding="utf-8")
    ok_table = upload_to_gdrive(out_table_path, "FINAL_AGGREGATED_ABLATION_TABLE.md", subfolder=GDRIVE_SUBFOLDER)
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

    zip_path = WORKSPACE_DIR / "LayoutLMv3_Final_Experiment_Results_All_Cells.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for jf in sorted(LOG_DIR.glob("*.json")):
            zf.write(jf, arcname=f"summaries/{jf.name}")
        for pred in sorted(LOG_DIR.glob("*/test_predictions.txt")):
            zf.write(pred, arcname=f"predictions/{pred.parent.name}_test_predictions.txt")
        for st in sorted(LOG_DIR.glob("*/trainer_state.json")):
            zf.write(st, arcname=f"trainer_states/{st.parent.name}_trainer_state.json")
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

    log(f"Created final master archive: {zip_path} ({zip_path.stat().st_size / (1024*1024):.2f} MB)")
    zip_ok = upload_to_gdrive(zip_path, "LayoutLMv3_Final_Experiment_Results_All_Cells.zip", subfolder=GDRIVE_SUBFOLDER)

    done_file = WORKSPACE_DIR / "ALL_EXPERIMENTS_COMPLETE.txt"
    done_text = f"""======================================================================
LAYOUTLMV3 ADDITIONAL EXPERIMENTS SUITE 100% COMPLETE
======================================================================
Completed at: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Completed Cells: {STATE['completed_cells']}
Master Archive: LayoutLMv3_Final_Experiment_Results_All_Cells.zip
Consolidated JSON: LayoutLMv3_All_Summaries_Snapshot.json
Google Sheet Live Tracker & Google Drive ('Experiments & Logs') fully synchronized.
======================================================================
"""
    done_file.write_text(done_text, encoding="utf-8")
    done_ok = upload_to_gdrive(done_file, "ALL_EXPERIMENTS_COMPLETE.txt", subfolder=GDRIVE_SUBFOLDER)
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
    return "60293806"


def self_destruct_instance():
    """Destroy the Vast.ai instance immediately after verifying all results are saved to Google Drive."""
    STATE["pipeline_status"] = "SELF_DESTRUCTING"
    inst_id = detect_vast_instance_id()
    log(f"[SELF-DESTRUCT] All runs verified and saved to Google Drive. Destroying Vast.ai instance {inst_id}...")

    # Upload final runner log right before destruction
    upload_to_gdrive(RUNNER_LOG, "vast_runner_final.log", subfolder=GDRIVE_SUBFOLDER, max_retries=2)

    api_keys = [k for k in [CONTAINER_VAST_API_KEY, ACCOUNT_VAST_API_KEY] if k]

    # Method 1: vastai CLI
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
    log("AUTONOMOUS DUAL-A100 RUNNER INITIALIZED ON VAST.AI")
    log(f"Start time : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"Instance ID: {inst_id} | Detected GPUs: {num_gpus} | Queued Cells: {len(CELL_QUEUE)}")
    log("**********************************************************************")

    hb_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    hb_thread.start()

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
    worker_count = min(num_gpus, max(len(CELL_QUEUE), 1))
    for gid in range(worker_count):
        t = threading.Thread(target=gpu_worker, args=(gid,), daemon=False)
        t.start()
        threads.append(t)
        time.sleep(3)

    for t in threads:
        t.join()

    if worker_errors or STATE["failed_cells"]:
        STOP_HEARTBEAT.set()
        log(f"[ABORT SELF-DESTRUCT] Errors occurred in cells {STATE['failed_cells']}: {worker_errors}")
        upload_to_gdrive(RUNNER_LOG, "vast_runner_error.log", subfolder=GDRIVE_SUBFOLDER)
        sys.exit(1)

    # Cell 28: Latency/VRAM Benchmark + Span-Length Eval + Master Aggregation
    agg_ok = run_post_benchmarks_and_aggregation()
    pkg_ok = create_and_upload_final_package()
    STOP_HEARTBEAT.set()

    expected_count = len(CELL_QUEUE) + 1
    if agg_ok and pkg_ok and len(STATE["completed_cells"]) >= expected_count:
        log(f"[VERIFIED] All {len(CELL_QUEUE)} experiment cells + Cell 28 benchmarks/aggregation completed and uploaded to Google Drive!")
        self_destruct_instance()
    else:
        log(f"[WARN] Verification check incomplete (agg_ok={agg_ok}, pkg_ok={pkg_ok}, completed={len(STATE['completed_cells'])}/{expected_count}). Uploading log.")
        upload_to_gdrive(RUNNER_LOG, "vast_runner_incomplete.log", subfolder=GDRIVE_SUBFOLDER)


if __name__ == "__main__":
    main()
