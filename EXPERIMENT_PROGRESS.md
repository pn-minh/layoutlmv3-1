# Colab A100-SXM4-80GB Live Execution & Ablation Tracker

## Hardware, Optimization & Environment Status
- **Compute Instance:** Vast.ai `NVIDIA A100-SXM4-80GB` (`58195778`) — **Status:** 🛑 **DESTROYED** (Halted and deleted per user request to prevent additional costs).
- **Repository:** `https://github.com/pn-minh/layoutlmv3-1` (`main`)
- **Master Deliverables:**
  - Google Drive: `LayoutLMv3_Ablation_Results_Completed_Cells.zip` (All 19 summaries and execution logs).
  - Google Sheets: [Live Tracker](https://docs.google.com/spreadsheets/d/173WXkbMXDCEVs4pYBRNXGTHihOda18adbJRJ7RpFw7o/edit) fully synchronized (39 rows updated).
  - GitHub: All 19 ablation summaries + `FINAL_AGGREGATED_ABLATION_TABLE.md` committed and pushed.

---

## Cell Execution Progress

| Cell | Stage / Experiment | Variant | Dataset | Mode | Status | Elapsed / Est. Time | 3-Seed Precision (%) | 3-Seed Recall (%) | 3-Seed F1 (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cell 1** | Hardware Check & Repo Clone | — | — | — | ✅ Done | `6.0s` (Est. `10-15s`) | — | — | — |
| **Cell 2** | Miniconda (`py3.7`) + Packages Setup | — | — | — | ✅ Done | `178.3s` (`2.97m`) | — | — | — |
| **Cell 3** | Download & Verify `FUNSD` + `CORD` | — | — | — | ✅ Done | `632.1s` (`10.5m`) | — | — | — |
| **Cell 4** | Baseline (3 seeds) | `base` | `FUNSD` | `baseline` | ✅ Done | `2044.8s` (`34.1m`) | `89.32 ± 1.31` | `90.53 ± 0.48` | **`89.92 ± 0.85`** |
| **Cell 5** | Baseline (3 seeds) | `base` | `CORD` | `baseline` | ✅ Done | `7274.8s` (`121.2m`) | `96.50 ± 0.39` | `96.94 ± 0.28` | **`96.72 ± 0.33`** |
| **Cell 6** | Full Model (3 seeds) | `base` | `FUNSD` | `full` | ✅ Done | `4153.8s` (`69.2m`) | `91.82 ± 0.05` | `91.33 ± 0.28` | **`91.58 ± 0.16`** |
| **Cell 7** | Full Model (3 seeds) | `base` | `CORD` | `full` | ✅ Done | `10287.3s` (`171.5m`) | `96.80 ± 0.27` | `97.02 ± 0.15` | **`96.91 ± 0.21`** |
| **Cell 8** | Ablation: w/o Boundary Loss (3 seeds) | `base` | `FUNSD` | `no_boundary` | ✅ Done | `4069.8s` (`67.8m`) | `91.72 ± 0.26` | `91.52 ± 0.15` | **`91.62 ± 0.19`** |
| **Cell 9** | Ablation: w/o Boundary Loss (3 seeds) | `base` | `CORD` | `no_boundary` | ✅ Done | `10034.1s` (`167.2m`) | `97.00 ± 0.18` | `97.12 ± 0.19` | **`97.06 ± 0.18`** |
| **Cell 10** | Ablation: w/o Token-Segment (3 seeds) | `base` | `FUNSD` | `no_segment` | ✅ Done | `2161.8s` (`36.0m`) | `89.54 ± 0.53` | `91.18 ± 0.41` | **`90.36 ± 0.30`** |
| **Cell 11** | Ablation: w/o Token-Segment (3 seeds) | `base` | `CORD` | `no_segment` | ✅ Done | `7620.7s` (`127.0m`) | `96.28 ± 0.71` | `96.89 ± 0.42` | **`96.59 ± 0.57`** |
| **Cell 12** | Ablation: w/o HPE (3 seeds) | `base` | `FUNSD` | `no_hpe` | ✅ Done | `4040.7s` (`67.3m`) | `91.42 ± 0.33` | `91.25 ± 0.33` | **`91.33 ± 0.27`** |
| **Cell 13** | Ablation: w/o HPE (3 seeds) | `base` | `CORD` | `no_hpe` | ✅ Done | `10131.1s` (`168.9m`) | `97.05 ± 0.16` | `97.15 ± 0.16` | **`97.10 ± 0.15`** |
| **Cell 14** | Baseline (3 seeds) | `large` | `FUNSD` | `baseline` | ✅ Done | `4086.8s` (`68.1m`) | `90.69 ± 1.01` | `91.80 ± 0.23` | **`91.24 ± 0.61`** |
| **Cell 15** | Baseline (3 seeds) | `large` | `CORD` | `baseline` | ✅ Done | `10260.0s` (`171.0m`) | `96.96 ± 0.30` | `97.35 ± 0.04` | **`97.15 ± 0.17`** |
| **Cell 16** | Full Model (3 seeds) | `large` | `FUNSD` | `full` | ✅ Done | `6509.2s` (`108.5m`) | `92.31 ± 0.51` | `92.60 ± 0.10` | **`92.45 ± 0.26`** |
| **Cell 17** | Full Model (3 seeds) | `large` | `CORD` | `full` | ✅ Done | `18241.4s` (`304.0m`) | `97.28 ± 0.04` | `97.43 ± 0.04` | **`97.35 ± 0.04`** |
| **Cell 18** | Ablation: w/o Boundary Loss (3 seeds) | `large` | `FUNSD` | `no_boundary` | ✅ Done | `6630.2s` (`110.5m`) | `91.97 ± 0.37` | `92.33 ± 0.23` | **`92.15 ± 0.24`** |
| **Cell 19** | Ablation: w/o Boundary Loss (3 seeds) | `large` | `CORD` | `no_boundary` | ✅ Done | `9413.6s` (`156.9m`) | `96.90 ± 0.49` | `97.12 ± 0.36` | **`97.01 ± 0.42`** |
| **Cell 20** | Ablation: w/o Token-Segment (3 seeds) | `large` | `FUNSD` | `no_segment` | ✅ Done | `4610.1s` (`76.8m`) | `90.34 ± 0.45` | `91.68 ± 0.08` | **`91.01 ± 0.23`** |
| **Cell 21** | Ablation: w/o Token-Segment (3 seeds) | `large` | `CORD` | `no_segment` | ✅ Done | `7863.6s` (`131.1m`) | `96.69 ± 0.15` | `96.98 ± 0.17` | **`96.84 ± 0.13`** |
| **Cell 22** | Ablation: w/o HPE (3 seeds) | `large` | `FUNSD` | `no_hpe` | ✅ Done | `5993.0s` (`99.9m`) | `92.67 ± 0.13` | `92.72 ± 0.28` | **`92.69 ± 0.18`** |
| **Cell 23** | Ablation: w/o HPE (3 seeds) | `large` | `CORD` | `no_hpe` | 🛑 Halted | Stopped per user request | — | — | — |
| **Cell 24** | Final Aggregated Master Table | — | — | — | ✅ Done | Completed | — | — | — |
