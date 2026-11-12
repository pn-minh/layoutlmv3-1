/**
 * Local Real-Time Tracking Dashboard Server & Vast.ai SSH Watcher
 * Serves the new Additional Experiments Dashboard at http://localhost:8765
 * (and http://localhost:8765/additional_experiments.html; legacy dashboard at /legacy)
 * and automatically pulls results from Vast.ai /workspace/live_status.json and logs/.
 */
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const PORT = 8765;
const ROOT_DIR = path.resolve(__dirname, '..');
const NEW_DASHBOARD_HTML = path.join(ROOT_DIR, 'dashboard', 'additional_experiments.html');
const LEGACY_DASHBOARD_HTML = path.join(ROOT_DIR, 'dashboard', 'index.html');
const LOGS_DIR = path.join(ROOT_DIR, 'layoutlmv3', 'logs');
const SUMMARIES_DIR = path.join(ROOT_DIR, 'scratch', 'colab_summaries');
const SSH_CONFIG_PATH = path.join(ROOT_DIR, 'scratch', 'ssh_config');
const LOCAL_STATUS_JSON = path.join(ROOT_DIR, 'scratch', 'live_status_local.json');
const VAST_API_KEY = process.env.VAST_API_KEY || '3ad44c08d95a4f951cced4d2fdbda4698d1cfab2c81ccc51f7ad6830e573bd50';

const ADDITIONAL_CELLS_PLAN = [
  { cell: 27, pack: 'Pack A (Core + Curves)', dataset: 'cord',  variant: 'large', mode: 'contrastive',     label: 'CORD large contrastive (Calibrated 4-Module)',  summary_file: 'cord-large-contrastive_3seed_summary.json' },
  { cell: 26, pack: 'Pack A (Core + Curves)', dataset: 'funsd', variant: 'large', mode: 'contrastive',     label: 'FUNSD large contrastive (Calibrated 4-Module)', summary_file: 'funsd-large-contrastive_3seed_summary.json' },
  { cell: 25, pack: 'Pack A (Core + Curves)', dataset: 'cord',  variant: 'base',  mode: 'contrastive',     label: 'CORD base contrastive (Calibrated 4-Module)',   summary_file: 'cord-base-contrastive_3seed_summary.json' },
  { cell: 24, pack: 'Pack A (Core + Curves)', dataset: 'funsd', variant: 'base',  mode: 'contrastive',     label: 'FUNSD base contrastive (Calibrated 4-Module)',  summary_file: 'funsd-base-contrastive_3seed_summary.json' },
  { cell: 29, pack: 'Pack A (Step Curves)',   dataset: 'cord',  variant: 'base',  mode: 'baseline',        label: 'CORD base baseline (Step & Per-Class Curves)',  summary_file: 'cord-base-baseline_3seed_summary.json' },
  { cell: 30, pack: 'Pack A (Step Curves)',   dataset: 'funsd', variant: 'base',  mode: 'baseline',        label: 'FUNSD base baseline (Step & Per-Class Curves)', summary_file: 'funsd-base-baseline_3seed_summary.json' },
  { cell: 31, pack: 'Pack B (Sensitivity)',   dataset: 'funsd', variant: 'base',  mode: 'sens_bound_005',  label: 'Sensitivity: λ_bound = 0.05',                   summary_file: 'funsd-base-sens_bound_005_3seed_summary.json' },
  { cell: 32, pack: 'Pack B (Sensitivity)',   dataset: 'funsd', variant: 'base',  mode: 'sens_bound_020',  label: 'Sensitivity: λ_bound = 0.20',                   summary_file: 'funsd-base-sens_bound_020_3seed_summary.json' },
  { cell: 33, pack: 'Pack B (Sensitivity)',   dataset: 'funsd', variant: 'base',  mode: 'sens_tau_007',    label: 'Sensitivity: Contrastive τ = 0.07',             summary_file: 'funsd-base-sens_tau_007_3seed_summary.json' },
  { cell: 34, pack: 'Pack B (Sensitivity)',   dataset: 'funsd', variant: 'base',  mode: 'sens_tau_020',    label: 'Sensitivity: Contrastive τ = 0.20',             summary_file: 'funsd-base-sens_tau_020_3seed_summary.json' },
  { cell: 37, pack: 'Pack C (Few-Shot)',      dataset: 'funsd', variant: 'base',  mode: 'fewshot_base_50', label: 'Few-Shot 50% Data: Baseline',                   summary_file: 'funsd-base-fewshot_base_50_3seed_summary.json' },
  { cell: 38, pack: 'Pack C (Few-Shot)',      dataset: 'funsd', variant: 'base',  mode: 'fewshot_full_50', label: 'Few-Shot 50% Data: Full 4-Module',              summary_file: 'funsd-base-fewshot_full_50_3seed_summary.json' },
  { cell: 35, pack: 'Pack C (Few-Shot)',      dataset: 'funsd', variant: 'base',  mode: 'fewshot_base_25', label: 'Few-Shot 25% Data: Baseline',                   summary_file: 'funsd-base-fewshot_base_25_3seed_summary.json' },
  { cell: 36, pack: 'Pack C (Few-Shot)',      dataset: 'funsd', variant: 'base',  mode: 'fewshot_full_25', label: 'Few-Shot 25% Data: Full 4-Module',              summary_file: 'funsd-base-fewshot_full_25_3seed_summary.json' },
  { cell: 28, pack: 'Benchmarks & Sync',      dataset: 'all',   variant: 'all',   mode: 'aggregate',       label: 'Latency/VRAM + Span-Length Eval + Sheet Sync',  summary_file: 'FINAL_AGGREGATED_ABLATION_TABLE.md' }
];

function loadLocalSummaries() {
  const map = new Map();
  for (const dir of [SUMMARIES_DIR, LOGS_DIR]) {
    if (!fs.existsSync(dir)) continue;
    const files = fs.readdirSync(dir).filter(f => f.endsWith('_3seed_summary.json')).sort();
    for (const fname of files) {
      try {
        const data = JSON.parse(fs.readFileSync(path.join(dir, fname), 'utf8'));
        const ms = data.mean_std || data.metrics || {};
        const f1 = ms.eval_f1 || {};
        const p = ms.eval_precision || {};
        const r = ms.eval_recall || {};
        const acc = ms.eval_accuracy || {};
        if (typeof f1.mean === 'number') {
          map.set(fname, {
            file: fname,
            dataset: data.dataset,
            variant: data.variant,
            mode: data.mode,
            f1_mean: Number((f1.mean * 100).toFixed(2)),
            f1_std: Number(((f1.std || 0) * 100).toFixed(2)),
            p_mean: Number(((p.mean || 0) * 100).toFixed(2)),
            r_mean: Number(((r.mean || 0) * 100).toFixed(2)),
            acc_mean: typeof acc.mean === 'number' ? Number((acc.mean * 100).toFixed(2)) : null,
            has_step_history: Boolean(data.step_history && Object.keys(data.step_history).length > 0),
          });
        }
      } catch (_) {}
    }
  }
  return Array.from(map.values());
}

let liveState = {
  pipeline_status: 'STANDBY — READY FOR DUAL-A100 VAST.AI LAUNCH',
  updated_at: new Date().toISOString().replace('T', ' ').slice(0, 19),
  elapsed_total_sec: 0,
  active_workers: {},
  gpu_telemetry: [],
  completed_cells: [],
  additional_cells_plan: ADDITIONAL_CELLS_PLAN,
  cells_plan: ADDITIONAL_CELLS_PLAN,
  completed_summaries: loadLocalSummaries(),
};

function saveLocalState() {
  try {
    fs.writeFileSync(LOCAL_STATUS_JSON, JSON.stringify(liveState, null, 2), 'utf8');
  } catch (_) {}
}

function destroyVastInstanceRest(instanceId) {
  if (!instanceId || !VAST_API_KEY) return;
  const req = https.request({
    hostname: 'console.vast.ai',
    path: `/api/v0/instances/${instanceId}/?api_key=${VAST_API_KEY}`,
    method: 'DELETE',
    timeout: 15000,
  }, (res) => {
    console.log(`[SELF-DESTRUCT REST] Vast.ai instance ${instanceId} DELETE status: ${res.statusCode}`);
  });
  req.on('error', (err) => console.error('[SELF-DESTRUCT REST ERROR]', err.message));
  req.end();
}

function pollRemoteVast() {
  liveState.completed_summaries = loadLocalSummaries();
  liveState.updated_at = new Date().toISOString().replace('T', ' ').slice(0, 19);

  if (!fs.existsSync(SSH_CONFIG_PATH)) {
    saveLocalState();
    return;
  }

  const cmd = `ssh -F "${SSH_CONFIG_PATH}" -o ConnectTimeout=6 -o BatchMode=yes vast "cat /workspace/live_status.json 2>/dev/null"`;
  exec(cmd, { timeout: 12000 }, (err, stdout) => {
    if (err || !stdout || !stdout.trim().startsWith('{')) {
      saveLocalState();
      return;
    }
    try {
      const remoteData = JSON.parse(stdout.trim());
      // Pull any newly completed summary JSONs to local layoutlmv3/logs & scratch/colab_summaries
      exec(`scp -F "${SSH_CONFIG_PATH}" "vast:/workspace/layoutlmv3-1/layoutlmv3/logs/*.json" "${LOGS_DIR}/"`, () => {
        liveState.completed_summaries = loadLocalSummaries();
      });

      liveState = {
        ...liveState,
        ...remoteData,
        additional_cells_plan: ADDITIONAL_CELLS_PLAN,
        cells_plan: ADDITIONAL_CELLS_PLAN,
        completed_summaries: loadLocalSummaries(),
      };
      saveLocalState();
    } catch (_) {}
  });
}

const server = http.createServer((req, res) => {
  if (req.url.startsWith('/api/status')) {
    liveState.completed_summaries = loadLocalSummaries();
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    res.end(JSON.stringify(liveState));
    return;
  }
  if (req.url.startsWith('/legacy')) {
    if (fs.existsSync(LEGACY_DASHBOARD_HTML)) {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(fs.readFileSync(LEGACY_DASHBOARD_HTML, 'utf8'));
      return;
    }
  }
  const targetHtml = fs.existsSync(NEW_DASHBOARD_HTML) ? NEW_DASHBOARD_HTML : LEGACY_DASHBOARD_HTML;
  if (fs.existsSync(targetHtml)) {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(fs.readFileSync(targetHtml, 'utf8'));
  } else {
    res.writeHead(404);
    res.end('Dashboard HTML not found');
  }
});

server.listen(PORT, () => {
  console.log(`[LOCAL DASHBOARD] Additional Experiments Live Tracker running at http://localhost:${PORT}`);
  saveLocalState();
  setInterval(pollRemoteVast, 12000);
});
