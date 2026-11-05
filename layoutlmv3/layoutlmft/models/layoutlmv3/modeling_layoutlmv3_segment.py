#layoutlmft/models/layoutlmv3/modeling_layoutlmv3_segment.py
# coding=utf-8
#modeling_layoutlmv3_segment.py
"""
LayoutLMv3ForSegmentTokenClassification

Core idea (grounded in error analysis on FUNSD + CORD):
  - Segment self-consistency is already ~98-99% solved by the base model
    (confirmed empirically) -> a consistency REGULARIZER has little to gain.
  - The real errors are (a) whole segments classified wrong as a unit
    (esp. long free-text spans dropped entirely via BIO "drift"), and
    (b) confusions that depend on the NEIGHBORING segment's role
    (HEADER vs QUESTION on FUNSD; parent vs sub-item on CORD).
  - Fix: pool each segment's token hidden states into one vector, run a
    tiny Transformer encoder over the SEQUENCE of segment vectors (reading
    order) so adjacent segments exchange information, then broadcast the
    context-enriched vector back to every token in the segment before the
    (unchanged) token classifier.
  - To keep the existing BIO scheme / seqeval / compute_metrics pipeline
    100% unchanged, we do NOT collapse labels to entity-type-only. Instead
    we add a tiny learned "is-first-token-of-segment" embedding so the
    (otherwise identical) broadcast vector can still support the B-/I-
    distinction at the classifier.

This class does NOT touch attention, does NOT build any graph/hypergraph,
and does NOT modify the pretrained backbone. It only replaces what the
token classifier head "sees" for tokens inside multi-token segments -- an
orthogonal mechanism to HGA / GraphLayoutLM.
"""
import torch
import torch.nn as nn
from torch.nn import CrossEntropyLoss
from transformers.modeling_outputs import TokenClassifierOutput
import torch.nn.functional as F

from .modeling_layoutlmv3 import (
    LayoutLMv3ClassificationHead,
    LayoutLMv3Model,
    LayoutLMv3PreTrainedModel,
)

class LayoutLMv3ForSegmentTokenClassification(LayoutLMv3PreTrainedModel):
    _keys_to_ignore_on_load_unexpected = [r"pooler"]
    _keys_to_ignore_on_load_missing = [r"position_ids"]

    def __init__(self, config):
        super().__init__(config)
        self.num_labels = config.num_labels

        self.layoutlmv3 = LayoutLMv3Model(config)
        self.dropout = nn.Dropout(config.hidden_dropout_prob)
        if config.num_labels < 10:
            self.classifier = nn.Linear(config.hidden_size, config.num_labels)
        else:
            self.classifier = LayoutLMv3ClassificationHead(config, pool_feature=False)

        # ---- NEW: lightweight inter-segment context module ----
        # Only instantiate Token-Segment modules when use_token_segment is enabled (allows clean ablation)
        self.use_token_segment = getattr(config, "use_token_segment", True)
        if self.use_token_segment:
            # Config knobs (optional; safe defaults if not set on the config object).
            seg_ctx_layers = getattr(config, "segment_context_layers", 1)
            seg_ctx_heads = getattr(config, "segment_context_heads", 4)
            seg_ctx_dropout = getattr(config, "segment_context_dropout", config.hidden_dropout_prob)

            encoder_layer = nn.TransformerEncoderLayer(
                d_model=config.hidden_size,
                nhead=seg_ctx_heads,
                dim_feedforward=config.hidden_size * 2,
                dropout=seg_ctx_dropout,
                batch_first=True,
            )
            self.segment_context = nn.TransformerEncoder(encoder_layer, num_layers=seg_ctx_layers)
        else:
            self.segment_context = None
        if getattr(config, "use_intra_line_boundary", False):
            self.boundary_classifier = nn.Sequential(
                nn.Linear(config.hidden_size * 2, config.hidden_size),
                nn.ReLU(),
                nn.Linear(config.hidden_size, 1)
            )
            # Float cố định, không phải Parameter -- tránh bị gradient descent
            # đẩy xuống âm (sẽ đảo ngược mục đích của boundary loss), nhất
            # quán với cách xử lý lambda_geo/lambda_orth ở dưới.
            self.lambda_bound = float(getattr(config, "lambda_bound_init", 0.1))
        else:
            self.boundary_classifier = None
            self.lambda_bound = 0.0
        
        # ====== SEMANTIC-GEOMETRY DISENTANGLE ======
        if getattr(config, "use_semantic_geometry_disentangle", False):
            self.geo_head = nn.Linear(config.hidden_size, config.hidden_size)
            self.geo_line_classifier = nn.Linear(config.hidden_size, config.max_line_position)
            self.geo_block_classifier = nn.Linear(config.hidden_size, config.max_block_position)
            self.semi_head = nn.Linear(config.hidden_size, config.hidden_size)
            
            # ====== SỬA: Dùng float thay vì Parameter ======
            self.lambda_geo = float(getattr(config, "lambda_geo_init", 0.1))
            self.lambda_orth = float(getattr(config, "lambda_orth_init", 0.1))
        else:
            self.geo_head = None
            self.geo_line_classifier = None
            self.geo_block_classifier = None
            self.semi_head = None
            self.lambda_geo = 0.0
            self.lambda_orth = 0.0

        # ====== CROSS-MODAL CONTRASTIVE LOSS ======
        # Aligns contextualized text token representations with their corresponding
        # spatial visual image patches using an InfoNCE objective in a shared
        # low-dimensional projection space (default 128-d, temperature tau=0.07).
        # Used only during training -> adds zero latency at inference time.
        if getattr(config, "use_contrastive_loss", False):
            proj_dim = int(getattr(config, "contrastive_proj_dim", 128))
            # Linear projection g_text: R^H -> R^proj_dim for text tokens
            self.contrastive_text_proj = nn.Linear(config.hidden_size, proj_dim)
            # Linear projection g_img: R^H -> R^proj_dim for visual image patches
            self.contrastive_img_proj = nn.Linear(config.hidden_size, proj_dim)
            # Balanced scalar weight lambda_cont (default 0.03 for regularizing alignment) and temperature tau (default 0.10)
            self.lambda_contrastive = float(getattr(config, "lambda_contrastive_init", 0.03))
            self.contrastive_temperature = float(getattr(config, "contrastive_temperature", 0.10))
        else:
            self.contrastive_text_proj = None
            self.contrastive_img_proj = None
            self.lambda_contrastive = 0.0
            self.contrastive_temperature = 0.10
                # ReZero-style gate: starts at 0 so at step 0 the context module is a
        # NO-OP (output == plain mean-pooled vector, i.e. identical to a
        # "segment pooling only, no inter-segment context" ablation). Training
        # then gradually learns how much of the (initially random) context
        # transform to blend in. This avoids injecting a large random
        # perturbation into a well-pretrained backbone's features right at
        # the start of fine-tuning -- important on tiny datasets like FUNSD
        # (149 docs) where a high-variance early gradient can permanently
        # damage the pretrained representation.
        if self.use_token_segment:
            self.segment_context_gate = nn.Parameter(torch.zeros(1))

            # Small embedding so the classifier can still tell "first token of the
            # segment" (-> should predict B-xxx) apart from the rest (-> I-xxx),
            # even though every token in the segment otherwise shares one pooled
            # vector. Initialized near zero so early training resembles the
            # unmodified baseline.
            self.is_first_token_embedding = nn.Embedding(2, config.hidden_size)
            nn.init.normal_(self.is_first_token_embedding.weight, mean=0.0, std=0.02)
        else:
            self.segment_context_gate = None
            self.is_first_token_embedding = None

        self.init_weights()
        # for param in self.layoutlmv3.parameters():
        #     param.requires_grad = False

    def _segment_pool_and_contextualize(self, text_hidden, seg_id):
        """
        text_hidden: (B, L, H) hidden states for the TEXT part only
                     (image-patch positions, if any, are handled separately
                     by the caller and never enter this function).
        seg_id:      (B, L) long tensor. -1 marks tokens that do not belong
                     to any segment (special tokens / padding). Non-negative
                     values are LOCAL segment indices per example, assigned
                     in reading order (0, 1, 2, ...), exactly matching the
                     bbox-equality grouping used in run_funsd_cord.py's
                     tokenize_and_align_labels (see patch).

        Returns:
            broadcast_hidden: (B, L, H) -- every token belonging to the same
                segment gets an IDENTICAL context-enriched vector (before the
                is-first-token embedding is added back in `forward`).
        """
        B, L, H = text_hidden.shape
        device = text_hidden.device
        broadcast_hidden = text_hidden.clone()

        for b in range(B):
            ids = seg_id[b]
            valid = ids >= 0
            if valid.sum() == 0:
                continue

            uniq_segs = torch.unique(ids[valid], sorted=True)  # reading order
            n_seg = uniq_segs.shape[0]

            seg_vecs = torch.zeros(n_seg, H, device=device, dtype=text_hidden.dtype)
            seg_masks = []
            for i, s in enumerate(uniq_segs):
                mask = ids == s
                seg_masks.append(mask)
                seg_vecs[i] = text_hidden[b, mask].mean(dim=0)

            # The only place adjacent segments exchange information.
            # Cheap: n_seg is typically tens, not hundreds, per document.
            ctx_out = self.segment_context(seg_vecs.unsqueeze(0)).squeeze(0)  # (n_seg, H)
            # ReZero blend: at init (gate=0) this reduces to seg_vecs_ctx == seg_vecs
            # (pure mean-pooling, no context) -- see comment on self.segment_context_gate.
            seg_vecs_ctx = seg_vecs + self.segment_context_gate * (ctx_out - seg_vecs)

            for i, mask in enumerate(seg_masks):
                broadcast_hidden[b, mask] = seg_vecs_ctx[i]

        return broadcast_hidden
    def _compute_boundary_loss(self, text_hidden, entity_ids, attention_mask, text_len):
        """
        Intra-Line/Entity Boundary Loss -- bản vector hóa, dùng entity_ids
        (đã tính sẵn từ chuỗi nhãn thật "B-.../I-...", không suy luận theo
        số chẵn/lẻ -> tổng quát cho mọi dataset).

        Với mỗi cặp token liên tiếp (i, i+1):
            boundary_label = 0  nếu cùng entity_ids (đang ở giữa 1 entity)
            boundary_label = 1  nếu khác entity_ids (ranh giới thật)
        Token có entity_ids = -1 (O / special / padding) bị loại khỏi loss.
        """
        device = text_hidden.device

        if entity_ids is None:
            return torch.tensor(0.0, device=device)

        h_i = text_hidden[:, :-1, :]        # (B, L-1, H)
        h_next = text_hidden[:, 1:, :]      # (B, L-1, H)
        h_pair = torch.cat([h_i, h_next], dim=-1)                    # (B, L-1, 2H)
        boundary_logits = self.boundary_classifier(h_pair).squeeze(-1)  # (B, L-1)

        ent_i = entity_ids[:, :-1]
        ent_next = entity_ids[:, 1:]

        valid = (ent_i >= 0) & (ent_next >= 0)
        if attention_mask is not None:
            am = attention_mask[:, :text_len]
            valid = valid & (am[:, :-1] == 1) & (am[:, 1:] == 1)

        if valid.sum() == 0:
            return torch.tensor(0.0, device=device)

        boundary_labels = (ent_i != ent_next).float()

        return F.binary_cross_entropy_with_logits(
            boundary_logits[valid], boundary_labels[valid]
        )

    def _compute_disentangle_loss(self, text_hidden, line_ids, block_ids, 
                                attention_mask, text_len):
        device = text_hidden.device
        B = text_hidden.shape[0]
        
        # Cắt line_ids, block_ids về text_len
        if line_ids is not None and line_ids.shape[1] > text_len:
            line_ids = line_ids[:, :text_len]
        if block_ids is not None and block_ids.shape[1] > text_len:
            block_ids = block_ids[:, :text_len]
        
        h_geo = self.geo_head(text_hidden)
        h_semi = self.semi_head(text_hidden)
        
        # ====== GEOMETRY LOSS ======
        geo_loss = torch.tensor(0.0, device=device)
        
        if line_ids is not None:
            line_logits = self.geo_line_classifier(h_geo)
            block_logits = self.geo_block_classifier(h_geo)
            
            valid_mask = (line_ids >= 0) & (block_ids >= 0)
            if attention_mask is not None:
                text_attention_mask = attention_mask[:, :text_len]
                valid_mask = valid_mask & (text_attention_mask == 1)
            
            if valid_mask.sum() > 0:
                line_ids_clamped = torch.clamp(line_ids, 0, self.geo_line_classifier.out_features - 1)
                block_ids_clamped = torch.clamp(block_ids, 0, self.geo_block_classifier.out_features - 1)
                
                geo_loss_line = F.cross_entropy(
                    line_logits[valid_mask], 
                    line_ids_clamped[valid_mask]
                )
                geo_loss_block = F.cross_entropy(
                    block_logits[valid_mask],
                    block_ids_clamped[valid_mask]
                )
                geo_loss = geo_loss_line + geo_loss_block
                
                # ====== KIỂM TRA NaN ======
                if torch.isnan(geo_loss) or torch.isinf(geo_loss):
                    geo_loss = torch.tensor(0.0, device=device)
        
        # ====== ORTHOGONALITY LOSS ======
        h_geo_norm = F.normalize(h_geo, dim=-1)
        h_semi_norm = F.normalize(h_semi, dim=-1)
        
        cos_sim = torch.matmul(h_geo_norm, h_semi_norm.transpose(1, 2))
        
        if attention_mask is not None:
            text_attention_mask = attention_mask[:, :text_len]
            valid_mask_2d = text_attention_mask.bool()
            pair_mask = valid_mask_2d.unsqueeze(1) & valid_mask_2d.unsqueeze(2)
            cos_sim = cos_sim * pair_mask.float()
        
        orth_loss = (cos_sim ** 2).mean()
        
        # ====== KIỂM TRA NaN ======
        if torch.isnan(orth_loss) or torch.isinf(orth_loss):
            orth_loss = torch.tensor(0.0, device=device)
        
        return geo_loss, orth_loss

    def _compute_contrastive_loss(
        self,
        text_hidden,
        image_hidden,
        bbox,
        attention_mask,
        text_len,
    ):
        """
        Cross-Modal Contrastive Loss (L_cont) -- aligns contextualized text tokens
        with their spatially corresponding visual image patches via Spatial-Overlap InfoNCE.

        How it works:
          1. LayoutLMv3 divides the document image into a grid of G x G visual
             patches (e.g., 14 x 14 = 196 patches after index 0, which is the
             visual CLS token) spanning normalized coordinates [0, 1000] x [0, 1000].
          2. For each valid text token i with bounding box b_i = (x0, y0, x1, y1),
             we identify both its center patch p_center(i) and the full set of visual
             patches P+(i) whose spatial grid cells overlap [x0, x1] x [y0, y1].
             Using P+(i) prevents patches covered by the same multi-token segment from
             being falsely penalized as negatives.
          3. Text token states h_i and visual patch states v_p are projected into a
             shared 128-d space via g_text and g_img, cast to FP32 for numerical
             stability under AMP/FP16, and L2-normalized:
                 z_i^text = normalize(g_text(h_i)),  z_p^img = normalize(g_img(v_p))
          4. Soft-target InfoNCE cross-entropy over scaled cosine similarities
             (z_i^text . z_p^img / tau) pulls each token toward its overlapping visual
             patches (with strongest weight on the center patch) while pushing
             non-overlapping background/other patches apart.
        """
        device = text_hidden.device

        # Require valid bounding boxes and spatial visual patches (index 0 is visual CLS)
        if bbox is None or image_hidden is None or image_hidden.shape[1] <= 1:
            return torch.tensor(0.0, device=device)

        # Extract spatial patch representations v_p, excluding the visual CLS token at index 0.
        # Detach visual representations so they serve as a stable spatial anchor without
        # distorting the pre-trained visual encoder weights.
        patch_hidden = image_hidden[:, 1:, :].detach()  # (B, N_patches, H)
        num_patches = patch_hidden.shape[1]
        grid_size = int(round(num_patches ** 0.5))
        if grid_size * grid_size != num_patches or grid_size <= 0:
            return torch.tensor(0.0, device=device)

        # Align bbox sequence length with text_len (slice or pad with zeros if needed)
        if bbox.shape[1] >= text_len:
            text_bbox = bbox[:, :text_len, :]
        else:
            pad_len = text_len - bbox.shape[1]
            pad_box = torch.zeros(
                bbox.shape[0], pad_len, 4, device=bbox.device, dtype=bbox.dtype
            )
            text_bbox = torch.cat([bbox, pad_box], dim=1)

        # Compute bounding box coordinates in float32 in [0, 1000]
        x0 = text_bbox[:, :, 0].float()
        y0 = text_bbox[:, :, 1].float()
        x1 = text_bbox[:, :, 2].float()
        y1 = text_bbox[:, :, 3].float()
        cx = 0.5 * (x0 + x1)
        cy = 0.5 * (y0 + y1)

        # Map center (cx, cy) and box bounds [x0, y0, x1, y1] to 2D patch grid indices in [0, grid_size - 1]
        col_center = torch.clamp((cx / 1000.0 * grid_size).long(), 0, grid_size - 1)
        row_center = torch.clamp((cy / 1000.0 * grid_size).long(), 0, grid_size - 1)
        patch_targets = row_center * grid_size + col_center  # (B, L)

        col_min = torch.clamp((x0 / 1000.0 * grid_size).long(), 0, grid_size - 1)
        col_max = torch.clamp((x1 / 1000.0 * grid_size).long(), 0, grid_size - 1)
        row_min = torch.clamp((y0 / 1000.0 * grid_size).long(), 0, grid_size - 1)
        row_max = torch.clamp((y1 / 1000.0 * grid_size).long(), 0, grid_size - 1)

        # Build validity mask: only active non-padding tokens with positive-area non-full-page bounding boxes
        has_valid_bbox = (
            (x1 > x0)
            & (y1 > y0)
            & ((x1 - x0 < 995.0) | (y1 - y0 < 995.0))
        )
        if attention_mask is not None:
            valid_mask = (attention_mask[:, :text_len] == 1) & has_valid_bbox
        else:
            valid_mask = has_valid_bbox

        if valid_mask.sum() == 0:
            return torch.tensor(0.0, device=device)

        # Project text tokens and visual patches into shared space in FP32 to prevent FP16 overflow/underflow
        text_proj = self.contrastive_text_proj(text_hidden).float()
        img_proj = self.contrastive_img_proj(patch_hidden).float()
        z_text = F.normalize(text_proj, p=2, dim=-1, eps=1e-6)  # (B, L, D_proj)
        z_img = F.normalize(img_proj, p=2, dim=-1, eps=1e-6)    # (B, N_patches, D_proj)

        # Compute temperature-scaled cosine similarity logits in FP32: (B, L, N_patches)
        sim_logits = torch.matmul(z_text, z_img.transpose(1, 2)) / max(
            self.contrastive_temperature, 1e-3
        )

        # Build spatial overlap mask P+(i) over the G x G patch grid so multi-patch segments
        # pull all covered patches positively rather than penalizing them as false negatives
        grid_arange = torch.arange(grid_size, device=device)
        patch_rows = grid_arange.view(grid_size, 1).expand(grid_size, grid_size).reshape(1, 1, num_patches)
        patch_cols = grid_arange.view(1, grid_size).expand(grid_size, grid_size).reshape(1, 1, num_patches)
        pos_mask = (
            (patch_rows >= row_min.unsqueeze(-1))
            & (patch_rows <= row_max.unsqueeze(-1))
            & (patch_cols >= col_min.unsqueeze(-1))
            & (patch_cols <= col_max.unsqueeze(-1))
        )  # (B, L, N_patches)

        # Emphasize the center patch (weight +1.0 on top of spatial overlap weight 1.0)
        # Reduces to exact one-hot cross-entropy when a token bbox lies within a single patch
        target_weights = pos_mask.float()
        target_weights.scatter_add_(
            2,
            patch_targets.unsqueeze(-1),
            torch.ones_like(patch_targets, dtype=torch.float32).unsqueeze(-1),
        )
        target_dist = target_weights / target_weights.sum(dim=-1, keepdim=True).clamp(min=1e-6)

        # Compute soft-target InfoNCE loss over all valid tokens in the batch
        log_probs = F.log_softmax(sim_logits[valid_mask], dim=-1)
        contrastive_loss = -(target_dist[valid_mask] * log_probs).sum(dim=-1).mean()

        # Guard against numerical instability
        if torch.isnan(contrastive_loss) or torch.isinf(contrastive_loss):
            return torch.tensor(0.0, device=device)

        return contrastive_loss.to(text_hidden.dtype)

    def forward(
        self,
        input_ids=None,
        bbox=None,
        attention_mask=None,
        token_type_ids=None,
        position_ids=None,
        valid_span=None,
        head_mask=None,
        inputs_embeds=None,
        labels=None,
        seg_id=None,
        line_ids=None,
        block_ids=None,
        column_ids=None,
        entity_ids=None, 
        output_attentions=None,
        output_hidden_states=None,
        return_dict=None,
        images=None,
        
    ):
        return_dict = return_dict if return_dict is not None else self.config.use_return_dict

        outputs = self.layoutlmv3(
            input_ids,
            bbox=bbox,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            position_ids=position_ids,
            head_mask=head_mask,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
            images=images,
            valid_span=valid_span,
            line_ids=line_ids,
            block_ids=block_ids,
            column_ids=column_ids, 
        )

        sequence_output = outputs[0]  # (B, text_len + image_len, H)
        text_len = input_ids.shape[1]
        text_hidden = sequence_output[:, :text_len, :]
        image_hidden = sequence_output[:, text_len:, :]

        # ====== SỬA: Cắt seg_id để chỉ lấy phần text ======
        # Run segment pooling and contextualization only when use_token_segment is True and seg_id is provided
        if self.use_token_segment and seg_id is not None:
            # Đảm bảo seg_id có đúng độ dài text
            if seg_id.shape[1] != text_len:
                # Nếu seg_id dài hơn text_len, chỉ lấy phần text
                if seg_id.shape[1] > text_len:
                    seg_id = seg_id[:, :text_len]
                else:
                    # Nếu seg_id ngắn hơn, pad với -1
                    pad_len = text_len - seg_id.shape[1]
                    pad_tensor = torch.ones(seg_id.shape[0], pad_len, device=seg_id.device, dtype=seg_id.dtype) * -1
                    seg_id = torch.cat([seg_id, pad_tensor], dim=1)
            
            text_hidden = self._segment_pool_and_contextualize(text_hidden, seg_id)

            # Add the is-first-token-of-segment signal
            is_first = torch.zeros_like(seg_id, dtype=torch.long)
            is_first[:, 0] = 0
            if seg_id.shape[1] > 1:
                prev = seg_id[:, :-1]
                cur = seg_id[:, 1:]
                changed = (cur != prev) & (cur >= 0)
                is_first[:, 1:] = changed.long()
            is_first = is_first * (seg_id >= 0).long()

            text_hidden = text_hidden + self.is_first_token_embedding(is_first)

        if image_hidden.shape[1] > 0:
            pooled_sequence = torch.cat([text_hidden, image_hidden], dim=1)
        else:
            pooled_sequence = text_hidden

        pooled_sequence = self.dropout(pooled_sequence)
        logits = self.classifier(pooled_sequence)
        # ====== TÍNH CÁC LOSS PHỤ ======
        aux_loss = torch.tensor(0.0, device=logits.device)

        if labels is not None:
            # ====== INTRA-LINE BOUNDARY LOSS ======
            if self.boundary_classifier is not None:
                entity_ids_for_loss = entity_ids
                if entity_ids_for_loss is not None and entity_ids_for_loss.shape[1] != text_len:
                    if entity_ids_for_loss.shape[1] > text_len:
                        entity_ids_for_loss = entity_ids_for_loss[:, :text_len]
                    else:
                        pad_len = text_len - entity_ids_for_loss.shape[1]
                        pad_tensor = torch.ones(
                            entity_ids_for_loss.shape[0], pad_len,
                            device=entity_ids_for_loss.device, dtype=entity_ids_for_loss.dtype
                        ) * -1
                        entity_ids_for_loss = torch.cat([entity_ids_for_loss, pad_tensor], dim=1)

                boundary_loss = self._compute_boundary_loss(
                    text_hidden=sequence_output[:, :text_len, :],
                    entity_ids=entity_ids_for_loss,   # thay labels bằng entity_ids đã tính đúng
                    attention_mask=attention_mask,
                    text_len=text_len,
                )
                aux_loss = aux_loss + self.lambda_bound * boundary_loss
            
            # ====== SEMANTIC-GEOMETRY DISENTANGLE LOSS ======
            if self.geo_head is not None:
                geo_loss, orth_loss = self._compute_disentangle_loss(
                    text_hidden=sequence_output[:, :text_len, :],
                    line_ids=line_ids if line_ids is not None else None,
                    block_ids=block_ids if block_ids is not None else None,
                    attention_mask=attention_mask,
                    text_len=text_len,
                )
                aux_loss = aux_loss + self.lambda_geo * geo_loss + self.lambda_orth * orth_loss

            # ====== CROSS-MODAL CONTRASTIVE LOSS ======
            # Aligns pre-segment backbone text representations (sequence_output[:, :text_len, :])
            # with spatial visual patch representations (image_hidden) to ground token features
            # without interfering with downstream segment-level contextualization (SCM).
            if self.contrastive_text_proj is not None and image_hidden.shape[1] > 1:
                contrastive_loss = self._compute_contrastive_loss(
                    text_hidden=sequence_output[:, :text_len, :],
                    image_hidden=image_hidden,
                    bbox=bbox,
                    attention_mask=attention_mask,
                    text_len=text_len,
                )
                aux_loss = aux_loss + self.lambda_contrastive * contrastive_loss
        loss = None
        if labels is not None:
            loss_fct = CrossEntropyLoss()
            if attention_mask is not None:
                active_loss = attention_mask.view(-1) == 1
                active_logits = logits.view(-1, self.num_labels)
                active_labels = torch.where(
                    active_loss, labels.view(-1), torch.tensor(loss_fct.ignore_index).type_as(labels)
                )
                loss = loss_fct(active_logits, active_labels)
            else:
                loss = loss_fct(logits.view(-1, self.num_labels), labels.view(-1))

            loss = loss + aux_loss

        if not return_dict:
            output = (logits,) + outputs[2:]
            return ((loss,) + output) if loss is not None else output

        return TokenClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )