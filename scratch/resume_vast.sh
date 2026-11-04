#!/bin/bash
set -e

echo "[RESUME] Stopping deadlocked vast_runner.py process..."
tmux kill-session -t pipeline_vast 2>/dev/null || true
pkill -9 -f vast_runner.py 2>/dev/null || true

cat << 'EOF' > /workspace/start_runner_only.sh
#!/bin/bash
set -a
source /etc/environment 2>/dev/null || true
set +a
/workspace/miniconda3/envs/layoutlmv3/bin/python -u /workspace/layoutlmv3-1/scratch/vast_runner.py 2>&1 | tee -a /workspace/bootstrap_and_runner.log
EOF
chmod +x /workspace/start_runner_only.sh

echo "[RESUME] Launching vast_runner.py in tmux session pipeline_vast..."
tmux new-session -d -s pipeline_vast "bash /workspace/start_runner_only.sh"

sleep 12
echo "=== VAST_RUNNER.LOG TAIL ==="
tail -n 35 /workspace/vast_runner.log
echo "=== GPU STATUS ==="
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader
