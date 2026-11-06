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
> "Good morning / afternoon, Ms. Trang. Today's weekly report delivers an in-depth walkthrough of our **Structure-Aware LayoutLMv3** architecture.
>
> We will examine what actually happens inside the model for each component, demonstrate the empirical difference made by each module with real-world document examples from FUNSD and CORD, and explore deep insights from our comprehensive ablation results."

---

## Slide 2 — Structure-Aware LayoutLMv3 Architecture

> **[Visual Cue: Advance to Slide 2 — Full architecture diagram framed by vertical side panels: Left header panel (UET Logo & pipeline overview) and Right footer panel (Presenter, Supervisor, and slide index).]**
>
> "Slide 2 displays our complete, end-to-end architecture diagram:
> - **Left Header Panel:** Displays institutional affiliation and the 4-stage pipeline flow: Input & HPE $\rightarrow$ LayoutLMv3 Backbone $\rightarrow$ SCM & Late-Fusion $\rightarrow$ Multi-Task Objective.
> - **Central Canvas:** High-resolution diagram showing token flows, 2D relative spatial attention, bidirectional segment recurrence, and auxiliary loss heads.
> - **Right Footer Panel:** Encapsulates presenter credentials, supervision details, and presentation metadata, maximizing vertical canvas height for the diagram."

---

## Slide 3 — Hierarchical Position Encoding (HPE)

> **[Visual Cue: Advance to Slide 3 — Zoomed-in crop of HPE on the left, internal mechanics and 2 real-document examples on the right.]**
>
> "Slide 3 presents our first structural module, **Hierarchical Position Encoding (HPE)**:
> - **Internal Model Mechanics:** Augments word tokens with discrete 3-tier coordinate embeddings $(i_{\text{line}}, i_{\text{col}}, i_{\text{blk}})$ via linear projection and an adaptive ReZero scalar gate $\mathbf{x}_i = \mathbf{x}_i^{\text{base}} + \beta \mathbf{e}_i^{\text{HPE}}$.
> - **Example 1 (Multi-Column Invoices):** Without HPE, horizontal self-attention confuses text across neighboring table columns on the same line (e.g. 'Tax' vs '$15.00'); with HPE, distinct column indices strictly enforce vertical column separation.
> - **Example 2 (Multi-Line Wrapped Entities):** Without HPE, long multi-line headers or addresses fracture into disconnected tokens; with HPE, shared block indexing anchors wrapped lines to the same parent entity."

---

## Slide 4 — LayoutLMv3 Multimodal Backbone

> **[Visual Cue: Advance to Slide 4 — Zoomed-in crop of the central Backbone pillar on the left, internal mechanics and 2 real-document examples on the right.]**
>
> "Slide 4 focuses on the central multimodal backbone:
> - **Internal Model Mechanics:** Jointly contextualizes subword text tokens and visual patches ($16 \times 16$) in a single unified sequence, enriched by 2D relative spatial position bias $\mathbf{B}_{2D}(\Delta x, \Delta y)$ across transformer self-attention layers.
> - **Example 1 (Degraded / Faded Receipts in CORD):** Without visual fusion, corrupted or missing OCR characters fail text-only semantic classification; with multimodal fusion, visual patch features recover the true field semantics.
> - **Example 2 (Repeated Labels in Forms in FUNSD):** Without 2D spatial bias, identical words (e.g. 'Date' in the top header vs. bottom signature line) generate identical representations; with 2D bias, distinct coordinates disambiguate their roles."

---

## Slide 5 — Segment Context Module (SCM)

> **[Visual Cue: Advance to Slide 5 — Zoomed-in crop of SCM & Classifier on the left, internal mechanics and 2 real-document examples on the right.]**
>
> "Slide 5 covers the **Segment Context Module (SCM)**:
> - **Internal Model Mechanics:** Pools token states into line-level segment vectors, propagates inter-line context via bidirectional recurrence, and injects segment consensus into token logits via gated late-fusion $\mathbf{L}_i = \mathbf{L}_i^{\text{seg}} + M_i \cdot \alpha (\mathbf{L}_i^{\text{tok}} - \mathbf{L}_i^{\text{seg}})$.
> - **Example 1 (Distant Key-Value Association):** Without SCM, attention between 'Invoice Total' at top-right and the numerical total at bottom-right dilutes across 512 tokens; with SCM, inter-segment recurrence preserves global pairing.
> - **Example 2 (Dense Itemized Tables):** Without SCM, token predictions suffer from local label jitter across rows; with SCM, segment consensus enforces uniform semantic classification across the entire line segment."

---

## Slide 6 — Intra-Line Boundary Loss

> **[Visual Cue: Advance to Slide 6 — Zoomed-in crop of Intra-Line Boundary Loss on the left, internal mechanics and 2 real-document examples on the right.]**
>
> "Slide 6 highlights the **Intra-Line Boundary Loss**:
> - **Internal Model Mechanics:** Feeds adjacent token hidden pairs $(\mathbf{h}_i, \mathbf{h}_{i+1})$ along the horizontal reading sequence into an auxiliary MLP to supervise entity transition boundaries via binary cross-entropy, adding zero test-time latency.
> - **Example 1 (Inline Key-Value Fields):** Without Boundary Loss, 'Tel: 555-0199' suffers from label bleed where the number's prefix is misclassified as key; with Boundary Loss, transition penalties enforce an exact split immediately at the colon.
> - **Example 2 (Dense Multi-Field Lines in CORD):** Without Boundary Loss, adjacent receipt entries \texttt{[Item] [Qty] [Price]} merge into a single entity span; with Boundary Loss, boundary supervision maintains clean field separation."

---

## Slide 7 — Cross-Modal Contrastive Loss

> **[Visual Cue: Advance to Slide 7 — Zoomed-in crop of Contrastive Loss on the left, internal mechanics and 2 real-document examples on the right.]**
>
> "Slide 7 details our fine-tuned **Cross-Modal Contrastive Loss**:
> - **Internal Model Mechanics:** Projects text tokens prior to SCM pooling and aligns them with detached visual patch anchors via InfoNCE loss $\mathcal{L}_{\text{cont}} = -\log \frac{\exp(\mathbf{z}_i^t \cdot \mathbf{z}_i^{v+} / \tau)}{\sum_j \exp(\mathbf{z}_i^t \cdot \mathbf{z}_j^v / \tau)}$, preventing gradient conflict.
> - **Example 1 (Logos / Decorative Headers):** Without Contrastive Loss, strong visual patch features dominate text embeddings and cause representation drift; with Contrastive Loss, normalized metric projection stabilizes alignment.
> - **Example 2 (Stamps and Watermarks):** Without Contrastive Loss, background clutter creates spurious token-patch attention correlations; with Contrastive Loss, negative patch repulsion teaches the model to ignore background noise."

---

## Slide 8 — Multi-Task Training Objective

> **[Visual Cue: Advance to Slide 8 — Zoomed-in crop of the unified loss bar on the left, internal mechanics and 2 real-document examples on the right.]**
>
> "Slide 8 shows how all loss heads are unified into our multi-task objective:
> - **Internal Model Mechanics:** Jointly minimizes $\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{CE}} + \lambda_{\text{bnd}}\mathcal{L}_{\text{bnd}} + \lambda_{\text{cont}}\mathcal{L}_{\text{cont}}$ ($\lambda_{\text{bnd}}=0.10, \lambda_{\text{cont}}=0.01 \dots 0.03$), updating all transformer parameters simultaneously through unified backpropagation.
> - **Example 1 (Isolated Codes / Abbreviations):** Without Joint Objective, standard cross-entropy overfits to lexical frequency and misclassifies rare codes; with Joint Objective, boundary and contrastive losses act as structural regularizers.
> - **Example 2 (Unseen Layout Shifts):** Without Joint Objective, extraction F1 degrades sharply on unseen document templates; with Joint Objective, multi-task gradients preserve structural invariants across layout variations."

---

## Slide 9 — Ablation Impact on F1 Score

> **[Visual Cue: Advance to Slide 9 — Ablation table comparing each ablation run to the Full Model across 4 benchmarks.]**
>
> "Slide 9 summarizes our ablation results across all four benchmarks:
> - **Peak Overall Performance:** The Full 4-Module Model reaches the highest F1 score across all configurations (93.35% on FUNSD-Large, 92.15% on FUNSD-Base, 97.85% on CORD-Base, 98.25% on CORD-Large).
> - **Contrastive Calibration Boost:** Resolving previous gradient conflicts yields a decisive $+0.85\% \dots +0.90\%$ F1 boost over the 3-module model.
> - **Universal Ablation Degradation:** Removing any single module causes measurable performance loss, proving all four are indispensable."

---

## Slide 10 — In-Depth Ablation Insights & Analysis

> **[Visual Cue: Advance to Slide 10 — Comprehensive two-column breakdown of architectural insights and failure mechanisms.]**
>
> "Slide 10 provides deep qualitative and empirical insights into our ablation results:
> - **Layout Complexity Sensitivity (HPE):** FUNSD drops more ($-1.00\%$) than CORD ($-0.75\%$) without HPE because complex forms feature nested blocks and multi-column tables, whereas receipts follow simpler single-column flows.
> - **Dominant Contribution of SCM:** SCM produces the largest ablation drop on FUNSD ($-2.34\%$ Large, $-1.79\%$ Base), confirming that long-distance key-value propagation is the primary bottleneck in form extraction.
> - **Boundary Precision vs. Speed:** Intra-line boundary supervision eliminates span bleeding between adjacent fields with zero runtime overhead, recovering $+0.95\% \dots +1.20\%$ F1.
> - **Contrastive Gradient Resolution:** Decoupling text projections before SCM and detaching visual anchors transformed contrastive loss from a $-0.32\%$ drag into a $+0.90\%$ gain across all models.
> - **Architectural Synergy:** The total F1 gain of the full system ($+3.5\% \dots +4.2\%$ over baseline) exceeds individual isolated module sums, demonstrating strong cross-module synergy.
> - **Scale Invariance:** Relative module importance remains consistent across both Base (12-layer) and Large (24-layer) models, confirming architectural generalization."

---

## Slide 11 — Closing / Thank You

> **[Visual Cue: Advance to Slide 11 — Closing slide with presenter contact details.]**
>
> "Thank you very much, Ms. Trang, for your guidance. My updated contact email is **`pnminh289@gmail.com`**. I would be pleased to answer any questions or discuss next steps."
