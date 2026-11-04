#!/bin/bash
set -e

echo "[RESUME] Stopping any existing vast_runner.py or training processes..."
tmux kill-session -t pipeline_vast 2>/dev/null || true
pkill -9 -f vast_runner.py 2>/dev/null || true
pkill -9 -f run_ablation_suite.sh 2>/dev/null || true
pkill -9 -f run_funsd_cord.py 2>/dev/null || true
sleep 2

set -a
source /etc/environment 2>/dev/null || true
set +a

source /workspace/miniconda3/etc/profile.d/conda.sh 2>/dev/null || true
conda activate layoutlmv3 2>/dev/null || true
if [ -x "/venv/layoutlmv3/bin/python" ]; then
    export PATH="/venv/layoutlmv3/bin:$PATH"
fi

echo "[RESUME] Using python: $(which python)"

echo "[RESUME] Stripping dummy 2-class classifier head from pre-cached backbone checkpoints..."
cd /workspace/layoutlmv3-1/layoutlmv3
python - << 'PY'
import os
import torch
import layoutlmft
from transformers import AutoConfig
from layoutlmft.models.layoutlmv3.modeling_layoutlmv3_segment import LayoutLMv3ForSegmentTokenClassification

for short in ["layoutlmv3-base", "layoutlmv3-large"]:
    target = os.path.join("models", short)
    bin_path = os.path.join(target, "pytorch_model.bin")
    if os.path.isfile(bin_path):
        sd = torch.load(bin_path, map_location="cpu")
        removed = [k for k in list(sd.keys()) if k.startswith("classifier.")]
        if removed:
            for k in removed:
                del sd[k]
            torch.save(sd, bin_path + ".tmp")
            os.replace(bin_path + ".tmp", bin_path)
            print(f"[PATCH] Stripped {removed} from {bin_path}", flush=True)
        else:
            print(f"[OK] {bin_path} already clean (no classifier.* keys)", flush=True)
    # Verify loading with FUNSD num_labels=7
    cfg = AutoConfig.from_pretrained(target, num_labels=7, use_token_segment=True, use_hierarchical_position_encoding=True, use_column_encoding=True, use_intra_line_boundary=True, use_contrastive_loss=True)
    mdl = LayoutLMv3ForSegmentTokenClassification.from_pretrained(target, config=cfg)
    del mdl
    print(f"[VERIFIED] {short} loads cleanly with FUNSD num_labels=7!", flush=True)
PY

cd /workspace/layoutlmv3-1
echo "[RESUME] Launching vast_runner.py in background with nohup..."
nohup python -u /workspace/layoutlmv3-1/scratch/vast_runner.py >> /workspace/bootstrap_and_runner.log 2>&1 < /dev/null &
RUNNER_PID=$!
echo "[RESUME] vast_runner.py started with PID: $RUNNER_PID"

sleep 25
echo "=== VAST_RUNNER.LOG TAIL ==="
tail -n 30 /workspace/vast_runner.log
echo "=== GPU STATUS ==="
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader
echo "=== RUNNING PROCESSES ==="
ps aux | grep -E "vast_runner|run_ablation|run_funsd|run_cord" | grep -v grep || true
echo "=== CELL 26 LOG TAIL ==="
tail -n 15 /tmp/cell_26.log 2>/dev/null || true
echo "=== CELL 25 LOG TAIL ==="
tail -n 15 /tmp/cell_25.log 2>/dev/null || true
