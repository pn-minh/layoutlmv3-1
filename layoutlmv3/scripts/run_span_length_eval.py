#!/usr/bin/env python3
"""
Computes Entity Span-Length Bucketed F1 (1 token, 2-3 tokens, 4-6 tokens, 7+ tokens)
and Boundary Split/Merge vs. Role Classification Error Breakdown across seeds
from saved test_predictions.txt files.
Outputs: logs/span_length_and_error_analysis.json
"""
import os
import sys
import json
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_DIR)

from datasets import load_dataset, ClassLabel
import layoutlmft.data.funsd
import layoutlmft.data.cord


def extract_spans(bio_tags):
    """Extract (label_type, start_idx, end_idx_inclusive) spans from BIO tag sequence."""
    spans = []
    cur_type = None
    cur_start = None
    for i, tag in enumerate(bio_tags):
        if tag == "O" or tag is None:
            if cur_type is not None:
                spans.append((cur_type, cur_start, i - 1))
                cur_type = None
                cur_start = None
        elif tag.startswith("B-"):
            if cur_type is not None:
                spans.append((cur_type, cur_start, i - 1))
            cur_type = tag[2:]
            cur_start = i
        elif tag.startswith("I-"):
            t = tag[2:]
            if cur_type == t:
                continue
            else:
                if cur_type is not None:
                    spans.append((cur_type, cur_start, i - 1))
                cur_type = t
                cur_start = i
        else:
            if cur_type is not None:
                spans.append((cur_type, cur_start, i - 1))
            cur_type = tag
            cur_start = i
    if cur_type is not None:
        spans.append((cur_type, cur_start, len(bio_tags) - 1))
    return spans


def bucket_name(length: int) -> str:
    if length <= 1:
        return "1_token"
    elif length <= 3:
        return "2_3_tokens"
    elif length <= 6:
        return "4_6_tokens"
    else:
        return "7plus_tokens"


def evaluate_predictions(gold_docs, pred_docs):
    buckets = ["1_token", "2_3_tokens", "4_6_tokens", "7plus_tokens"]
    stats = {b: {"tp": 0, "fp": 0, "fn": 0} for b in buckets}
    error_counts = {
        "boundary_split_merge_errors": 0,
        "role_confusion_exact_span_errors": 0,
        "false_alarm_background_errors": 0,
        "missed_entity_errors": 0,
        "total_gold_spans": 0,
    }

    for gold_seq, pred_seq in zip(gold_docs, pred_docs):
        L = min(len(gold_seq), len(pred_seq))
        gold_spans = extract_spans(gold_seq[:L])
        pred_spans = extract_spans(pred_seq[:L])

        error_counts["total_gold_spans"] += len(gold_spans)
        gold_set = set(gold_spans)
        pred_set = set(pred_spans)

        for sp in gold_spans:
            b = bucket_name(sp[2] - sp[1] + 1)
            if sp in pred_set:
                stats[b]["tp"] += 1
            else:
                stats[b]["fn"] += 1

        for sp in pred_spans:
            b = bucket_name(sp[2] - sp[1] + 1)
            if sp not in gold_set:
                stats[b]["fp"] += 1

        # Classify error types for unmatched gold spans
        pred_by_bounds = {(s, e): t for (t, s, e) in pred_spans}
        for (g_type, g_s, g_e) in gold_spans:
            if (g_type, g_s, g_e) in pred_set:
                continue
            if (g_s, g_e) in pred_by_bounds:
                error_counts["role_confusion_exact_span_errors"] += 1
            else:
                # Check if any predicted span overlaps [g_s, g_e]
                overlaps = [
                    (p_t, p_s, p_e)
                    for (p_t, p_s, p_e) in pred_spans
                    if not (p_e < g_s or p_s > g_e)
                ]
                if overlaps:
                    error_counts["boundary_split_merge_errors"] += 1
                else:
                    error_counts["missed_entity_errors"] += 1

        for (p_type, p_s, p_e) in pred_spans:
            if (p_type, p_s, p_e) in gold_set:
                continue
            overlaps_gold = [
                (g_t, g_s, g_e)
                for (g_t, g_s, g_e) in gold_spans
                if not (g_e < p_s or g_s > p_e)
            ]
            if not overlaps_gold:
                error_counts["false_alarm_background_errors"] += 1

    bucket_f1 = {}
    for b in buckets:
        tp = stats[b]["tp"]
        fp = stats[b]["fp"]
        fn = stats[b]["fn"]
        prec = tp / max(tp + fp, 1)
        rec = tp / max(tp + fn, 1)
        f1 = (2 * prec * rec) / max(prec + rec, 1e-9)
        bucket_f1[b] = {
            "f1": round(f1 * 100.0, 2),
            "precision": round(prec * 100.0, 2),
            "recall": round(rec * 100.0, 2),
            "support": tp + fn,
        }

    return {"bucket_metrics": bucket_f1, "error_breakdown": error_counts}


def load_gold_sequences(dataset_name: str):
    mod = layoutlmft.data.funsd if dataset_name == "funsd" else layoutlmft.data.cord
    ds = load_dataset(os.path.abspath(mod.__file__))
    test_ds = ds["test"]
    col = "ner_tags"
    feat = test_ds.features[col].feature
    label_list = feat.names if isinstance(feat, ClassLabel) else sorted(list({x for seq in test_ds[col] for x in seq}))
    gold_docs = [[label_list[i] for i in seq] for seq in test_ds[col]]
    return gold_docs


def main():
    logs_dir = os.path.join(PROJECT_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    output = {}

    for dataset_name in ["funsd", "cord"]:
        try:
            gold_docs = load_gold_sequences(dataset_name)
        except Exception as e:
            print(f"[WARN] Could not load {dataset_name} gold sequences: {e}")
            continue

        output[dataset_name] = {}
        for variant in ["base", "large"]:
            for mode in ["baseline", "full", "contrastive"]:
                seed_analyses = []
                for seed in [42, 123, 1993]:
                    pred_file = os.path.join(
                        logs_dir,
                        f"{dataset_name}-{variant}-{mode}-seed{seed}",
                        "test_predictions.txt",
                    )
                    if not os.path.exists(pred_file):
                        continue
                    with open(pred_file, "r") as f:
                        pred_docs = [line.strip().split() for line in f if line.strip()]
                    if len(pred_docs) == len(gold_docs):
                        seed_analyses.append(evaluate_predictions(gold_docs, pred_docs))

                if not seed_analyses:
                    continue

                key = f"{variant}_{mode}"
                agg_buckets = {}
                for b in ["1_token", "2_3_tokens", "4_6_tokens", "7plus_tokens"]:
                    f1s = [s["bucket_metrics"][b]["f1"] for s in seed_analyses]
                    agg_buckets[b] = {
                        "mean_f1": round(float(np.mean(f1s)), 2),
                        "std_f1": round(float(np.std(f1s, ddof=1)) if len(f1s) > 1 else 0.0, 2),
                        "support": seed_analyses[0]["bucket_metrics"][b]["support"],
                    }

                agg_errors = {}
                for ek in seed_analyses[0]["error_breakdown"].keys():
                    vals = [s["error_breakdown"][ek] for s in seed_analyses]
                    agg_errors[ek] = round(float(np.mean(vals)), 1)

                output[dataset_name][key] = {
                    "num_seeds": len(seed_analyses),
                    "span_length_buckets": agg_buckets,
                    "error_breakdown": agg_errors,
                }
                print(f"[SPAN EVAL] {dataset_name}-{key}: {agg_buckets}")

    out_path = os.path.join(logs_dir, "span_length_and_error_analysis.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"[SPAN EVAL] Saved analysis to {out_path}")


if __name__ == "__main__":
    main()
