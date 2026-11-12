#!/usr/bin/env python3
"""
Automated Computational Overhead, Inference Latency (ms/doc), and Peak VRAM Benchmark
for Vanilla LayoutLMv3 vs. Full 4-Module Architecture (Base & Large).
Outputs: logs/latency_vram_benchmark.json
"""
import os
import sys
import time
import json
import torch

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_DIR)

from transformers import AutoConfig
from layoutlmft.models.layoutlmv3.modeling_layoutlmv3 import LayoutLMv3ForTokenClassification
from layoutlmft.models.layoutlmv3.modeling_layoutlmv3_segment import LayoutLMv3ForSegmentTokenClassification


def benchmark_config(variant: str, mode: str, num_warmup: int = 10, num_iters: int = 50):
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model_path = f"models/layoutlmv3-{variant}"
    if not os.path.isdir(model_path):
        model_path = f"microsoft/layoutlmv3-{variant}"

    is_full = (mode == "full_4module")
    config = AutoConfig.from_pretrained(
        model_path,
        num_labels=7,
        input_size=224,
        use_hierarchical_position_encoding=is_full,
        max_line_position=100,
        max_block_position=30,
        use_column_encoding=is_full,
        max_column_position=8,
        use_intra_line_boundary=is_full,
        lambda_bound_init=0.1,
        use_token_segment=is_full,
        use_contrastive_loss=is_full,
        lambda_contrastive_init=0.03,
        contrastive_proj_dim=128,
        contrastive_temperature=0.10,
    )

    model_cls = LayoutLMv3ForSegmentTokenClassification if is_full else LayoutLMv3ForTokenClassification
    model = model_cls.from_pretrained(model_path, config=config).to(device)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    B, L = 1, 256
    input_ids = torch.randint(0, 1000, (B, L), device=device)
    bbox = torch.zeros((B, L, 4), dtype=torch.long, device=device)
    bbox[:, :, 2] = 200
    bbox[:, :, 3] = 200
    attention_mask = torch.ones((B, L), dtype=torch.long, device=device)
    images = torch.randn((B, 3, 224, 224), device=device)
    labels = torch.randint(0, 7, (B, L), dtype=torch.long, device=device)

    extra_kwargs = {}
    if is_full:
        extra_kwargs["segment_ids"] = torch.arange(L, device=device).unsqueeze(0) // 4
        extra_kwargs["line_ids"] = torch.arange(L, device=device).unsqueeze(0) // 4
        extra_kwargs["block_ids"] = torch.arange(L, device=device).unsqueeze(0) // 16

    # 1. Inference Latency & Peak Inference VRAM (Batch Size = 1, FP16)
    model.eval()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(device)

    with torch.no_grad(), torch.cuda.amp.autocast(enabled=torch.cuda.is_available()):
        for _ in range(num_warmup):
            _ = model(
                input_ids=input_ids,
                bbox=bbox,
                attention_mask=attention_mask,
                images=images,
                **extra_kwargs,
            )
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        for _ in range(num_iters):
            _ = model(
                input_ids=input_ids,
                bbox=bbox,
                attention_mask=attention_mask,
                images=images,
                **extra_kwargs,
            )
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        t1 = time.perf_counter()

    infer_latency_ms = ((t1 - t0) / num_iters) * 1000.0
    infer_vram_gb = (
        torch.cuda.max_memory_allocated(device) / (1024 ** 3) if torch.cuda.is_available() else 0.0
    )

    # 2. Training Step Time & Peak Training VRAM (Batch Size = 8, FP16)
    model.train()
    B_train = 8
    input_ids_tr = input_ids.repeat(B_train, 1)
    bbox_tr = bbox.repeat(B_train, 1, 1)
    att_tr = attention_mask.repeat(B_train, 1)
    img_tr = images.repeat(B_train, 1, 1, 1)
    lbl_tr = labels.repeat(B_train, 1)
    extra_tr = {k: v.repeat(B_train, 1) for k, v in extra_kwargs.items()}

    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(device)

    for _ in range(5):
        model.zero_grad(set_to_none=True)
        with torch.cuda.amp.autocast(enabled=torch.cuda.is_available()):
            out = model(
                input_ids=input_ids_tr,
                bbox=bbox_tr,
                attention_mask=att_tr,
                images=img_tr,
                labels=lbl_tr,
                **extra_tr,
            )
            loss = out[0] if isinstance(out, tuple) else out.loss
        loss.backward()

    if torch.cuda.is_available():
        torch.cuda.synchronize()
    t2 = time.perf_counter()
    train_iters = 20
    for _ in range(train_iters):
        model.zero_grad(set_to_none=True)
        with torch.cuda.amp.autocast(enabled=torch.cuda.is_available()):
            out = model(
                input_ids=input_ids_tr,
                bbox=bbox_tr,
                attention_mask=att_tr,
                images=img_tr,
                labels=lbl_tr,
                **extra_tr,
            )
            loss = out[0] if isinstance(out, tuple) else out.loss
        loss.backward()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    t3 = time.perf_counter()

    train_step_ms = ((t3 - t2) / train_iters) * 1000.0
    train_vram_gb = (
        torch.cuda.max_memory_allocated(device) / (1024 ** 3) if torch.cuda.is_available() else 0.0
    )

    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return {
        "variant": variant,
        "mode": mode,
        "total_params": int(total_params),
        "total_params_millions": round(total_params / 1e6, 2),
        "trainable_params": int(trainable_params),
        "infer_latency_ms_per_doc": round(infer_latency_ms, 2),
        "infer_throughput_docs_per_sec": round(1000.0 / max(infer_latency_ms, 1e-6), 2),
        "infer_peak_vram_gb": round(infer_vram_gb, 3),
        "train_step_ms_bs8": round(train_step_ms, 2),
        "train_peak_vram_gb_bs8": round(train_vram_gb, 3),
    }


def main():
    os.makedirs(os.path.join(PROJECT_DIR, "logs"), exist_ok=True)
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    print(f"[BENCHMARK] Running Latency & Peak VRAM Benchmark on {gpu_name}...")
    configs = [
        ("base", "baseline"),
        ("base", "full_4module"),
        ("large", "baseline"),
        ("large", "full_4module"),
    ]
    results = {
        "gpu_name": gpu_name,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "benchmarks": {},
    }
    for variant, mode in configs:
        key = f"{variant}_{mode}"
        print(f"  -> Benchmarking {key}...")
        res = benchmark_config(variant, mode)
        results["benchmarks"][key] = res
        print(
            f"     Params: {res['total_params_millions']}M | "
            f"Infer: {res['infer_latency_ms_per_doc']} ms/doc ({res['infer_peak_vram_gb']} GB) | "
            f"Train (BS=8): {res['train_step_ms_bs8']} ms ({res['train_peak_vram_gb_bs8']} GB)"
        )

    out_path = os.path.join(PROJECT_DIR, "logs", "latency_vram_benchmark.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[BENCHMARK] Saved to {out_path}")


if __name__ == "__main__":
    main()
