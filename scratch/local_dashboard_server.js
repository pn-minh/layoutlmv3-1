/**
 * Local Real-Time Tracking Dashboard Server & Vast.ai SSH Watcher
 * Serves http://localhost:8765 and polls Vast.ai /workspace/live_status.json when SSH is active.
 */
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const PORT = 8765;
const ROOT_DIR = path.resolve(__dirname, '..');
const DASHBOARD_HTML = path.join(ROOT_DIR, 'dashboard', 'index.html');
const SUMMARIES_DIR = path.join(ROOT_DIR, 'scratch', 'colab_summaries');
const SSH_CONFIG_PATH = path.join(ROOT_DIR, 'scratch', 'ssh_config');
const LOCAL_STATUS_JSON = path.join(ROOT_DIR, 'scratch', 'live_status_local.json');
const EXP_PROGRESS_MD = path.join(ROOT_DIR, 'EXPERIMENT_PROGRESS.md');
const VAST_API_KEY = process.env.VAST_API_KEY || '3ad44c08d95a4f951cced4d2fdbda4698d1cfab2c81ccc51f7ad6830e573bd50';

const CELLS_PLAN = [
  { cell: 23, dataset: 'cord',  variant: 'large', mode: 'no_hpe',      label: 'CORD large no_hpe (w/o HPE)',                  summary_file: 'cord-large-no_hpe_3seed_summary.json' },
  { cell: 24, dataset: 'funsd', variant: 'base',  mode: 'contrastive', label: 'FUNSD base contrastive (+Contrastive Loss)',   summary_file: 'funsd-base-contrastive_3seed_summary.json' },
  { cell: 25, dataset: 'cord',  variant: 'base',  mode: 'contrastive', label: 'CORD base contrastive (+Contrastive Loss)',    summary_file: 'cord-base-contrastive_3seed_summary.json' },
  { cell: 26, dataset: 'funsd', variant: 'large', mode: 'contrastive', label: 'FUNSD large contrastive (+Contrastive Loss)',  summary_file: 'funsd-large-contrastive_3seed_summary.json' },
  { cell: 27, dataset: 'cord',  variant: 'large', mode: 'contrastive', label: 'CORD large contrastive (+Contrastive Loss)',   summary_file: 'cord-large-contrastive_3seed_summary.json' },
  { cell: 28, dataset: 'all',   variant: 'all',   mode: 'aggregate',   label: 'Master 24-Config Aggregation & Drive Archive', summary_file: 'FINAL_AGGREGATED_ABLATION_TABLE.md' }
];

function loadLocalSummaries() {
  const list = [];
  if (!fs.existsSync(SUMMARIES_DIR)) return list;
  const files = fs.readdirSync(SUMMARIES_DIR).filter(f => f.endsWith('_3seed_summary.json')).sort();
  for (const fname of files) {
    try {
      const data = JSON.parse(fs.readFileSync(path.join(SUMMARIES_DIR, fname), 'utf8'));
      const ms = data.mean_std || data.metrics || {};
      const f1 = ms.eval_f1 || {};
      const p = ms.eval_precision || {};
      const r = ms.eval_recall || {};
      if (typeof f1.mean === 'number') {
        list.push({
          file: fname,
          dataset: data.dataset,
          variant: data.variant,
          mode: data.mode,
          f1_mean: Number((f1.mean * 100).toFixed(2)),
          f1_std: Number(((f1.std || 0) * 100).toFixed(2)),
          p_mean: Number(((p.mean || 0) * 100).toFixed(2)),
          r_mean: Number(((r.mean || 0) * 100).toFixed(2)),
        });
      }
    } catch (_) {}
  }
  return list;
}

let liveState = {
  pipeline_status: 'STANDBY — WAITING FOR VAST.AI SSH CONNECTION',
  updated_at: new Date().toISOString().replace('T', ' ').slice(0, 19),
  elapsed_total_sec: 0,
  current_cell: 23,
  current_label: 'CORD large no_hpe (w/o HPE)',
  current_dataset: 'cord',
  current_variant: 'large',
  current_mode: 'no_hpe',
  current_seed: '',
  current_seed_idx: 0,
  step: 0,
  max_steps: 500,
  step_pct: 0.0,
  seed_eta_sec: 0,
  latest_eval: {},
  gpu: {},
  completed_cells: [],
  cells_plan: CELLS_PLAN,
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

let syncingFinal = false;

function pollRemoteVast() {
  if (!fs.existsSync(SSH_CONFIG_PATH)) {
    liveState.completed_summaries = loadLocalSummaries();
    liveState.updated_at = new Date().toISOString().replace('T', ' ').slice(0, 19);
    saveLocalState();
    return;
  }

  const cmd = `ssh -F "${SSH_CONFIG_PATH}" -o ConnectTimeout=6 -o BatchMode=yes vast "cat /workspace/live_status.json 2>/dev/null"`;
  exec(cmd, { timeout: 12000 }, (err, stdout) => {
    if (err || !stdout || !stdout.trim().startsWith('{')) {
      return;
    }
    try {
      const remoteData = JSON.parse(stdout.trim());
      liveState = {
        ...liveState,
        ...remoteData,
        cells_plan: CELLS_PLAN,
      };
      saveLocalState();

      // Pull any newly completed summary JSONs to local scratch/colab_summaries
      if (Array.isArray(remoteData.completed_summaries)) {
        for (const item of remoteData.completed_summaries) {
          const localPath = path.join(SUMMARIES_DIR, item.file);
          if (!fs.existsSync(localPath)) {
            exec(`scp -F "${SSH_CONFIG_PATH}" vast:/workspace/layoutlmv3-1/layoutlmv3/logs/${item.file} "${localPath}"`, () => {});
          }
        }
      }

      // If pipeline finished and is waiting for final local sync before self-destruction
      if (remoteData.pipeline_status === 'COMPLETED_WAITING_LOCAL_SYNC' && !syncingFinal) {
        syncingFinal = true;
        console.log('[FINAL SYNC] Pulling final table, summaries, and master archive before Vast.ai self-destruction...');
        const syncCmd = [
          `scp -F "${SSH_CONFIG_PATH}" "vast:/workspace/layoutlmv3-1/layoutlmv3/logs/*_3seed_summary.json" "${SUMMARIES_DIR}/"`,
          `scp -F "${SSH_CONFIG_PATH}" vast:/workspace/layoutlmv3-1/FINAL_AGGREGATED_ABLATION_TABLE.md "${path.join(ROOT_DIR, 'FINAL_AGGREGATED_ABLATION_TABLE.md')}"`,
          `scp -F "${SSH_CONFIG_PATH}" vast:/workspace/LayoutLMv3_Final_Experiment_Results_All_28_Cells.zip "${path.join(ROOT_DIR, 'scratch', 'LayoutLMv3_Final_Experiment_Results_All_28_Cells.zip')}"`,
          `ssh -F "${SSH_CONFIG_PATH}" vast "touch /workspace/LOCAL_SYNC_CONFIRMED"`
        ].join(' && ');

        exec(syncCmd, { timeout: 60000 }, () => {
          console.log('[FINAL SYNC] Local sync complete! Triggering Vast.ai self-destruct confirmation.');
          const idFile = path.join(ROOT_DIR, 'scratch', 'vast_instance_id.txt');
          if (fs.existsSync(idFile)) {
            const instId = fs.readFileSync(idFile, 'utf8').trim();
            destroyVastInstanceRest(instId);
          }
          liveState.pipeline_status = 'COMPLETED & INSTANCE SELF-DESTRUCTED';
          saveLocalState();
        });
      }
    } catch (_) {}
  });
}

const server = http.createServer((req, res) => {
  if (req.url.startsWith('/api/status')) {
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    res.end(JSON.stringify(liveState));
    return;
  }
  if (fs.existsSync(DASHBOARD_HTML)) {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(fs.readFileSync(DASHBOARD_HTML, 'utf8'));
  } else {
    res.writeHead(404);
    res.end('Dashboard HTML not found');
  }
});

server.listen(PORT, () => {
  console.log(`[LOCAL DASHBOARD] Live Tracking Dashboard running at http://localhost:${PORT}`);
  saveLocalState();
  setInterval(pollRemoteVast, 15000);
});
