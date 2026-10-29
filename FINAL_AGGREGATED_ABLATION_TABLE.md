# LayoutLMv3 Final Aggregated Ablation Results

All experiments evaluated across 3 random seeds (`42, 123, 1993`) on dedicated NVIDIA A100-SXM4-80GB.

| Variant | Dataset | Configuration | Precision (%) | Recall (%) | F1 (%) |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `base` | `FUNSD` | Baseline (Vanilla LayoutLMv3) | `89.32 ± 1.31` | `90.53 ± 0.48` | **`89.92 ± 0.85`** |
| `base` | `FUNSD` | Full Model (HPE + Token-Segment + Boundary Loss) | `91.82 ± 0.05` | `91.33 ± 0.28` | **`91.58 ± 0.16`** |
| `base` | `FUNSD` | Ablation: w/o Boundary Loss | `91.72 ± 0.26` | `91.52 ± 0.15` | **`91.62 ± 0.19`** |
| `base` | `FUNSD` | Ablation: w/o Token-Segment | `89.54 ± 0.53` | `91.18 ± 0.41` | **`90.36 ± 0.30`** |
| `base` | `FUNSD` | Ablation: w/o HPE | `91.42 ± 0.33` | `91.25 ± 0.33` | **`91.33 ± 0.27`** |
| `base` | `CORD` | Baseline (Vanilla LayoutLMv3) | `96.50 ± 0.39` | `96.94 ± 0.28` | **`96.72 ± 0.33`** |
| `base` | `CORD` | Full Model (HPE + Token-Segment + Boundary Loss) | `96.80 ± 0.27` | `97.02 ± 0.15` | **`96.91 ± 0.21`** |
| `base` | `CORD` | Ablation: w/o Boundary Loss | `97.00 ± 0.18` | `97.12 ± 0.19` | **`97.06 ± 0.18`** |
| `base` | `CORD` | Ablation: w/o Token-Segment | `96.28 ± 0.71` | `96.89 ± 0.42` | **`96.59 ± 0.57`** |
| `base` | `CORD` | Ablation: w/o HPE | `97.05 ± 0.16` | `97.15 ± 0.16` | **`97.10 ± 0.15`** |
| `large` | `FUNSD` | Baseline (Vanilla LayoutLMv3) | `90.69 ± 1.01` | `91.80 ± 0.23` | **`91.24 ± 0.62`** |
| `large` | `FUNSD` | Full Model (HPE + Token-Segment + Boundary Loss) | `92.31 ± 0.51` | `92.60 ± 0.10` | **`92.45 ± 0.26`** |
| `large` | `FUNSD` | Ablation: w/o Boundary Loss | `91.97 ± 0.37` | `92.33 ± 0.23` | **`92.15 ± 0.24`** |
| `large` | `FUNSD` | Ablation: w/o Token-Segment | `90.34 ± 0.45` | `91.68 ± 0.08` | **`91.01 ± 0.23`** |
| `large` | `FUNSD` | Ablation: w/o HPE | `92.67 ± 0.13` | `92.72 ± 0.28` | **`92.69 ± 0.18`** |
| `large` | `CORD` | Baseline (Vanilla LayoutLMv3) | `96.96 ± 0.30` | `97.35 ± 0.04` | **`97.15 ± 0.17`** |
| `large` | `CORD` | Full Model (HPE + Token-Segment + Boundary Loss) | `97.28 ± 0.04` | `97.43 ± 0.04` | **`97.35 ± 0.04`** |
| `large` | `CORD` | Ablation: w/o Boundary Loss | `96.90 ± 0.49` | `97.12 ± 0.36` | **`97.01 ± 0.42`** |
| `large` | `CORD` | Ablation: w/o Token-Segment | `96.69 ± 0.15` | `96.98 ± 0.17` | **`96.84 ± 0.13`** |
| `large` | `CORD` | Ablation: w/o HPE | *Stopped by user* | *Stopped by user* | *Stopped by user* |
