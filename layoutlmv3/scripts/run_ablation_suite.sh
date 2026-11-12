#!/bin/bash
# Unified runner for Baseline, Full Model, Leave-One-Out Ablations, Sensitivity Sweeps, and Few-Shot Runs
# across FUNSD & CORD (Base & Large, 3 Seeds) — Optimized for Dual A100 GPUs
# Usage: bash scripts/run_ablation_suite.sh <dataset: funsd|cord> <variant: base|large> <mode>
set -e

DATASET="${1:-funsd}"
VARIANT="${2:-base}"
MODE="${3:-baseline}"

# Resolve the layoutlmv3 project root directory dynamically
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
export TOKENIZERS_PARALLELISM=false
export WANDB_DISABLED=true

# Raise file descriptor limit to prevent IPC socket exhaustion on multi-GPU runs
ulimit -n 65535 2>/dev/null || true

# Select pretrained checkpoint (use local models/ folder if downloaded, otherwise HuggingFace Hub)
if [ "$VARIANT" = "base" ]; then
    MODEL_PATH="${MODEL_BASE_PATH:-microsoft/layoutlmv3-base}"
    if [ -d "models/layoutlmv3-base" ]; then
        MODEL_PATH="models/layoutlmv3-base"
    fi
elif [ "$VARIANT" = "large" ]; then
    MODEL_PATH="${MODEL_LARGE_PATH:-microsoft/layoutlmv3-large}"
    if [ -d "models/layoutlmv3-large" ]; then
        MODEL_PATH="models/layoutlmv3-large"
    fi
else
    echo "ERROR: Invalid variant '$VARIANT'. Choose 'base' or 'large'."
    exit 1
fi

# Configure dataset-specific hyperparameters optimized for 2x NVIDIA CMP 170HX (64GB HBM2e VRAM each):
# Leveraging 64GB VRAM per GPU allows larger micro-batches (BS=16 on FUNSD-large, BS=32 on CORD-large)
# and EVAL_BS=64 while preserving the exact effective batch size (16 for FUNSD, 64 for CORD)
# and minimizing PCIe host-to-device transfer overhead.
if [ "$DATASET" = "funsd" ]; then
    LR="1e-5"
    PER_DEV_BS=16
    GRAD_ACC=1
    EVAL_BS=64
    MAX_LINE=100
    MAX_BLOCK=30
    MAX_COL=8
    MAX_STEPS=1000
elif [ "$DATASET" = "cord" ]; then
    LR="3e-5"
    PER_DEV_BS=32
    GRAD_ACC=2
    EVAL_BS=64
    MAX_LINE=80
    MAX_BLOCK=15
    MAX_COL=8
    # 800 steps for CORD allows 4-module multi-task auxiliary heads to reach full convergence
    MAX_STEPS=800
else
    echo "ERROR: Invalid dataset '$DATASET'. Choose 'funsd' or 'cord'."
    exit 1
fi

# Isolate HuggingFace datasets cache in /dev/shm (RAM disk) per cell so parallel GPU workers never collide
export HF_DATASETS_CACHE="/dev/shm/hf_cache_${DATASET}_${VARIANT}_${MODE}"
mkdir -p "$HF_DATASETS_CACHE"

CONT_LAMBDA="0.03"
if [ "$DATASET" = "cord" ]; then
    CONT_LAMBDA="0.01"
fi

EXTRA_ARGS=()
case "$MODE" in
    baseline)
        # Vanilla LayoutLMv3: all added feature flags remain at their default False
        EXTRA_ARGS=()
        ;;
    full)
        # 3-module model: Token-Segment + HPE (Line/Block/Column) + Intra-Line Boundary Loss
        EXTRA_ARGS=(
            --use_segment_head
            --use_token_segment True
            --use_hierarchical_position_encoding
            --max_line_position "$MAX_LINE"
            --max_block_position "$MAX_BLOCK"
            --use_column_encoding True
            --max_column_position "$MAX_COL"
            --use_intra_line_boundary True
            --lambda_bound_init 0.1
        )
        ;;
    contrastive|with_contrastive)
        # Full 4-module model: Token-Segment + HPE + Intra-Line Boundary Loss + Calibrated Cross-Modal Contrastive Loss
        EXTRA_ARGS=(
            --use_segment_head
            --use_token_segment True
            --use_hierarchical_position_encoding
            --max_line_position "$MAX_LINE"
            --max_block_position "$MAX_BLOCK"
            --use_column_encoding True
            --max_column_position "$MAX_COL"
            --use_intra_line_boundary True
            --lambda_bound_init 0.1
            --use_contrastive_loss True
            --lambda_contrastive_init "$CONT_LAMBDA"
            --contrastive_proj_dim 128
            --contrastive_temperature 0.10
        )
        ;;
    no_boundary)
        # Ablation 1 (w/o Boundary Loss): Token-Segment + HPE active; Boundary Loss disabled
        EXTRA_ARGS=(
            --use_segment_head
            --use_token_segment True
            --use_hierarchical_position_encoding
            --max_line_position "$MAX_LINE"
            --max_block_position "$MAX_BLOCK"
            --use_column_encoding True
            --max_column_position "$MAX_COL"
        )
        ;;
    no_segment)
        # Ablation 2 (w/o Token-Segment): HPE + Boundary Loss active; Token-Segment pooling/SCM disabled
        EXTRA_ARGS=(
            --use_segment_head
            --use_token_segment False
            --use_hierarchical_position_encoding
            --max_line_position "$MAX_LINE"
            --max_block_position "$MAX_BLOCK"
            --use_column_encoding True
            --max_column_position "$MAX_COL"
            --use_intra_line_boundary True
            --lambda_bound_init 0.1
        )
        ;;
    no_hpe)
        # Ablation 3 (w/o HPE): Token-Segment + Boundary Loss active; HPE disabled
        EXTRA_ARGS=(
            --use_segment_head
            --use_token_segment True
            --use_intra_line_boundary True
            --lambda_bound_init 0.1
        )
        ;;
    sens_bound_005)
        # Sensitivity Sweep: Boundary Loss weight lambda_bound = 0.05
        EXTRA_ARGS=(
            --use_segment_head
            --use_token_segment True
            --use_hierarchical_position_encoding
            --max_line_position "$MAX_LINE"
            --max_block_position "$MAX_BLOCK"
            --use_column_encoding True
            --max_column_position "$MAX_COL"
            --use_intra_line_boundary True
            --lambda_bound_init 0.05
            --use_contrastive_loss True
            --lambda_contrastive_init "$CONT_LAMBDA"
            --contrastive_proj_dim 128
            --contrastive_temperature 0.10
        )
        ;;
    sens_bound_020)
        # Sensitivity Sweep: Boundary Loss weight lambda_bound = 0.20
        EXTRA_ARGS=(
            --use_segment_head
            --use_token_segment True
            --use_hierarchical_position_encoding
            --max_line_position "$MAX_LINE"
            --max_block_position "$MAX_BLOCK"
            --use_column_encoding True
            --max_column_position "$MAX_COL"
            --use_intra_line_boundary True
            --lambda_bound_init 0.20
            --use_contrastive_loss True
            --lambda_contrastive_init "$CONT_LAMBDA"
            --contrastive_proj_dim 128
            --contrastive_temperature 0.10
        )
        ;;
    sens_tau_007)
        # Sensitivity Sweep: Contrastive temperature tau = 0.07
        EXTRA_ARGS=(
            --use_segment_head
            --use_token_segment True
            --use_hierarchical_position_encoding
            --max_line_position "$MAX_LINE"
            --max_block_position "$MAX_BLOCK"
            --use_column_encoding True
            --max_column_position "$MAX_COL"
            --use_intra_line_boundary True
            --lambda_bound_init 0.1
            --use_contrastive_loss True
            --lambda_contrastive_init "$CONT_LAMBDA"
            --contrastive_proj_dim 128
            --contrastive_temperature 0.07
        )
        ;;
    sens_tau_020)
        # Sensitivity Sweep: Contrastive temperature tau = 0.20
        EXTRA_ARGS=(
            --use_segment_head
            --use_token_segment True
            --use_hierarchical_position_encoding
            --max_line_position "$MAX_LINE"
            --max_block_position "$MAX_BLOCK"
            --use_column_encoding True
            --max_column_position "$MAX_COL"
            --use_intra_line_boundary True
            --lambda_bound_init 0.1
            --use_contrastive_loss True
            --lambda_contrastive_init "$CONT_LAMBDA"
            --contrastive_proj_dim 128
            --contrastive_temperature 0.20
        )
        ;;
    fewshot_base_25)
        # Few-Shot 25% Training Data (37 docs on FUNSD): Baseline
        MAX_STEPS=400
        EXTRA_ARGS=(
            --max_train_samples 37
        )
        ;;
    fewshot_base_50)
        # Few-Shot 50% Training Data (75 docs on FUNSD): Baseline
        MAX_STEPS=600
        EXTRA_ARGS=(
            --max_train_samples 75
        )
        ;;
    fewshot_full_25)
        # Few-Shot 25% Training Data (37 docs on FUNSD): Full 4-Module Model
        MAX_STEPS=400
        EXTRA_ARGS=(
            --max_train_samples 37
            --use_segment_head
            --use_token_segment True
            --use_hierarchical_position_encoding
            --max_line_position "$MAX_LINE"
            --max_block_position "$MAX_BLOCK"
            --use_column_encoding True
            --max_column_position "$MAX_COL"
            --use_intra_line_boundary True
            --lambda_bound_init 0.1
            --use_contrastive_loss True
            --lambda_contrastive_init "$CONT_LAMBDA"
            --contrastive_proj_dim 128
            --contrastive_temperature 0.10
        )
        ;;
    fewshot_full_50)
        # Few-Shot 50% Training Data (75 docs on FUNSD): Full 4-Module Model
        MAX_STEPS=600
        EXTRA_ARGS=(
            --max_train_samples 75
            --use_segment_head
            --use_token_segment True
            --use_hierarchical_position_encoding
            --max_line_position "$MAX_LINE"
            --max_block_position "$MAX_BLOCK"
            --use_column_encoding True
            --max_column_position "$MAX_COL"
            --use_intra_line_boundary True
            --lambda_bound_init 0.1
            --use_contrastive_loss True
            --lambda_contrastive_init "$CONT_LAMBDA"
            --contrastive_proj_dim 128
            --contrastive_temperature 0.10
        )
        ;;
    *)
        echo "ERROR: Invalid mode '$MODE'."
        exit 1
        ;;
esac

if [ -n "$SEEDS_OVERRIDE" ]; then
    read -r -a SEEDS <<< "$SEEDS_OVERRIDE"
else
    SEEDS=(42 123 1993)
fi

BASE_OUT_DIR="./logs/${DATASET}-${VARIANT}-${MODE}"
mkdir -p "./logs"

SUITE_START=$(date +%s)
TOTAL_SEEDS=${#SEEDS[@]}
SEED_IDX=0

for SEED in "${SEEDS[@]}"
do
    SEED_IDX=$((SEED_IDX + 1))
    OUT_DIR="${BASE_OUT_DIR}-seed${SEED}"

    echo ""
    echo "============================================================"
    echo "[RUN ${SEED_IDX}/${TOTAL_SEEDS}] DATASET=${DATASET} | VARIANT=${VARIANT} | MODE=${MODE} | SEED=${SEED}"
    echo "============================================================"

    # Skip seed if evaluation results AND trainer_state.json already exist
    if [ -f "$OUT_DIR/eval_results.json" ] && [ -f "$OUT_DIR/trainer_state.json" ]; then
        echo "[SKIP] Seed ${SEED} already completed at $OUT_DIR/eval_results.json"
        continue
    fi

    rm -rf "$OUT_DIR"
    SEED_START=$(date +%s)

    CACHE_ARGS=()
    if [ "$SEED_IDX" -eq 1 ]; then
        CACHE_ARGS=(--overwrite_cache)
    fi

    # Run training with Dual-CMP-170HX (64GB HBM2e) hardware & stability optimizations:
    # 1. --fp16 True + TF32: Mixed precision on GA100 Ampere Tensor Cores
    # 2. --save_strategy no + In-RAM Best Checkpoint: Avoids 4.3GB PCIe Gen1/2 & 20GB overlay disk stalls every 100 steps
    # 3. --return_entity_level_metrics True: Logs per-class F1 & step-by-step accuracy/F1 curves at every eval step
    export SKIP_SAVE_MODEL_BIN=1
    python examples/run_funsd_cord.py \
        --dataset_name "$DATASET" \
        --do_train \
        --do_eval \
        --do_predict \
        --return_entity_level_metrics True \
        --model_name_or_path "$MODEL_PATH" \
        --output_dir "$OUT_DIR" \
        --segment_level_layout 1 \
        --visual_embed 1 \
        --input_size 224 \
        --max_steps "$MAX_STEPS" \
        --save_strategy no \
        --evaluation_strategy steps \
        --eval_steps 100 \
        --learning_rate "$LR" \
        --warmup_ratio 0.1 \
        --per_device_train_batch_size "$PER_DEV_BS" \
        --per_device_eval_batch_size "$EVAL_BS" \
        --gradient_accumulation_steps "$GRAD_ACC" \
        --fp16 True \
        --dataloader_num_workers 4 \
        --dataloader_pin_memory True \
        --group_by_length True \
        --report_to none \
        --seed "$SEED" \
        --overwrite_output_dir \
        "${CACHE_ARGS[@]}" \
        "${EXTRA_ARGS[@]}"

    SEED_END=$(date +%s)
    SEED_ELAPSED=$((SEED_END - SEED_START))
    REMAINING_SEEDS=$((TOTAL_SEEDS - SEED_IDX))
    EST_REMAINING=$((REMAINING_SEEDS * SEED_ELAPSED))
    # Remove multi-GB model weight binary & intermediate checkpoints after evaluation to preserve container disk space
    rm -f "$OUT_DIR/pytorch_model.bin"
    rm -rf "$OUT_DIR"/checkpoint-*
    echo "[CELL TIMING] Seed ${SEED} finished in ${SEED_ELAPSED}s | Estimated time left for this cell: ${EST_REMAINING}s"
done

# Clean up temporary RAM-disk dataset cache for this cell
rm -rf "$HF_DATASETS_CACHE"

echo ""
echo "============================================================"
echo "CALCULATING MULTI-SEED SUMMARY + STEP CURVES + PER-CLASS METRICS: ${DATASET} | ${VARIANT} | ${MODE}"
echo "============================================================"

export BASE_OUT_DIR DATASET VARIANT MODE
python - <<'PY'
import os
import json
import numpy as np

base_dir = os.environ["BASE_OUT_DIR"]
dataset = os.environ["DATASET"]
variant = os.environ["VARIANT"]
mode = os.environ["MODE"]

seeds = [42, 123, 1993]
core_metrics = [
    "eval_precision",
    "eval_recall",
    "eval_f1",
    "eval_accuracy",
    "eval_loss",
]

results = {m: [] for m in core_metrics}
per_class_raw = {}
per_seed = {}
step_curves_raw = {}

active_seeds = []
for seed in seeds:
    eval_path = f"{base_dir}-seed{seed}/eval_results.json"
    state_path = f"{base_dir}-seed{seed}/trainer_state.json"
    if not os.path.exists(eval_path):
        continue
    active_seeds.append(seed)
    print(f"\nSeed {seed}:")
    with open(eval_path, "r") as f:
        data = json.load(f)
    per_seed[str(seed)] = {}
    for metric in core_metrics:
        if metric in data:
            val = float(data[metric])
            results[metric].append(val)
            per_seed[str(seed)][metric] = val
            print(f"  {metric:18s} = {val:.6f}")

    # Collect per-class entity metrics (e.g. eval_HEADER_f1, eval_QUESTION_f1, eval_ANSWER_f1)
    for k, v in data.items():
        if k.startswith("eval_") and k not in core_metrics and isinstance(v, (int, float)):
            if k not in per_class_raw:
                per_class_raw[k] = []
            per_class_raw[k].append(float(v))
            per_seed[str(seed)][k] = float(v)

    # Collect step-by-step evaluation history from trainer_state.json
    if os.path.exists(state_path):
        try:
            with open(state_path, "r") as sf:
                state_data = json.load(sf)
            for entry in state_data.get("log_history", []):
                if "eval_f1" in entry and "step" in entry:
                    step_str = str(int(entry["step"]))
                    if step_str not in step_curves_raw:
                        step_curves_raw[step_str] = {m: [] for m in core_metrics}
                    for m in core_metrics:
                        if m in entry:
                            step_curves_raw[step_str][m].append(float(entry[m]))
        except Exception as e:
            print(f"  [WARN] Could not parse trainer_state.json for seed {seed}: {e}")

print("\n" + "=" * 70)
print(f"FINAL RESULT ({dataset.upper()} - {variant.upper()} - {mode.upper()}): MEAN ± STD")
print("=" * 70)

summary = {
    "dataset": dataset,
    "variant": variant,
    "mode": mode,
    "seeds": active_seeds,
    "per_seed": per_seed,
    "mean_std": {},
    "metrics": {},
    "per_class_metrics": {},
    "step_history": {},
}

for metric in core_metrics:
    values = results[metric]
    if not values:
        print(f"{metric:18s}: NO DATA")
        continue
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    print(f"{metric:18s}: {mean:.4f} ± {std:.4f}  (pct: {mean*100:.2f} ± {std*100:.2f})")
    summary["mean_std"][metric] = {"mean": mean, "std": std}
    summary["metrics"][metric] = {
        "values": values,
        "mean": mean,
        "std": std,
        "mean_pct": round(mean * 100, 2),
        "std_pct": round(std * 100, 2),
    }

for k, values in sorted(per_class_raw.items()):
    if not values:
        continue
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    summary["per_class_metrics"][k] = {
        "values": values,
        "mean": mean,
        "std": std,
        "mean_pct": round(mean * 100, 2),
        "std_pct": round(std * 100, 2),
    }

for step_str in sorted(step_curves_raw.keys(), key=lambda x: int(x)):
    summary["step_history"][step_str] = {}
    for m, values in step_curves_raw[step_str].items():
        if values:
            mean = float(np.mean(values))
            std = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
            summary["step_history"][step_str][m] = {
                "mean": mean,
                "std": std,
                "mean_pct": round(mean * 100, 2),
                "std_pct": round(std * 100, 2),
            }

output_summary_file = f"{base_dir}_3seed_summary.json"
with open(output_summary_file, "w") as f:
    json.dump(summary, f, indent=2)

print("=" * 70)
print("Saved summary:", output_summary_file)
PY
