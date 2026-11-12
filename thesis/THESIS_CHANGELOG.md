# English Thesis PDF — Master Changelog (Local & Overleaf Revisions)

**Project Title:** Enhancing LayoutLMv3 for Key Information Extraction on Visually Rich Documents via Hierarchical Position Encoding, Segment Context Modeling, Intra-Line Boundary Loss, and Cross-Modal Contrastive Alignment
**Overleaf Project:** https://www.overleaf.com/project/6aeeb45d264c70bbb1215bc4
**Local Source Directory:** `thesis/en/` (Extracted Overleaf Package: `thesis_en_overleaf_extracted/`)

---

## [2026-11-12] LOCAL REVISION — Pre-Experiment Infrastructure, Layout Fixes & Diagram Migration
- **Model Architecture Diagram (`Figure 3.1` & `Figure 3.2`):** Adapted the updated Draw.io diagram (`heads_model_architecture_migrated.drawio`) exported to vector PDF (`model_architecture_heads_style.pdf`) and 300 DPI PNG, ensuring crisp visual hierarchy for all four proposed modules (HPE, Token-Segment SCM, Intra-Line Boundary Loss, and Cross-Modal Contrastive Alignment).
- **Table 4.5 Bottom Margin Overflow Fix (`thesis/en/chapter4/main.tex`):** Added `\clearpage` before Table 4.5, changed float placement from `[!htbp]` to dedicated page float `[p]`, tightened `\arraystretch` to `0.92` and `\tabcolsep` to `1.8pt`, and removed redundant vertical rules so the 24-row 3-seed ablation table fits comfortably within the page margins with zero `Overfull \vbox` warnings.
- **Figure 4.3 Legend & Title Overlap Fix (`thesis/en/chapter4/main.tex`):** Increased y-axis headroom (`ymax=99.2` on FUNSD, `ymax=99.6` on CORD), shifted legend boxes (`at={(0.97,0.05)}, anchor=south east`), and added title spacing (`yshift=4pt`) to eliminate all title/legend overlap.
- **Figure 4.4 Y-Axis & Subplot Title Collision Fix (`thesis/en/chapter4/main.tex`):** Shortened y-axis label to `Entity F1 (\%)`, tightened `ylabel shift=-3pt`, widened horizontal separation between subplots (`\hspace{0.03\textwidth}`), and raised `ymax` headroom (`101.5` on FUNSD, `101.0` on CORD).
- **Strict Non-Hyphenation & Veteran DL Reader Style:** Verified 0 word-splitting hyphenations across all 37 pages (`\tolerance=9999`, `\emergencystretch=6em`, `\hyphenpenalty=10000`, `\exhyphenpenalty=10000`), first-person singular pronouns (`I`, `my`), and concise formulation tailored for deep learning researchers.

## [2026-11-09] LOCAL REVISION — Accuracy & Per-Class Convergence Plots Added
- **Section 4.3.1 (`Training Dynamics and Convergence Behavior`):** Added `Figure 4.3` comparing validation entity-level F1 and token-level accuracy progression from 100 to 1,000 steps across FUNSD and CORD (`base` and `large`).
- **Section 4.3.2 (`Per-Class Entity Breakdown`):** Added `Figure 4.4` analyzing per-category F1 improvements (`HEADER`, `QUESTION`, `ANSWER` on FUNSD; `MENU`, `SUB_TOTAL`, `TOTAL` on CORD).

## [2026-11-04] LOCAL REVISION — Comprehensive English Thesis Restructuring
- **Pronoun Standardization:** Converted all first-person plural references (`we`, `our`, `us`) to first-person singular (`I`, `my`, `me`) throughout Chapters 1–5 and Abstract.
- **Veteran DL Reader Streamlining:** Removed textbook definitions of standard cross-entropy, AdamW, and basic precision/recall/F1 equations; focused directly on the mathematical formulation of the four proposed architectural modules.
- **Problem Statement & Real-World Applicability (`Chapter 1` & `Chapter 5`):** Clarified exact multimodal inputs (OCR word tokens, normalized 2D bounding boxes, document page image), BIO entity outputs, and production deployment pathways (invoice/receipt automation, banking KYC, medical form digitization, tax processing).
- **Overleaf Free-Tier Compilation Optimization:** Pre-compiled TikZ/PGF figures into standalone vector PDFs so full compilation completes in `< 5 seconds` on Overleaf's free tier.

## [PENDING SYNC] OVERLEAF COLLABORATOR & SUPERVISOR REVISIONS
- *Tracking Status:* Ready to ingest collaborator/supervisor edits and comments from Overleaf History (`https://www.overleaf.com/project/6aeeb45d264c70bbb1215bc4`).
- *Workflow:* Every change made on Overleaf by the supervisor or author is diffed against `thesis_en_overleaf_extracted/` and logged in this section with date, author, affected chapter/section, and resolution status.
