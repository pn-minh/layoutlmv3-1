# Weekly Report Presentation — Speaker Script (11 Slides)

* **Presentation Title:** *Weekly report*
* **Presenter:** Pham Nhat Minh (*Major: Information Systems*)
* **Supervisor:** PhD. Pham Thi Quynh Trang (*Faculty of Information Technology, VNU-UET*)
* **Contact:** `pnminh289@gmail.com`
* **Deck Formats:** [weekly_update_slides.pdf](file:///c:/Users/nhatm/.gemini/antigravity/scratch/layoutlmv3-1/thesis/presentation/weekly_update_slides.pdf) | [weekly_update_slides.pptx](file:///c:/Users/nhatm/.gemini/antigravity/scratch/layoutlmv3-1/thesis/presentation/weekly_update_slides.pptx)

---

## Slide 1 — Title Slide

> **[Visual Cue: Show Slide 1 — Clean UET Header, "Weekly report" Title Banner, Presenter & Supervisor Information.]**
>
> "Good morning / afternoon, Ms. Trang. Today's weekly report delivers a focused walkthrough of our **Structure-Aware LayoutLMv3** architecture.
>
> We will examine the internal mechanics of each model component with high-resolution zoomed-in views, and review our latest **Cross-Modal Contrastive Loss** fine-tuning and its empirical impact across all four standard dataset benchmarks."

---

## Slide 2 — Structure-Aware LayoutLMv3 Architecture

> **[Visual Cue: Advance to Slide 2 — High-resolution full model diagram filling the slide.]**
>
> "Slide 2 displays our complete, end-to-end architecture diagram:
> - **Input & Position Stream (Left):** OCR text tokens and document image patches enter with **Hierarchical Position Encoding (HPE)**, adding Line, Column, and Block indices to standard 2D boxes.
> - **Central Backbone:** The **LayoutLMv3 Multimodal Transformer** performs joint self-attention across text subwords and visual image patches.
> - **Context & Classification (Right):** Contextualized text tokens pass through the **Segment Context Module (SCM)** with ReZero residual gating before final token classification.
> - **Multi-Task Supervision (Bottom):** Three complementary loss objectives—**Classification Loss**, **Intra-Line Boundary Loss**, and **Cross-Modal Contrastive Loss**—are optimized jointly."

---

## Slide 3 — Hierarchical Position Encoding (HPE)

> **[Visual Cue: Advance to Slide 3 — Zoomed-in crop of HPE on the left, quick key notes on the right.]**
>
> "Slide 3 presents our first structural module, **Hierarchical Position Encoding (HPE)**:
> - **Structural Hierarchy:** Encodes Line, Column, and Block indices for every word token.
> - **Multi-Column Disambiguation:** Prevents text across adjacent table columns from merging horizontally into one reading line.
> - **Residual Linear Projection:** Concatenates the three hierarchical coordinates and projects them into the backbone hidden dimension.
> - **Adaptive ReZero Gating:** Scaled by $\beta$ initialized at zero, guaranteeing zero initial disturbance to pre-trained weights."

---

## Slide 4 — LayoutLMv3 Multimodal Backbone

> **[Visual Cue: Advance to Slide 4 — Zoomed-in crop of the central Backbone pillar on the left, quick key notes on the right.]**
>
> "Slide 4 focuses on the central multimodal backbone:
> - **Unified Sequence:** Processes text subwords and visual image patches jointly in a single unified sequence.
> - **Model Capacities:** Evaluated on Base (12 layers, 133M parameters) and Large (24 layers, 368M parameters) architectures.
> - **2D Spatial Relative Bias:** Enriches self-attention scores with learned relative horizontal and vertical distance offsets.
> - **Dual Output States:** Emits contextualized word vectors and spatial visual patch vectors for downstream heads."

---

## Slide 5 — Segment Context Module (SCM)

> **[Visual Cue: Advance to Slide 5 — Zoomed-in crop of SCM & Classifier on the left, quick key notes on the right.]**
>
> "Slide 5 covers the **Segment Context Module (SCM)**:
> - **Entity Fragmentation Fix:** Prevents multi-word entities from fracturing into inconsistent word-level labels.
> - **Segment Mean Pooling:** Aggregates individual word tokens into line-level segment representations.
> - **Inter-Segment Transformer:** Captures semantic dependencies across lines throughout the entire page.
> - **ReZero Residual Gate:** Dynamically blends segment-level consensus without losing fine-grained word details.
> - **Late-Fusion Head:** Combines word representations, segment context, and first-token tags prior to final classification."

---

## Slide 6 — Intra-Line Boundary Loss

> **[Visual Cue: Advance to Slide 6 — Zoomed-in crop of Intra-Line Boundary Loss on the left, quick key notes on the right.]**
>
> "Slide 6 highlights the **Intra-Line Boundary Loss**:
> - **Span Merging Prevention:** Separates adjacent key-value pairs that share the same horizontal line (e.g., `TOTAL:` and `$50.00`).
> - **Pairwise Representation:** Evaluates adjacent token pairs along the reading line with an MLP.
> - **Binary Objective:** Directly penalizes false merges between distinct semantic entities.
> - **Zero Inference Latency:** Acts strictly as an auxiliary training regularization loss; discarded at test time with zero extra runtime."

---

## Slide 7 — Cross-Modal Contrastive Loss

> **[Visual Cue: Advance to Slide 7 — Zoomed-in crop of Contrastive Loss on the left, quick key notes on the right.]**
>
> "Slide 7 details our latest fine-tuned **Cross-Modal Contrastive Loss**:
> - **Spatial InfoNCE Alignment:** Pulls text tokens toward their overlapping visual patches in a shared projection space.
> - **Pre-SCM Decoupling:** Grounded on backbone tokens before segment pooling, eliminating previous objective conflicts with SCM.
> - **Detached Visual Anchors:** Freezes patch representations to prevent visual encoder drift during downstream fine-tuning.
> - **Calibrated Loss Weighting:** Scaled to low weights (0.03 for FUNSD, 0.01 for CORD) with temperature $\tau = 0.10$ to regularize cleanly without competing with classification."

---

## Slide 8 — Multi-Task Training Objective

> **[Visual Cue: Advance to Slide 8 — Zoomed-in crop of the unified loss bar on the left, quick key notes on the right.]**
>
> "Slide 8 shows how all three loss functions are synthesized into our multi-task objective:
> - **Unified Loss Formulation:** Integrates classification, boundary, and contrastive objectives together.
> - **Complementary Roles:** Classification sets semantic labels, boundary loss sharpens span edges, and contrastive loss grounds layout.
> - **Joint Optimization:** End-to-end backpropagation allows all modules to mutually reinforce each other.
> - **Best Checkpoint Loading:** Evaluates at peak validation F1 score to eliminate late-epoch training noise."

---

## Slide 9 — Ablation Impact on F1 Score

> **[Visual Cue: Advance to Slide 9 — Ablation table comparing each ablation to the Full Model across 4 benchmarks.]**
>
> "Slide 9 summarizes our ablation results across all four benchmarks:
> - **Peak Overall Performance:** The Full 4-Module Model reaches the highest F1 score across all configurations (93.35% on FUNSD-Large, 92.15% on FUNSD-Base, 97.85% on CORD-Base, 98.25% on CORD-Large).
> - **Contrastive Alignment Impact:** Contrastive Loss provides a decisive $+0.85\% \dots +0.90\%$ F1 boost over the 3-module model without contrastive loss.
> - **Universal Ablation Drop:** Removing any single module causes performance degradation, confirming that all four components are indispensable."

---

## Slide 10 — Summary & Next Milestones

> **[Visual Cue: Advance to Slide 10 — Two-column quick notes on achievements and upcoming tasks.]**
>
> "Slide 10 outlines our recent completions and upcoming tasks:
> - **Current Progress:** Vector model diagram finalized; pre-SCM contrastive alignment refined; turnkey Vast.ai runner established; Google Sheets tracker updated to 49 columns.
> - **Next Priorities:** Finalizing qualitative attention heatmaps for the English thesis; polishing Chapters 4 and 5; completing final multi-seed validation; packaging reproducible code for defense."

---

## Slide 11 — Closing / Thank You

> **[Visual Cue: Advance to Slide 11 — Closing slide with presenter contact details.]**
>
> "Thank you very much, Ms. Trang, for your guidance. My updated contact email is **`pnminh289@gmail.com`**. I would be pleased to answer any questions or discuss next steps."
