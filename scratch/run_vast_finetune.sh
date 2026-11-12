#!/bin/bash
# ==============================================================================
# Autonomous Vast.ai End-to-End Fine-Tuning & Error-Self-Resolving Runner
# ==============================================================================
# Resolves:
#   1. noexec on /dev/shm -> installs Miniconda in /workspace/miniconda3
#   2. HuggingFace relative 307 redirects in transformers==4.12.5 -> auto-prefixes https://huggingface.co
#   3. datasets.data_files huggingface_hub.hf_api import bug -> auto-patched
#   4. Pretrained backbone classifier dimension mismatch -> strips classifier.* from pytorch_model.bin
#   5. Contrastive loss degradation -> applies grounded pre-SCM alignment, balanced lambda (0.03/0.01),
#      softened tau=0.10, best-model selection, and optimized CORD convergence steps
#   6. Multi-GPU parallel scheduling (LPT) -> runs across all available GPUs
#   7. Live Google Sheet & Google Drive auto-sync + self-destruction
# ==============================================================================
set -e

echo "=========================================================="
echo "[VAST.AI] 1/6: SYSTEM & GPU ENVIRONMENT DISCOVERY"
echo "=========================================================="
nvidia-smi

# Route HuggingFace, GitHub, Google Drive, and Google Sheets through SSH Reverse Proxy (127.0.0.1:18888)
grep -q "^precedence ::ffff:0:0/96  100" /etc/gai.conf 2>/dev/null || echo "precedence ::ffff:0:0/96  100" >> /etc/gai.conf
export HTTP_PROXY="http://127.0.0.1:18888"
export HTTPS_PROXY="http://127.0.0.1:18888"
export http_proxy="http://127.0.0.1:18888"
export https_proxy="http://127.0.0.1:18888"
export NO_PROXY="localhost,127.0.0.1"
export no_proxy="localhost,127.0.0.1"

export DEBIAN_FRONTEND=noninteractive
if ! command -v git >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
    apt-get update -y || true
    apt-get install -y git curl tmux psmisc rsync unzip wget libgl1 libglib2.0-0 || true
fi

mkdir -p /workspace
cd /workspace

if [ ! -d "/workspace/layoutlmv3-1" ]; then
    echo "[SETUP] Cloning repository..."
    git clone https://github.com/pn-minh/layoutlmv3-1.git /workspace/layoutlmv3-1
else
    echo "[SETUP] Updating repository to latest commit..."
    cd /workspace/layoutlmv3-1 && git fetch origin main && git reset --hard origin/main || true
fi

cd /workspace/layoutlmv3-1

echo "=========================================================="
echo "[VAST.AI] 2/6: MINICONDA SETUP (EXEC OVERLAY + RAM CACHES)"
echo "=========================================================="
# Prevent /dev/shm noexec execution error while keeping heavy models/datasets in 78GB /dev/shm RAM disk
mkdir -p /dev/shm/hf_home /dev/shm/conda_pkgs /dev/shm/pip_cache /dev/shm/models /dev/shm/datasets /dev/shm/CORD
ln -sfn /dev/shm/hf_home /workspace/.hf_home
rm -rf /workspace/layoutlmv3-1/layoutlmv3/models /workspace/layoutlmv3-1/layoutlmv3/datasets /workspace/layoutlmv3-1/layoutlmv3/CORD
ln -sfn /dev/shm/models /workspace/layoutlmv3-1/layoutlmv3/models
ln -sfn /dev/shm/datasets /workspace/layoutlmv3-1/layoutlmv3/datasets
ln -sfn /dev/shm/CORD /workspace/layoutlmv3-1/layoutlmv3/CORD
export CONDA_PKGS_DIRS="/dev/shm/conda_pkgs"
export PIP_CACHE_DIR="/dev/shm/pip_cache"
export HF_HOME="/workspace/.hf_home"

if [ -x "/opt/miniforge3/bin/conda" ] && [ ! -e "/workspace/miniconda3" ]; then
    echo "[CONDA] Reusing pre-installed /opt/miniforge3 via symlink /workspace/miniconda3..."
    ln -sfn /opt/miniforge3 /workspace/miniconda3
elif [ ! -x "/workspace/miniconda3/bin/conda" ]; then
    echo "[CONDA] Installing Miniconda to /workspace/miniconda3..."
    rm -rf /workspace/miniconda3 /dev/shm/miniconda.sh
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /dev/shm/miniconda.sh
    bash /dev/shm/miniconda.sh -b -p /workspace/miniconda3
    rm -f /dev/shm/miniconda.sh
fi

source /workspace/miniconda3/etc/profile.d/conda.sh
conda config --set always_yes yes
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main 2>/dev/null || true
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r 2>/dev/null || true

if ! conda info --envs | grep -q "^layoutlmv3 "; then
    echo "[CONDA] Creating Python 3.7 environment..."
    conda create -n layoutlmv3 python=3.7 -c conda-forge -c defaults -y
fi
conda activate layoutlmv3

echo "=========================================================="
echo "[VAST.AI] 3/6: TORCH, DETECTRON2 & DEPENDENCY INSTALL"
echo "=========================================================="
if ! python -c "import torch, detectron2, transformers, datasets, seqeval, layoutlmft, psutil, requests" 2>/dev/null; then
    python -m pip install --upgrade "pip<24.1" "setuptools<68.0" "wheel<0.43" certifi
    python -m pip install torch==1.10.0+cu111 torchvision==0.11.1+cu111 -f https://download.pytorch.org/whl/cu111/torch_stable.html
    python -m pip install detectron2 --trusted-host dl.fbaipublicfiles.com -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu111/torch1.10/index.html
    python -m pip install -r layoutlmv3/requirements.txt
    python -m pip install requests psutil vastai
    python -m pip install -e layoutlmv3/
fi

echo "=========================================================="
echo "[VAST.AI] 4/6: RESOLVING HUGGINGFACE REDIRECT & IMPORT BUGS"
echo "=========================================================="
python - << 'PY'
import site, os, pathlib
site_pkgs = pathlib.Path(site.getsitepackages()[0])

# 1. Patch datasets/data_files.py
df_path = site_pkgs / "datasets" / "data_files.py"
if df_path.exists():
    txt = df_path.read_text(encoding="utf-8")
    if "import huggingface_hub.hf_api" not in txt:
        df_path.write_text(txt.replace("import huggingface_hub", "import huggingface_hub\nimport huggingface_hub.hf_api"), encoding="utf-8")
        print("[PATCH] Patched datasets/data_files.py for huggingface_hub.hf_api.")

# 2. Patch transformers/file_utils.py for relative Location redirects
tf_fu = site_pkgs / "transformers" / "file_utils.py"
if tf_fu.exists():
    txt = tf_fu.read_text(encoding="utf-8")
    target = 'url_to_download = r.headers["Location"]'
    replacement = 'url_to_download = ("https://huggingface.co" + r.headers["Location"]) if r.headers["Location"].startswith("/") else r.headers["Location"]'
    if target in txt and replacement not in txt:
        tf_fu.write_text(txt.replace(target, replacement), encoding="utf-8")
        print("[PATCH] Patched transformers/file_utils.py for HuggingFace relative redirects.")

# 3. Patch requests/sessions.py for fallback
req_sess = site_pkgs / "requests" / "sessions.py"
if req_sess.exists():
    txt = req_sess.read_text(encoding="utf-8")
    target = "req = Request(\n            method=method.upper(),"
    replacement = 'if isinstance(url, str) and url.startswith("/"):\n            url = "https://huggingface.co" + url\n        req = Request(\n            method=method.upper(),'
    if target in txt and 'url.startswith("/")' not in txt:
        req_sess.write_text(txt.replace(target, replacement), encoding="utf-8")
        print("[PATCH] Patched requests/sessions.py for relative URL fallback.")
PY

echo "=========================================================="
echo "[VAST.AI] 5/6: PRE-CACHING DATASETS & MODELS"
echo "=========================================================="
cd /workspace/layoutlmv3-1/layoutlmv3
python scripts/prepare_datasets.py

python - << 'PY'
import os
import torch
import layoutlmft
from transformers import AutoConfig, AutoTokenizer, AutoModelForTokenClassification
for name in ["microsoft/layoutlmv3-base", "microsoft/layoutlmv3-large"]:
    short = name.split("/")[-1]
    target = os.path.join("models", short)
    if not os.path.isdir(target):
        print(f"[PRE-CACHE] Downloading {name} to {target} ...", flush=True)
        cfg = AutoConfig.from_pretrained(name)
        tok = AutoTokenizer.from_pretrained(name)
        mdl = AutoModelForTokenClassification.from_pretrained(name)
        os.makedirs(target, exist_ok=True)
        cfg.save_pretrained(target)
        tok.save_pretrained(target)
        mdl.save_pretrained(target)
    bin_path = os.path.join(target, "pytorch_model.bin")
    if os.path.isfile(bin_path):
        sd = torch.load(bin_path, map_location="cpu")
        removed = [k for k in list(sd.keys()) if k.startswith("classifier.")]
        if removed:
            for k in removed:
                del sd[k]
            torch.save(sd, bin_path + ".tmp")
            os.replace(bin_path + ".tmp", bin_path)
            print(f"[PRE-CACHE] Stripped dummy classifier {removed} from {bin_path}", flush=True)
PY

cd /workspace/layoutlmv3-1
python scratch/backup_summaries.py /workspace/layoutlmv3-1/layoutlmv3/logs 2>/dev/null || true

# Smoke test
python - << 'PY'
import torch
from layoutlmft.models.layoutlmv3.configuration_layoutlmv3 import LayoutLMv3Config
from layoutlmft.models.layoutlmv3.modeling_layoutlmv3_segment import LayoutLMv3ForSegmentTokenClassification

device = "cuda" if torch.cuda.is_available() else "cpu"
cfg = LayoutLMv3Config(
    vocab_size=100,
    hidden_size=192,
    num_hidden_layers=2,
    num_attention_heads=4,
    intermediate_size=256,
    coordinate_size=32,
    shape_size=32,
    num_labels=7,
    visual_embed=True,
    input_size=224,
    use_token_segment=True,
    use_hierarchical_position_encoding=True,
    use_column_encoding=True,
    use_intra_line_boundary=True,
    use_contrastive_loss=True,
    lambda_contrastive_init=0.03,
    contrastive_proj_dim=128,
    contrastive_temperature=0.10,
)
model = LayoutLMv3ForSegmentTokenClassification(cfg).to(device)
B, L = 2, 16
input_ids = torch.randint(0, 100, (B, L), device=device)
bbox = torch.tensor([[100, 100, 300, 150]] * L, device=device).unsqueeze(0).expand(B, L, 4).contiguous()
attention_mask = torch.ones((B, L + 197), dtype=torch.long, device=device)
labels = torch.cat([torch.randint(0, 7, (B, L), device=device), torch.full((B, 197), -100, dtype=torch.long, device=device)], dim=1)
seg_id = torch.arange(L, device=device).unsqueeze(0).expand(B, L)
line_ids = torch.zeros((B, L), dtype=torch.long, device=device)
block_ids = torch.zeros((B, L), dtype=torch.long, device=device)
column_ids = torch.zeros((B, L), dtype=torch.long, device=device)
entity_ids = torch.arange(L, device=device).unsqueeze(0).expand(B, L)
images = torch.randn(B, 3, 224, 224, device=device)

with torch.cuda.amp.autocast(enabled=(device == "cuda")):
    out = model(
        input_ids=input_ids,
        bbox=bbox,
        attention_mask=attention_mask,
        labels=labels,
        seg_id=seg_id,
        line_ids=line_ids,
        block_ids=block_ids,
        column_ids=column_ids,
        entity_ids=entity_ids,
        images=images,
    )
    loss = out.loss

loss.backward()
assert not torch.isnan(loss) and not torch.isinf(loss), "Loss is NaN/Inf!"
assert model.contrastive_text_proj.weight.grad is not None, "Missing grad on contrastive_text_proj!"
assert model.contrastive_img_proj.weight.grad is not None, "Missing grad on contrastive_img_proj!"
print(f"[SMOKE TEST PASSED] FP16 Forward+Backward Loss={loss.item():.4f} on {device}!")
PY

echo "=========================================================="
echo "[VAST.AI] 6/6: LAUNCHING AUTONOMOUS FINE-TUNING PIPELINE"
echo "=========================================================="
tmux kill-session -t pipeline_vast 2>/dev/null || true
pkill -9 -f vast_runner.py 2>/dev/null || true
pkill -9 -f run_ablation_suite.sh 2>/dev/null || true
pkill -9 -f run_funsd_cord.py 2>/dev/null || true

# Free /dev/shm RAM disk after package installation so dual-GPU DataLoaders never exhaust shared memory
rm -rf /dev/shm/conda_pkgs /dev/shm/pip_cache 2>/dev/null || true

export FORCE_RERUN="${FORCE_RERUN:-0}"
export CELLS="${CELLS:-24,25,26,27,29,30,31,32,33,34,35,36,37,38}"

echo "[LAUNCH] Running cells: $CELLS with FORCE_RERUN=$FORCE_RERUN"
nohup python -u /workspace/layoutlmv3-1/scratch/vast_runner.py >> /workspace/vast_runner.log 2>&1 < /dev/null &
RUNNER_PID=$!
echo "[LAUNCH] Pipeline started with PID $RUNNER_PID in background."

sleep 10
echo "=== LOG OUTPUT ==="
tail -n 25 /workspace/vast_runner.log || true
echo "=== ACTIVE PROCESSES ==="
ps aux | grep -E "vast_runner|run_ablation|run_funsd" | grep -v grep || true
echo "=========================================================="
echo "[VAST.AI] MASTER PIPELINE RUNNING AUTONOMOUSLY."
echo "Results will auto-sync to Google Sheet and Google Drive."
echo "Instance will self-destruct upon verified completion."
echo "=========================================================="

