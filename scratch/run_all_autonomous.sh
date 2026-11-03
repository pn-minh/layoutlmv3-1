#!/bin/bash
set -e
exec > >(tee -a /workspace/bootstrap_and_runner.log) 2>&1

echo "[AUTONOMOUS MASTER] Starting at $(date)"
echo "${CONTAINER_ID:-58981233}" > /workspace/vast_instance_id.txt

cd /workspace
if [ ! -d "/workspace/layoutlmv3-1" ]; then
    git clone https://github.com/pn-minh/layoutlmv3-1.git /workspace/layoutlmv3-1
else
    cd /workspace/layoutlmv3-1 && git fetch origin main && git reset --hard origin/main
fi

# Strip any CRLF line endings from shell and python scripts
sed -i 's/\r$//' /workspace/layoutlmv3-1/scratch/*.sh /workspace/layoutlmv3-1/scratch/*.py /workspace/layoutlmv3-1/layoutlmv3/scripts/*.sh /workspace/layoutlmv3-1/layoutlmv3/scripts/*.py

# Run full bootstrap (Conda + PyTorch + Detectron2 + FUNSD/CORD + Pre-cache Models + 19 Summaries + FP16 Contrastive Smoke Test)
bash /workspace/layoutlmv3-1/scratch/vast_bootstrap.sh

# Activate environment and launch the Dual-GPU Autonomous Runner
source /workspace/miniconda3/etc/profile.d/conda.sh
conda activate layoutlmv3
export PYTHONUNBUFFERED=1
python -u /workspace/layoutlmv3-1/scratch/vast_runner.py
