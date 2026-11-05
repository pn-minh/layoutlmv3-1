#!/bin/bash
# Vast.ai Automated Bootstrap Script for LayoutLMv3 Modified Suite
# Prepares environment, verifies GPU, installs Python 3.7.16 + PyTorch 1.10+cu111 + Detectron2,
# downloads FUNSD & CORD datasets, restores all 19 prior 3-seed summaries, and verifies Contrastive Loss on GPU.
set -e

echo "=========================================================="
echo "[VAST.AI] INITIALIZING GPU & SYSTEM ENVIRONMENT"
echo "=========================================================="

nvidia-smi

# System packages (Ubuntu 22.04 / 24.04 compatible)
export DEBIAN_FRONTEND=noninteractive
if ! command -v tmux >/dev/null 2>&1 || ! dpkg -s libgl1 >/dev/null 2>&1; then
    apt-get update -y || true
    apt-get install -y git curl tmux psmisc rsync unzip wget libgl1 libglib2.0-0 || true
fi

# Create workspace
mkdir -p /workspace
cd /workspace

# Clone or update repository
if [ ! -d "/workspace/layoutlmv3-1" ]; then
    git clone https://github.com/pn-minh/layoutlmv3-1.git /workspace/layoutlmv3-1
else
    cd /workspace/layoutlmv3-1 && git fetch origin main && git reset --hard origin/main
fi

cd /workspace/layoutlmv3-1

# Install Miniconda3 in /workspace/miniconda3 (exec-enabled overlay) while keeping caches in /dev/shm (noexec 78GB RAM disk)
if [ -L "/workspace/miniconda3" ] || [ ! -x "/workspace/miniconda3/bin/conda" ]; then
    rm -rf /workspace/miniconda3 /dev/shm/miniconda3
fi
mkdir -p /dev/shm/hf_home /dev/shm/conda_pkgs /dev/shm/pip_cache
ln -sfn /dev/shm/hf_home /workspace/.hf_home
export CONDA_PKGS_DIRS="/dev/shm/conda_pkgs"
export PIP_CACHE_DIR="/dev/shm/pip_cache"

if [ ! -x "/workspace/miniconda3/bin/conda" ]; then
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /dev/shm/miniconda.sh
    bash /dev/shm/miniconda.sh -b -p /workspace/miniconda3
    rm -f /dev/shm/miniconda.sh
fi

export HF_HOME="/workspace/.hf_home"
source /workspace/miniconda3/etc/profile.d/conda.sh
conda config --set always_yes yes
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main 2>/dev/null || true
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r 2>/dev/null || true

# Create conda environment with Python 3.7.16 (exact match for Torch 1.10.0+cu111 & Detectron2 wheels)
if ! conda info --envs | grep -q "^layoutlmv3 "; then
    conda create -n layoutlmv3 python=3.7.16 -y
fi
conda activate layoutlmv3

# Upgrade pip & install PyTorch 1.10.0+cu111 + Detectron2 + requirements (skip if already installed)
if ! python -c "import torch, detectron2, transformers, datasets, seqeval, layoutlmft, psutil, requests" 2>/dev/null; then
    python -m pip install --upgrade "pip<24.1" "setuptools<68.0" "wheel<0.43"
    python -m pip install torch==1.10.0+cu111 torchvision==0.11.1+cu111 -f https://download.pytorch.org/whl/cu111/torch_stable.html
    python -m pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu111/torch1.10/index.html
    python -m pip install -r layoutlmv3/requirements.txt
    python -m pip install requests psutil vastai
    python -m pip install -e layoutlmv3/
fi

# Ensure huggingface_hub.hf_api import compatibility and relative redirect URL resolution for transformers 4.12.5
python - << 'PY'
import site, os, pathlib
site_pkgs = pathlib.Path(site.getsitepackages()[0])

df_path = site_pkgs / "datasets" / "data_files.py"
if df_path.exists():
    txt = df_path.read_text(encoding="utf-8")
    if "import huggingface_hub.hf_api" not in txt:
        df_path.write_text(txt.replace("import huggingface_hub", "import huggingface_hub\nimport huggingface_hub.hf_api"), encoding="utf-8")

tf_fu = site_pkgs / "transformers" / "file_utils.py"
if tf_fu.exists():
    txt = tf_fu.read_text(encoding="utf-8")
    target = 'url_to_download = r.headers["Location"]'
    replacement = 'url_to_download = ("https://huggingface.co" + r.headers["Location"]) if r.headers["Location"].startswith("/") else r.headers["Location"]'
    if target in txt and replacement not in txt:
        tf_fu.write_text(txt.replace(target, replacement), encoding="utf-8")
        print("[PATCH] Patched transformers/file_utils.py for HuggingFace relative redirects.")

req_sess = site_pkgs / "requests" / "sessions.py"
if req_sess.exists():
    txt = req_sess.read_text(encoding="utf-8")
    target = "req = Request(\n            method=method.upper(),"
    replacement = 'if isinstance(url, str) and url.startswith("/"):\n            url = "https://huggingface.co" + url\n        req = Request(\n            method=method.upper(),'
    if target in txt and 'url.startswith("/")' not in txt:
        req_sess.write_text(txt.replace(target, replacement), encoding="utf-8")
        print("[PATCH] Patched requests/sessions.py for relative URL fallback.")
PY

# Download and verify FUNSD and CORD datasets
cd /workspace/layoutlmv3-1/layoutlmv3
python scripts/prepare_datasets.py

# Pre-cache microsoft/layoutlmv3-base and microsoft/layoutlmv3-large into ./models/ so dual-GPU workers never race on download
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
            print(f"[PRE-CACHE] Stripped {removed} from {bin_path}", flush=True)
PY

# Restore all 19 completed 3-seed summaries
cd /workspace/layoutlmv3-1
python scratch/backup_summaries.py /workspace/layoutlmv3-1/layoutlmv3/logs

# Verify Contrastive Loss module forward + backward pass under FP16 on GPU
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
print(f"[SMOKE TEST PASSED] FP16 Forward+Backward Loss={loss.item():.4f} | Contrastive grads verified on {device}!")
PY

echo "=========================================================="
echo "[VAST.AI] BOOTSTRAP COMPLETE: DATASETS + 19 SUMMARIES READY"
echo "=========================================================="

