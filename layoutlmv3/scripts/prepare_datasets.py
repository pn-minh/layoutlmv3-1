#!/usr/bin/env python3
# coding=utf-8
# Helper script to download and verify FUNSD and CORD datasets into ./datasets/funsd and ./CORD
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path


def download_with_eta(url: str, dest_path: Path, label: str):
    """Download a file from a URL with real-time progress and ETA output."""
    start_time = time.time()

    def reporthook(block_num, block_size, total_size):
        if total_size > 0 and block_num % 50 == 0:
            downloaded = min(block_num * block_size, total_size)
            elapsed = max(time.time() - start_time, 1e-3)
            speed = downloaded / elapsed
            eta = (total_size - downloaded) / max(speed, 1e-3)
            pct = 100.0 * downloaded / total_size
            print(
                f"[{label}] {pct:5.1f}% ({downloaded / 1e6:.1f}/{total_size / 1e6:.1f} MB) | "
                f"Elapsed: {elapsed:.1f}s | ETA: {eta:.1f}s",
                flush=True,
            )

    urllib.request.urlretrieve(url, str(dest_path), reporthook=reporthook)


def prepare_funsd(project_dir: Path):
    """Ensure FUNSD dataset is present at <project_dir>/datasets/funsd/dataset/{training_data,testing_data}."""
    funsd_dir = Path(os.environ.get("FUNSD_DATA_DIR", str(project_dir / "datasets" / "funsd")))
    train_dir = funsd_dir / "dataset" / "training_data" / "annotations"
    test_dir = funsd_dir / "dataset" / "testing_data" / "annotations"

    if train_dir.is_dir() and test_dir.is_dir():
        n_train = len(list(train_dir.glob("*.json")))
        n_test = len(list(test_dir.glob("*.json")))
        print(f"[FUNSD] Ready at {funsd_dir} (train={n_train}, test={n_test})", flush=True)
        return

    print(f"[FUNSD] Downloading FUNSD dataset to {funsd_dir} ...", flush=True)
    funsd_dir.mkdir(parents=True, exist_ok=True)
    zip_path = funsd_dir / "dataset.zip"
    download_with_eta("https://guillaumejaume.github.io/FUNSD/dataset.zip", zip_path, "FUNSD")
    with zipfile.ZipFile(str(zip_path), "r") as zf:
        zf.extractall(str(funsd_dir))
    zip_path.unlink()
    print(f"[FUNSD] Extracted successfully to {funsd_dir}", flush=True)


def prepare_cord(project_dir: Path):
    """Ensure CORD dataset is present at <project_dir>/CORD/{train,dev,test}/{image,json}."""
    cord_dir = Path(os.environ.get("CORD_DATA_DIR", str(project_dir / "CORD")))
    train_json = cord_dir / "train" / "json"
    dev_json = cord_dir / "dev" / "json"
    test_json = cord_dir / "test" / "json"

    if train_json.is_dir() and dev_json.is_dir() and test_json.is_dir():
        n_train = len(list(train_json.glob("*.json")))
        n_dev = len(list(dev_json.glob("*.json")))
        n_test = len(list(test_json.glob("*.json")))
        if n_train >= 800 and n_dev >= 100 and n_test >= 100:
            print(f"[CORD] Ready at {cord_dir} (train={n_train}, dev={n_dev}, test={n_test})", flush=True)
            return

    print(f"[CORD] Downloading CORD-1k archives to {cord_dir} ...", flush=True)
    tmp_dir = project_dir / "datasets" / "_cord_tmp"
    if tmp_dir.exists():
        shutil.rmtree(str(tmp_dir))
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Download official CORD-1k parts 1 & 2 from Google Drive using gdown (handles large-file confirmation tokens)
    drive_ids = [
        ("1MqhTbcj-AHXOqYoeoh12aRUwIprzTJYI", tmp_dir / "CORD-1k-001.zip"),
        ("1wYdp5nC9LnHQZ2FcmOoC0eClyWvcuARU", tmp_dir / "CORD-1k-002.zip"),
    ]
    for file_id, zip_target in drive_ids:
        subprocess.check_call(
            [sys.executable, "-m", "gdown", "--id", file_id, "-O", str(zip_target)]
        )
        with zipfile.ZipFile(str(zip_target), "r") as zf:
            zf.extractall(str(tmp_dir))
        zip_target.unlink()

    extracted_cord = tmp_dir / "CORD"
    if extracted_cord.is_dir():
        if cord_dir.exists():
            shutil.rmtree(str(cord_dir))
        shutil.move(str(extracted_cord), str(cord_dir))
    shutil.rmtree(str(tmp_dir), ignore_errors=True)

    n_train = len(list((cord_dir / "train" / "json").glob("*.json")))
    n_dev = len(list((cord_dir / "dev" / "json").glob("*.json")))
    n_test = len(list((cord_dir / "test" / "json").glob("*.json")))
    print(f"[CORD] Extracted successfully to {cord_dir} (train={n_train}, dev={n_dev}, test={n_test})", flush=True)


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    prepare_funsd(root)
    prepare_cord(root)

