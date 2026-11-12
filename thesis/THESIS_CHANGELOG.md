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

## [2026-11-12] OVERLEAF COLLABORATOR & SUPERVISOR REVISION AUDIT (`v0 -> v149`)
- **Project Identity:** `Thesis - Phạm Nhật Minh` (`https://www.overleaf.com/project/6aeeb45d264c70bbb1215bc4`)
- **Owner:** `Minh Pham` (`21020651@vnu.edu.vn`, User ID: `65410c60afb99827363302af`)
- **Invited Collaborator (Supervisor):** `TrangPTQ` (`phamthiquynhtrang95@gmail.com`, User ID: `627484779e22a519f0756650`, Role: `Editor / readAndWrite`)
- **Review Threads & Comments (`/threads` & `/messages`):** `0` open or resolved comment threads; `0` chat messages.
- **Chronological Overleaf Version History (`v0` to `v149`):**
  - **`v0 -> v17` (2026-11-07 12:17 ICT — Minh Pham):** Initial project creation and upload of all 17 thesis files (`main.tex`, `ref.bib`, `chapter0/main.tex`..`chapter5/main.tex`, `chapter2/architecture.png`, `chapter3/model_architecture.pdf`, and 7 files in `frontMatter/`).
  - **`v17 -> v23` (2026-11-09 08:01–08:07 ICT — Minh Pham):** Tested uploading and removing `thesis_en_overleaf.zip`.
  - **`v23 -> v89` (2026-11-09 08:12–08:13 ICT — Minh Pham):** Uploaded extracted package `thesis_en_overleaf_extracted/`, then cleaned up nested subfolder and re-uploaded the 15 chapter/frontMatter files and updated root `main.tex`.
  - **`v89 -> v119` (2026-11-09 17:30–17:31 ICT — Minh Pham):** Refreshed all 15 files inside `chapter0/`–`chapter5/` and `frontMatter/` with updated accuracy and per-class convergence plots.
  - **`v119 -> v149` (2026-11-09 17:34–17:35 ICT — Minh Pham):** Latest Overleaf upload replacing all 15 chapter and frontMatter files.
  - **Supervisor Edits Status:** Confirmed `0` edits or comments made by `TrangPTQ` (`phamthiquynhtrang95@gmail.com`) between `v0` and `v149`. Continuous tracking via Overleaf's `/updates` and `/threads` endpoints is active.
