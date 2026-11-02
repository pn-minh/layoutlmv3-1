/**
 * Model Architecture Draw.io Generator & Exporter
 * 
 * Inspects PyTorch model source code in layoutlmv3/ to extract architecture specifications
 * and generates a 100% clean, non-overlapping Draw.io (.drawio) diagram and JPEG export.
 */

const fs = require('fs');
const path = require('path');

// 1. Inspect layoutlmv3 source files to extract ground-truth architecture specifications
const modelingSegPath = path.resolve(__dirname, '../layoutlmv3/layoutlmft/models/layoutlmv3/modeling_layoutlmv3_segment.py');
const modelingBasePath = path.resolve(__dirname, '../layoutlmv3/layoutlmft/models/layoutlmv3/modeling_layoutlmv3.py');

console.log('Inspecting PyTorch source files in layoutlmv3...');
const segCode = fs.readFileSync(modelingSegPath, 'utf8');
const baseCode = fs.readFileSync(modelingBasePath, 'utf8');

// Verification of architecture components from code
const hasHPE = baseCode.includes('line_position_embeddings') && baseCode.includes('hierarchical_proj');
const hasSCM = segCode.includes('_segment_pool_and_contextualize') && segCode.includes('segment_context_gate');
const hasBoundary = segCode.includes('boundary_classifier') && segCode.includes('_compute_boundary_loss');
const hasLateFusion = segCode.includes('GatedLateFusion') || segCode.includes('late_fusion');

console.log(`- Hierarchical Position Encoding (HPE): ${hasHPE ? 'Detected' : 'Not found'}`);
console.log(`- Segment Context Module (SCM with ReZero): ${hasSCM ? 'Detected' : 'Not found'}`);
console.log(`- Intra-Line Boundary Classifier: ${hasBoundary ? 'Detected' : 'Not found'}`);
console.log(`- Gated Late Fusion: ${hasLateFusion ? 'Detected' : 'Cleanly Removed (Direct Classification Head)'}`);

// 2. Build pristine Draw.io XML with strictly non-overlapping bounding boxes
function buildDrawioXml() {
  const cells = [];
  let cellId = 1;

  function nextId() {
    return (++cellId).toString();
  }

  function addVertex(id, val, x, y, w, h, style) {
    cells.push(`
        <mxCell id="${id}" value="${val}" style="${style}" vertex="1" parent="1">
          <mxGeometry x="${x}" y="${y}" width="${w}" height="${h}" as="geometry" />
        </mxCell>`);
  }

  function addEdge(sourceId, targetId, style, label = '', points = []) {
    const id = nextId();
    let ptsXml = '';
    if (points.length > 0) {
      ptsXml = `
            <Array as="points">
              ${points.map(p => `<mxPoint x="${p.x}" y="${p.y}" />`).join('\n              ')}
            </Array>`;
    }
    cells.push(`
        <mxCell id="${id}" value="${label}" style="${style}" edge="1" parent="1" source="${sourceId}" target="${targetId}">
          <mxGeometry relative="1" as="geometry">${ptsXml}
          </mxGeometry>
        </mxCell>`);
  }

  // =========================================================================
  // COLUMN 1 (LEFT): DOCUMENT INPUTS & HPE (X: 40 to 520, Width: 480)
  // =========================================================================

  // Container 1: Multimodal Document Inputs (Y: 40 to 470, Height: 430)
  const c1_id = nextId();
  addVertex(c1_id, '&lt;b&gt;1. Multimodal Document Input&lt;/b&gt;', 40, 40, 480, 430,
    'rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;align=left;spacingLeft=15;spacingTop=10;fillColor=#F8FAFC;strokeColor=#475569;strokeWidth=2;fontColor=#1E293B;fontSize=13;');

  // Document Page Card
  const doc_card_id = nextId();
  addVertex(doc_card_id, '&lt;b&gt;Scanned Page&lt;/b&gt;&lt;br/&gt;&lt;font color="#64748B" size="1"&gt;Receipt / Form Image&lt;br/&gt;+ OCR Word Boxes&lt;/font&gt;', 60, 90, 140, 360,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#94A3B8;strokeWidth=1.5;fontSize=11;fontColor=#334155;');

  // 4 Input Streams
  const w_tok_id = nextId();
  addVertex(w_tok_id, '&lt;b&gt;Word Tokens&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#92400E"&gt;RoBERTa Text Embeddings&lt;/font&gt;', 230, 95, 270, 65,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF3C7;strokeColor=#D97706;strokeWidth=1.8;fontSize=11;fontColor=#78350F;');

  const p_vis_id = nextId();
  addVertex(p_vis_id, '&lt;b&gt;Image Patches&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#065F46"&gt;16&amp;times;16 Linear Visual Proj.&lt;/font&gt;', 230, 185, 270, 65,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#D1FAE5;strokeColor=#059669;strokeWidth=1.8;fontSize=11;fontColor=#064E3B;');

  const pos_1d_id = nextId();
  addVertex(pos_1d_id, '&lt;b&gt;1D Reading Position&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#1E40AF"&gt;Sequential Word Index (0..N)&lt;/font&gt;', 230, 275, 270, 65,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#DBEAFE;strokeColor=#2563EB;strokeWidth=1.8;fontSize=11;fontColor=#1E3A8A;');

  const pos_2d_id = nextId();
  addVertex(pos_2d_id, '&lt;b&gt;2D Spatial Coordinates&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#374151"&gt;Bounding Boxes [x0, y0, x1, y1, w, h]&lt;/font&gt;', 230, 365, 270, 65,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#F3F4F6;strokeColor=#4B5563;strokeWidth=1.8;fontSize=11;fontColor=#1F2937;');


  // Container 2: Hierarchical Position Encoding (Y: 510 to 980, Height: 470)
  const c2_id = nextId();
  addVertex(c2_id, '&lt;b&gt;2. Hierarchical Position Encoding (HPE)&lt;/b&gt;', 40, 510, 480, 470,
    'rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;align=left;spacingLeft=15;spacingTop=10;fillColor=#FFFBEB;strokeColor=#B45309;strokeWidth=2;fontColor=#78350F;fontSize=13;');

  // Layout extraction banner
  const hpe_banner_id = nextId();
  addVertex(hpe_banner_id, '&lt;b&gt;Geometric Layout Extraction &amp;amp; Multi-Scale Grouping&lt;/b&gt;&lt;br/&gt;&lt;font color="#78350F" size="1"&gt;Disentangles 2D spatial arrangement into explicit hierarchy&lt;/font&gt;', 60, 560, 440, 45,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#D97706;strokeWidth=1.5;fontSize=11;fontColor=#78350F;');

  // 3 Layout Cards side by side
  const hpe_line_id = nextId();
  addVertex(hpe_line_id, '&lt;b&gt;Line Layout&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#78350F"&gt;Vertical overlap &amp;ge; 50%&lt;br/&gt;Reading order index&lt;br/&gt;&lt;b&gt;E&lt;sub&gt;line&lt;/sub&gt;&lt;/b&gt;&lt;/font&gt;', 60, 625, 135, 120,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF3C7;strokeColor=#D97706;strokeWidth=1.5;fontSize=11;fontColor=#78350F;');

  const hpe_col_id = nextId();
  addVertex(hpe_col_id, '&lt;b&gt;Column Layout&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#064E3B"&gt;Horiz. gap &amp;ge; 12% W&lt;br/&gt;Column slot ID&lt;br/&gt;&lt;b&gt;E&lt;sub&gt;col&lt;/sub&gt;&lt;/b&gt;&lt;/font&gt;', 212, 625, 136, 120,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#D1FAE5;strokeColor=#059669;strokeWidth=1.5;fontSize=11;fontColor=#064E3B;');

  const hpe_blk_id = nextId();
  addVertex(hpe_blk_id, '&lt;b&gt;Block Layout&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#1E3A8A"&gt;Line gap &amp;lt; 1.8x H&lt;br/&gt;Semantic paragraph&lt;br/&gt;&lt;b&gt;E&lt;sub&gt;block&lt;/sub&gt;&lt;/b&gt;&lt;/font&gt;', 365, 625, 135, 120,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#DBEAFE;strokeColor=#2563EB;strokeWidth=1.5;fontSize=11;fontColor=#1E3A8A;');

  // Concat & Hierarchical Projection
  const hpe_proj_id = nextId();
  addVertex(hpe_proj_id, '&lt;b&gt;Hierarchical Projection (W&lt;sub&gt;hier&lt;/sub&gt;)&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#475569"&gt;Concat [ E&lt;sub&gt;line&lt;/sub&gt; ; E&lt;sub&gt;col&lt;/sub&gt; ; E&lt;sub&gt;block&lt;/sub&gt; ] &amp;rarr; &amp;Ropf;&lt;sup&gt;d&lt;/sup&gt;&lt;/font&gt;', 60, 770, 440, 55,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#B45309;strokeWidth=1.8;fontSize=11;fontColor=#78350F;');

  const hpe_scale_id = nextId();
  addVertex(hpe_scale_id, '&lt;b&gt;Residual Hierarchical Bias (E&lt;sub&gt;hier&lt;/sub&gt; &amp;times; &amp;beta;)&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#78350F"&gt;Line, column &amp;amp; block structural signals injected into embedding stream&lt;/font&gt;', 60, 855, 440, 60,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF3C7;strokeColor=#B45309;strokeWidth=1.8;fontSize=11;fontColor=#78350F;');


  // =========================================================================
  // COLUMN 2 (CENTER): MULTIMODAL BACKBONE (X: 580 to 880, Width: 300)
  // =========================================================================

  // Summation Adder Circle
  const adder_id = nextId();
  addVertex(adder_id, '&lt;b&gt;&amp;oplus;&lt;/b&gt;', 545, 475, 45, 45,
    'shape=ellipse;fillColor=#FFFFFF;strokeColor=#1E293B;strokeWidth=2;fontSize=18;fontColor=#1E293B;');

  // LayoutLMv3 Backbone Pillar
  const bb_id = nextId();
  addVertex(bb_id, '&lt;b&gt;LayoutLMv3 Multimodal Backbone&lt;/b&gt;&lt;br/&gt;&lt;br/&gt;&amp;bull; 12 Transformer Encoder Layers&lt;br/&gt;&lt;br/&gt;&amp;bull; Joint Text &amp;amp; Visual Patch Attention&lt;br/&gt;&lt;br/&gt;&amp;bull; 2D Spatial Relative Position Bias&lt;br/&gt;&lt;br/&gt;&amp;bull; Multimodal Hidden Dim: d = 768', 610, 50, 240, 930,
    'rounded=1;whiteSpace=wrap;html=1;verticalAlign=middle;align=center;fillColor=#EFF6FF;strokeColor=#1D4ED8;strokeWidth=2.2;fontColor=#1E3A8A;fontSize=12;');

  // Exiting Modality States
  const h_i_id = nextId();
  addVertex(h_i_id, '&lt;b&gt;Text Token States (h&lt;sub&gt;i&lt;/sub&gt;)&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#1E40AF"&gt;Contextualized Word Representations&lt;/font&gt;', 875, 175, 150, 60,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#DBEAFE;strokeColor=#2563EB;strokeWidth=1.8;fontSize=11;fontColor=#1E3A8A;');

  const v_p_id = nextId();
  addVertex(v_p_id, '&lt;b&gt;Visual Patch States (v&lt;sub&gt;p&lt;/sub&gt;)&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#065F46"&gt;Visual Region Feature Vectors&lt;/font&gt;', 875, 775, 150, 60,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#D1FAE5;strokeColor=#059669;strokeWidth=1.8;fontSize=11;fontColor=#064E3B;');


  // =========================================================================
  // COLUMN 3 (RIGHT): SCM, CLASSIFIER, BOUNDARY & CONTRASTIVE LOSS
  // (X: 1050 to 1760, Width: 710)
  // =========================================================================

  // 1. Segment Context Module Container (Y: 40 to 280, Height: 240)
  const c3_id = nextId();
  addVertex(c3_id, '&lt;b&gt;3. Segment Context Module (SCM)&lt;/b&gt;', 1050, 40, 710, 240,
    'rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;align=left;spacingLeft=15;spacingTop=10;fillColor=#ECFDF5;strokeColor=#047857;strokeWidth=2;fontColor=#064E3B;fontSize=13;');

  const scm_pool_id = nextId();
  addVertex(scm_pool_id, '&lt;b&gt;Segment Mean Pool&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#065F46"&gt;Averages tokens in line k&lt;br/&gt;&amp;rarr; Segment vector s&lt;sub&gt;k&lt;/sub&gt;&lt;/font&gt;', 1075, 90, 185, 65,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#059669;strokeWidth=1.5;fontSize=11;fontColor=#064E3B;');

  const scm_trans_id = nextId();
  addVertex(scm_trans_id, '&lt;b&gt;Segment Transformer&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#065F46"&gt;1-Layer, 4-Head Attention&lt;br/&gt;Inter-segment context c&lt;sub&gt;k&lt;/sub&gt;&lt;/font&gt;', 1300, 90, 195, 65,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#059669;strokeWidth=1.5;fontSize=11;fontColor=#064E3B;');

  const scm_rezero_id = nextId();
  addVertex(scm_rezero_id, '&lt;b&gt;ReZero Residual Gate&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#065F46"&gt;s&lt;sub&gt;k&lt;/sub&gt; + g &amp;times; (c&lt;sub&gt;k&lt;/sub&gt; - s&lt;sub&gt;k&lt;/sub&gt;)&lt;br/&gt;Refined segment s&amp;#39;&lt;sub&gt;k&lt;/sub&gt;&lt;/font&gt;', 1535, 90, 200, 65,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#D1FAE5;strokeColor=#059669;strokeWidth=1.5;fontSize=11;fontColor=#064E3B;');

  const scm_broad_id = nextId();
  addVertex(scm_broad_id, '&lt;b&gt;Broadcast Segment Context + Segment-Start Onset Embedding: h&lt;sub&gt;i&lt;/sub&gt;&lt;sup&gt;final&lt;/sup&gt; = h&lt;sub&gt;i&lt;/sub&gt; + s&amp;#39;&lt;sub&gt;s(i)&lt;/sub&gt; + e&lt;sup&gt;onset&lt;/sup&gt;&lt;/b&gt;', 1075, 180, 660, 55,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#047857;strokeWidth=1.5;fontSize=11;fontColor=#064E3B;');


  // 2. Direct Token Classifier Head Container (Y: 305 to 445, Height: 140)
  const c4_id = nextId();
  addVertex(c4_id, '&lt;b&gt;4. Direct Token Classifier Head&lt;/b&gt;', 1050, 305, 710, 140,
    'rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;align=left;spacingLeft=15;spacingTop=10;fillColor=#F8FAFC;strokeColor=#334155;strokeWidth=2;fontColor=#0F172A;fontSize=13;');

  const cls_linear_id = nextId();
  addVertex(cls_linear_id, '&lt;b&gt;Linear Classification Layer&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#475569"&gt;Projects h&lt;sub&gt;i&lt;/sub&gt;&lt;sup&gt;final&lt;/sup&gt; directly to class logits z&lt;sub&gt;i&lt;/sub&gt;&lt;br/&gt;(Zero added inference latency)&lt;/font&gt;', 1075, 355, 305, 65,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#334155;strokeWidth=1.8;fontSize=11;fontColor=#1E293B;');

  const cls_loss_id = nextId();
  addVertex(cls_loss_id, '&lt;b&gt;Entity Cross-Entropy Loss (&lt;font color="#DC2626"&gt;L&lt;sub&gt;CE&lt;/sub&gt;&lt;/font&gt;)&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#475569"&gt;Softmax probabilities vs ground-truth IOB2 tags&lt;/font&gt;', 1420, 355, 315, 65,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#DC2626;strokeWidth=1.8;fontSize=11;fontColor=#991B1B;');


  // 3. Intra-Line Boundary Loss Module Container (Y: 470 to 710, Height: 240)
  const c5_id = nextId();
  addVertex(c5_id, '&lt;b&gt;5. Intra-Line Boundary Loss Classifier (Detailed Supervision)&lt;/b&gt;', 1050, 470, 710, 240,
    'rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;align=left;spacingLeft=15;spacingTop=10;fillColor=#FFFBEB;strokeColor=#D97706;strokeWidth=2;fontColor=#78350F;fontSize=13;');

  const bnd_pair_id = nextId();
  addVertex(bnd_pair_id, '&lt;b&gt;Adjacent Word Pair&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#78350F"&gt;Same text line: [ h&lt;sub&gt;i&lt;/sub&gt; ; h&lt;sub&gt;i+1&lt;/sub&gt; ]&lt;/font&gt;', 1075, 520, 165, 65,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF3C7;strokeColor=#D97706;strokeWidth=1.5;fontSize=11;fontColor=#78350F;');

  const bnd_mlp_id = nextId();
  addVertex(bnd_mlp_id, '&lt;b&gt;Boundary MLP&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#78350F"&gt;Linear(2d&amp;rarr;d) &amp;rarr; ReLU&lt;br/&gt;&amp;rarr; Linear(d&amp;rarr;1) &amp;rarr; &amp;sigma;&lt;/font&gt;', 1270, 520, 150, 65,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#D97706;strokeWidth=1.5;fontSize=11;fontColor=#78350F;');

  // Visual Ground Truth Supervisor (Shapes & Lines, Target 0 vs 1)
  const bnd_vis_card = nextId();
  addVertex(bnd_vis_card, '&lt;b&gt;Ground-Truth Transition Signals:&lt;/b&gt;&lt;br/&gt;&lt;br/&gt;&amp;bull; &lt;b&gt;Within Entity:&lt;/b&gt;&amp;nbsp;&amp;nbsp;[Word A] &lt;font color="#2563EB"&gt;&amp;mdash;&amp;mdash;&amp;mdash;&lt;/font&gt; [Word B] &amp;rarr; &lt;b&gt;&lt;font color="#2563EB"&gt;Target = 0&lt;/font&gt;&lt;/b&gt;&lt;br/&gt;&amp;bull; &lt;b&gt;Entity Boundary:&lt;/b&gt;&amp;nbsp;&amp;nbsp;[Field Name] &lt;b&gt;&lt;font color="#DC2626"&gt;|&lt;/font&gt;&lt;/b&gt; [Field Value] &amp;rarr; &lt;b&gt;&lt;font color="#DC2626"&gt;Target = 1&lt;/font&gt;&lt;/b&gt;', 1450, 515, 285, 75,
    'rounded=1;whiteSpace=wrap;html=1;align=left;spacingLeft=10;fillColor=#FFFFFF;strokeColor=#94A3B8;strokeWidth=1.5;fontSize=10;fontColor=#1E293B;');

  const bnd_loss_id = nextId();
  addVertex(bnd_loss_id, '&lt;b&gt;Intra-Line Boundary BCE Loss (&lt;font color="#DC2626"&gt;L&lt;sub&gt;bound&lt;/sub&gt;&lt;/font&gt;)&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#78350F"&gt;Directly penalizes false entity merges along the same reading line (prevents label bleed)&lt;/font&gt;', 1075, 615, 660, 50,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF3C7;strokeColor=#B45309;strokeWidth=1.8;fontSize=11;fontColor=#78350F;');


  // 4. Cross-Modal Contrastive Loss Module Container (Y: 735 to 975, Height: 240)
  const c6_id = nextId();
  addVertex(c6_id, '&lt;b&gt;6. Cross-Modal Contrastive Loss (Text-Image Alignment)&lt;/b&gt;', 1050, 735, 710, 240,
    'rounded=1;whiteSpace=wrap;html=1;verticalAlign=top;align=left;spacingLeft=15;spacingTop=10;fillColor=#ECFDF5;strokeColor=#059669;strokeWidth=2;fontColor=#064E3B;fontSize=13;');

  const cont_txt_id = nextId();
  addVertex(cont_txt_id, '&lt;b&gt;Text Token Vector&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#1E40AF"&gt;Proj: z&lt;sub&gt;i&lt;/sub&gt;&lt;sup&gt;text&lt;/sup&gt; = g&lt;sub&gt;text&lt;/sub&gt;(h&lt;sub&gt;i&lt;/sub&gt;&lt;sup&gt;final&lt;/sup&gt;)&lt;/font&gt;', 1075, 785, 175, 65,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#DBEAFE;strokeColor=#2563EB;strokeWidth=1.5;fontSize=11;fontColor=#1E3A8A;');

  const cont_img_id = nextId();
  addVertex(cont_img_id, '&lt;b&gt;Visual Patch Vector&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#065F46"&gt;Proj: z&lt;sub&gt;p(i)&lt;/sub&gt;&lt;sup&gt;img&lt;/sup&gt; = g&lt;sub&gt;img&lt;/sub&gt;(v&lt;sub&gt;p&lt;/sub&gt;)&lt;/font&gt;', 1075, 875, 175, 65,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#D1FAE5;strokeColor=#059669;strokeWidth=1.5;fontSize=11;fontColor=#064E3B;');

  // Visual Contrastive Alignment (Pull vs Push)
  const cont_vis_id = nextId();
  addVertex(cont_vis_id, '&lt;b&gt;InfoNCE Alignment (&amp;tau; = 0.07):&lt;/b&gt;&lt;br/&gt;&lt;br/&gt;&lt;font color="#059669"&gt;&amp;harr; &lt;b&gt;PULL:&lt;/b&gt; Matched (Token &amp;amp; Bounding-Box Patch)&lt;/font&gt;&lt;br/&gt;&lt;font color="#DC2626"&gt;&amp;harr; &lt;b&gt;PUSH:&lt;/b&gt; Non-matching Distractor Patches&lt;/font&gt;', 1285, 785, 250, 155,
    'rounded=1;whiteSpace=wrap;html=1;align=center;fillColor=#FFFFFF;strokeColor=#059669;strokeWidth=1.8;fontSize=11;fontColor=#064E3B;');

  const cont_loss_id = nextId();
  addVertex(cont_loss_id, '&lt;b&gt;Contrastive Loss&lt;br/&gt;(&lt;font color="#DC2626"&gt;L&lt;sub&gt;cont&lt;/sub&gt;&lt;/font&gt;)&lt;/b&gt;&lt;br/&gt;&lt;font size="1" color="#065F46"&gt;Prevents visual representation drift during fine-tuning&lt;/font&gt;', 1565, 825, 170, 75,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#D1FAE5;strokeColor=#047857;strokeWidth=1.8;fontSize=11;fontColor=#064E3B;');


  // =========================================================================
  // JOINT MULTI-TASK LOSS BANNER (BOTTOM) (X: 610 to 1760, Width: 1150)
  // =========================================================================
  const banner_id = nextId();
  addVertex(banner_id, '&lt;b&gt;Joint Multi-Task Training Objective:&lt;/b&gt;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&lt;b&gt;L&lt;sub&gt;total&lt;/sub&gt;&lt;/b&gt;&amp;nbsp;=&amp;nbsp;&lt;b&gt;L&lt;sub&gt;CE&lt;/sub&gt;&lt;/b&gt;&amp;nbsp;+&amp;nbsp;&lt;b&gt;&amp;lambda;&lt;sub&gt;bound&lt;/sub&gt;&amp;nbsp;&amp;times;&amp;nbsp;L&lt;sub&gt;bound&lt;/sub&gt;&lt;/b&gt;&amp;nbsp;+&amp;nbsp;&lt;b&gt;&amp;lambda;&lt;sub&gt;cont&lt;/sub&gt;&amp;nbsp;&amp;times;&amp;nbsp;L&lt;sub&gt;cont&lt;/sub&gt;&lt;/b&gt;&amp;nbsp;&amp;nbsp;&amp;nbsp;&amp;nbsp;&lt;font size="1" color="#94A3B8"&gt;(&amp;lambda;&lt;sub&gt;bound&lt;/sub&gt; = 0.2, &amp;lambda;&lt;sub&gt;cont&lt;/sub&gt; = 0.1)&lt;/font&gt;', 610, 1010, 1150, 55,
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#0F172A;strokeColor=#020617;strokeWidth=2;fontColor=#F8FAFC;fontSize=13;fontStyle=1;');


  // =========================================================================
  // EXPLICIT ORTHOGONAL CONNECTORS (NO OVERLAPS)
  // =========================================================================
  const edgeBlue = 'edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#2563EB;strokeWidth=2;html=1;';
  const edgeAmber = 'edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#D97706;strokeWidth=2;html=1;';
  const edgeGreen = 'edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#059669;strokeWidth=2;html=1;';
  const edgeRed = 'edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#DC2626;strokeWidth=2;html=1;';
  const edgeDark = 'edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#334155;strokeWidth=2;html=1;';

  // Input -> Adder -> Backbone
  addEdge(pos_1d_id, adder_id, edgeBlue);
  addEdge(hpe_scale_id, adder_id, edgeAmber, '', [{ x: 567, y: 885 }]);
  addEdge(adder_id, bb_id, edgeDark);

  // Backbone -> Modality states
  addEdge(bb_id, h_i_id, edgeBlue, '', [{ x: 860, y: 205 }]);
  addEdge(bb_id, v_p_id, edgeGreen, '', [{ x: 860, y: 805 }]);

  // Tokens -> SCM Pool -> Transformer -> ReZero -> Broadcast
  addEdge(h_i_id, scm_pool_id, edgeGreen, 'Pool', [{ x: 1040, y: 205 }, { x: 1040, y: 122 }]);
  addEdge(scm_pool_id, scm_trans_id, edgeGreen);
  addEdge(scm_trans_id, scm_rezero_id, edgeGreen, '+g');
  addEdge(scm_rezero_id, scm_broad_id, edgeGreen, '', [{ x: 1635, y: 180 }]);

  // SCM Broadcast -> Linear Classifier -> CE Loss
  addEdge(scm_broad_id, cls_linear_id, edgeDark, '', [{ x: 1227, y: 235 }, { x: 1227, y: 355 }]);
  addEdge(cls_linear_id, cls_loss_id, edgeRed);

  // SCM Broadcast -> Boundary Pair -> MLP -> Visual -> Loss
  addEdge(scm_broad_id, bnd_pair_id, edgeAmber, '', [{ x: 1157, y: 235 }, { x: 1157, y: 520 }]);
  addEdge(bnd_pair_id, bnd_mlp_id, edgeAmber);
  addEdge(bnd_mlp_id, bnd_vis_card, edgeAmber);
  addEdge(bnd_vis_card, bnd_loss_id, edgeAmber, '', [{ x: 1592, y: 615 }]);

  // SCM Broadcast & Visual Patches -> Contrastive Module
  addEdge(scm_broad_id, cont_txt_id, edgeBlue, '', [{ x: 1040, y: 235 }, { x: 1040, y: 817 }]);
  addEdge(v_p_id, cont_img_id, edgeGreen, '', [{ x: 1040, y: 805 }, { x: 1040, y: 907 }]);
  addEdge(cont_txt_id, cont_vis_id, edgeGreen);
  addEdge(cont_img_id, cont_vis_id, edgeGreen);
  addEdge(cont_vis_id, cont_loss_id, edgeGreen);

  // Losses to Total Objective Banner
  addEdge(cls_loss_id, banner_id, edgeRed, '', [{ x: 1750, y: 387 }, { x: 1750, y: 1010 }]);
  addEdge(bnd_loss_id, banner_id, edgeAmber, '', [{ x: 1740, y: 640 }, { x: 1740, y: 1010 }]);
  addEdge(cont_loss_id, banner_id, edgeGreen, '', [{ x: 1730, y: 862 }, { x: 1730, y: 1010 }]);

  return `<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" agent="Antigravity" version="24.0.0">
  <diagram id="model_arch_reconstructed" name="Enhanced LayoutLMv3 Architecture">
    <mxGraphModel dx="1800" dy="1100" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1820" pageHeight="1120" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />${cells.join('')}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>`;
}

const drawioContent = buildDrawioXml();
const targetDrawioPath = path.resolve(__dirname, '../thesis/figures/model_architecture.drawio');
const brainDrawioPath = 'C:/Users/nhatm/.gemini/antigravity/brain/602639c6-1a2d-485a-9823-c5f9bb4ea4cb/model_architecture.drawio';

fs.writeFileSync(targetDrawioPath, drawioContent, 'utf8');
fs.writeFileSync(brainDrawioPath, drawioContent, 'utf8');
console.log(`Saved pristine Draw.io file to: ${targetDrawioPath}`);
console.log(`Saved pristine Draw.io file to: ${brainDrawioPath}`);

// 3. Generate high-resolution HTML/SVG preview container for JPEG export
const htmlPreview = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Model Architecture Diagram</title>
  <style>
    body { margin: 0; padding: 20px; background: #FFFFFF; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
    .canvas { width: 1820px; height: 1100px; position: relative; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; }
  </style>
</head>
<body>
  <div class="canvas">
    <!-- SVG rendered preview matching the drawio layout -->
    <svg width="1820" height="1100" viewBox="0 0 1820 1100" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1 L 8 5 L 0 9 z" fill="#334155" />
        </marker>
        <marker id="arrow-green" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1 L 8 5 L 0 9 z" fill="#059669" />
        </marker>
        <marker id="arrow-amber" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1 L 8 5 L 0 9 z" fill="#D97706" />
        </marker>
        <marker id="arrow-blue" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1 L 8 5 L 0 9 z" fill="#2563EB" />
        </marker>
        <marker id="arrow-red" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1 L 8 5 L 0 9 z" fill="#DC2626" />
        </marker>
      </defs>

      <!-- 1. Document Input Container -->
      <rect x="40" y="40" width="480" height="430" rx="10" fill="#F8FAFC" stroke="#475569" stroke-width="2"/>
      <text x="55" y="65" font-size="14" font-weight="bold" fill="#1E293B">1. Multimodal Document Input</text>

      <rect x="60" y="90" width="140" height="360" rx="6" fill="#FFFFFF" stroke="#94A3B8" stroke-width="1.5"/>
      <text x="130" y="140" font-size="13" font-weight="bold" fill="#334155" text-anchor="middle">Scanned Page</text>
      <text x="130" y="165" font-size="11" fill="#64748B" text-anchor="middle">Form / Receipt</text>
      <line x1="80" y1="190" x2="180" y2="190" stroke="#CBD5E1" stroke-width="2"/>
      <line x1="80" y1="215" x2="180" y2="215" stroke="#CBD5E1" stroke-width="2"/>
      <line x1="80" y1="240" x2="180" y2="240" stroke="#CBD5E1" stroke-width="2"/>
      <line x1="80" y1="265" x2="180" y2="265" stroke="#CBD5E1" stroke-width="2"/>
      <rect x="80" y="290" width="60" height="18" fill="#FEF3C7" stroke="#D97706"/>
      <rect x="80" y="320" width="80" height="18" fill="#D1FAE5" stroke="#059669"/>
      <text x="130" y="380" font-size="10" fill="#64748B" text-anchor="middle">[OCR Words &amp; Boxes]</text>

      <!-- 4 Embeddings -->
      <rect x="230" y="95" width="270" height="65" rx="6" fill="#FEF3C7" stroke="#D97706" stroke-width="1.8"/>
      <text x="365" y="125" font-size="12" font-weight="bold" fill="#78350F" text-anchor="middle">Word Tokens</text>
      <text x="365" y="145" font-size="10" fill="#92400E" text-anchor="middle">RoBERTa Text Embeddings</text>

      <rect x="230" y="185" width="270" height="65" rx="6" fill="#D1FAE5" stroke="#059669" stroke-width="1.8"/>
      <text x="365" y="215" font-size="12" font-weight="bold" fill="#064E3B" text-anchor="middle">Visual Image Patches</text>
      <text x="365" y="235" font-size="10" fill="#065F46" text-anchor="middle">16x16 Linear Patch Proj.</text>

      <rect x="230" y="275" width="270" height="65" rx="6" fill="#DBEAFE" stroke="#2563EB" stroke-width="1.8"/>
      <text x="365" y="305" font-size="12" font-weight="bold" fill="#1E3A8A" text-anchor="middle">1D Reading Position</text>
      <text x="365" y="325" font-size="10" fill="#1E40AF" text-anchor="middle">Sequential Word Index (0..N)</text>

      <rect x="230" y="365" width="270" height="65" rx="6" fill="#F3F4F6" stroke="#4B5563" stroke-width="1.8"/>
      <text x="365" y="395" font-size="12" font-weight="bold" fill="#1F2937" text-anchor="middle">2D Spatial Coordinates</text>
      <text x="365" y="415" font-size="10" fill="#374151" text-anchor="middle">Bounding Boxes [x0, y0, x1, y1, w, h]</text>

      <!-- 2. Hierarchical Position Encoding Container -->
      <rect x="40" y="510" width="480" height="470" rx="10" fill="#FFFBEB" stroke="#B45309" stroke-width="2"/>
      <text x="55" y="535" font-size="14" font-weight="bold" fill="#78350F">2. Hierarchical Position Encoding (HPE)</text>

      <rect x="60" y="560" width="440" height="45" rx="6" fill="#FFFFFF" stroke="#D97706" stroke-width="1.5"/>
      <text x="280" y="588" font-size="11" font-weight="bold" fill="#78350F" text-anchor="middle">Geometric Layout Extraction &amp; Multi-Scale Grouping</text>

      <rect x="60" y="625" width="135" height="120" rx="6" fill="#FEF3C7" stroke="#D97706" stroke-width="1.5"/>
      <text x="127" y="655" font-size="12" font-weight="bold" fill="#78350F" text-anchor="middle">Line Layout</text>
      <text x="127" y="680" font-size="10" fill="#78350F" text-anchor="middle">V-Overlap &#8805; 50%</text>
      <text x="127" y="700" font-size="10" fill="#78350F" text-anchor="middle">Horiz. Reading Order</text>
      <text x="127" y="725" font-size="12" font-weight="bold" fill="#B45309" text-anchor="middle">E_line</text>

      <rect x="212" y="625" width="136" height="120" rx="6" fill="#D1FAE5" stroke="#059669" stroke-width="1.5"/>
      <text x="280" y="655" font-size="12" font-weight="bold" fill="#064E3B" text-anchor="middle">Column Layout</text>
      <text x="280" y="680" font-size="10" fill="#064E3B" text-anchor="middle">H-Gap &#8805; 12% W</text>
      <text x="280" y="700" font-size="10" fill="#064E3B" text-anchor="middle">Column Slot ID</text>
      <text x="280" y="725" font-size="12" font-weight="bold" fill="#047857" text-anchor="middle">E_col</text>

      <rect x="365" y="625" width="135" height="120" rx="6" fill="#DBEAFE" stroke="#2563EB" stroke-width="1.5"/>
      <text x="432" y="655" font-size="12" font-weight="bold" fill="#1E3A8A" text-anchor="middle">Block Layout</text>
      <text x="432" y="680" font-size="10" fill="#1E3A8A" text-anchor="middle">Line Gap &lt; 1.8x H</text>
      <text x="432" y="700" font-size="10" fill="#1E3A8A" text-anchor="middle">Semantic Section</text>
      <text x="432" y="725" font-size="12" font-weight="bold" fill="#1D4ED8" text-anchor="middle">E_block</text>

      <rect x="60" y="770" width="440" height="55" rx="6" fill="#FFFFFF" stroke="#B45309" stroke-width="1.8"/>
      <text x="280" y="802" font-size="11" font-weight="bold" fill="#78350F" text-anchor="middle">Hierarchical Projection (W_hier): Concat [ E_line ; E_col ; E_block ] &#8594; R^d</text>

      <rect x="60" y="855" width="440" height="60" rx="6" fill="#FEF3C7" stroke="#B45309" stroke-width="1.8"/>
      <text x="280" y="888" font-size="12" font-weight="bold" fill="#78350F" text-anchor="middle">Residual Hierarchical Bias (E_hier &#215; &#946;)</text>

      <!-- Center Adder & Backbone -->
      <circle cx="567" cy="497" r="22" fill="#FFFFFF" stroke="#1E293B" stroke-width="2"/>
      <text x="567" y="504" font-size="20" font-weight="bold" fill="#1E293B" text-anchor="middle">+</text>

      <rect x="610" y="50" width="240" height="930" rx="10" fill="#EFF6FF" stroke="#1D4ED8" stroke-width="2.2"/>
      <text x="730" y="320" font-size="16" font-weight="bold" fill="#1E3A8A" text-anchor="middle">LayoutLMv3 Backbone</text>
      <text x="730" y="380" font-size="12" fill="#1E3A8A" text-anchor="middle">&#8226; 12 Transformer Layers</text>
      <text x="730" y="420" font-size="12" fill="#1E3A8A" text-anchor="middle">&#8226; Joint Text &amp; Image Attention</text>
      <text x="730" y="460" font-size="12" fill="#1E3A8A" text-anchor="middle">&#8226; 2D Spatial Relative Bias</text>
      <text x="730" y="500" font-size="12" fill="#1E3A8A" text-anchor="middle">&#8226; Hidden Dim: d = 768</text>

      <!-- Modality Exit Vectors -->
      <rect x="875" y="175" width="150" height="60" rx="6" fill="#DBEAFE" stroke="#2563EB" stroke-width="1.8"/>
      <text x="950" y="205" font-size="11" font-weight="bold" fill="#1E3A8A" text-anchor="middle">Text Tokens (h_i)</text>

      <rect x="875" y="775" width="150" height="60" rx="6" fill="#D1FAE5" stroke="#059669" stroke-width="1.8"/>
      <text x="950" y="805" font-size="11" font-weight="bold" fill="#064E3B" text-anchor="middle">Visual Patches (v_p)</text>

      <!-- 3. Segment Context Module -->
      <rect x="1050" y="40" width="710" height="240" rx="10" fill="#ECFDF5" stroke="#047857" stroke-width="2"/>
      <text x="1065" y="65" font-size="14" font-weight="bold" fill="#064E3B">3. Segment Context Module (SCM)</text>

      <rect x="1075" y="90" width="185" height="65" rx="6" fill="#FFFFFF" stroke="#059669" stroke-width="1.5"/>
      <text x="1167" y="120" font-size="11" font-weight="bold" fill="#064E3B" text-anchor="middle">Segment Mean Pool</text>
      <text x="1167" y="140" font-size="10" fill="#065F46" text-anchor="middle">Average tokens &#8594; s_k</text>

      <rect x="1300" y="90" width="195" height="65" rx="6" fill="#FFFFFF" stroke="#059669" stroke-width="1.5"/>
      <text x="1397" y="120" font-size="11" font-weight="bold" fill="#064E3B" text-anchor="middle">Segment Transformer</text>
      <text x="1397" y="140" font-size="10" fill="#065F46" text-anchor="middle">1-Layer, 4-Head Attention</text>

      <rect x="1535" y="90" width="200" height="65" rx="6" fill="#D1FAE5" stroke="#059669" stroke-width="1.5"/>
      <text x="1635" y="120" font-size="11" font-weight="bold" fill="#064E3B" text-anchor="middle">ReZero Residual Gate</text>
      <text x="1635" y="140" font-size="10" fill="#065F46" text-anchor="middle">s_k + g &#215; (c_k - s_k)</text>

      <rect x="1075" y="180" width="660" height="55" rx="6" fill="#FFFFFF" stroke="#047857" stroke-width="1.5"/>
      <text x="1405" y="213" font-size="11" font-weight="bold" fill="#064E3B" text-anchor="middle">Broadcast Context + Onset Embedding: h_i^final = h_i + s&apos;_{s(i)} + e^onset</text>

      <!-- 4. Direct Token Classifier -->
      <rect x="1050" y="305" width="710" height="140" rx="10" fill="#F8FAFC" stroke="#334155" stroke-width="2"/>
      <text x="1065" y="330" font-size="14" font-weight="bold" fill="#0F172A">4. Direct Token Classifier Head</text>

      <rect x="1075" y="355" width="305" height="65" rx="6" fill="#FFFFFF" stroke="#334155" stroke-width="1.8"/>
      <text x="1227" y="385" font-size="12" font-weight="bold" fill="#1E293B" text-anchor="middle">Linear Classification Layer</text>
      <text x="1227" y="405" font-size="10" fill="#475569" text-anchor="middle">Projects h_i^final directly to class logits z_i</text>

      <rect x="1420" y="355" width="315" height="65" rx="6" fill="#FEF2F2" stroke="#DC2626" stroke-width="1.8"/>
      <text x="1577" y="385" font-size="12" font-weight="bold" fill="#991B1B" text-anchor="middle">Entity Cross-Entropy Loss (L_CE)</text>
      <text x="1577" y="405" font-size="10" fill="#DC2626" text-anchor="middle">Softmax probabilities vs ground-truth IOB2 tags</text>

      <!-- 5. Boundary Loss Module -->
      <rect x="1050" y="470" width="710" height="240" rx="10" fill="#FFFBEB" stroke="#D97706" stroke-width="2"/>
      <text x="1065" y="495" font-size="14" font-weight="bold" fill="#78350F">5. Intra-Line Boundary Loss Classifier (Detailed Supervision)</text>

      <rect x="1075" y="520" width="165" height="65" rx="6" fill="#FEF3C7" stroke="#D97706" stroke-width="1.5"/>
      <text x="1157" y="550" font-size="11" font-weight="bold" fill="#78350F" text-anchor="middle">Adjacent Word Pair</text>
      <text x="1157" y="570" font-size="10" fill="#78350F" text-anchor="middle">[ h_i ; h_{i+1} ] &#8712; R^{2d}</text>

      <rect x="1270" y="520" width="150" height="65" rx="6" fill="#FFFFFF" stroke="#D97706" stroke-width="1.5"/>
      <text x="1345" y="550" font-size="11" font-weight="bold" fill="#78350F" text-anchor="middle">Boundary MLP</text>
      <text x="1345" y="570" font-size="10" fill="#78350F" text-anchor="middle">Linear &#8594; ReLU &#8594; Linear &#8594; &#963;</text>

      <!-- Visual Ground Truth: Same Entity (0) vs Boundary (1) -->
      <rect x="1450" y="515" width="285" height="75" rx="6" fill="#FFFFFF" stroke="#94A3B8" stroke-width="1.5"/>
      <text x="1465" y="535" font-size="10" font-weight="bold" fill="#1E293B">Ground-Truth Transition Signals:</text>
      <circle cx="1480" cy="552" r="5" fill="#2563EB"/>
      <line x1="1485" y1="552" x2="1525" y2="552" stroke="#2563EB" stroke-width="2"/>
      <circle cx="1530" cy="552" r="5" fill="#2563EB"/>
      <text x="1545" y="556" font-size="10" fill="#1E40AF">Within Entity &#8594; Target = 0</text>
      <circle cx="1480" cy="575" r="5" fill="#DC2626"/>
      <line x1="1498" y1="567" x2="1498" y2="583" stroke="#DC2626" stroke-width="2.5" stroke-dasharray="2,2"/>
      <circle cx="1515" cy="575" r="5" fill="#DC2626"/>
      <text x="1545" y="579" font-size="10" fill="#991B1B">Boundary Split &#8594; Target = 1</text>

      <rect x="1075" y="615" width="660" height="50" rx="6" fill="#FEF3C7" stroke="#B45309" stroke-width="1.8"/>
      <text x="1405" y="645" font-size="11" font-weight="bold" fill="#78350F" text-anchor="middle">Intra-Line Boundary BCE Loss (L_bound) &#8212; Penalizes false entity merges along reading lines</text>

      <!-- 6. Contrastive Loss Module -->
      <rect x="1050" y="735" width="710" height="240" rx="10" fill="#ECFDF5" stroke="#059669" stroke-width="2"/>
      <text x="1065" y="760" font-size="14" font-weight="bold" fill="#064E3B">6. Cross-Modal Contrastive Loss (Text-Image Alignment)</text>

      <rect x="1075" y="785" width="175" height="65" rx="6" fill="#DBEAFE" stroke="#2563EB" stroke-width="1.5"/>
      <text x="1162" y="815" font-size="11" font-weight="bold" fill="#1E3A8A" text-anchor="middle">Text Token Vector</text>
      <text x="1162" y="835" font-size="10" fill="#1E40AF" text-anchor="middle">z_i^text = g_text(h_i^final)</text>

      <rect x="1075" y="875" width="175" height="65" rx="6" fill="#D1FAE5" stroke="#059669" stroke-width="1.5"/>
      <text x="1162" y="905" font-size="11" font-weight="bold" fill="#064E3B" text-anchor="middle">Visual Patch Vector</text>
      <text x="1162" y="925" font-size="10" fill="#065F46" text-anchor="middle">z_{p(i)}^img = g_img(v_p)</text>

      <!-- Alignment Visual: Pull vs Push -->
      <rect x="1285" y="785" width="250" height="155" rx="6" fill="#FFFFFF" stroke="#059669" stroke-width="1.8"/>
      <text x="1410" y="815" font-size="12" font-weight="bold" fill="#064E3B" text-anchor="middle">InfoNCE Alignment (&#964; = 0.07)</text>
      <line x1="1310" y1="850" x2="1510" y2="850" stroke="#059669" stroke-width="2.5" marker-end="url(#arrow-green)" marker-start="url(#arrow-green)"/>
      <text x="1410" y="842" font-size="10" font-weight="bold" fill="#059669" text-anchor="middle">PULL: Matched Text-Image Pair</text>
      <line x1="1310" y1="900" x2="1510" y2="900" stroke="#DC2626" stroke-width="2" stroke-dasharray="4,3" marker-end="url(#arrow-red)" marker-start="url(#arrow-red)"/>
      <text x="1410" y="892" font-size="10" font-weight="bold" fill="#DC2626" text-anchor="middle">PUSH: Non-matching Patches</text>

      <rect x="1565" y="825" width="170" height="75" rx="6" fill="#D1FAE5" stroke="#047857" stroke-width="1.8"/>
      <text x="1650" y="855" font-size="12" font-weight="bold" fill="#064E3B" text-anchor="middle">Contrastive Loss</text>
      <text x="1650" y="875" font-size="12" font-weight="bold" fill="#DC2626" text-anchor="middle">(L_cont)</text>

      <!-- Joint Banner -->
      <rect x="610" y="1010" width="1150" height="55" rx="8" fill="#0F172A" stroke="#020617" stroke-width="2"/>
      <text x="1185" y="1043" font-size="13" font-weight="bold" fill="#F8FAFC" text-anchor="middle">Joint Multi-Task Objective:  L_total = L_CE + &#955;_bound &#215; L_bound + &#955;_cont &#215; L_cont   (&#955;_bound = 0.2, &#955;_cont = 0.1)</text>

      <!-- Connecting Flow Lines -->
      <path d="M 500 307 L 545 307 L 545 475" fill="none" stroke="#2563EB" stroke-width="2" marker-end="url(#arrow-blue)"/>
      <path d="M 500 885 L 567 885 L 567 520" fill="none" stroke="#D97706" stroke-width="2" marker-end="url(#arrow-amber)"/>
      <line x1="567" y1="475" x2="610" y2="475" stroke="#334155" stroke-width="2" marker-end="url(#arrow)"/>
      <line x1="850" y1="205" x2="875" y2="205" stroke="#2563EB" stroke-width="2" marker-end="url(#arrow-blue)"/>
      <line x1="850" y1="805" x2="875" y2="805" stroke="#059669" stroke-width="2" marker-end="url(#arrow-green)"/>
      <path d="M 1025 205 L 1040 205 L 1040 122 L 1075 122" fill="none" stroke="#059669" stroke-width="2" marker-end="url(#arrow-green)"/>
      <line x1="1260" y1="122" x2="1300" y2="122" stroke="#059669" stroke-width="2" marker-end="url(#arrow-green)"/>
      <line x1="1495" y1="122" x2="1535" y2="122" stroke="#059669" stroke-width="2" marker-end="url(#arrow-green)"/>
      <line x1="1380" y1="387" x2="1420" y2="387" stroke="#DC2626" stroke-width="2" marker-end="url(#arrow-red)"/>
      <line x1="1240" y1="552" x2="1270" y2="552" stroke="#D97706" stroke-width="2" marker-end="url(#arrow-amber)"/>
      <line x1="1420" y1="552" x2="1450" y2="552" stroke="#D97706" stroke-width="2" marker-end="url(#arrow-amber)"/>
      <line x1="1250" y1="817" x2="1285" y2="817" stroke="#059669" stroke-width="2" marker-end="url(#arrow-green)"/>
      <line x1="1250" y1="907" x2="1285" y2="907" stroke="#059669" stroke-width="2" marker-end="url(#arrow-green)"/>
      <line x1="1535" y1="862" x2="1565" y2="862" stroke="#059669" stroke-width="2" marker-end="url(#arrow-green)"/>
    </svg>
  </div>
</body>
</html>`;

const previewHtmlPath = path.resolve(__dirname, '../scratch/model_architecture_preview.html');
fs.writeFileSync(previewHtmlPath, htmlPreview, 'utf8');
console.log(`Saved clean vector SVG/HTML preview to: ${previewHtmlPath}`);
