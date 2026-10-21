import RFB from './vendor/novnc/core/rfb.js';

const WS_URL = 'ws://localhost:9001';
const VNC_WS_URL = 'ws://localhost:6080';

const MODELS = {
  T1B1: { header: 'Trezor One', short: 'T1' },
  T2T1: { header: 'Trezor T', short: 'TT' },
  T3B1: { header: 'Safe 3', short: 'S3' },
  T3T1: { header: 'Safe 5', short: 'S5' },
  T3W1: { header: 'Safe 7', short: 'S7' },
};

const MNEMONICS = {
  all: 'all all all all all all all all all all all all',
  academic: 'academic academic academic academic academic academic academic academic academic academic academic academic academic academic academic academic academic academic academic academic',
};

let ws = null;
let rfb = null;
let selectedModel = 'T3T1';
let firmwareVersions = {};
let emulatorRunning = false;
let bridgeRunning = false;
let vncConnected = false;
let msgId = 0;

const $ = (sel) => document.querySelector(sel);
const titleStatus = $('#title-status');
const vncContainer = $('#vnc-container');
const vncPlaceholder = $('#vnc-placeholder');
const vncTarget = $('#vnc-target');
const modelGrid = $('#model-grid');
const versionSelect = $('#version-select');
const statusDot = $('#status-dot');
const statusText = $('#status-text');
const bridgeDot = $('#bridge-dot');
const toast = $('#toast');

function showToast(text, duration = 2500) {
  toast.textContent = text;
  toast.classList.remove('hidden');
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => toast.classList.add('hidden'), duration);
}

let bridgePending = false;
let bridgePendingTimer = null;

function setBridgePending(pending) {
  bridgePending = pending;
  clearTimeout(bridgePendingTimer);
  if (pending) bridgePendingTimer = setTimeout(() => setBridgePending(false), 10000);
  updateStatus();
}

function toggleBridge() {
  if (ws?.readyState !== WebSocket.OPEN) return showToast('Not connected to controller');
  if (bridgePending) return;
  send(bridgeRunning ? { type: 'bridge-stop' } : { type: 'bridge-start', version: 'node-bridge' });
  setBridgePending(true);
}

function updateStatus() {
  const bridgeState = bridgePending ? 'dot--yellow' : bridgeRunning ? 'dot--green' : 'dot--off';
  bridgeDot.className = `dot ${bridgeState}`;
  $('#btn-bridge').title = bridgeRunning ? 'Stop bridge' : 'Start bridge';

  if (!ws || ws.readyState !== WebSocket.OPEN) {
    statusDot.className = 'dot dot--red';
    statusText.textContent = 'Disconnected';
    titleStatus.textContent = '';
  } else if (emulatorRunning) {
    statusDot.className = 'dot dot--green';
    statusText.textContent = 'Emulator running';
    titleStatus.textContent = '· running';
  } else {
    statusDot.className = 'dot dot--yellow';
    statusText.textContent = 'Connected';
    titleStatus.textContent = '';
  }
  updatePlaceholder();
  syncMenu();
}

let connectFailed = false;
let tenvStarting = false;
let tenvExitNote = '';

function updatePlaceholder() {
  const connected = ws?.readyState === WebSocket.OPEN;
  const text = $('#placeholder-text');
  const hint = $('#placeholder-hint');
  const button = $('#btn-start-tenv');
  let hintText = '';
  let showButton = false;

  if (connected) {
    text.textContent = 'No emulator running';
  } else if (tenvStarting) {
    text.textContent = 'Starting trezor-user-env…';
    hintText = 'Pulling images and starting containers. This can take a minute.';
  } else if (connectFailed) {
    text.textContent = 'trezor-user-env is not running';
    hintText = tenvExitNote;
    showButton = Boolean(window.__TAURI__);
  } else {
    text.textContent = 'Connecting to trezor-user-env…';
  }

  hint.textContent = hintText;
  hint.hidden = !hintText;
  button.hidden = !showButton;
}

async function startTenv() {
  const tauri = window.__TAURI__;
  if (!tauri || tenvStarting || ws?.readyState === WebSocket.OPEN) return;
  tenvStarting = true;
  tenvExitNote = '';
  updateStatus();
  showToast('Starting trezor-user-env…');
  try {
    tenvLog = await tauri.core.invoke('start_tenv');
  } catch (e) {
    tenvStarting = false;
    tenvExitNote = String(e);
    showToast('Could not start trezor-user-env', 4000);
  }
  updateStatus();
}

let tenvLog = '';
window.__TAURI__?.event.listen('tenv-exited', ({ payload: code }) => {
  tenvStarting = false;
  if (ws?.readyState !== WebSocket.OPEN) {
    const status = code == null ? 'stopped' : `exited with code ${code}`;
    tenvExitNote = `run.sh ${status}. Log: ${tenvLog}`;
  }
  updateStatus();
});

// Emulator frame backgrounds: most models use #C8CDD3, T3B1 uses white.
const MASK_BACKGROUNDS = [
  [0xC8, 0xCD, 0xD3],
  [0xFF, 0xFF, 0xFF],
];
const MASK_TOL2 = 48 * 48;
let maskTimer = null;
let maskKey = '';

// Alpha mask of everything except the grey background reachable from the frame edges.
function buildMaskUrl(canvas) {
  const w = canvas.width;
  const h = canvas.height;
  if (!w || !h) return null;
  const src = canvas.getContext('2d').getImageData(0, 0, w, h).data;
  const near = (p, [r, g, b]) => {
    const i = p * 4;
    const dr = src[i] - r;
    const dg = src[i + 1] - g;
    const db = src[i + 2] - b;
    return dr * dr + dg * dg + db * db <= MASK_TOL2;
  };
  const bgColor = MASK_BACKGROUNDS.find((c) => near(0, c));
  if (!bgColor) return null;
  const isBg = (p) => near(p, bgColor);

  const bg = new Uint8Array(w * h);
  const stack = new Int32Array(w * h);
  let sp = 0;
  const seed = (p) => {
    if (!bg[p] && isBg(p)) { bg[p] = 1; stack[sp++] = p; }
  };
  for (let x = 0; x < w; x++) { seed(x); seed((h - 1) * w + x); }
  for (let y = 0; y < h; y++) { seed(y * w); seed(y * w + w - 1); }
  while (sp) {
    const p = stack[--sp];
    const x = p % w;
    if (x > 0) seed(p - 1);
    if (x < w - 1) seed(p + 1);
    if (p >= w) seed(p - w);
    if (p < w * (h - 1)) seed(p + w);
  }

  // Erode 1px to drop the grey anti-aliasing fringe, then 3x3 blur for a soft edge.
  const solid = new Uint8Array(w * h);
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const p = y * w + x;
      solid[p] = !bg[p] && !bg[p - 1] && !bg[p + 1] && !bg[p - w] && !bg[p + w] ? 1 : 0;
    }
  }
  const m = document.createElement('canvas');
  m.width = w;
  m.height = h;
  const mctx = m.getContext('2d');
  const img = mctx.createImageData(w, h);
  let x0 = w, y0 = h, x1 = -1, y1 = -1;
  for (let y = 1; y < h - 1; y++) {
    for (let x = 1; x < w - 1; x++) {
      const p = y * w + x;
      let sum = 0;
      for (let dy = -w; dy <= w; dy += w) {
        sum += solid[p + dy - 1] + solid[p + dy] + solid[p + dy + 1];
      }
      if (!sum) continue;
      img.data[p * 4 + 3] = Math.round((sum / 9) * 255);
      if (x < x0) x0 = x;
      if (x > x1) x1 = x;
      if (y < y0) y0 = y;
      if (y > y1) y1 = y;
    }
  }
  if (x1 < 0) return null;
  mctx.putImageData(img, 0, 0);
  return {
    url: m.toDataURL(),
    fw: w,
    fh: h,
    bbox: { x: x0, y: y0, w: x1 - x0 + 1, h: y1 - y0 + 1 },
  };
}

let device = null;
const DEVICE_CORNER_RADIUS = 0.09; // fraction of the displayed device width
const DEVICE_PADDING = 18;
const FIT_WINDOW_WIDTH = 360;

// Size noVNC's container so that, once noVNC scales the framebuffer to fit it,
// the device bounding box exactly fills the visible display frame.
function layoutTarget() {
  const s = vncTarget.style;
  if (!device) {
    s.left = s.top = '0';
    s.width = s.height = '100%';
    s.clipPath = s.webkitClipPath = '';
    return;
  }
  const W = vncContainer.clientWidth;
  const H = vncContainer.clientHeight;
  const { bbox, fw, fh } = device;
  const scale = Math.max(0, Math.min((W - 2 * DEVICE_PADDING) / bbox.w, (H - 2 * DEVICE_PADDING) / bbox.h));
  s.width = `${fw * scale}px`;
  s.height = `${fh * scale}px`;
  s.left = `${(W - bbox.w * scale) / 2 - bbox.x * scale}px`;
  s.top = `${(H - bbox.h * scale) / 2 - bbox.y * scale}px`;

  const top = bbox.y * scale;
  const left = bbox.x * scale;
  const right = (fw - bbox.x - bbox.w) * scale;
  const bottom = (fh - bbox.y - bbox.h) * scale;
  const radius = bbox.w * scale * DEVICE_CORNER_RADIUS;
  s.clipPath = s.webkitClipPath =
    `inset(${top}px ${right}px ${bottom}px ${left}px round ${radius}px)`;
}

new ResizeObserver(layoutTarget).observe(vncContainer);

async function fitWindowToDevice() {
  const tauriWindow = window.__TAURI__?.window;
  const LogicalSize = window.__TAURI__?.dpi?.LogicalSize ?? tauriWindow?.LogicalSize;
  if (!tauriWindow || !LogicalSize || !device) return;
  const aspect = device.bbox.w / device.bbox.h;
  const chromeW = window.innerWidth - vncContainer.clientWidth;
  const chromeH = window.innerHeight - vncContainer.clientHeight;
  const maxH = window.screen.availHeight - 60;

  const pad = 2 * DEVICE_PADDING;
  let width = FIT_WINDOW_WIDTH;
  let height = (width - chromeW - pad) / aspect + pad + chromeH;
  if (height > maxH) {
    height = maxH;
    width = Math.max(FIT_WINDOW_WIDTH, (height - chromeH - pad) * aspect + pad + chromeW);
  }
  try {
    await tauriWindow.getCurrentWindow().setSize(new LogicalSize(Math.round(width), Math.round(height)));
  } catch (e) {
    console.error('Window resize failed:', e);
  }
}

function setCanvasMask(canvas, url) {
  const value = url ? `url(${url})` : '';
  for (const prop of ['webkitMaskImage', 'maskImage']) canvas.style[prop] = value;
  for (const prop of ['webkitMaskSize', 'maskSize']) canvas.style[prop] = url ? '100% 100%' : '';
  for (const prop of ['webkitMaskRepeat', 'maskRepeat']) canvas.style[prop] = url ? 'no-repeat' : '';
}

function startMask() {
  stopMask();
  maskTimer = setInterval(() => {
    const canvas = vncContainer.querySelector('canvas');
    if (!canvas) return;
    const key = `${canvas.width}x${canvas.height}`;
    if (key === maskKey) return;
    const result = buildMaskUrl(canvas);
    if (!result) return;
    setCanvasMask(canvas, result.url);
    maskKey = key;
    device = result;
    vncContainer.classList.add('live');
    layoutTarget();
    fitWindowToDevice();
  }, 500);
}

function stopMask() {
  clearInterval(maskTimer);
  maskTimer = null;
  maskKey = '';
  device = null;
  layoutTarget();
  vncContainer.classList.remove('live');
}

function connectVnc() {
  if (rfb) {
    rfb.disconnect();
    rfb = null;
  }

  vncPlaceholder.style.display = 'none';

  try {
    rfb = new RFB(vncTarget, VNC_WS_URL, {
      scaleViewport: true,
      resizeSession: false,
      showDotCursor: false,
    });
    rfb.viewOnly = false;
    rfb.focusOnClick = true;
    rfb.clipViewport = true;
    rfb.scaleViewport = true;
    rfb.background = 'transparent';
    rfb.qualityLevel = 9;

    rfb.addEventListener('connect', () => {
      vncConnected = true;
      vncPlaceholder.style.display = 'none';
      startMask();
    });

    rfb.addEventListener('disconnect', (e) => {
      vncConnected = false;
      stopMask();
      if (emulatorRunning) {
        setTimeout(() => {
          if (emulatorRunning && !vncConnected) connectVnc();
        }, 1500);
      } else {
        disconnectVnc();
      }
    });
  } catch (e) {
    console.error('VNC connect error:', e);
  }
}

function disconnectVnc() {
  stopMask();
  if (rfb) {
    try { rfb.disconnect(); } catch (_) {}
    rfb = null;
  }
  vncConnected = false;
  vncTarget.replaceChildren();
  vncPlaceholder.style.display = 'flex';
}

function updateVnc() {
  if (emulatorRunning && !vncConnected && !rfb) {
    connectVnc();
  } else if (!emulatorRunning && (vncConnected || rfb)) {
    disconnectVnc();
  }
}

function renderModels() {
  modelGrid.innerHTML = '';
  for (const [id, info] of Object.entries(MODELS)) {
    const btn = document.createElement('button');
    btn.className = `model-btn ${id === selectedModel ? 'active' : ''}`;
    btn.innerHTML = `${id}<span class="model-name">${info.short}</span>`;
    btn.addEventListener('click', () => selectModel(id));
    modelGrid.appendChild(btn);
  }
}

function selectModel(id) {
  if (!MODELS[id]) return;
  selectedModel = id;
  renderModels();
  renderVersions();
}

function renderVersions() {
  versionSelect.innerHTML = '';
  const versions = firmwareVersions[selectedModel] || [];
  if (versions.length === 0) {
    const opt = document.createElement('option');
    opt.textContent = 'No versions available';
    versionSelect.appendChild(opt);
  }
  for (const v of versions) {
    const opt = document.createElement('option');
    opt.value = v;
    opt.textContent = v;
    versionSelect.appendChild(opt);
  }
  syncMenu();
}

let lastMenuState = '';
function syncMenu() {
  const tauri = window.__TAURI__;
  if (!tauri) return;
  const versions = firmwareVersions[selectedModel] || [];
  const state = {
    models: Object.entries(MODELS).map(([id, info]) => ({ id, name: info.header })),
    model: selectedModel,
    versions,
    version: versions.length ? versionSelect.value : '',
    wipe: $('#opt-wipe').checked,
    seedOnStart: $('#opt-seed').checked,
    alwaysOnTop: $('#opt-ontop').checked,
    running: emulatorRunning,
    connected: ws?.readyState === WebSocket.OPEN,
    tenvStarting,
    bridgeRunning,
    bridgePending,
    drawerOpen: $('#drawer').classList.contains('open'),
  };
  const key = JSON.stringify(state);
  if (key === lastMenuState) return;
  lastMenuState = key;
  tauri.core.invoke('update_menu', { state }).catch((e) => console.error('Menu update failed:', e));
}

function runAction(id) {
  if (id === 'start-tenv') return startTenv();
  if (id === 'toggle-bridge') return toggleBridge();
  if (id === 'start') return $('#btn-start').click();
  if (id === 'stop') return $('#btn-stop').click();
  if (id === 'toggle-commands') return $('#drawer-toggle').click();
  const option = {
    'wipe-on-start': '#opt-wipe',
    'seed-on-start': '#opt-seed',
    'always-on-top': '#opt-ontop',
  }[id];
  if (option) {
    const el = $(option);
    el.checked = !el.checked;
    el.dispatchEvent(new Event('change'));
    return;
  }
  if (id.startsWith('model:')) return selectModel(id.slice('model:'.length));
  if (id.startsWith('version:')) {
    versionSelect.value = id.slice('version:'.length);
    return syncMenu();
  }
  if (id.startsWith('cmd:')) $(`#btn-${id.slice('cmd:'.length)}`)?.click();
}

function send(payload) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    showToast('Not connected to controller');
    return;
  }
  payload.id = String(++msgId);
  ws.send(JSON.stringify(payload));
}

function connectWs() {
  statusDot.className = 'dot dot--yellow';
  statusText.textContent = 'Connecting...';

  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    tenvStarting = false;
    tenvExitNote = '';
    updateStatus();
    showToast('Connected to controller');
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleMessage(data);
    } catch (e) {
      console.error('Parse error:', e);
    }
  };

  ws.onclose = () => {
    ws = null;
    connectFailed = true;
    emulatorRunning = false;
    bridgeRunning = false;
    updateStatus();
    disconnectVnc();
    setTimeout(connectWs, 3000);
  };

  ws.onerror = () => {
    ws?.close();
  };
}

function handleMessage(data) {
  if (data.type === 'client' && data.firmwares) {
    firmwareVersions = data.firmwares;
    renderVersions();
    return;
  }

  if (data.background_check) {
    const wasRunning = emulatorRunning;
    emulatorRunning = data.emulator_status?.is_running ?? false;
    const wasBridgeRunning = bridgeRunning;
    bridgeRunning = data.bridge_status?.is_running ?? false;
    if (bridgePending && wasBridgeRunning !== bridgeRunning) setBridgePending(false);
    updateStatus();
    if (wasRunning !== emulatorRunning) {
      updateVnc();
    }
    return;
  }

  if (data.success === false) {
    if (bridgePending) setBridgePending(false);
    showToast(`Error: ${data.error || 'Unknown error'}`, 4000);
    return;
  }

  if (data.emulator_started) {
    emulatorRunning = true;
    updateStatus();
    updateVnc();
    if ($('#opt-seed').checked) {
      loadSeed('all');
      showToast('Emulator started, loading “all” seed…');
    } else {
      showToast('Emulator started');
    }
    return;
  }

  if (typeof data.response === 'string') {
    if (data.response === 'Emulator stopped') {
      emulatorRunning = false;
      updateStatus();
      updateVnc();
    }
    showToast(data.response);
  }
}

// Background polling
setInterval(() => {
  if (ws?.readyState === WebSocket.OPEN) {
    send({ type: 'background-check' });
  }
}, 2000);

// Button handlers
$('#btn-start').addEventListener('click', () => {
  const version = versionSelect.value;
  if (!version) return;
  send({
    type: 'emulator-start',
    model: selectedModel,
    version,
    wipe: $('#opt-wipe').checked,
    show_animations: false,
  });
  showToast(`Starting ${selectedModel}...`);
});

$('#btn-stop').addEventListener('click', () => {
  send({ type: 'emulator-stop' });
});

function loadSeed(name) {
  send({
    type: 'emulator-setup',
    mnemonic: MNEMONICS[name],
    pin: '',
    passphrase_protection: false,
    label: 'Emulator',
    needs_backup: false,
  });
}

$('#btn-seed-all').addEventListener('click', () => loadSeed('all'));
$('#btn-seed-academic').addEventListener('click', () => loadSeed('academic'));

function applyAlwaysOnTop() {
  window.__TAURI__?.window.getCurrentWindow()
    .setAlwaysOnTop($('#opt-ontop').checked)
    .catch((e) => console.error('setAlwaysOnTop failed:', e));
}

// Options persist between launches.
for (const id of ['opt-wipe', 'opt-seed', 'opt-ontop']) {
  const el = $(`#${id}`);
  try {
    const saved = localStorage.getItem(id);
    if (saved !== null) el.checked = saved === '1';
  } catch (_) {}
  el.addEventListener('change', () => {
    try { localStorage.setItem(id, el.checked ? '1' : '0'); } catch (_) {}
    if (id === 'opt-ontop') applyAlwaysOnTop();
    syncMenu();
  });
}
applyAlwaysOnTop();

$('#btn-yes').addEventListener('click', () => send({ type: 'emulator-press-yes' }));
$('#btn-no').addEventListener('click', () => send({ type: 'emulator-press-no' }));
$('#btn-wipe').addEventListener('click', () => send({ type: 'emulator-wipe' }));
$('#btn-reset').addEventListener('click', () => send({ type: 'emulator-reset-device' }));
$('#btn-features').addEventListener('click', () => send({ type: 'emulator-get-features' }));
$('#btn-unsafe').addEventListener('click', () => send({ type: 'emulator-allow-unsafe-paths' }));
$('#btn-confirm-mnemonic').addEventListener('click', () => send({ type: 'emulator-read-and-confirm-mnemonic' }));

// noVNC swallows all keys while the display has focus, so menu shortcuts never reach the menu.
// Keep in sync with the accelerators in src-tauri/src/app_menu.rs.
const SHORTCUTS = {
  r: 'start',
  '.': 'stop',
  enter: 'cmd:yes',
  backspace: 'cmd:no',
  j: 'toggle-commands',
  b: 'toggle-bridge',
  ...Object.fromEntries(Object.keys(MODELS).map((id, i) => [String(i + 1), `model:${id}`])),
};

window.addEventListener('keydown', (e) => {
  if (!e.metaKey || e.ctrlKey || e.altKey) return;
  const key = e.key.toLowerCase();
  const tauri = window.__TAURI__;
  if (!tauri) return;
  const action = SHORTCUTS[key];
  if (!action && !['q', 'w', 'h'].includes(key)) return;
  e.preventDefault();
  e.stopImmediatePropagation();
  if (action) runAction(action);
  else if (key === 'h') tauri.app.hide();
  else tauri.core.invoke('quit');
}, true);

window.__TAURI__?.event.listen('menu-action', ({ payload }) => runAction(payload));
versionSelect.addEventListener('change', syncMenu);
$('#btn-start-tenv').addEventListener('click', startTenv);
$('#btn-bridge').addEventListener('click', toggleBridge);

// Native Liquid Glass buttons float over the HTML placeholders, which keep the layout.
async function setupNativeButtons() {
  const tauri = window.__TAURI__;
  if (!tauri || !(await tauri.core.invoke('native_buttons_available'))) return;

  const placeholders = [
    { tag: 1, el: $('#btn-start') },
    { tag: 2, el: $('#btn-stop') },
  ];
  document.body.classList.add('native-buttons');

  let pending = false;
  const sync = () => {
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => {
      pending = false;
      const rects = placeholders.map(({ tag, el }) => {
        const r = el.getBoundingClientRect();
        return { tag, x: r.left, y: r.top, w: r.width, h: r.height, visible: r.width > 0 && r.height > 0 };
      });
      tauri.core.invoke('layout_native_buttons', { rects });
    });
  };

  const observer = new ResizeObserver(sync);
  observer.observe($('#app'));
  observer.observe($('.dock'));
  window.addEventListener('resize', sync);
  sync();

  await tauri.event.listen('native-button', ({ payload }) => {
    placeholders.find((p) => p.tag === payload)?.el.click();
  });
}

setupNativeButtons().catch((e) => console.error('Native buttons unavailable:', e));

// Drawer toggle
const drawerToggle = $('#drawer-toggle');
const drawer = $('#drawer');
drawerToggle.addEventListener('click', () => {
  drawerToggle.classList.toggle('open');
  drawer.classList.toggle('open');
  syncMenu();
});

// Init
renderModels();
renderVersions();
connectWs();
