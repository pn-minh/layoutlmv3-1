/**
 * Generates Draw.io XML following strict drawio-skill specifications:
 * - Proper swimlane/container hierarchy with relative child coordinates
 * - Non-overlapping geometry snapped to grid
 * - Semantic color palette with clean icons & shapes
 * - Zero complex math formulas (intuitive visual indicators)
 * - Orthogonal non-crossing edge routing
 */

const fs = require('fs');
const path = require('path');
const { Resvg } = require('@resvg/resvg-js');

function createSkillCompliantDrawio() {
  const cells = [];

  function addCell(id, val, style, vertex, edge, parent, geomXml) {
    cells.push(`
        <mxCell id="${id}" value="${val}" style="${style}" vertex="${vertex ? '1' : '0'}" edge="${edge ? '1' : '0'}" parent="${parent}">
          ${geomXml}
        </mxCell>`);
  }

  function addNode(id, val, style, x, y, w, h, parent = '1') {
    const geom = `<mxGeometry x="${x}" y="${y}" width="${w}" height="${h}" as="geometry" />`;
    addCell(id, val, style, true, false, parent, geom);
  }

  function addEdge(id, source, target, style, val = '', waypoints = [], extraGeom = '') {
    let pts = '';
    if (waypoints.length > 0) {
      pts = `
            <Array as="points">
              ${waypoints.map(p => `<mxPoint x="${p.x}" y="${p.y}" />`).join('\n              ')}
            </Array>`;
    }
    const geom = `<mxGeometry relative="1" as="geometry">${pts}${extraGeom}
          </mxGeometry>`;
    addCell(id, val, style, false, true, '1', geom);
  }

  // =========================================================================
  // 1. CONTAINER: MULTIMODAL DOCUMENT INPUT (c_input)
  // =========================================================================
  addNode('c_input', '1. Multimodal Document Input',
    'swimlane;startSize=35;rounded=1;whiteSpace=wrap;html=1;fillColor=#F8FAFC;strokeColor=#475569;strokeWidth=2;fontStyle=1;fontSize=13;fontColor=#1E293B;',
    40, 40, 460, 420, '1');

  // Children of c_input (coordinates relative to c_input!)
  addNode('doc_page', 'Scanned Document&#xa;&#xa;Receipt / Form&#xa;+ Word Bounding Boxes',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#94A3B8;strokeWidth=1.5;fontColor=#334155;fontSize=11;align=center;',
    20, 50, 130, 350, 'c_input');

  addNode('emb_word', 'Word Tokens&#xa;RoBERTa Text Embeddings',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF3C7;strokeColor=#D97706;strokeWidth=1.8;fontColor=#78350F;fontSize=11;fontStyle=1;align=center;',
    170, 50, 270, 65, 'c_input');

  addNode('emb_patch', 'Visual Image Patches&#xa;16&#215;16 Linear Visual Proj.',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#D1FAE5;strokeColor=#059669;strokeWidth=1.8;fontColor=#064E3B;fontSize=11;fontStyle=1;align=center;',
    170, 145, 270, 65, 'c_input');

  addNode('emb_1d', '1D Reading Sequence Position&#xa;Word Order Indices (0..N)',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#DBEAFE;strokeColor=#2563EB;strokeWidth=1.8;fontColor=#1E3A8A;fontSize=11;fontStyle=1;align=center;',
    170, 240, 270, 65, 'c_input');

  addNode('emb_2d', '2D Spatial Coordinates&#xa;Bounding Box [x0, y0, x1, y1]',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#F3F4F6;strokeColor=#4B5563;strokeWidth=1.8;fontColor=#1F2937;fontSize=11;fontStyle=1;align=center;',
    170, 335, 270, 65, 'c_input');


  // =========================================================================
  // 2. CONTAINER: HIERARCHICAL POSITION ENCODING (c_hpe)
  // =========================================================================
  addNode('c_hpe', '2. Hierarchical Position Encoding (HPE)',
    'swimlane;startSize=35;rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFBEB;strokeColor=#B45309;strokeWidth=2;fontStyle=1;fontSize=13;fontColor=#78350F;',
    40, 490, 460, 460, '1');

  // Children of c_hpe
  addNode('hpe_banner', 'Spatial Layout Extraction &amp; Structure Grouping',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#D97706;strokeWidth=1.5;fontColor=#78350F;fontSize=11;fontStyle=1;align=center;',
    20, 50, 420, 40, 'c_hpe');

  addNode('hpe_line', 'Line Layout&#xa;&#xa;V-Overlap &#8805; 50%&#xa;Reading Order&#xa;E_line',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF3C7;strokeColor=#D97706;strokeWidth=1.5;fontColor=#78350F;fontSize=10;fontStyle=1;align=center;',
    20, 105, 125, 115, 'c_hpe');

  addNode('hpe_col', 'Column Layout&#xa;&#xa;H-Gap &#8805; 12% W&#xa;Column Slot&#xa;E_col',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#D1FAE5;strokeColor=#059669;strokeWidth=1.5;fontColor=#064E3B;fontSize=10;fontStyle=1;align=center;',
    165, 105, 130, 115, 'c_hpe');

  addNode('hpe_blk', 'Block Layout&#xa;&#xa;Line Gap &lt; 1.8x&#xa;Paragraph&#xa;E_block',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#DBEAFE;strokeColor=#2563EB;strokeWidth=1.5;fontColor=#1E3A8A;fontSize=10;fontStyle=1;align=center;',
    315, 105, 125, 115, 'c_hpe');

  addNode('hpe_proj', 'Hierarchical Projection (W_hier)&#xa;Concat [ E_line ; E_col ; E_block ] &#8594; Hidden Space',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#B45309;strokeWidth=1.8;fontColor=#78350F;fontSize=11;fontStyle=1;align=center;',
    20, 235, 420, 55, 'c_hpe');

  addNode('hpe_scale', 'Residual Hierarchical Bias (E_hier &#215; &#946;)&#xa;Injected directly into token representation stream',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF3C7;strokeColor=#B45309;strokeWidth=1.8;fontColor=#78350F;fontSize=11;fontStyle=1;align=center;',
    20, 310, 420, 55, 'c_hpe');

  addNode('hpe_desc', 'Disentangles reading lines, columns &amp; paragraphs without manual coordinate heuristics',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF8E7;strokeColor=#D97706;strokeWidth=1;fontColor=#92400E;fontSize=10;align=center;',
    20, 385, 420, 50, 'c_hpe');


  // =========================================================================
  // 3. CENTER: SUMMATION ADDER & MULTIMODAL BACKBONE PILLAR
  // =========================================================================
  addNode('adder', '+',
    'ellipse;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1E293B;strokeWidth=2;fontSize=22;fontStyle=1;fontColor=#1E293B;align=center;',
    535, 465, 50, 50, '1');

  addNode('backbone', 'LayoutLMv3 Multimodal Backbone&#xa;&#xa;&bull; 12 Transformer Encoder Layers&#xa;&bull; Joint Text-Image 2D Relative Attention&#xa;&bull; Multimodal Hidden Dim: d = 768',
    'rounded=1;whiteSpace=wrap;html=1;verticalAlign=middle;align=center;fillColor=#EFF6FF;strokeColor=#1D4ED8;strokeWidth=2.5;fontColor=#1E3A8A;fontSize=12;fontStyle=1;',
    620, 40, 240, 910, '1');

  addNode('h_tok', 'Text Tokens (h_i)&#xa;Contextualized Word Vectors',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#DBEAFE;strokeColor=#2563EB;strokeWidth=1.8;fontColor=#1E3A8A;fontSize=11;fontStyle=1;align=center;',
    895, 175, 130, 60, '1');

  addNode('v_patch', 'Visual Patches (v_p)&#xa;Image Region Vectors',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#D1FAE5;strokeColor=#059669;strokeWidth=1.8;fontColor=#064E3B;fontSize=11;fontStyle=1;align=center;',
    895, 775, 130, 60, '1');


  // =========================================================================
  // 4. CONTAINER: SEGMENT CONTEXT MODULE (c_scm)
  // =========================================================================
  addNode('c_scm', '3. Segment Context Module (SCM)',
    'swimlane;startSize=35;rounded=1;whiteSpace=wrap;html=1;fillColor=#ECFDF5;strokeColor=#047857;strokeWidth=2;fontStyle=1;fontSize=13;fontColor=#064E3B;',
    1060, 40, 750, 230, '1');

  addNode('scm_pool', 'Segment Mean Pool&#xa;Averages tokens in line k &#8594; s_k',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#059669;strokeWidth=1.5;fontColor=#064E3B;fontSize=11;fontStyle=1;align=center;',
    20, 50, 210, 65, 'c_scm');

  addNode('scm_trans', 'Segment Transformer&#xa;1-Layer, 4-Head Line Attention',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#059669;strokeWidth=1.5;fontColor=#064E3B;fontSize=11;fontStyle=1;align=center;',
    260, 50, 220, 65, 'c_scm');

  addNode('scm_rezero', 'ReZero Residual Gate (+g)&#xa;s_k + g &#215; (c_k - s_k) &#8594; s&apos;_k',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#D1FAE5;strokeColor=#059669;strokeWidth=1.5;fontColor=#064E3B;fontSize=11;fontStyle=1;align=center;',
    510, 50, 220, 65, 'c_scm');

  addNode('scm_broad', 'Broadcast Context + Segment-Start Onset Embedding:  h_i^final = h_i + s&apos;_{s(i)} + e^onset',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#047857;strokeWidth=1.8;fontColor=#064E3B;fontSize=11;fontStyle=1;align=center;',
    20, 145, 710, 60, 'c_scm');


  // =========================================================================
  // 5. CONTAINER: DIRECT TOKEN CLASSIFIER HEAD (c_cls)
  // =========================================================================
  addNode('c_cls', '4. Direct Token Classifier Head',
    'swimlane;startSize=35;rounded=1;whiteSpace=wrap;html=1;fillColor=#F8FAFC;strokeColor=#334155;strokeWidth=2;fontStyle=1;fontSize=13;fontColor=#0F172A;',
    1060, 295, 750, 135, '1');

  addNode('cls_linear', 'Linear Classification Layer&#xa;Projects h_i^final directly to class logits z_i',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#334155;strokeWidth=1.8;fontColor=#1E293B;fontSize=11;fontStyle=1;align=center;',
    20, 50, 320, 60, 'c_cls');

  addNode('cls_loss', 'Entity Cross-Entropy Loss (L_CE)&#xa;Softmax probabilities vs ground-truth IOB2 tags',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#DC2626;strokeWidth=1.8;fontColor=#991B1B;fontSize=11;fontStyle=1;align=center;',
    380, 50, 350, 60, 'c_cls');


  // =========================================================================
  // 6. CONTAINER: INTRA-LINE BOUNDARY LOSS MODULE (c_bnd)
  // =========================================================================
  addNode('c_bnd', '5. Intra-Line Boundary Loss Classifier (Detailed Supervision)',
    'swimlane;startSize=35;rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFBEB;strokeColor=#D97706;strokeWidth=2;fontStyle=1;fontSize=13;fontColor=#78350F;',
    1060, 455, 750, 230, '1');

  addNode('bnd_pair', 'Adjacent Word Pair&#xa;Same text line: [ h_i ; h_{i+1} ]',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF3C7;strokeColor=#D97706;strokeWidth=1.5;fontColor=#78350F;fontSize=11;fontStyle=1;align=center;',
    20, 50, 180, 65, 'c_bnd');

  addNode('bnd_mlp', 'Boundary MLP&#xa;Linear &#8594; ReLU &#8594; Linear &#8594; &#963;',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#D97706;strokeWidth=1.5;fontColor=#78350F;fontSize=11;fontStyle=1;align=center;',
    230, 50, 160, 65, 'c_bnd');

  // Ground Truth Transition Visual Card
  addNode('bnd_vis', 'Transition Ground Truth:&#xa;&#xa;&bull; Within Entity: [Word A] &mdash; [Word B] &#8594; Target = 0&#xa;&bull; Entity Boundary: [Field Name] | [Field Value] &#8594; Target = 1',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#94A3B8;strokeWidth=1.5;fontColor=#1E293B;fontSize=10;fontStyle=1;align=left;spacingLeft=10;',
    420, 45, 310, 75, 'c_bnd');

  addNode('bnd_loss', 'Intra-Line Boundary BCE Loss (L_bound)&#xa;Directly penalizes false entity merges along the reading line',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF3C7;strokeColor=#B45309;strokeWidth=1.8;fontColor=#78350F;fontSize=11;fontStyle=1;align=center;',
    20, 145, 710, 55, 'c_bnd');


  // =========================================================================
  // 7. CONTAINER: CROSS-MODAL CONTRASTIVE LOSS MODULE (c_cont)
  // =========================================================================
  addNode('c_cont', '6. Cross-Modal Contrastive Loss (Text-Image Alignment)',
    'swimlane;startSize=35;rounded=1;whiteSpace=wrap;html=1;fillColor=#ECFDF5;strokeColor=#059669;strokeWidth=2;fontStyle=1;fontSize=13;fontColor=#064E3B;',
    1060, 710, 750, 250, '1');

  addNode('cont_txt', 'Text Token Vector&#xa;Proj: z_i^text = g_text(h_i^final)',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#DBEAFE;strokeColor=#2563EB;strokeWidth=1.5;fontColor=#1E3A8A;fontSize=11;fontStyle=1;align=center;',
    20, 50, 190, 65, 'c_cont');

  addNode('cont_img', 'Visual Patch Vector&#xa;Proj: z_{p(i)}^img = g_img(v_p)',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#D1FAE5;strokeColor=#059669;strokeWidth=1.5;fontColor=#064E3B;fontSize=11;fontStyle=1;align=center;',
    20, 145, 190, 65, 'c_cont');

  addNode('cont_vis', 'InfoNCE Alignment (&#964; = 0.07):&#xa;&#xa;&harr; PULL: Matched Text-Image Pair&#xa;&harr; PUSH: Distractor Non-matching Patches',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#059669;strokeWidth=1.8;fontColor=#064E3B;fontSize=11;fontStyle=1;align=center;',
    240, 50, 280, 160, 'c_cont');

  addNode('cont_loss', 'Contrastive Loss&#xa;(L_cont)&#xa;Prevents visual representation drift',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#D1FAE5;strokeColor=#047857;strokeWidth=1.8;fontColor=#064E3B;fontSize=11;fontStyle=1;align=center;',
    550, 90, 180, 80, 'c_cont');


  // =========================================================================
  // 8. BANNER: JOINT MULTI-TASK TRAINING OBJECTIVE (banner)
  // =========================================================================
  addNode('banner', 'Joint Multi-Task Training Objective:  L_total = L_CE + &lambda;_bound &times; L_bound + &lambda;_cont &times; L_cont  (&lambda;_bound = 0.2, &lambda;_cont = 0.1)',
    'rounded=1;whiteSpace=wrap;html=1;fillColor=#0F172A;strokeColor=#020617;strokeWidth=2;fontColor=#F8FAFC;fontStyle=1;fontSize=13;align=center;',
    620, 985, 1190, 55, '1');


  // =========================================================================
  // CONNECTORS (ORTHOGONAL, SMART PINS, NO OVERLAPS)
  // =========================================================================
  const edgeBlue = 'edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;strokeColor=#2563EB;strokeWidth=2;html=1;';
  const edgeAmber = 'edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;strokeColor=#D97706;strokeWidth=2;html=1;';
  const edgeGreen = 'edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;strokeColor=#059669;strokeWidth=2;html=1;';
  const edgeRed = 'edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;strokeColor=#DC2626;strokeWidth=2;html=1;';
  const edgeDark = 'edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;strokeColor=#334155;strokeWidth=2;html=1;';

  // Input -> Adder
  addEdge('e_in_add', 'emb_1d', 'adder', edgeBlue, '', [{ x: 560, y: 312 }]);

  // HPE -> Adder
  addEdge('e_hpe_add', 'hpe_scale', 'adder', edgeAmber, '', [{ x: 560, y: 832 }]);

  // Adder -> Backbone
  addEdge('e_add_bb', 'adder', 'backbone', edgeDark);

  // Backbone -> Modality States
  addEdge('e_bb_htok', 'backbone', 'h_tok', edgeBlue, '', [], ';exitX=1;exitY=0.17;entryX=0;entryY=0.5;');
  addEdge('e_bb_vpatch', 'backbone', 'v_patch', edgeGreen, '', [], ';exitX=1;exitY=0.85;entryX=0;entryY=0.5;');

  // Tokens -> SCM Pool
  addEdge('e_htok_scm', 'h_tok', 'scm_pool', edgeGreen, 'Pool', [{ x: 1040, y: 205 }, { x: 1040, y: 122 }]);

  // Inside SCM
  addEdge('e_pool_trans', 'scm_pool', 'scm_trans', edgeGreen);
  addEdge('e_trans_rezero', 'scm_trans', 'scm_rezero', edgeGreen, '+g');
  addEdge('e_rezero_broad', 'scm_rezero', 'scm_broad', edgeGreen, '', [{ x: 1680, y: 155 }, { x: 1680, y: 215 }]);

  // SCM Broadcast -> Linear Classifier Head
  addEdge('e_broad_cls', 'scm_broad', 'cls_linear', edgeDark, '', [{ x: 1240, y: 260 }, { x: 1240, y: 345 }]);
  addEdge('e_cls_loss', 'cls_linear', 'cls_loss', edgeRed);

  // SCM Broadcast -> Boundary Module
  addEdge('e_broad_bnd', 'scm_broad', 'bnd_pair', edgeAmber, '', [{ x: 1170, y: 260 }, { x: 1170, y: 537 }]);
  addEdge('e_pair_mlp', 'bnd_pair', 'bnd_mlp', edgeAmber);
  addEdge('e_mlp_vis', 'bnd_mlp', 'bnd_vis', edgeAmber);
  addEdge('e_vis_loss', 'bnd_vis', 'bnd_loss', edgeAmber, '', [{ x: 1635, y: 615 }]);

  // Contrastive Connections
  addEdge('e_broad_ctok', 'scm_broad', 'cont_txt', edgeBlue, '', [{ x: 1045, y: 260 }, { x: 1045, y: 792 }]);
  addEdge('e_vpatch_cimg', 'v_patch', 'cont_img', edgeGreen, '', [{ x: 1045, y: 805 }, { x: 1045, y: 887 }]);
  addEdge('e_ctxt_vis', 'cont_txt', 'cont_vis', edgeGreen);
  addEdge('e_cimg_vis', 'cont_img', 'cont_vis', edgeGreen);
  addEdge('e_vis_closs', 'cont_vis', 'cont_loss', edgeGreen);

  // Losses -> Joint Objective Banner
  addEdge('e_lce_banner', 'cls_loss', 'banner', edgeRed, '', [{ x: 1795, y: 375 }, { x: 1795, y: 985 }]);
  addEdge('e_lbnd_banner', 'bnd_loss', 'banner', edgeAmber, '', [{ x: 1785, y: 627 }, { x: 1785, y: 985 }]);
  addEdge('e_lcont_banner', 'cont_loss', 'banner', edgeGreen, '', [{ x: 1775, y: 840 }, { x: 1775, y: 985 }]);

  return `<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="drawio" version="26.0.0">
  <diagram id="model_arch_skill_compliant" name="Structure-Aware LayoutLMv3 Architecture">
    <mxGraphModel dx="1850" dy="1100" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1850" pageHeight="1100" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />${cells.join('')}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>`;
}

const finalXml = createSkillCompliantDrawio();
const drawioPath = path.resolve(__dirname, '../thesis/figures/model_architecture.drawio');
const brainDrawioPath = 'C:/Users/nhatm/.gemini/antigravity/brain/602639c6-1a2d-485a-9823-c5f9bb4ea4cb/model_architecture.drawio';

fs.writeFileSync(drawioPath, finalXml, 'utf8');
fs.writeFileSync(brainDrawioPath, finalXml, 'utf8');
console.log(`Saved skill-compliant Draw.io file: ${drawioPath}`);
console.log(`Saved skill-compliant Draw.io file: ${brainDrawioPath}`);

// Generate high-resolution JPEG via @resvg/resvg-js and System.Drawing
const svgXml = `
<svg width="1850" height="1060" viewBox="0 0 1850 1060" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9 z" fill="#334155" />
    </marker>
    <marker id="arr-g" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9 z" fill="#059669" />
    </marker>
    <marker id="arr-a" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9 z" fill="#D97706" />
    </marker>
    <marker id="arr-b" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9 z" fill="#2563EB" />
    </marker>
    <marker id="arr-r" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 8 5 L 0 9 z" fill="#DC2626" />
    </marker>
  </defs>

  <!-- 1. Document Input Container -->
  <rect x="40" y="40" width="460" height="420" rx="10" fill="#F8FAFC" stroke="#475569" stroke-width="2"/>
  <rect x="40" y="40" width="460" height="35" rx="10" fill="#E2E8F0" stroke="#475569" stroke-width="2"/>
  <text x="55" y="63" font-size="13" font-weight="bold" fill="#1E293B">1. Multimodal Document Input</text>

  <rect x="60" y="90" width="130" height="350" rx="6" fill="#FFFFFF" stroke="#94A3B8" stroke-width="1.5"/>
  <text x="125" y="140" font-size="12" font-weight="bold" fill="#334155" text-anchor="middle">Scanned Document</text>
  <text x="125" y="165" font-size="10" fill="#64748B" text-anchor="middle">Receipt / Form Image</text>
  <line x1="80" y1="190" x2="170" y2="190" stroke="#CBD5E1" stroke-width="2"/>
  <line x1="80" y1="215" x2="170" y2="215" stroke="#CBD5E1" stroke-width="2"/>
  <line x1="80" y1="240" x2="170" y2="240" stroke="#CBD5E1" stroke-width="2"/>
  <line x1="80" y1="265" x2="170" y2="265" stroke="#CBD5E1" stroke-width="2"/>
  <rect x="80" y="290" width="60" height="18" fill="#FEF3C7" stroke="#D97706"/>
  <rect x="80" y="320" width="75" height="18" fill="#D1FAE5" stroke="#059669"/>
  <text x="125" y="375" font-size="10" fill="#64748B" text-anchor="middle">[Word Bounding Boxes]</text>

  <rect x="210" y="90" width="270" height="65" rx="6" fill="#FEF3C7" stroke="#D97706" stroke-width="1.8"/>
  <text x="345" y="120" font-size="11" font-weight="bold" fill="#78350F" text-anchor="middle">Word Tokens</text>
  <text x="345" y="138" font-size="10" fill="#92400E" text-anchor="middle">RoBERTa Text Embeddings</text>

  <rect x="210" y="185" width="270" height="65" rx="6" fill="#D1FAE5" stroke="#059669" stroke-width="1.8"/>
  <text x="345" y="215" font-size="11" font-weight="bold" fill="#064E3B" text-anchor="middle">Visual Image Patches</text>
  <text x="345" y="233" font-size="10" fill="#065F46" text-anchor="middle">16&#215;16 Linear Visual Proj.</text>

  <rect x="210" y="280" width="270" height="65" rx="6" fill="#DBEAFE" stroke="#2563EB" stroke-width="1.8"/>
  <text x="345" y="310" font-size="11" font-weight="bold" fill="#1E3A8A" text-anchor="middle">1D Reading Sequence Position</text>
  <text x="345" y="328" font-size="10" fill="#1E40AF" text-anchor="middle">Sequential Word Indices (0..N)</text>

  <rect x="210" y="375" width="270" height="65" rx="6" fill="#F3F4F6" stroke="#4B5563" stroke-width="1.8"/>
  <text x="345" y="405" font-size="11" font-weight="bold" fill="#1F2937" text-anchor="middle">2D Spatial Coordinates</text>
  <text x="345" y="423" font-size="10" fill="#374151" text-anchor="middle">Bounding Box [x0, y0, x1, y1]</text>

  <!-- 2. HPE Container -->
  <rect x="40" y="490" width="460" height="460" rx="10" fill="#FFFBEB" stroke="#B45309" stroke-width="2"/>
  <rect x="40" y="490" width="460" height="35" rx="10" fill="#FEF3C7" stroke="#B45309" stroke-width="2"/>
  <text x="55" y="513" font-size="13" font-weight="bold" fill="#78350F">2. Hierarchical Position Encoding (HPE)</text>

  <rect x="60" y="540" width="420" height="40" rx="6" fill="#FFFFFF" stroke="#D97706" stroke-width="1.5"/>
  <text x="270" y="565" font-size="11" font-weight="bold" fill="#78350F" text-anchor="middle">Spatial Layout Extraction &amp; Structure Grouping</text>

  <rect x="60" y="595" width="125" height="115" rx="6" fill="#FEF3C7" stroke="#D97706" stroke-width="1.5"/>
  <text x="122" y="625" font-size="11" font-weight="bold" fill="#78350F" text-anchor="middle">Line Layout</text>
  <text x="122" y="650" font-size="9.5" fill="#78350F" text-anchor="middle">V-Overlap &#8805; 50%</text>
  <text x="122" y="670" font-size="9.5" fill="#78350F" text-anchor="middle">Reading Order</text>
  <text x="122" y="695" font-size="11" font-weight="bold" fill="#B45309" text-anchor="middle">E_line</text>

  <rect x="205" y="595" width="130" height="115" rx="6" fill="#D1FAE5" stroke="#059669" stroke-width="1.5"/>
  <text x="270" y="625" font-size="11" font-weight="bold" fill="#064E3B" text-anchor="middle">Column Layout</text>
  <text x="270" y="650" font-size="9.5" fill="#064E3B" text-anchor="middle">H-Gap &#8805; 12% W</text>
  <text x="270" y="670" font-size="9.5" fill="#064E3B" text-anchor="middle">Column Slot ID</text>
  <text x="270" y="695" font-size="11" font-weight="bold" fill="#047857" text-anchor="middle">E_col</text>

  <rect x="355" y="595" width="125" height="115" rx="6" fill="#DBEAFE" stroke="#2563EB" stroke-width="1.5"/>
  <text x="417" y="625" font-size="11" font-weight="bold" fill="#1E3A8A" text-anchor="middle">Block Layout</text>
  <text x="417" y="650" font-size="9.5" fill="#1E3A8A" text-anchor="middle">Line Gap &lt; 1.8x</text>
  <text x="417" y="670" font-size="9.5" fill="#1E3A8A" text-anchor="middle">Paragraph</text>
  <text x="417" y="695" font-size="11" font-weight="bold" fill="#1D4ED8" text-anchor="middle">E_block</text>

  <rect x="60" y="725" width="420" height="55" rx="6" fill="#FFFFFF" stroke="#B45309" stroke-width="1.8"/>
  <text x="270" y="757" font-size="11" font-weight="bold" fill="#78350F" text-anchor="middle">Hierarchical Projection (W_hier): Concat [ E_line ; E_col ; E_block ] &#8594; Hidden Space</text>

  <rect x="60" y="800" width="420" height="55" rx="6" fill="#FEF3C7" stroke="#B45309" stroke-width="1.8"/>
  <text x="270" y="832" font-size="11" font-weight="bold" fill="#78350F" text-anchor="middle">Residual Hierarchical Bias (E_hier &#215; &#946;) injected into representation stream</text>

  <rect x="60" y="875" width="420" height="50" rx="6" fill="#FFF8E7" stroke="#D97706" stroke-width="1"/>
  <text x="270" y="905" font-size="10" fill="#92400E" text-anchor="middle">Disentangles multi-scale reading structure without manual coordinate heuristics</text>

  <!-- Central Summation Adder & Backbone -->
  <circle cx="560" cy="490" r="24" fill="#FFFFFF" stroke="#1E293B" stroke-width="2"/>
  <text x="560" y="498" font-size="22" font-weight="bold" fill="#1E293B" text-anchor="middle">+</text>

  <rect x="620" y="40" width="240" height="910" rx="10" fill="#EFF6FF" stroke="#1D4ED8" stroke-width="2.5"/>
  <text x="740" y="300" font-size="16" font-weight="bold" fill="#1E3A8A" text-anchor="middle">LayoutLMv3 Backbone</text>
  <text x="740" y="370" font-size="12" fill="#1E3A8A" text-anchor="middle">&#8226; 12 Transformer Layers</text>
  <text x="740" y="410" font-size="12" fill="#1E3A8A" text-anchor="middle">&#8226; Joint Text-Image 2D Relative Bias</text>
  <text x="740" y="450" font-size="12" fill="#1E3A8A" text-anchor="middle">&#8226; Multimodal Hidden Dim: d = 768</text>

  <rect x="895" y="175" width="130" height="60" rx="6" fill="#DBEAFE" stroke="#2563EB" stroke-width="1.8"/>
  <text x="960" y="202" font-size="11" font-weight="bold" fill="#1E3A8A" text-anchor="middle">Text Tokens (h_i)</text>
  <text x="960" y="220" font-size="9.5" fill="#1E40AF" text-anchor="middle">Contextualized Vectors</text>

  <rect x="895" y="775" width="130" height="60" rx="6" fill="#D1FAE5" stroke="#059669" stroke-width="1.8"/>
  <text x="960" y="802" font-size="11" font-weight="bold" fill="#064E3B" text-anchor="middle">Visual Patches (v_p)</text>
  <text x="960" y="820" font-size="9.5" fill="#065F46" text-anchor="middle">Image Region Features</text>

  <!-- 3. Segment Context Module -->
  <rect x="1060" y="40" width="750" height="230" rx="10" fill="#ECFDF5" stroke="#047857" stroke-width="2"/>
  <rect x="1060" y="40" width="750" height="35" rx="10" fill="#D1FAE5" stroke="#047857" stroke-width="2"/>
  <text x="1075" y="63" font-size="13" font-weight="bold" fill="#064E3B">3. Segment Context Module (SCM)</text>

  <rect x="1080" y="90" width="210" height="65" rx="6" fill="#FFFFFF" stroke="#059669" stroke-width="1.5"/>
  <text x="1185" y="118" font-size="11" font-weight="bold" fill="#064E3B" text-anchor="middle">Segment Mean Pool</text>
  <text x="1185" y="138" font-size="10" fill="#065F46" text-anchor="middle">Tokens in line k &#8594; s_k</text>

  <rect x="1320" y="90" width="220" height="65" rx="6" fill="#FFFFFF" stroke="#059669" stroke-width="1.5"/>
  <text x="1430" y="118" font-size="11" font-weight="bold" fill="#064E3B" text-anchor="middle">Segment Transformer</text>
  <text x="1430" y="138" font-size="10" fill="#065F46" text-anchor="middle">1-Layer, 4-Head Attention</text>

  <rect x="1570" y="90" width="220" height="65" rx="6" fill="#D1FAE5" stroke="#059669" stroke-width="1.5"/>
  <text x="1680" y="118" font-size="11" font-weight="bold" fill="#064E3B" text-anchor="middle">ReZero Residual Gate (+g)</text>
  <text x="1680" y="138" font-size="10" fill="#065F46" text-anchor="middle">s_k + g &#215; (c_k - s_k) &#8594; s&apos;_k</text>

  <rect x="1080" y="185" width="710" height="60" rx="6" fill="#FFFFFF" stroke="#047857" stroke-width="1.8"/>
  <text x="1435" y="220" font-size="11" font-weight="bold" fill="#064E3B" text-anchor="middle">Broadcast Context + Onset Embedding:  h_i^final = h_i + s&apos;_{s(i)} + e^onset</text>

  <!-- 4. Direct Token Classifier -->
  <rect x="1060" y="295" width="750" height="135" rx="10" fill="#F8FAFC" stroke="#334155" stroke-width="2"/>
  <rect x="1060" y="295" width="750" height="35" rx="10" fill="#E2E8F0" stroke="#334155" stroke-width="2"/>
  <text x="1075" y="318" font-size="13" font-weight="bold" fill="#0F172A">4. Direct Token Classifier Head</text>

  <rect x="1080" y="345" width="320" height="60" rx="6" fill="#FFFFFF" stroke="#334155" stroke-width="1.8"/>
  <text x="1240" y="372" font-size="11" font-weight="bold" fill="#1E293B" text-anchor="middle">Linear Classification Layer</text>
  <text x="1240" y="392" font-size="9.5" fill="#475569" text-anchor="middle">Projects h_i^final directly to class logits z_i</text>

  <rect x="1440" y="345" width="350" height="60" rx="6" fill="#FEF2F2" stroke="#DC2626" stroke-width="1.8"/>
  <text x="1615" y="372" font-size="11" font-weight="bold" fill="#991B1B" text-anchor="middle">Entity Cross-Entropy Loss (L_CE)</text>
  <text x="1615" y="392" font-size="9.5" fill="#DC2626" text-anchor="middle">Softmax probabilities vs ground-truth IOB2 tags</text>

  <!-- 5. Boundary Loss Module -->
  <rect x="1060" y="455" width="750" height="230" rx="10" fill="#FFFBEB" stroke="#D97706" stroke-width="2"/>
  <rect x="1060" y="455" width="750" height="35" rx="10" fill="#FEF3C7" stroke="#D97706" stroke-width="2"/>
  <text x="1075" y="478" font-size="13" font-weight="bold" fill="#78350F">5. Intra-Line Boundary Loss Classifier (Detailed Supervision)</text>

  <rect x="1080" y="505" width="180" height="65" rx="6" fill="#FEF3C7" stroke="#D97706" stroke-width="1.5"/>
  <text x="1170" y="533" font-size="11" font-weight="bold" fill="#78350F" text-anchor="middle">Adjacent Word Pair</text>
  <text x="1170" y="553" font-size="9.5" fill="#78350F" text-anchor="middle">[ h_i ; h_{i+1} ] &#8712; R^{2d}</text>

  <rect x="1290" y="505" width="160" height="65" rx="6" fill="#FFFFFF" stroke="#D97706" stroke-width="1.5"/>
  <text x="1370" y="533" font-size="11" font-weight="bold" fill="#78350F" text-anchor="middle">Boundary MLP</text>
  <text x="1370" y="553" font-size="9.5" fill="#78350F" text-anchor="middle">Linear &#8594; ReLU &#8594; Linear &#8594; &#963;</text>

  <rect x="1480" y="500" width="310" height="75" rx="6" fill="#FFFFFF" stroke="#94A3B8" stroke-width="1.5"/>
  <text x="1495" y="520" font-size="10" font-weight="bold" fill="#1E293B">Transition Ground Truth:</text>
  <circle cx="1510" cy="537" r="4" fill="#2563EB"/>
  <line x1="1514" y1="537" x2="1550" y2="537" stroke="#2563EB" stroke-width="2"/>
  <circle cx="1554" cy="537" r="4" fill="#2563EB"/>
  <text x="1568" y="541" font-size="9.5" fill="#1E40AF">Within Entity &#8594; <tspan font-weight="bold">Target = 0</tspan></text>
  <circle cx="1510" cy="560" r="4" fill="#DC2626"/>
  <line x1="1527" y1="552" x2="1527" y2="568" stroke="#DC2626" stroke-width="2" stroke-dasharray="2,2"/>
  <circle cx="1544" cy="560" r="4" fill="#DC2626"/>
  <text x="1568" y="564" font-size="9.5" fill="#991B1B">Entity Boundary &#8594; <tspan font-weight="bold">Target = 1</tspan></text>

  <rect x="1080" y="600" width="710" height="55" rx="6" fill="#FEF3C7" stroke="#B45309" stroke-width="1.8"/>
  <text x="1435" y="632" font-size="11" font-weight="bold" fill="#78350F" text-anchor="middle">Intra-Line Boundary BCE Loss (L_bound) &#8212; Directly penalizes false entity merges along the reading line</text>

  <!-- 6. Contrastive Loss Module -->
  <rect x="1060" y="710" width="750" height="250" rx="10" fill="#ECFDF5" stroke="#059669" stroke-width="2"/>
  <rect x="1060" y="710" width="750" height="35" rx="10" fill="#D1FAE5" stroke="#059669" stroke-width="2"/>
  <text x="1075" y="733" font-size="13" font-weight="bold" fill="#064E3B">6. Cross-Modal Contrastive Loss (Text-Image Alignment)</text>

  <rect x="1080" y="760" width="190" height="65" rx="6" fill="#DBEAFE" stroke="#2563EB" stroke-width="1.5"/>
  <text x="1175" y="788" font-size="11" font-weight="bold" fill="#1E3A8A" text-anchor="middle">Text Token Vector</text>
  <text x="1175" y="808" font-size="9.5" fill="#1E40AF" text-anchor="middle">z_i^text = g_text(h_i^final)</text>

  <rect x="1080" y="855" width="190" height="65" rx="6" fill="#D1FAE5" stroke="#059669" stroke-width="1.5"/>
  <text x="1175" y="883" font-size="11" font-weight="bold" fill="#064E3B" text-anchor="middle">Visual Patch Vector</text>
  <text x="1175" y="903" font-size="9.5" fill="#065F46" text-anchor="middle">z_{p(i)}^img = g_img(v_p)</text>

  <rect x="1300" y="760" width="280" height="160" rx="6" fill="#FFFFFF" stroke="#059669" stroke-width="1.8"/>
  <text x="1440" y="790" font-size="11" font-weight="bold" fill="#064E3B" text-anchor="middle">InfoNCE Alignment (&#964; = 0.07):</text>
  <line x1="1330" y1="830" x2="1550" y2="830" stroke="#059669" stroke-width="2.5" marker-end="url(#arr-g)" marker-start="url(#arr-g)"/>
  <text x="1440" y="822" font-size="10" font-weight="bold" fill="#059669" text-anchor="middle">PULL: Matched Text-Image Pair</text>
  <line x1="1330" y1="880" x2="1550" y2="880" stroke="#DC2626" stroke-width="2" stroke-dasharray="4,3" marker-end="url(#arr-r)" marker-start="url(#arr-r)"/>
  <text x="1440" y="872" font-size="10" font-weight="bold" fill="#DC2626" text-anchor="middle">PUSH: Non-matching Patches</text>

  <rect x="1610" y="800" width="180" height="80" rx="6" fill="#D1FAE5" stroke="#047857" stroke-width="1.8"/>
  <text x="1700" y="832" font-size="12" font-weight="bold" fill="#064E3B" text-anchor="middle">Contrastive Loss</text>
  <text x="1700" y="852" font-size="12" font-weight="bold" fill="#DC2626" text-anchor="middle">(L_cont)</text>

  <!-- Joint Objective Banner -->
  <rect x="620" y="985" width="1190" height="55" rx="8" fill="#0F172A" stroke="#020617" stroke-width="2"/>
  <text x="1215" y="1018" font-size="13" font-weight="bold" fill="#F8FAFC" text-anchor="middle">Joint Multi-Task Objective:  L_total = L_CE + &#955;_bound &#215; L_bound + &#955;_cont &#215; L_cont  (&#955;_bound = 0.2, &#955;_cont = 0.1)</text>

  <!-- Connector Flow Lines -->
  <path d="M 480 312 L 560 312 L 560 466" fill="none" stroke="#2563EB" stroke-width="2" marker-end="url(#arr-b)"/>
  <path d="M 480 832 L 560 832 L 560 514" fill="none" stroke="#D97706" stroke-width="2" marker-end="url(#arr-a)"/>
  <line x1="560" y1="466" x2="620" y2="466" stroke="#334155" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="860" y1="205" x2="895" y2="205" stroke="#2563EB" stroke-width="2" marker-end="url(#arr-b)"/>
  <line x1="860" y1="805" x2="895" y2="805" stroke="#059669" stroke-width="2" marker-end="url(#arr-g)"/>
  <path d="M 1025 205 L 1050 205 L 1050 122 L 1080 122" fill="none" stroke="#059669" stroke-width="2" marker-end="url(#arr-g)"/>
  <line x1="1290" y1="122" x2="1320" y2="122" stroke="#059669" stroke-width="2" marker-end="url(#arr-g)"/>
  <line x1="1540" y1="122" x2="1570" y2="122" stroke="#059669" stroke-width="2" marker-end="url(#arr-g)"/>
  <line x1="1400" y1="375" x2="1440" y2="375" stroke="#DC2626" stroke-width="2" marker-end="url(#arr-r)"/>
  <line x1="1260" y1="537" x2="1290" y2="537" stroke="#D97706" stroke-width="2" marker-end="url(#arr-a)"/>
  <line x1="1450" y1="537" x2="1480" y2="537" stroke="#D97706" stroke-width="2" marker-end="url(#arr-a)"/>
  <line x1="1270" y1="792" x2="1300" y2="792" stroke="#059669" stroke-width="2" marker-end="url(#arr-g)"/>
  <line x1="1270" y1="887" x2="1300" y2="887" stroke="#059669" stroke-width="2" marker-end="url(#arr-g)"/>
  <line x1="1580" y1="840" x2="1610" y2="840" stroke="#059669" stroke-width="2" marker-end="url(#arr-g)"/>
</svg>`;

const resvg = new Resvg(svgXml, {
  fitTo: { mode: 'zoom', value: 2.0 },
  font: { loadSystemFonts: true, defaultFontFamily: 'Arial' }
});

const pngBuffer = resvg.render().asPng();
const pngPath = path.resolve(__dirname, '../thesis/figures/model_architecture.png');
fs.writeFileSync(pngPath, pngBuffer);
console.log(`Saved high-res PNG: ${pngPath}`);
