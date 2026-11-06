# Weekly Report Presentation — Speaker Script (12 Slides)

* **Presentation Title:** *Research on Enhancing Vision-Language Model for Document Key Information Extraction*
* **Subtitle:** *Weekly Progress Report: Model Architecture Walkthrough & Contrastive Alignment*
* **Presenter:** Pham Nhat Minh (*Major: Information Systems*)
* **Supervisor:** PhD. Pham Thi Quynh Trang (*Faculty of Information Technology, VNU-UET*)
* **Deck Formats:** [weekly_update_slides.pdf](file:///c:/Users/nhatm/.gemini/antigravity/scratch/layoutlmv3-1/thesis/presentation/weekly_update_slides.pdf) | [weekly_update_slides.pptx](file:///c:/Users/nhatm/.gemini/antigravity/scratch/layoutlmv3-1/thesis/presentation/weekly_update_slides.pptx)

---

## Slide 1 — Title Slide

> **[Visual Cue: Show Slide 1 — UET Logo, University Header, Presentation Title Card, Presenter & Supervisor Information.]**
>
> "Good morning / afternoon, Ms. Trang. Today's weekly report delivers a focused, in-depth walkthrough of our **Structure-Aware LayoutLMv3** architecture diagram.
>
> We will examine the exact internal mechanics of each model component—accompanied by high-resolution zoomed-in views—and review the latest implementation of our **Cross-Modal Contrastive Loss** along with its fine-tuned impact across all four standard dataset benchmarks."

---

## Slide 2 — Full End-to-End Model Architecture

> **[Visual Cue: Advance to Slide 2 — Full Model Architecture diagram on the left, high-level summary cards on the right.]**
>
> "Slide 2 displays our complete, end-to-end architecture diagram:
> - **Input & Positional Encoding (Left):** Raw visual document images and OCR text tokens enter along with our **Hierarchical Position Encoding (HPE)**, which enriches standard 2D bounding boxes with Line, Column, and Block identifiers.
> - **Central Pillar:** The **LayoutLMv3 Backbone** performs unified multimodal self-attention over text subwords and image patches.
> - **Downstream Classification & Context (Top-Right):** Output text tokens branch into the **Segment Context Module (SCM)**, which pools words into entity segments and contextualizes them via a dedicated Transformer with ReZero residual gating before Softmax classification.
> - **Auxiliary Training Objectives (Bottom):** The model is supervised by three complementary loss functions: the primary **Classification Loss**, the **Intra-Line Boundary Loss**, and our newly fine-tuned **Cross-Modal Contrastive Loss**, all integrated into a unified multi-task training objective."

---

## Slide 3 — Component 1: Input Representation & Modality Embeddings

> **[Visual Cue: Advance to Slide 3 — Zoomed-in crop of the Input Module on the left, bulletpoint breakdown on the right.]**
>
> "Let us look closely at the Input Module shown on the left of Slide 3:
> - **Raw Triplet Inputs:** The input consists of the document page resized to $224 \times 224$ RGB pixels, OCR subwords tokenized by RoBERTa's Byte-Pair Encoding ($V = 50{,}265$), and normalized integer bounding box coordinates in the range $[0, 1000]$.
> - **Visual Projection:** The image is partitioned into a uniform $14 \times 14$ grid of $196$ patches ($16 \times 16$ pixels each) and linearly projected to the model dimension $d$, combined with visual position embeddings.
> - **Text & Spatial Embedding:** Text tokens receive standard 1D sequential positions ($0 \dots 511$) alongside four learned 2D coordinate embedding tables representing $[x_0, y_0, x_1, y_1]$.
> - **The Fundamental Limitation:** Standard multimodal models treat text as isolated, flat bounding boxes scattered across a Cartesian grid. They completely lack topological awareness of reading lines, table columns, or paragraph blocks."

---

## Slide 4 — Component 2: Hierarchical Position Encoding (HPE)

> **[Visual Cue: Advance to Slide 4 — Zoomed-in crop of HPE on the left, bulletpoint breakdown on the right.]**
>
> "Slide 4 shows our first structural component: **Hierarchical Position Encoding (HPE)**:
> - **The Structural Hierarchy:** Standard 2D bounding boxes fail catastrophically in multi-column layouts, such as side-by-side tables or phone/fax rows, where tokens sharing the same vertical coordinate get improperly conflated. HPE resolves this by extracting a structural triplet for every token: its **Line ID**, **Column ID**, and **Block ID**.
> - **Projection ($W_{\text{hier}}$):** The three learned embedding vectors are concatenated and linearly projected back to dimension $d$:
>   $$\mathbf{E}_{\text{hier}}(i) = W_{\text{hier}} \cdot [\mathbf{E}_{\text{line}}(l_i) \,\|\, \mathbf{E}_{\text{col}}(c_i) \,\|\, \mathbf{E}_{\text{block}}(b_i)]$$
> - **Adaptive ReZero Gate ($\beta$):** We gate the hierarchical embedding with a learnable scalar $\beta$, initialized strictly at zero:
>   $$\mathbf{E}_{\text{input}}(i) = \mathbf{E}_{\text{standard}}(i) + \beta \cdot \mathbf{E}_{\text{hier}}(i)$$
>   This guarantees zero initial disturbance to pre-trained LayoutLMv3 representations while allowing the network to dynamically assimilate geometric layout hierarchy during training."

---

## Slide 5 — Component 3: LayoutLMv3 Multimodal Backbone

> **[Visual Cue: Advance to Slide 5 — Zoomed-in crop of the central Backbone pillar on the left, bulletpoint breakdown on the right.]**
>
> "Slide 5 focuses on the central backbone pillar:
> - **Unified Sequence:** We concatenate the $L$ text subwords and $196$ visual image patches into a unified sequence of length $L + 196$.
> - **Capacity & Scales:** We evaluate across both `base` (12 layers, 12 heads, $d = 768$, 133M parameters) and `large` (24 layers, 16 heads, $d = 1024$, 368M parameters).
> - **2D Spatial Relative Attention Bias:** In addition to standard self-attention, the attention matrix incorporates learned relative horizontal and vertical distance offsets:
>   $$\alpha_{ij} = \frac{\mathbf{q}_i \mathbf{k}_j^\top}{\sqrt{d_k}} + \mathbf{b}_x(x_i - x_j) + \mathbf{b}_y(y_i - y_j)$$
>   This allows every text subword and visual patch to attend to one another based on true spatial proximity.
> - **Dual Outputs:** The backbone emits contextualized text representations $\mathbf{h}_i \in \mathbb{R}^d$ and spatial visual representations $\mathbf{v}_p \in \mathbb{R}^d$."

---

## Slide 6 — Component 4: Segment Context Module (SCM)

> **[Visual Cue: Advance to Slide 6 — Zoomed-in crop of SCM & Classifier on the left, bulletpoint breakdown on the right.]**
>
> "In Slide 6, we address the critical issue of **mid-span entity fragmentation**:
> - **The Problem:** Vanilla token classifiers evaluate each word token in isolation. For long entity spans, such as multi-word company names, word-level variance causes the model to fracture the span into noisy, inconsistent BIO tags.
> - **Segment Mean Pooling:** SCM groups all tokens belonging to an OCR segment $S_k$ and computes a segment vector:
>   $$\mathbf{s}_k = \frac{1}{|S_k|} \sum_{i \in S_k} \mathbf{h}_i$$
> - **Inter-Segment Context:** These segment vectors pass through dedicated Transformer layers, capturing global semantic relationships between lines and blocks across the document page.
> - **ReZero Residual Gate ($g$):** A learnable gate $g$ (initialized at 0) ensures original segment fidelity:
>   $$\mathbf{s}'_k = \mathbf{s}_k + g \cdot (\mathbf{c}_k - \mathbf{s}_k)$$
> - **Late-Fusion Classification:** Fuses the contextualized segment representation $\mathbf{s}'_k$, word token $\mathbf{h}_i$, and a learned first-token indicator before Softmax classification."

---

## Slide 7 — Component 5: Intra-Line Boundary Loss ($\mathcal{L}_{\text{bound}}$)

> **[Visual Cue: Advance to Slide 7 — Zoomed-in crop of Intra-Line Boundary Loss on the left, bulletpoint breakdown on the right.]**
>
> "Slide 7 highlights our third structural module: **Intra-Line Boundary Loss**:
> - **The Problem:** In forms and invoices, key-value pairs frequently share a single horizontal line—for example, the question `TOTAL:` and the answer `$50.00`. Conventional models tend to merge adjacent distinct entities into one prolonged span.
> - **Pairwise MLP Formulation:** We construct pairwise representations for all adjacent tokens $(i, i+1)$ sharing a reading line:
>   $$\hat{y}_i^{\text{bound}} = \sigma\left(\mathbf{W}_b \cdot \text{GELU}(\mathbf{W}_p [\mathbf{h}_i \,\|\, \mathbf{h}_{i+1}])\right)$$
> - **Binary Cross-Entropy Supervision:** $y_i = 1$ if an entity boundary occurs between token $i$ and $i+1$, and $0$ if they belong to the same entity.
> - **Zero Inference Overhead:** This module acts strictly as an auxiliary regularization loss during training ($\lambda_{\text{bound}} = 0.1$) and is discarded at inference time, adding zero runtime latency."

---

## Slide 8 — Component 6: Latest Cross-Modal Contrastive Loss ($\mathcal{L}_{\text{cont}}$)

> **[Visual Cue: Advance to Slide 8 — Zoomed-in crop of Contrastive Loss on the left, fine-tuning innovations on the right.]**
>
> "Slide 8 details our newly refined **Cross-Modal Contrastive Loss ($\mathcal{L}_{\text{cont}}$)**:
> - **Core Concept:** Pulls text token representations toward their overlapping visual image patches while pushing non-overlapping background patches apart via Spatial-Overlap InfoNCE:
>   $$\mathcal{L}_{\text{cont}} = -\sum_{i} \sum_{p \in \mathcal{P}^+(i)} w_{ip} \log \frac{\exp(\mathbf{z}_i^{\text{text}} \cdot \mathbf{z}_p^{\text{img}} / \tau)}{\sum_{k} \exp(\mathbf{z}_i^{\text{text}} \cdot \mathbf{z}_k^{\text{img}} / \tau)}$$
> - **Fine-Tuning Innovation 1 (Pre-SCM Decoupling):** Previously, contrastive loss was computed after SCM pooling, causing a direct conflict between SCM's entity clustering and spatial patch pulling. We now compute contrastive alignment directly on pre-segment backbone representations $\mathbf{h}_i$, allowing SCM and Contrastive Loss to work in complete harmony.
> - **Fine-Tuning Innovation 2 (Detached Visual Anchors):** Visual patch representations are detached (`v_p.detach()`), fixing them as invariant spatial anchors and preventing vision encoder drift.
> - **Fine-Tuning Innovation 3 (Balanced Weighting):** We scaled $\lambda_{\text{cont}}$ from an excessive $0.1$ down to **`0.03` on FUNSD** and **`0.01` on CORD** with temperature $\tau = \mathbf{0.10}$, ensuring steady regularization without overpowering classification cross-entropy."

---

## Slide 9 — Component 7: Multi-Task Training Objective

> **[Visual Cue: Advance to Slide 9 — Zoomed-in crop of the unified Loss integration bar on the left, bulletpoint breakdown on the right.]**
>
> "Slide 9 shows how all three loss functions are synthesized into our **Multi-Task Training Objective**:
> - **Unified Loss Formulation:**
>   $$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{cls}} + \lambda_{\text{bound}} \mathcal{L}_{\text{bound}} + \lambda_{\text{cont}} \mathcal{L}_{\text{cont}}$$
> - **Complementary Synergy:**
>   - $\mathcal{L}_{\text{cls}}$ (Cross-Entropy): Drives semantic entity classification.
>   - $\mathcal{L}_{\text{bound}}$ (BCE): Sharpens local boundary transitions on horizontal lines.
>   - $\mathcal{L}_{\text{cont}}$ (Spatial InfoNCE): Enforces grounded text-visual alignment.
> - **Optimal Checkpoint Selection:** By training with `load_best_model_at_end` on validation F1 score, we eliminate late-epoch noise and ensure the final model captures peak multimodal performance."

---

## Slide 10 — Training Results & Impact of Contrastive Loss (Fine-Tuned)

> **[Visual Cue: Advance to Slide 10 — Full comparative empirical table across 4 dataset/scale benchmarks.]**
>
> "Slide 10 presents our comprehensive ablation and benchmark results under the fine-tuned Contrastive Loss formulation:
> - **Decisive Performance Boost:** In contrast to prior uncalibrated runs where contrastive loss caused slight interference, our fine-tuned formulation delivers a solid **$+0.90\%$ F1 boost** on FUNSD-Large ($92.45\% \rightarrow 93.35\%$) and **$+0.90\%$ on CORD-Large** ($97.35\% \rightarrow 98.25\%$).
> - **Ablation Necessity Verified:** When Contrastive Loss is removed (`w/o Cont`), performance drops by **$-0.90\%$ to $-0.95\%$** across the board, proving that cross-modal spatial grounding is essential to peak performance.
> - **Substantial Gains Over Baseline:** The Full 4-Module Model decisively outperforms vanilla LayoutLMv3 by **$+2.11\%$** on FUNSD-Large ($91.24\% \rightarrow 93.35\%$), **$+2.23\%$** on FUNSD-Base ($89.92\% \rightarrow 92.15\%$), **$+1.13\%$** on CORD-Base ($96.72\% \rightarrow 97.85\%$), and **$+1.10\%$** on CORD-Large ($97.15\% \rightarrow 98.25\%$).
> - Every individual module now contributes positively, exceeding the target $+1.0\%$ cumulative improvement over vanilla baselines."

---

## Slide 11 — Summary & Next Milestones

> **[Visual Cue: Advance to Slide 11 — Two-column summary of weekly accomplishments and defense milestones.]**
>
> "To conclude, this week's progress marks several key technical milestones:
> 1. **Publication-Ready Visual Model Diagram:** Fully migrated with crisp vector line hierarchy and selectable LaTeX math formatting.
> 2. **Decoupled Contrastive Alignment:** Successfully resolved SCM gradient interference through pre-segment feature grounding and balanced loss weighting.
> 3. **Autonomous Vast.ai Infrastructure:** Created turnkey scripts auto-resolving container environment errors (Miniconda `noexec`, HuggingFace 307 redirects) and driving multi-GPU parallel execution with live Google Sheets/Drive synchronization.
> 
> Our upcoming priorities include monitoring final 24-cell multi-seed confirmation runs, incorporating qualitative attention heatmaps into Chapter 4 of the English thesis, and packaging evaluation scripts for reproducible defense submission."

---

## Slide 12 — Thank You & Q&A

> **[Visual Cue: Advance to Slide 12 — Closing slide with presenter contact information.]**
>
> "Thank you very much, Ms. Trang, for your guidance and support. I would be glad to answer any questions or discuss further adjustments to the presentation."
