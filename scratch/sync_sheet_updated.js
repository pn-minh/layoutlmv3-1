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
  // Use 4-decimal rounded value matching the displayed Mean ± STD column
  return parseFloat(raw.toFixed(4));
}

/**
 * Calculates Delta for a given metric between targetObj and refObj.
 * - For eval_accuracy, eval_f1, eval_precision, eval_recall: (target - ref) * 100 formatted as +X.XX%
 * - For eval_loss: raw difference (target - ref) formatted as +X.XXXX
 */
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
 * Builds a 6-Table Horizontal Section Row Block (7 rows x 45 columns)
 * matching the user's manually updated layout:
 * - Table 1 (cols 0..4, 5 cols): Baseline LayoutLMv3
 * - Spacer 1 (cols 5..6, 2 blank cols)
 * - Table 2 (cols 7..12, 6 cols): HPE + SCM + Contrastive Loss + Boundary Loss (Delta vs Baseline)
 * - Spacer 2 (cols 13..14, 2 blank cols)
 * - Table 3 (cols 15..20, 6 cols): w/o HPE (Delta vs Full 4-Module)
 * - Spacer 3 (cols 21..22, 2 blank cols)
 * - Table 4 (cols 23..28, 6 cols): w/o Token-Segment SCM (Delta vs Full 4-Module)
 * - Spacer 4 (cols 29..30, 2 blank cols)
 * - Table 5 (cols 31..36, 6 cols): w/o Boundary Loss (Delta vs Full 4-Module)
 * - Spacer 5 (cols 37..38, 2 blank cols)
 * - Table 6 (cols 39..44, 6 cols): w/o Contrastive Loss (Delta vs Full 4-Module)
 */
function makeSixTableSection(suffix, baseObj, fullObj, noHpeObj, noSegObj, noBdrObj, noContObj) {
  const rows = [];

  // Row 0: Configuration Titles
  const r0 = new Array(45).fill('');
  r0[0]  = `Baseline LayoutLMv3 (${suffix})`;
  r0[7]  = `HPE + SCM + Contrastive Loss + Boundary Loss (${suffix})`;
  r0[15] = `w/o HPE (${suffix})`;
  r0[23] = `w/o Token-Segment SCM (${suffix})`;
  r0[31] = `w/o Boundary Loss (${suffix})`;
  r0[39] = `w/o Contrastive Loss (${suffix})`;
  rows.push(r0);

  // Row 1: Column Headers
  const r1 = new Array(45).fill('');
  // Table 1 (5 cols: 0..4)
  r1[0] = 'Metric'; r1[1] = 'Seed 42'; r1[2] = 'Seed 123'; r1[3] = 'Seed 1993'; r1[4] = 'Mean ± STD';
  // Tables 2..6 (6 cols each, starting at 7, 15, 23, 31, 39)
  const starts = [7, 15, 23, 31, 39];
  for (const s of starts) {
    r1[s]     = 'Metric';
    r1[s + 1] = 'Seed 42';
    r1[s + 2] = 'Seed 123';
    r1[s + 3] = 'Seed 1993';
    r1[s + 4] = 'Mean ± STD';
    r1[s + 5] = 'Delta';
  }
  rows.push(r1);

  // Rows 2..6: Metric rows
  const metrics = ['eval_accuracy', 'eval_f1', 'eval_precision', 'eval_recall', 'eval_loss'];
  const ablatedObjs = [noHpeObj, noSegObj, noBdrObj, noContObj];

  for (const m of metrics) {
    const row = new Array(45).fill('');

    // Table 1: Baseline (cols 0..4)
    row[0] = m;
    const b1Vals = extractSeedAndMS(baseObj, m);
    row[1] = b1Vals[0]; row[2] = b1Vals[1]; row[3] = b1Vals[2]; row[4] = b1Vals[3];

    // Table 2: Full 4-Module Model (cols 7..12) -> Compared against Baseline
    row[7] = m;
    const b2Vals = extractSeedAndMS(fullObj, m);
    row[8] = b2Vals[0]; row[9] = b2Vals[1]; row[10] = b2Vals[2]; row[11] = b2Vals[3];
    row[12] = calcMetricDelta(fullObj, baseObj, m);

    // Tables 3..6: 4 Ablation Models -> Each compared against Full 4-Module Model (fullObj)
    const ablStarts = [15, 23, 31, 39];
    for (let i = 0; i < 4; i++) {
      const s = ablStarts[i];
      const ablObj = ablatedObjs[i];
      row[s] = m;
      const vals = extractSeedAndMS(ablObj, m);
      row[s + 1] = vals[0];
      row[s + 2] = vals[1];
      row[s + 3] = vals[2];
      row[s + 4] = vals[3];
      row[s + 5] = calcMetricDelta(ablObj, fullObj, m);
    }

    rows.push(row);
  }

  return rows;
}

function buildFullMatrix() {
  console.log('Loading all 24 3-seed ablation summaries...');

  // Note on filenames:
  // *-contrastive_3seed_summary.json = Full 4-Module Model (HPE + SCM + Contrastive Loss + Boundary Loss)
  // *-full_3seed_summary.json        = 3-Module Model (w/o Contrastive Loss)
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

  const blankRow = new Array(45).fill('');
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

  // Print summary of calculated deltas for verification
  const sectionRows = [0, 9, 18, 27];
  for (const sr of sectionRows) {
    console.log(`\n--- ${matrix[sr][0]} ---`);
    for (let r = sr + 2; r <= sr + 6; r++) {
      const m = matrix[r][0];
      console.log(
        `${m.padEnd(15)} | Full(vs Base): ${matrix[r][12].padStart(8)} | w/o HPE: ${matrix[r][20].padStart(8)} | w/o SCM: ${matrix[r][28].padStart(8)} | w/o Bdr: ${matrix[r][36].padStart(8)} | w/o Cont: ${matrix[r][44].padStart(8)}`
      );
    }
  }

  // Write local CSV
  const csvPath = path.resolve('thesis/tracker.csv');
  const csvContent = matrix
    .map(r => r.map(c => (c.includes(',') || c.includes('"') || c.includes('\n')) ? `"${c.replace(/"/g, '""')}"` : c).join(','))
    .join('\n');
  fs.writeFileSync(csvPath, csvContent, 'utf8');
  console.log('\nSaved CSV to:', csvPath);

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
