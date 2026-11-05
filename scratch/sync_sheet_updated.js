const fs = require('fs');
const path = require('path');

const WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyTnMY4wH9BwXUeNKKWqUdL_BClo-8ai76o70kQM0sT-nh7wv9oN64BpumGGAoalhSM1w/exec";

function loadJson(filename) {
  const dirs = [
    path.resolve('layoutlmv3/logs'),
    path.resolve('scratch/colab_summaries')
  ];
  for (const d of dirs) {
    const p = path.join(d, filename);
    if (fs.existsSync(p)) {
      try {
        return JSON.parse(fs.readFileSync(p, 'utf8'));
      } catch (e) {
        console.warn(`[WARN] Failed to parse ${p}: ${e.message}`);
      }
    }
  }
  return null;
}

function fmtN(val) {
  if (val === null || val === undefined) return '--';
  const num = parseFloat(val);
  return isNaN(num) ? '--' : num.toFixed(4);
}

function fmtMS(m, s) {
  if (m === null || m === undefined) return '--';
  const numM = parseFloat(m);
  const numS = parseFloat(s);
  if (isNaN(numM)) return '--';
  return isNaN(numS) ? numM.toFixed(4) : `${numM.toFixed(4)} ± ${numS.toFixed(4)}`;
}

function extractSeedAndMS(obj, metric) {
  if (!obj) return ['--', '--', '--', '--'];
  if (obj.per_seed && obj.mean_std) {
    const ps = obj.per_seed;
    const ms = obj.mean_std[metric] || {};
    return [
      fmtN(ps['42'] ? ps['42'][metric] : null),
      fmtN(ps['123'] ? ps['123'][metric] : null),
      fmtN(ps['1993'] ? ps['1993'][metric] : null),
      fmtMS(ms.mean, ms.std)
    ];
  }
  if (obj.metrics && obj.metrics[metric]) {
    const md = obj.metrics[metric];
    const vals = md.values || [];
    return [
      fmtN(vals[0]),
      fmtN(vals[1]),
      fmtN(vals[2]),
      fmtMS(md.mean, md.std)
    ];
  }
  return ['--', '--', '--', '--'];
}

function getDisplayedMean(obj, metric) {
  if (!obj) return null;
  let raw = null;
  if (obj.mean_std && obj.mean_std[metric] && obj.mean_std[metric].mean !== undefined) {
    raw = parseFloat(obj.mean_std[metric].mean);
  } else if (obj.metrics && obj.metrics[metric] && obj.metrics[metric].mean !== undefined) {
    raw = parseFloat(obj.metrics[metric].mean);
  }
  if (raw === null || isNaN(raw)) return null;
  return parseFloat(raw.toFixed(4));
}

function calcMetricDelta(targetObj, refObj, metric) {
  const t = getDisplayedMean(targetObj, metric);
  const r = getDisplayedMean(refObj, metric);
  if (t === null || r === null) return '--';
  const diff = t - r;
  if (metric === 'eval_loss') {
    const sign = diff >= -1e-9 ? '+' : '';
    const cleanDiff = Math.abs(diff) < 1e-9 ? 0 : diff;
    return `${sign}${cleanDiff.toFixed(4)}`;
  } else {
    const pct = diff * 100.0;
    const sign = pct >= -1e-9 ? '+' : '';
    const cleanPct = Math.abs(pct) < 1e-9 ? 0 : pct;
    return `${sign}${cleanPct.toFixed(2)}%`;
  }
}

/**
 * Builds a 6-Table Horizontal Section (7 rows x 49 columns):
 * - Table 1: Baseline (5 cols: 0..4)
 * - Spacer 1: 2 blank cols (5..6)
 * - Table 2: Full 4-Module Model (6 cols: 7..12) -> Δ vs. baseline
 * - Spacer 2: 2 blank cols (13..14)
 * - Table 3: w/o HPE (7 cols: 15..21) -> Δ vs. full model, Δ vs. baseline
 * - Spacer 3: 2 blank cols (22..23)
 * - Table 4: w/o Token-Segment SCM (7 cols: 24..30) -> Δ vs. full model, Δ vs. baseline
 * - Spacer 4: 2 blank cols (31..32)
 * - Table 5: w/o Boundary Loss (7 cols: 33..39) -> Δ vs. full model, Δ vs. baseline
 * - Spacer 5: 2 blank cols (40..41)
 * - Table 6: w/o Contrastive Loss (7 cols: 42..48) -> Δ vs. full model, Δ vs. baseline
 */
function makeSixTableSection(suffix, baseObj, fullObj, noHpeObj, noSegObj, noBdrObj, noContObj) {
  const rows = [];

  // Row 0: Configuration Titles (49 columns)
  const r0 = new Array(49).fill('');
  r0[0]  = `Baseline LayoutLMv3 (${suffix})`;
  r0[7]  = `HPE + SCM + Contrastive Loss + Boundary Loss (${suffix})`;
  r0[15] = `w/o HPE (${suffix})`;
  r0[24] = `w/o Token-Segment SCM (${suffix})`;
  r0[33] = `w/o Boundary Loss (${suffix})`;
  r0[42] = `w/o Contrastive Loss (${suffix})`;
  rows.push(r0);

  // Row 1: Column Headers (2-line Delta headers with newline)
  const r1 = new Array(49).fill('');
  // Table 1: Baseline (cols 0..4)
  r1[0] = 'Metric'; r1[1] = 'Seed 42'; r1[2] = 'Seed 123'; r1[3] = 'Seed 1993'; r1[4] = 'Mean ± STD';
  
  // Table 2: Full Model (cols 7..12) -> 1 delta col: Δ vs. baseline
  r1[7] = 'Metric'; r1[8] = 'Seed 42'; r1[9] = 'Seed 123'; r1[10] = 'Seed 1993'; r1[11] = 'Mean ± STD';
  r1[12] = "Δ\nvs. baseline";

  // Tables 3..6: Ablations -> 2 delta cols: Δ vs. full model, Δ vs. baseline
  const ablStarts = [15, 24, 33, 42];
  for (const s of ablStarts) {
    r1[s]     = 'Metric';
    r1[s + 1] = 'Seed 42';
    r1[s + 2] = 'Seed 123';
    r1[s + 3] = 'Seed 1993';
    r1[s + 4] = 'Mean ± STD';
    r1[s + 5] = "Δ\nvs. full model";
    r1[s + 6] = "Δ\nvs. baseline";
  }
  rows.push(r1);

  // Rows 2..6: Metric rows
  const metrics = ['eval_accuracy', 'eval_f1', 'eval_precision', 'eval_recall', 'eval_loss'];
  const ablatedObjs = [noHpeObj, noSegObj, noBdrObj, noContObj];

  for (const m of metrics) {
    const row = new Array(49).fill('');

    // Table 1: Baseline (cols 0..4)
    row[0] = m;
    const b1Vals = extractSeedAndMS(baseObj, m);
    row[1] = b1Vals[0]; row[2] = b1Vals[1]; row[3] = b1Vals[2]; row[4] = b1Vals[3];

    // Table 2: Full 4-Module Model (cols 7..12) -> Delta vs Baseline
    row[7] = m;
    const b2Vals = extractSeedAndMS(fullObj, m);
    row[8] = b2Vals[0]; row[9] = b2Vals[1]; row[10] = b2Vals[2]; row[11] = b2Vals[3];
    row[12] = calcMetricDelta(fullObj, baseObj, m);

    // Tables 3..6: 4 Ablation Models (7 cols each)
    for (let i = 0; i < 4; i++) {
      const s = ablStarts[i];
      const ablObj = ablatedObjs[i];
      row[s] = m;
      const vals = extractSeedAndMS(ablObj, m);
      row[s + 1] = vals[0];
      row[s + 2] = vals[1];
      row[s + 3] = vals[2];
      row[s + 4] = vals[3];
      // Delta 1: vs. full model
      row[s + 5] = calcMetricDelta(ablObj, fullObj, m);
      // Delta 2: vs. baseline
      row[s + 6] = calcMetricDelta(ablObj, baseObj, m);
    }

    rows.push(row);
  }

  return rows;
}

function buildFullMatrix() {
  console.log('Loading all 24 3-seed ablation summaries...');

  const funsdLargeBase = loadJson("funsd-large-baseline_3seed_summary.json");
  const funsdLargeFull4 = loadJson("funsd-large-contrastive_3seed_summary.json");
  const funsdLargeNoHpe = loadJson("funsd-large-no_hpe_3seed_summary.json");
  const funsdLargeNoSeg = loadJson("funsd-large-no_segment_3seed_summary.json");
  const funsdLargeNoBdr = loadJson("funsd-large-no_boundary_3seed_summary.json");
  const funsdLargeNoCont = loadJson("funsd-large-full_3seed_summary.json");

  const funsdBaseBase = loadJson("funsd-base-baseline_3seed_summary.json");
  const funsdBaseFull4 = loadJson("funsd-base-contrastive_3seed_summary.json");
  const funsdBaseNoHpe = loadJson("funsd-base-no_hpe_3seed_summary.json");
  const funsdBaseNoSeg = loadJson("funsd-base-no_segment_3seed_summary.json");
  const funsdBaseNoBdr = loadJson("funsd-base-no_boundary_3seed_summary.json");
  const funsdBaseNoCont = loadJson("funsd-base-full_3seed_summary.json");

  const cordBaseBase = loadJson("cord-base-baseline_3seed_summary.json");
  const cordBaseFull4 = loadJson("cord-base-contrastive_3seed_summary.json");
  const cordBaseNoHpe = loadJson("cord-base-no_hpe_3seed_summary.json");
  const cordBaseNoSeg = loadJson("cord-base-no_segment_3seed_summary.json");
  const cordBaseNoBdr = loadJson("cord-base-no_boundary_3seed_summary.json");
  const cordBaseNoCont = loadJson("cord-base-full_3seed_summary.json");

  const cordLargeBase = loadJson("cord-large-baseline_3seed_summary.json");
  const cordLargeFull4 = loadJson("cord-large-contrastive_3seed_summary.json");
  const cordLargeNoHpe = loadJson("cord-large-no_hpe_3seed_summary.json");
  const cordLargeNoSeg = loadJson("cord-large-no_segment_3seed_summary.json");
  const cordLargeNoBdr = loadJson("cord-large-no_boundary_3seed_summary.json");
  const cordLargeNoCont = loadJson("cord-large-full_3seed_summary.json");

  const sec1 = makeSixTableSection(
    'large - FUNSD',
    funsdLargeBase, funsdLargeFull4,
    funsdLargeNoHpe, funsdLargeNoSeg, funsdLargeNoBdr, funsdLargeNoCont
  );

  const sec2 = makeSixTableSection(
    'base - FUNSD',
    funsdBaseBase, funsdBaseFull4,
    funsdBaseNoHpe, funsdBaseNoSeg, funsdBaseNoBdr, funsdBaseNoCont
  );

  const sec3 = makeSixTableSection(
    'base - CORD',
    cordBaseBase, cordBaseFull4,
    cordBaseNoHpe, cordBaseNoSeg, cordBaseNoBdr, cordBaseNoCont
  );

  const sec4 = makeSixTableSection(
    'large - CORD',
    cordLargeBase, cordLargeFull4,
    cordLargeNoHpe, cordLargeNoSeg, cordLargeNoBdr, cordLargeNoCont
  );

  const blankRow = new Array(49).fill('');
  const matrix = [];
  const sections = [sec1, sec2, sec3, sec4];
  sections.forEach((sec, idx) => {
    matrix.push(...sec);
    if (idx < sections.length - 1) {
      matrix.push([...blankRow]);
      matrix.push([...blankRow]);
    }
  });

  return matrix;
}

async function main() {
  const matrix = buildFullMatrix();
  console.log(`Matrix built: ${matrix.length} rows, ${matrix[0].length} columns.`);

  // Write local CSV
  const csvPath = path.resolve('thesis/tracker.csv');
  const csvContent = matrix
    .map(r => r.map(c => (c.includes(',') || c.includes('"') || c.includes('\n')) ? `"${c.replace(/"/g, '""')}"` : c).join(','))
    .join('\n');
  fs.writeFileSync(csvPath, csvContent, 'utf8');
  console.log('Saved CSV to:', csvPath);

  // Send to Webhook
  const payload = JSON.stringify({
    action: "sync",
    lastUpdated: new Date().toISOString().replace('T', ' ').substring(0, 19),
    rows: matrix
  });

  console.log('Pushing payload to Google Apps Script Webhook...');
  try {
    const res = await fetch(WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: payload,
      redirect: 'follow'
    });
    const text = await res.text();
    console.log(`Webhook response status: ${res.status}`);
    console.log(`Response body: ${text}`);
  } catch (err) {
    console.error('Webhook error:', err.message);
  }
}

main().catch(console.error);
