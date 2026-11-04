#!/bin/bash
set -e

echo "[RESUME] Stopping any existing vast_runner.py process..."
tmux kill-session -t pipeline_vast 2>/dev/null || true
pkill -9 -f vast_runner.py 2>/dev/null || true
sleep 1

set -a
source /etc/environment 2>/dev/null || true
set +a

echo "[RESUME] Launching vast_runner.py in background with nohup..."
nohup /workspace/miniconda3/envs/layoutlmv3/bin/python -u /workspace/layoutlmv3-1/scratch/vast_runner.py >> /workspace/bootstrap_and_runner.log 2>&1 < /dev/null &
RUNNER_PID=$!
echo "[RESUME] vast_runner.py started with PID: $RUNNER_PID"

sleep 15
echo "=== VAST_RUNNER.LOG TAIL ==="
tail -n 35 /workspace/vast_runner.log
echo "=== GPU STATUS ==="
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader
echo "=== RUNNING PROCESSES ==="
ps aux | grep -E "vast_runner|run_ablation|run_funsd|run_cord" | grep -v grep || true
