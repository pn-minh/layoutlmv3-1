# Weekly Report Presentation — Full Speaker Script (20 Slides)

* **Presentation Title:** *Research on Enhancing Vision-Language Model for Document Key Information Extraction*
* **Subtitle:** *Weekly report*
* **Presenter:** Pham Nhat Minh (*Major: Information Systems*)
* **Supervisor:** PhD. Pham Thi Quynh Trang (Faculty of Information Technology, VNU-UET)
* **Slide Deck:** [weekly_update_slides.pdf](file:///c:/Users/nhatm/.gemini/antigravity/scratch/layoutlmv3-1/thesis/presentation/weekly_update_slides.pdf) | [weekly_update_slides.pptx](file:///c:/Users/nhatm/.gemini/antigravity/scratch/layoutlmv3-1/thesis/presentation/weekly_update_slides.pptx)

---

## Slide 1 — Title Slide

> **[Visual Cue: Show Slide 1 — Title Banner ("Weekly report"), Presenter Card ("Pham Nhat Minh — Major: Information Systems"), and Supervisor Card ("Supervisor: PhD. Pham Thi Quynh Trang").]**
>
> "Good morning / Good afternoon, Ms. Trang. Today's weekly report presents the latest architectural refinements, visual formulations, and multi-seed experimental results for the thesis: **'Research on Enhancing Vision-Language Model for Document Key Information Extraction.'**
>
> As discussed previously, this updated thesis title keeps the high-level scope concise and clear for the evaluation committee without spoiling the four internal module names on the cover page."

---

## Slide 2 — Table of Contents

> **[Visual Cue: Advance to Slide 2 — Clean 8-Section Roadmap.]**
>
> "The presentation is structured into eight focused sections across twenty visual slides:
> 1. **Model Architecture & Backbone**
> 2. **Hierarchical Position Encoding (HPE)**
> 3. **Segment Context Module (SCM)**
> 4. **Masked Gated Late-Fusion**
> 5. **Intra-Line Boundary Loss**
> 6. **Experimental Setup & Datasets**
> 7. **Experimental Results & Ablations**
> 8. **Future Plans**"

---

## Slide 3 — End-to-End Model Architecture

> **[Visual Cue: Advance to Slide 3 — Full End-to-End Architecture Diagram.]**
>
> "Slide 3 displays the complete end-to-end architecture diagram:
> - **Before the backbone (bottom-left):** Raw OCR bounding boxes are grouped into reading lines, multi-column slots, and semantic blocks by **Hierarchical Position Encoding (HPE)** and projected into the input embedding stream.
> - **Inside the center:** The **LayoutLMv3 Backbone** performs unified multimodal self-attention across text tokens and visual image patches, outputting contextual token states $\mathbf{h}_i$.
> - **After the backbone (top-right and bottom-right):** Token states $\mathbf{h}_i$ branch into two complementary paths: a direct token shortcut path and the **Segment Context Module (SCM)** path. Both feed into the neural classification heads to produce **Token Logits** and **Segment Logits**, which are combined via **Masked Gated Late-Fusion** and trained jointly with the **Intra-Line Boundary Loss**."

---

## Slide 4 — LayoutLMv3 Backbone Overview

> **[Visual Cue: Advance to Slide 4 — Visual Shape Flow of the LayoutLMv3 Backbone.]**
>
> "Slide 4 illustrates the **LayoutLMv3 Backbone** as a four-stage visual flow:
> 1. **Raw Document Inputs:** The document image ($224 \times 224$ RGB page), OCR text subwords $w_i$, and normalized 2D bounding boxes $[x_0, y_0, x_1, y_1] \in [0, 1000]$.
> 2. **Modality Embeddings:** Linearly projected $16 \times 16$ visual patches, RoBERTa subword vectors, and 2D spatial embeddings augmented with the proposed **HPE** layout indices.
> 3. **Unified Multimodal Transformer:** Joint self-attention with 2D spatial bias, evaluated at both `base` scale (12 layers, $d=768$) and `large` scale (24 layers, $d=1024$).
> 4. **Contextual Output:** Contextual token hidden states $\mathbf{h}_i \in \mathbb{R}^d$, which are passed downstream to the Segment Context Module and classifier heads."

---

## Slide 5 — Backbone Limitations & Proposed Solutions

> **[Visual Cue: Advance to Slide 5 — 4-Column Table Pairing Each Backbone Limitation with a Real-Life Document Example and Proposed Solution.]**
>
> "While LayoutLMv3 provides strong multimodal representations, four structural limitations arise on real-world forms and receipts, shown in the table on Slide 5:
> 1. **Flat 2D Coordinates:** Raw $[x_0, y_0, x_1, y_1]$ coordinates lack explicit reading lines, table columns, and blocks. On a two-column fax row like `FAX: (336)... | PHONE: (336)...`, the baseline confuses left and right columns. **Proposed Solution:** **Hierarchical Position Encoding (HPE)**.
> 2. **Mid-Span Label Noise:** Multi-word entities such as `June Flynn for Eric Brown/...` fracture mid-line into inconsistent BIO tags (`B-ANS`, `O`, `I-ANS`). **Proposed Solution:** **Segment Context Module (SCM)**.
> 3. **Whole-Segment Drift:** Pure segment pooling can overwrite fine-grained subword boundaries on complex receipt lines like `TOTAL (Qty 2.00) 60.000`. **Proposed Solution:** **Masked Gated Late-Fusion**.
> 4. **Span Merging:** Adjacent key–value entities on the same horizontal line—such as `TO: George Baroody`—frequently merge into a single span. **Proposed Solution:** **Intra-Line Boundary Loss**."

---

## Slide 6 — Module 1: Hierarchical Position Encoding (HPE) — Visual Grouping

> **[Visual Cue: Advance to Slide 6 — Cropped Real-Life FUNSD Fax Cover Sheet (Left) and 3-Stage Visual Grouping Cards (Right).]**
>
> "Slide 6 shows **Module 1: Hierarchical Position Encoding (HPE)** on a real cropped FUNSD fax form (`82092117.png`):
> 1. **Line Grouping (`Line 1..5`, shown in blue):** Bounding boxes whose vertical overlap exceeds $50\%$ of the smaller box height are grouped into the same horizontal reading line.
> 2. **Column Detection (`Column 0..1`, shown in green):** Within `Line 2`, the horizontal jump between `(336) 335-7392` and `PHONE NUMBER:` exceeds $12\%$ of the page width, automatically separating the row into `Column 0` and `Column 1`.
> 3. **Block Grouping (`Block 0..1`, shown in orange):** Consecutive reading lines whose vertical gap is less than $1.8\times$ the median line height are grouped into coherent regions—separating `Block 0 (Header)` from `Block 1 (Form Body)`."

---

## Slide 7 — Module 1: Hierarchical Position Encoding (HPE) — Core Implementation

> **[Visual Cue: Advance to Slide 7 — Shape Diagram of Embedding Concatenation/Projection (Left) and Dark-Mode Python Code for `LayoutLMv3Embeddings.forward` (Right).]**
>
> "Slide 7 presents the core implementation of HPE inside `LayoutLMv3Embeddings.forward`:
> - As visualized on the left, the discrete `line_ids`, `block_ids`, and scaled `column_ids` ($0.3\times$) are embedded into $128$-dimensional vectors, concatenated into a $384$-dimensional hierarchical descriptor, and projected to hidden size $d$ via `hierarchical_proj`.
> - In the dark-mode code snippet on the right, lines 330–335 show the exact three lookup operations, `torch.cat([l_emb, b_emb, c_emb], dim=-1)`, and the residual addition into `embeddings` prior to `LayerNorm`."

---

## Slide 8 — Module 2: Segment Context Module (SCM) — Visual Concept

> **[Visual Cue: Advance to Slide 8 — Cropped Real-Life FUNSD Multi-Word Field (Top) and 4-Stage Visual Pipeline (Bottom).]**
>
> "Slide 8 illustrates **Module 2: Segment Context Module (SCM)** on the multi-word `SENDER/PHONE NUMBER:` row from FUNSD:
> - Without segment pooling, the 8 tokens of `June Flynn for Eric Brown/(614) 466-8980` are classified independently and often fracture mid-span.
> - SCM resolves this in four visual steps:
>   1. **Mean Pool:** Average all 8 token vectors in Segment $k$ into a single segment vector $\mathbf{s}_k$.
>   2. **Segment Attention:** Pass all page segments through a lightweight 1-layer, 4-head Transformer so `Segment k (ANSWER)` attends directly to `Segment k-1 (QUESTION: SENDER/PHONE NUMBER:)`.
>   3. **ReZero Gate ($g$):** Blend the contextualized segment vector smoothly via $\mathbf{s}_k + g(\mathbf{c}_k - \mathbf{s}_k)$, where $g$ starts at $0$ to preserve pretrained representations at step 0.
>   4. **Broadcast + Onset:** Broadcast the refined segment representation back to all 8 tokens and add an onset embedding so `June` is tagged `B-ANSWER` and the remaining 7 tokens are tagged `I-ANSWER`."

---

## Slide 9 — Module 2: Segment Context Module (SCM) — Core Implementation

> **[Visual Cue: Advance to Slide 9 — Shape Diagram of `_segment_pool_and_contextualize` (Left) and Dark-Mode Python Code (Right).]**
>
> "Slide 9 shows the core function `_segment_pool_and_contextualize` in `modeling_layoutlmv3_segment.py`:
> - First, `text_hidden[b, seg_b == sid].mean(dim=0)` computes the mean-pooled vector for each unique segment ID.
> - Next, `self.segment_context` applies inter-segment self-attention, stabilized by the learnable ReZero parameter `self.segment_context_gate`.
> - Finally, `is_first` detects segment onset transitions (`segment_ids[:, 1:] != segment_ids[:, :-1]`) and adds `self.is_first_token_embedding(is_first)` to distinguish `B-` anchors from `I-` continuations."

---

## Slide 10 — Module 3: Masked Gated Late-Fusion — Visual Concept

> **[Visual Cue: Advance to Slide 10 — Cropped Real-Life CORD Receipt Total Line (Left) and 2-Case Routing Diagram (Right).]**
>
> "Slide 10 demonstrates **Module 3: Masked Gated Late-Fusion** using a cropped retail receipt from the **CORD** test set:
> - On the receipt total line `TOTAL (Qty 2.00) 60.000`, different tokens have different granularity requirements:
>   - **Case 1 — Segment Anchor (`Mask = 0`, shown in blue on `TOTAL`):** The first token of a segment is locked to **100% Segment Logits**, anchoring the entity class to the segment-level consensus.
>   - **Case 2 — Internal Subwords (`Mask = 1`, shown in orange on `(Qty 2.00) 60.000`):** Continuation subwords receive a **Gated Blend ($\alpha$)** of Segment Logits and Token Shortcut Logits, allowing subword-level precision where a single visual line contains both quantity and total price sub-fields."

---

## Slide 11 — Module 3: Masked Gated Late-Fusion — Core Implementation

> **[Visual Cue: Advance to Slide 11 — Shape Gate Circuit (Left) and Dark-Mode Python Code for `LayoutLMv3ForSegmentTokenClassification.forward` (Right).]**
>
> "Slide 11 presents the core implementation inside `LayoutLMv3ForSegmentTokenClassification.forward`:
> - Two linear heads compute `token_logits` (from `text_hidden`) and `seg_logits` (from `seg_repr`).
> - `subword_mask = (1 - is_first).unsqueeze(-1).float()` evaluates to `0.0` on segment anchors and `1.0` on continuation subwords.
> - The bounded gate `alpha = self.alpha_max * torch.sigmoid(self.fusion_gate)` blends the two logit streams via `seg_logits + subword_mask * alpha * (token_logits - seg_logits)`."

---

## Slide 12 — Module 4: Intra-Line Boundary Loss — Visual Concept

> **[Visual Cue: Advance to Slide 12 — Cropped Real-Life FUNSD Form Showing Red Vertical Boundary Markers (Left) and Pair Target Comparison (Right).]**
>
> "Slide 12 illustrates **Module 4: Intra-Line Boundary Loss** on six consecutive rows of the FUNSD form:
> - On form lines like `TO: | George Baroody`, `FAX NUMBER: | (336) 335-7392`, and `DATE: | 12/10/98`, a `QUESTION` span (blue) is immediately followed by an `ANSWER` span (green) on the exact same horizontal line.
> - By supervising every adjacent token pair $(i, i+1)$:
>   - Pairs **inside the same span** (e.g., `["FAX", "NUMBER:"]`) share the same entity ID and receive **Target = 0**.
>   - Pairs **across an entity boundary** (e.g., `["NUMBER:", "(336)"]`, marked by the red vertical bars) have different entity IDs and receive **Target = 1**, explicitly training the encoder to sharpen intra-line transitions."

---

## Slide 13 — Module 4: Intra-Line Boundary Loss — Core Implementation

> **[Visual Cue: Advance to Slide 13 — Shape Flow of `_compute_boundary_loss` (Left) and Dark-Mode Python Code (Right).]**
>
> "Slide 13 shows the implementation of `_compute_boundary_loss`:
> - Adjacent hidden states `text_hidden[:, :-1, :]` and `text_hidden[:, 1:, :]` are concatenated along the feature dimension (`2d`) and scored by the 2-layer MLP `self.boundary_classifier`.
> - Ground-truth boundary targets `b_labels = (entity_ids[:, :-1] != entity_ids[:, 1:]).float()` are supervised via `F.binary_cross_entropy_with_logits` over all valid non-padding token pairs."

---

## Slide 14 — Experimental Setup: Hardware, Environment & Datasets

> **[Visual Cue: Advance to Slide 14 — Side-by-Side Tables for Remote Training Machine & Benchmark Datasets.]**
>
> "Moving to Section 6 on Slide 14, all training and ablation experiments were executed on a unified remote GPU server equipped with an **NVIDIA A100-SXM4-80GB GPU** and 167 GiB of system RAM, running Ubuntu Linux, Python 3.7.16, PyTorch 1.10.0 with FP16 mixed precision, and strict entity-level `seqeval` evaluation across **three random seeds (`42`, `123`, `1993`)**.
>
> Evaluation covers two complementary benchmarks:
> - **FUNSD:** 199 scanned forms (149 train, 50 test) with 3 entity classes (7 BIO tags) and irregular multi-column layouts.
> - **CORD:** 1,000 retail receipts (800 train, 100 validation, 100 test) with 30 fine-grained entity classes (61 BIO tags)."

---

## Slide 15 — Run Configurations & Hyperparameters

> **[Visual Cue: Advance to Slide 15 — Large-Font Run Configuration Table Across All 4 Regimes.]**
>
> "Slide 15 lists the exact run configurations across all four regimes (`FUNSD-base`, `CORD-base`, `FUNSD-large`, and `CORD-large`):
> - Every configuration trains for **1,000 optimization steps** with a 10% linear warmup (100 steps) using AdamW.
> - Differential learning rates are applied: the pretrained backbone uses $5 \times 10^{-5}$ ($1 \times 10^{-5}$ on `FUNSD-large`), while the newly initialized modules (HPE, SCM, Late-Fusion, and Boundary Classifier) use $5 \times 10^{-4}$."

---

## Slide 16 — Experimental Results: Baseline vs. Proposed Model (3 Seeds)

> **[Visual Cue: Advance to Slide 16 — Large-Font 3-Seed Comparison Table (Left) and Dual Bar Charts (Right).]**
>
> "Slide 16 presents the primary 3-seed comparison between the vanilla LayoutLMv3 Baseline and the Proposed Model:
> - **On FUNSD (`base`):** Entity F1 improves from **$89.92 \pm 0.85\%$** to **$91.58 \pm 0.16\%$** (**$+1.66\%$** absolute gain), while reducing seed standard deviation by over **$5\times$**.
> - **On FUNSD (`large`):** Entity F1 improves from **$91.24 \pm 0.62\%$** to **$92.45 \pm 0.26\%$** (**$+1.21\%$** gain).
> - **On CORD (`base` and `large`):** Even against a nearly saturated baseline above $96.7\%$, the proposed model consistently improves both Precision and Recall, reaching **$96.91 \pm 0.21\%$** on `base` and **$97.35 \pm 0.04\%$** on `large`."

---

## Slide 17 — Component Ablation Study (3-Seed Mean ± Std F1 %)

> **[Visual Cue: Advance to Slide 17 — Full 5-Row Leave-One-Out Ablation Table and Key Finding Callouts.]**
>
> "Slide 17 reports the leave-one-out component ablation study across 19 completed model-dataset-ablation cells (57 training runs):
> - **Removing the Segment Context Module (`w/o Segment`, Row 5)** causes the steepest performance drop across every single regime: **$-1.44\%$ F1** on `FUNSD-large` ($92.45\% \to 91.01\%$) and **$-1.22\%$ F1** on `FUNSD-base` ($91.58\% \to 90.36\%$). This confirms that segment-level contextual pooling is the primary driver of entity coherence.
> - **Removing the Boundary Loss (`w/o Boundary Loss`, Row 3)** degrades `large` F1 by **$-0.30\%$** on FUNSD and **$-0.34\%$** on CORD, while increasing seed variance on `CORD-large` more than tenfold ($\pm 0.04\% \to \pm 0.42\%$).
> - **Removing HPE (`w/o HPE`, Row 4)** reduces `FUNSD-base` F1 by **$-0.25\%$** ($91.58\% \to 91.33\%$), confirming that explicit line, column, and block indices provide valuable spatial inductive bias for smaller backbones."

---

## Slide 18 — Entity-Level Error Breakdown on FUNSD

> **[Visual Cue: Advance to Slide 18 — Entity-Level Error Table (Left) and Span Boundary Error Bar Chart (Right).]**
>
> "To verify *how* the proposed modules improve extraction quality, Slide 18 breaks down all $1,998$ ground-truth test entities on FUNSD:
> - **Exact Span & Class Matches (True Positives)** increase by **$+24$ entities** ($1,806 \to 1,830$).
> - Most importantly, **Span Boundary Errors**—where the model predicts the right entity location but splits or merges the span boundaries—drop by **$82.6\%$**, from **$23$ errors** in the baseline down to just **$4$ errors** in the proposed model (eliminating all $4$ boundary-plus-label errors completely).
> - Missed entities (FN) and spurious predictions (FP) also decrease by $8$ and $13$, respectively."

---

## Slide 19 — Future plans

> **[Visual Cue: Advance to Slide 19 — Three Clean Milestone Cards.]**
>
> "Slide 19 outlines the three key milestones for the upcoming week:
> 1. **Fine-Tuning on FUNSD and CORD Datasets:** Conduct targeted hyperparameter refinement for the fusion gate ceiling $\alpha_{\max}$, boundary loss weight $\lambda_{\text{bound}}$, and column scaling factor.
> 2. **Final Ablation Verification and Visual Case Studies:** Complete qualitative side-by-side prediction visualizations for Chapter 4 of the thesis.
> 3. **Continuous In-Depth Review of Thesis Papers:** Thoroughly proofread both the English and Vietnamese thesis manuscripts (`thesis_en.pdf` and `thesis_vi.pdf`) to ensure full consistency across all tables, figures, and citations."

---

## Slide 20 — Closing Slide

> **[Visual Cue: Advance to Slide 20 — Closing Slide Expressing Gratitude to Supervisor PhD. Pham Thi Quynh Trang.]**
>
> "That concludes this weekly progress report. Thank you very much, Ms. Trang, for your dedicated mentorship, insightful scientific guidance, and continuous encouragement throughout this research. I look forward to your feedback and questions."
