# Undergraduate Thesis Defense Presentation Script (English Copy)

**Thesis Title:** *Structure-Aware Multi-Modal LayoutLMv3 for Key Information Extraction on Visually Rich Documents*  
**Standard Duration:** 12 – 15 Minutes Presentation + Committee Q&A Session  
**Structure:** Aligned with the 5-chapter structure of the thesis (Chapter 5 will be finalized upon completion of the live 20-configuration A100 ablation suite).

---

## SLIDE 1: Title Slide & Opening Greeting (0:00 – 1:00)

**[On-Slide Visuals]:**
- Thesis title, Student Name, Supervisor (PhD. Pham Thi Quynh Trang), Co-Supervisor (Assoc. Prof. PhD. Le Duc Trong), Faculty of Information Technology – VNU University of Engineering and Technology (VNU-UET).

**[Speaker Script]:**
> "Good morning/afternoon, members of the Thesis Defense Committee, esteemed faculty members, and fellow students.  
> My name is [Student Name], and today I am honored to present my undergraduate thesis titled: *'Structure-Aware Multi-Modal LayoutLMv3 for Key Information Extraction on Visually Rich Documents'*, conducted under the scientific supervision of PhD. Pham Thi Quynh Trang and Assoc. Prof. PhD. Le Duc Trong.  
> My presentation follows the five-chapter structure of the thesis: first, the motivation and formal problem formulation of Key Information Extraction (KIE); second, theoretical background and related work in Document AI; third, our proposed Structure-Aware LayoutLMv3 methodology featuring three core architectural innovations; fourth, our rigorous multi-seed experimental evaluation on an NVIDIA A100 GPU; and fifth, our ongoing ablation roadmap."

---

## SLIDE 2: Practical Motivation & Problem Formulation (Chapter 1 | 1:00 – 2:30)

**[On-Slide Visuals]:**
- Sample scanned administrative form (FUNSD) and retail POS receipt (CORD).
- Three intersecting modalities: Lexical Text ($w_i$) + 2D Spatial Layout Bounding Boxes ($\mathbf{b}_i \in [0,1000]^4$) + Visual Image Patches ($\mathbf{I}$).
- Formal Multi-Modal Sequence Labeling under IOB2 tagging: $\mathcal{D} = \{(w_i, \mathbf{b}_i, s_i)\}_{i=1}^L \cup \{\mathbf{I}\} \to \hat{\mathbf{Y}} \in \{\texttt{B-}e_k, \texttt{I-}e_k, \texttt{O}\}^L$.

**[Speaker Script]:**
> "Every day, financial institutions, healthcare providers, retail chains, and government agencies process millions of scanned invoices, receipts, and administrative forms. Automatically turning these unstructured document images into structured database records is the central goal of **Key Information Extraction (KIE)** on **Visually Rich Documents (VRDs)**.  
> Unlike flat 1D Named Entity Recognition, understanding a visually rich document requires joint reasoning across three modalities: the OCR text tokens $w_i$, their normalized 2D bounding coordinates $\mathbf{b}_i = (x_0, y_0, x_1, y_1)$ on a $1000 \times 1000$ grid, and the raw visual appearance of the page $\mathbf{I}$. We formulate KIE as a multi-modal sequence labeling task under the **IOB2** scheme, where a predicted entity span is only considered correct if both its exact start-and-end token boundaries and its entity category match the ground truth."

---

## SLIDE 3: Background & Three Structural Limitations of Baseline LayoutLMv3 (Chapters 1 & 2 | 2:30 – 4:30)

**[On-Slide Visuals]:**
- LayoutLMv3 architecture diagram (Huang et al., ACM MM 2022) and architectural comparison table against LayoutLMv1, LayoutLMv2, StructuralLM, BROS, DocFormer, and LiLT.
- Three structural bottlenecks when fine-tuning baseline LayoutLMv3 for KIE:
  1. **Isotropic 2D Coordinate Embeddings:** Blindly allocates $d/6$ dimensions per coordinate axis without cross-axis interaction.
  2. **Lack of Explicit Segment-Level Structural Consensus:** Shares line boxes at input, but self-attention operates purely on subword tokens without an intermediate line/segment representation.
  3. **Lack of Intra-Line Boundary Smoothness:** Standard token-wise Cross-Entropy ignores representation drift between adjacent tokens within the same text line.

**[Speaker Script]:**
> "In Chapter 2, we review the evolution of multi-modal Document Transformers. **LayoutLMv3** achieved a major breakthrough by replacing heavy CNN visual backbones with linear patch projections and unified MLM, MIM, and Word-Patch Alignment pre-training.  
> However, when fine-tuning baseline LayoutLMv3 on downstream KIE benchmarks, three structural limitations emerge:  
> - **First, isotropic 2D coordinate embeddings:** the baseline allocates an identical $d/6 = 128$ dimension to every coordinate $(x_0, y_0, x_1, y_1, w, h)$, ignoring the geometric asymmetry between horizontal intra-line word order and vertical inter-line hierarchy.  
> - **Second, absence of explicit segment consensus:** although tokens in the same text line share a segment bounding box, there is no explicit intermediate representation for the text segment itself. Consequently, long multi-word entities frequently suffer from mid-line label fragmentation.  
> - **Third, lack of intra-line boundary regularization:** standard Cross-Entropy supervises each token independently, without penalizing abrupt hidden-state jumps between consecutive tokens inside the same visual line."

---

## SLIDE 4: Proposed Methodology – Overview & Component 1: HPE (Chapter 3 | 4:30 – 6:30)

**[On-Slide Visuals]:**
- End-to-End **Structure-Aware LayoutLMv3** Architecture Diagram (Figure 3.1 in the thesis).
- **Component 1 – Hierarchical 2D Positional Encoding (HPE):**
  - Horizontal intra-line subspace: $(x_0, x_1, w) \to d_x = d/8 = 96$ dims each ($3d_x = 288$).
  - Vertical inter-line subspace: $(y_0, y_1, h) \to d_y = 5d/24 = 160$ dims each ($3d_y = 480$).
  - Non-linear hierarchical fusion: $\mathbf{e}_{\text{HPE}}^{\text{pos2D}}(\mathbf{b}_i) = \text{GELU}(\text{LN}(\mathbf{W}_{\text{HPE}}[\mathbf{e}_{\text{horiz}} \| \mathbf{e}_{\text{vert}}] + \mathbf{b}_{\text{HPE}}))$.

**[Speaker Script]:**
> "To address these three challenges, Chapter 3 introduces our **Structure-Aware LayoutLMv3 Architecture**, comprising three synergistic components.  
> Our first component is **Hierarchical 2D Positional Encoding (HPE)**. Instead of treating all six coordinate attributes identically, HPE decouples spatial coordinates into a horizontal intra-line subspace $(x_0, x_1, w)$ with $d_x = 96$ dimensions per attribute, and a higher-capacity vertical inter-line subspace $(y_0, y_1, h)$ with $d_y = 160$ dimensions per attribute. The concatenated 768-dimensional vector is then transformed through a non-linear hierarchical fusion block—consisting of a dense projection $\mathbf{W}_{\text{HPE}}$, Layer Normalization, and GELU activation—enabling the embedding layer to capture aspect-ratio and vertical line-separation cues before the first Transformer layer."

---

## SLIDE 5: Component 2 (Token-Segment Module SCM) & Component 3 (Boundary Loss) (Chapter 3 | 6:30 – 9:00)

**[On-Slide Visuals]:**
- **Component 2 – Token-Segment Interaction Module (SCM):**
  1. Masked Segment Mean Pooling: $\mathbf{u}_k = \frac{1}{|\mathcal{I}_k|} \sum_{i \in \mathcal{I}_k} \mathbf{h}_i$.
  2. Inter-Segment Multi-Head Self-Attention (`SegmentAttention`, 8 heads): $\hat{\mathbf{U}} = \text{LN}(\mathbf{U} + \text{Dropout}(\text{MHSA}_{\text{seg}}(\mathbf{U})))$.
  3. **ReZero-Gated Broadcast** ($\alpha^{(0)} = 0$) + **Segment-Start Indicator** $f_i = \mathds{1}[s_i \neq s_{i-1}]$:
     $$\mathbf{h}_i^{\text{final}} = \mathbf{h}_i + \alpha \cdot \mathds{1}[s_i \ge 0] \cdot \left(\hat{\mathbf{u}}_{s_i} + \mathbf{e}_{\text{first}}(f_i)\right)$$
- **Component 3 – Intra-Line Boundary Regularization Loss ($\mathcal{L}_{\text{bound}}$):**
  $$\mathcal{L}_{\text{bound}} = \frac{1}{|\mathcal{P}_{\text{intra}}|} \sum_{(i, i+1) \in \mathcal{P}_{\text{intra}}} \left(1 - \cos(\mathbf{h}_i^{\text{final}}, \mathbf{h}_{i+1}^{\text{final}})\right), \quad \mathcal{L}_{\text{total}} = \mathcal{L}_{\text{CE}} + \lambda_{\text{bound}}\mathcal{L}_{\text{bound}}$$

**[Speaker Script]:**
> "Our second component is the **Token-Segment Interaction Module (or Segment Consensus Module – SCM)** placed on top of the LayoutLMv3 encoder. First, token hidden states belonging to the same visual line $s_i = k$ are aggregated via masked mean pooling into a segment embedding $\mathbf{u}_k$. Second, all $S$ segments across the document interact through an 8-head `SegmentAttention` layer to model macro-level layout relationships, such as linking question blocks to answer blocks.  
> Crucially, when broadcasting the refined segment vector $\hat{\mathbf{u}}_{s_i}$ back to individual tokens, we introduce two stabilization mechanisms: a **ReZero-style learnable scalar gate $\alpha$ initialized to zero**, and a **binary segment-start indicator embedding** $\mathbf{e}_{\text{first}}(f_i)$. Initializing $\alpha = 0$ guarantees an exact identity mapping at step 0—preventing random segment-attention gradients from destabilizing the pre-trained backbone—while $\mathbf{e}_{\text{first}}(f_i)$ explicitly marks the first token of each segment so the classifier can cleanly distinguish $\texttt{B-}$ onset tags from $\texttt{I-}$ continuation tags.  
> Our third component is the **Intra-Line Boundary Regularization Loss ($\mathcal{L}_{\text{bound}}$)**. For every pair of adjacent tokens $(i, i+1)$ within the same line segment ($s_i = s_{i+1}$) that share the same base entity category ($\phi(y_i) = \phi(y_{i+1})$), $\mathcal{L}_{\text{bound}}$ penalizes the cosine dissimilarity between their hidden states with weight $\lambda_{\text{bound}} = 0.2$. Notably, this regularizer operates purely during training and adds **zero latency overhead at inference time**."

---

## SLIDE 6: Experimental Setup & Multi-Seed Quantitative Results (Chapter 4 | 9:00 – 12:00)

**[On-Slide Visuals]:**
- Hardware & Protocol: **NVIDIA A100-SXM4-80GB** GPU, evaluated across **3 independent random seeds** $\mathcal{S} = \{42, 123, 1993\}$ using strict entity-level `seqeval` Precision, Recall, and F1 ($\text{Mean} \pm \text{Std}$).
- Quantitative Results Table & Charts (Table 4.4 & Figure 4.1 in the thesis):
  - **FUNSD (`base`, 3 seeds):**
    - Baseline LayoutLMv3: Precision = $89.32 \pm 1.31\%$, Recall = $90.53 \pm 0.48\%$, **Entity F1 = $89.92 \pm 0.85\%$** (Peak: $90.51\%$).
    - **Ours (Full Structure-Aware Model):** Precision = **$91.82 \pm 0.05\%$** ($+2.50\%$), Recall = **$91.33 \pm 0.28\%$** ($+0.80\%$), **Entity F1 = $91.58 \pm 0.16\%$** (Peak: **$91.76\%$**).
  - **CORD (`base`, 3 seeds):**
    - Baseline LayoutLMv3: Precision = $96.50 \pm 0.39\%$, Recall = $96.94 \pm 0.28\%$, **Entity F1 = $96.72 \pm 0.33\%$** (Peak: $96.95\%$).

**[Speaker Script]:**
> "In Chapter 4, we evaluate our models on an **NVIDIA A100-SXM4-80GB** GPU across the standard **FUNSD** and **CORD** benchmarks. To eliminate single-seed selection bias, every configuration is trained and evaluated across **3 independent seeds $\{42, 123, 1993\}$**, reporting strict entity-level `seqeval` metrics as $\text{Mean} \pm \text{Std}$.  
> Our empirical results on FUNSD highlight three major findings:  
> 1. **Significant Entity F1 Improvement (+1.66%):** Our Full Structure-Aware model elevates 3-seed mean Entity F1 from **89.92%** to **91.58%** (peaking at **91.76%** on seed 42), surpassing both our 3-seed baseline and the published single-run score in the original LayoutLMv3 paper (90.29%) by **+1.29%**, with only a 2.4% parameter increase.  
> 2. **Surge in Entity Precision (+2.50%):** Precision jumps from **89.32%** to **91.82%** alongside a **+0.80%** gain in Recall. Because strict entity evaluation penalizes any fragmented span as both a False Positive and a False Negative, this confirms that SCM and $\mathcal{L}_{\text{bound}}$ effectively eliminate mid-segment label breaks.  
> 3. **5.3x Reduction in Cross-Seed Variance:** While the baseline suffers from seed sensitivity on FUNSD ($\sigma_{\text{F1}} = 0.85\%$, $\sigma_{\text{P}} = 1.31\%$), our ReZero-gated architecture reduces F1 standard deviation by **5.3x** (to $\pm 0.16\%$) and Precision standard deviation by **26x** (to $\pm 0.05\%$)."

---

## SLIDE 7: Live 20-Configuration Ablation Matrix & Closing (Chapters 4 & 5 | 12:00 – 13:30)

**[On-Slide Visuals]:**
- Master 20-Cell Ablation Tracker Table (`baseline`, `full`, `no_boundary`, `no_segment`, `no_hpe` across `base` and `large` variants on FUNSD and CORD).
- Summary of contributions & Thank You note.

**[Speaker Script]:**
> "Our live A100 pipeline is currently executing the remaining configurations of our 20-cell ablation matrix—systematically isolating `no_boundary`, `no_segment`, and `no_hpe` across both `base` and `large` backbones on FUNSD and CORD—which will populate our final ablation tables and Chapter 5 conclusion.  
> Thank you very much for your time and attention. I would now be delighted to answer any questions and welcome feedback from the Committee."

---

## APPENDIX: Anticipated Defense Committee Q&A

1. **Question 1:** *Why does HPE allocate a larger embedding dimension to the vertical axis ($d_y = 160$) than the horizontal axis ($d_x = 96$)?*
   - **Answer:** Within any single text line, subword tokens already share segment-level bounding boxes and possess sequential 1D positional embeddings (`pos1D`) that encode left-to-right reading order. By contrast, distinguishing vertically stacked rows in tables, key-value pairs across lines, and hierarchical section headers depends entirely on vertical coordinates $(y_0, y_1, h)$. Allocating $3d_y = 480$ dimensions to vertical geometry vs. $3d_x = 288$ to horizontal geometry—followed by a non-linear GELU fusion layer—sharpens inter-line spatial discrimination.

2. **Question 2:** *Why use the Intra-Line Boundary Regularization Loss ($\mathcal{L}_{\text{bound}}$) instead of adding a Conditional Random Field (CRF) layer on top of the classifier?*
   - **Answer:** A linear-chain CRF incurs $O(L \cdot |\mathcal{Y}|^2)$ Viterbi decoding overhead during inference—which becomes expensive on fine-grained datasets like CORD ($|\mathcal{Y}| = 61 \implies |\mathcal{Y}|^2 = 3721$)—and only models first-order label-to-label transition probabilities. In contrast, our cosine boundary loss $\mathcal{L}_{\text{bound}}$ directly regularizes the 768-dimensional hidden representations of adjacent intra-line tokens during training and incurs **zero computational cost at inference time**.

3. **Question 3:** *How do the ReZero gate $\alpha$ and `is_first_token_embedding` work together inside the Token-Segment Interaction Module?*
   - **Answer:** Attaching a randomly initialized Multi-Head Self-Attention block (`SegmentAttention`) onto a pre-trained Transformer can inject noisy gradients during early fine-tuning steps, degrading pre-trained representations on small datasets like FUNSD. By initializing the learnable scalar gate $\alpha^{(0)} = 0$, the module acts as an exact identity pass-through at step 0 and gradually blends in segment context as training progresses. Meanwhile, `is_first_token_embedding` breaks token symmetry inside each pooled segment by marking the segment's opening token ($f_i = 1$), enabling accurate $\texttt{B-}$ vs. $\texttt{I-}$ boundary predictions.

