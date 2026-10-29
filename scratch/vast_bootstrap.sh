#!/bin/bash
# Vast.ai Bootstrap Script for LayoutLMv3 Modified Suite
# Prepares environment, verifies GPU, installs dependencies, and restores all prior 16 summaries
set -e

echo "=========================================================="
echo "[VAST.AI] INITIALIZING GPU & SYSTEM ENVIRONMENT"
echo "=========================================================="

nvidia-smi

# System packages
apt-get update -y
apt-get install -y git curl tmux psmisc rsync unzip wget libgl1-mesa-glx libglib2.0-0

# Create workspace
mkdir -p /workspace
cd /workspace

# Clone repository
if [ ! -d "/workspace/layoutlmv3-1" ]; then
    git clone https://github.com/pn-minh/layoutlmv3-1.git /workspace/layoutlmv3-1
else
    cd /workspace/layoutlmv3-1 && git pull origin main
fi

cd /workspace/layoutlmv3-1

# Install Miniconda
if [ ! -d "/workspace/miniconda3" ]; then
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /workspace/miniconda.sh
    bash /workspace/miniconda.sh -b -p /workspace/miniconda3
    rm -f /workspace/miniconda.sh
fi

source /workspace/miniconda3/etc/profile.d/conda.sh

# Create conda environment
if ! conda info --envs | grep -q "^layoutlmv3 "; then
    conda create -n layoutlmv3 python=3.8 -y
fi
conda activate layoutlmv3

# Upgrade pip & install torch
pip install --upgrade "pip<24.1" "setuptools<68.0" "wheel<0.43"
pip install torch torchvision --extra-index-url https://download.pytorch.org/whl/cu118
pip install -r layoutlmv3/requirements.txt
pip install -e layoutlmv3/

# Restore all 16 completed 3-seed summaries
python3 scratch/backup_summaries.py /workspace/layoutlmv3-1/layoutlmv3/logs

echo "=========================================================="
echo "[VAST.AI] BOOTSTRAP COMPLETE: 16 SUMMARIES RESTORED"
echo "=========================================================="
