/**
 * PromptForge LD — top toggles · hero canvas · prompt I/O
 */
import { app } from "../../scripts/app.js";
import { buildResMaster, LTX_AR_PRESETS } from "./res_master.js";
import { buildImageCarousel } from "./image_carousel.js";

const HIDE = [
  "model_file", "mmproj_file", "video_mode", "environment", "scenario",
  "camera_move", "music", "pov", "pov_gender", "dialogue_tier", "intensity",
  "user_intent", "confirmed_prompt",
  "image_b64", "image_filename", "rm_w", "rm_h", "duration_s", "fps",
];

const LTX_SNAP = Object.fromEntries(
  LTX_AR_PRESETS.map(([, aw, ah, , sw, sh]) => [`${aw}:${ah}`, [sw, sh]])
);

const NO_IMAGE_NAME = "__NO_IMAGE__";

const GPL_BACKENDS = {
  MANAGED: "llama.cpp (managed)",
  LMSTUDIO: "LM Studio (OpenAI-compatible)",
  OLLAMA: "Ollama",
};
const GPL_DEFAULT_PORTS = {
  [GPL_BACKENDS.MANAGED]: "http://127.0.0.1:8080",
  [GPL_BACKENDS.LMSTUDIO]: "http://127.0.0.1:1234",
  [GPL_BACKENDS.OLLAMA]: "http://127.0.0.1:11434",
};

// === Layout constants (centralized — tune here, except dialogue chips which are untouched) ===
const LAYOUT = {
  rootPad: 12,
  minNodeW: 580,
  heroResBasis: 390,   // res controls side gets more room for visual balance + bigger AR presets
  heroStageW: 135,
  heroMinH: 210,
  floorMin: 680,
};

let _debugPad = null; // for the temp UI padding debug in cog
let _debugLayout = null; // layout sizes exposed in cog for live resize tweaks (no bars)

const THEMES = {
  default: {
    '--bg': '#07040e',
    '--text': '#f0ebff',
    '--muted': '#7d7394',
    '--gold': '#ffc857',
    '--cyan': '#5ce1e6',
    '--violet': '#a855f7',
  },
  midnight: {
    '--bg': '#040308',
    '--text': '#d8d0e8',
    '--muted': '#5a5270',
    '--gold': '#d8a850',
    '--cyan': '#48a8b4',
    '--violet': '#7a38c0',
  },
  terminal: {
    '--bg': '#081208',
    '--text': '#a8d0a8',
    '--muted': '#557055',
    '--gold': '#c8a060',
    '--cyan': '#48b868',
    '--violet': '#608060',
  },
  neon: {
    '--bg': '#080410',
    '--text': '#f0e8ff',
    '--muted': '#806890',
    '--gold': '#ffcc66',
    '--cyan': '#66f0ff',
    '--violet': '#cc66ff',
  },
  warm: {
    '--bg': '#110c08',
    '--text': '#f0e0c8',
    '--muted': '#7a6650',
    '--gold': '#ffaa44',
    '--cyan': '#908060',
    '--violet': '#b07050',
  }
};

function ensureStyles() {
  const ID = "pfld-styles";
  if (document.getElementById(ID)) return;
  const link = document.createElement("link");
  link.id = ID;
  link.rel = "stylesheet";
  try {
    // Works when the JS is loaded as ESM module (preferred)
    link.href = new URL("./prompt_forge.css", import.meta.url).href;
  } catch (_) {
    // Fallback for ComfyUI asset serving
    link.href = "/extensions/PromptForgeLD/js/prompt_forge.css";
  }
  document.head.appendChild(link);
}

function hideWidget(w) {
  if (!w) return;
  w.hidden = true;
  if (!w.options) w.options = {};
  w.options.hidden = true;
  w.computeSize = () => [0, 0];
  if (w.name === "image_b64") w.serializeValue = async () => "";
  else w.serializeValue = undefined;
  if (w.element) w.element.style.display = "none";
}

app.registerExtension({
  name: "LD.PromptForge",

  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "PromptForgeLD") return;
    const orig = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      if (orig) orig.apply(this, arguments);
      for (const w of this.widgets || []) {
        if (HIDE.includes(w.name)) hideWidget(w);
      }
    };
  },

  async nodeCreated(node) {
    if (node.comfyClass !== "PromptForgeLD") return;
    try {
    for (const w of node.widgets || []) hideWidget(w);

    node.color = "#120a1c";
    node.bgcolor = "#08050f";

    const gw = (n) => node.widgets?.find((w) => w.name === n);
    const sw = (n, v) => { const w = gw(n); if (w) w.value = v; };
    sw("image_b64", "");

    let imgPreviewUrl = null, imgW = 0, imgH = 0, imgFilename = "";
    const savedName = (gw("image_filename")?.value || "").trim();
    if (savedName) {
      imgFilename = savedName;
      imgW = 0;
      imgH = 0;
    }
    let draftPrompt = "", generating = false, abortCtrl = null;
    let povMode = localStorage.getItem("pfld_pov") || "off";
    let dlgTier = localStorage.getItem("pfld_dlg") || "standard";
    let rmW = 720, rmH = 1280, resScale = 1.0;
    let resMaster = null, imageCarousel = null;
    let videoMode = gw("video_mode")?.value || localStorage.getItem("pfld_video_mode") || "i2v";
    let llmBackend = localStorage.getItem("pfld_backend") || GPL_BACKENDS.MANAGED;
    let inputFolder = localStorage.getItem("pfld_input_folder") || "";
    let previewCache = { system: "", user_text: "" };

    const _FLOOR_MIN = LAYOUT.floorMin;
    let _floor = _FLOOR_MIN;

    const container = document.createElement("div");
    container.className = "gpl-root";

    if (!document.getElementById("gpl-fonts")) {
      const lf = document.createElement("link");
      lf.id = "gpl-fonts";
      lf.rel = "stylesheet";
      lf.href = "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Outfit:wght@400;600;700&display=swap";
      document.head.appendChild(lf);
    }

    ensureStyles();
    container.innerHTML = `
<!-- TOP: toggles + dropdowns -->
<div class="gpl-zone gpl-top">
  <div class="gpl-row-spread">
    <span class="gpl-title">✦ PromptForge LD</span>
    <span class="gpl-badge" id="gpl-live">—</span>
    <button type="button" class="gpl-cog" id="gpl-cog" title="LLM connection only">⚙</button>
  </div>
  <div class="gpl-row">
    <div class="gpl-tabs" id="gpl-mode-tabs">
      <button type="button" class="gpl-tab on" data-mode="i2v">I2V</button>
      <button type="button" class="gpl-tab" data-mode="t2v">T2V</button>
    </div>
  </div>
  <div class="gpl-chips">
    <div class="gpl-chipgrp" id="gpl-dlg">
      <button type="button" class="gpl-chip" data-v="none">Silent</button>
      <button type="button" class="gpl-chip on" data-v="standard">Standard</button>
      <button type="button" class="gpl-chip rose" data-v="talkative">Talkative</button>
    </div>
    <div class="gpl-chipgrp" id="gpl-pov">
      <button type="button" class="gpl-chip pov-off on" data-v="off">Off</button>
      <button type="button" class="gpl-chip pov-f" data-v="female">POV ♀</button>
      <button type="button" class="gpl-chip pov-m" data-v="male">POV ♂</button>
    </div>
  </div>
  <div class="gpl-fields">
    <div class="gpl-field"><label>Camera</label><select id="gpl-cam"></select></div>
    <div class="gpl-field">
      <label>Scenario</label>
      <select id="gpl-scn"></select>
      <button type="button" id="gpl-edit-scn" title="Edit current scenario" style="margin-left:4px;padding:2px 6px;font-size:11px;border-radius:4px;border:1px solid rgba(168,85,247,.4);background:rgba(168,85,247,.1);color:#a855f7;cursor:pointer;">✎</button>
    </div>
    <div class="gpl-field"><label>Environment</label><select id="gpl-env"></select></div>
  </div>
  <div class="gpl-field" style="margin: 4px 0;">
    <label>Music / Soundtrack</label>
    <select id="gpl-music"></select>
  </div>
  <div class="gpl-inline">
    <label>Intensity <input type="range" id="gpl-int" min="1" max="10" value="5"><span class="val" id="gpl-int-val">5 · medium</span></label>
  </div>
</div>

<!-- MIDDLE: image hero -->
<div class="gpl-zone gpl-mid" id="gpl-mid">
  <div id="gpl-res"></div>
  <div class="gpl-folder">
    <input id="gpl-folder-path" placeholder="Image folder (default: ComfyUI/input)" spellcheck="false">
    <button type="button" id="gpl-folder-apply">Apply</button>
  </div>
</div>

<!-- BOTTOM: intent → output -->
<div class="gpl-zone gpl-bot">
  <div>
    <div class="gpl-lbl" style="color:var(--gold)">Intent</div>
    <textarea class="gpl-prompt gpl-intent" id="gpl-intent" placeholder="What happens in this clip…"></textarea>
  </div>

  <div style="flex:1;display:flex;flex-direction:column">
    <div class="gpl-lbl" style="color:var(--violet)">LTX Script</div>
    <textarea class="gpl-prompt gpl-out" id="gpl-out" placeholder="Generate fills here…"></textarea>
    <div class="gpl-actions" style="margin-top:8px">
      <button type="button" class="gpl-btn-prev" id="gpl-preview" title="Show assembled LLM prompt before generate">Preview</button>
      <button type="button" class="gpl-btn-prev" id="gpl-copy" title="Copy LTX script">Copy</button>
      <button type="button" class="gpl-btn gpl-btn-gen" id="gpl-gen">Generate</button>
    </div>
    <div class="gpl-st" id="gpl-st"></div>
  </div>
</div>

<div class="gpl-cogpanel" id="gpl-cogpanel">
  <div class="clbl">LLM Server <span class="gpl-conn-dot" id="gpl-conn-dot"></span></div>
  <div class="gpl-be-row" id="gpl-backend-row">
    <button type="button" class="gpl-be-btn on" data-be="llama.cpp (managed)">🖥 Local<span class="gpl-be-sub">llama.cpp</span></button>
    <button type="button" class="gpl-be-btn" data-be="LM Studio (OpenAI-compatible)">🔌 LM Studio<span class="gpl-be-sub">connect</span></button>
    <button type="button" class="gpl-be-btn" data-be="Ollama">🦙 Ollama<span class="gpl-be-sub">connect</span></button>
  </div>
  <div class="gpl-cogrow"><input id="gpl-server-url" placeholder="http://127.0.0.1:8080"><button type="button" id="gpl-probe" title="Test connection">⟳</button></div>
  <div id="gpl-external-block" style="display:none">
    <div class="clbl">Model name <span style="opacity:.55;font-weight:400">(as server reports)</span></div>
    <input id="gpl-remote-model" placeholder="local">
    <div class="gpl-ext-note" id="gpl-conn-hint">Start LM Studio with a model loaded — this only connects (model name: local or exact id).</div>
  </div>
  <div id="gpl-managed-block">
    <div class="clbl">llama-server.exe</div>
    <input id="gpl-llama-exe" placeholder="C:\\llama\\llama-server.exe">
    <div class="clbl">Models folder</div>
    <div class="gpl-cogrow"><input id="gpl-models-dir" placeholder="C:\\models"><button type="button" id="gpl-scan" title="Scan folder">⟳</button></div>
    <div class="clbl">Model (GGUF)</div>
    <select id="gpl-model"></select>
    <div class="clbl">Vision mmproj</div>
    <select id="gpl-mm"></select>
  </div>
  <button type="button" class="gpl-cog-save" id="gpl-save-conn">Save connection &amp; models</button>
  <div class="clbl">Sampler temp</div>
  <input type="number" id="gpl-temp" min="0" max="1.5" step="0.05" value="0.55">

  <div class="clbl" style="margin-top:8px">Theme</div>
  <select id="gpl-theme">
    <option value="default">Default</option>
    <option value="midnight">Midnight</option>
    <option value="terminal">Terminal</option>
    <option value="neon">Neon</option>
    <option value="warm">Warm</option>
  </select>

  <div class="clbl" style="margin-top:12px;border-top:1px solid rgba(255,255,255,.12);padding-top:8px">Node Layout — sliders (live preview)</div>
  <div style="font:600 9px JetBrains Mono;color:#8a7fa8;margin:2px 0 3px">Insets to cyan border</div>

  <div class="gpl-inline" style="margin:1px 0"><label>T <span class="val" id="val-t">-7</span></label><input type="range" id="sl-t" min="-50" max="30" step="1" value="-7" style="flex:1;accent-color:#a855f7"></div>
  <div class="gpl-inline" style="margin:1px 0"><label>R <span class="val" id="val-r">17</span></label><input type="range" id="sl-r" min="-50" max="30" step="1" value="17" style="flex:1;accent-color:#a855f7"></div>
  <div class="gpl-inline" style="margin:1px 0"><label>B <span class="val" id="val-b">13</span></label><input type="range" id="sl-b" min="-50" max="30" step="1" value="13" style="flex:1;accent-color:#a855f7"></div>
  <div class="gpl-inline" style="margin:1px 0"><label>L <span class="val" id="val-l">-3</span></label><input type="range" id="sl-l" min="-50" max="30" step="1" value="-3" style="flex:1;accent-color:#a855f7"></div>

  <div style="font:600 9px JetBrains Mono;color:#8a7fa8;margin:6px 0 3px">Hero area</div>
  <div class="gpl-inline" style="margin:1px 0"><label>Basis <span class="val" id="val-basis">224</span></label><input type="range" id="sl-basis" min="160" max="520" step="4" value="224" style="flex:1;accent-color:#5ce1e6"></div>
  <div class="gpl-inline" style="margin:1px 0"><label>Stage <span class="val" id="val-stage">96</span></label><input type="range" id="sl-stage" min="60" max="220" step="2" value="96" style="flex:1;accent-color:#5ce1e6"></div>
  <div class="gpl-inline" style="margin:1px 0"><label>Height <span class="val" id="val-hero-h">196</span></label><input type="range" id="sl-hero-h" min="140" max="380" step="2" value="196" style="flex:1;accent-color:#5ce1e6"></div>
  <div class="gpl-inline" style="margin:1px 0"><label>Controls scale <span class="val" id="val-res-scale">1.0</span></label><input type="range" id="sl-res-scale" min="0.6" max="1.8" step="0.05" value="1.0" style="flex:1;accent-color:#5ce1e6"></div>

  <div style="font:600 9px JetBrains Mono;color:#8a7fa8;margin:6px 0 3px">BBox placement (offset)</div>
  <div class="gpl-inline" style="margin:1px 0"><label>X <span class="val" id="val-box-x">0</span></label><input type="range" id="sl-box-x" min="-80" max="80" step="1" value="0" style="flex:1;accent-color:#a855f7"></div>
  <div class="gpl-inline" style="margin:1px 0"><label>Y <span class="val" id="val-box-y">0</span></label><input type="range" id="sl-box-y" min="-80" max="80" step="1" value="0" style="flex:1;accent-color:#a855f7"></div>

  <div style="font:600 9px JetBrains Mono;color:#8a7fa8;margin:6px 0 3px">Typography</div>
  <div class="gpl-inline" style="margin:1px 0"><label>Text scale <span class="val" id="val-text-scale">1.0</span></label><input type="range" id="sl-text-scale" min="0.7" max="1.5" step="0.05" value="1.0" style="flex:1;accent-color:#f0ebff"></div>

  <div style="font:600 9px JetBrains Mono;color:#8a7fa8;margin:6px 0 3px">Overall</div>
  <div class="gpl-inline" style="margin:1px 0"><label>Content pad <span class="val" id="val-cpad">12</span></label><input type="range" id="sl-cpad" min="2" max="28" step="1" value="12" style="flex:1;accent-color:#ffc857"></div>
  <div class="gpl-inline" style="margin:1px 0"><label>Floor min <span class="val" id="val-floor">584</span></label><input type="range" id="sl-floor" min="520" max="980" step="4" value="584" style="flex:1;accent-color:#ffc857"></div>

  <div style="display:flex; gap:6px; margin-top:8px;">
    <button type="button" class="gpl-cog-save" id="gpl-save-layout" style="flex:1;font-size:11px;padding:7px">Save Layout</button>
    <button type="button" id="gpl-reset-layout" style="flex:0 0 auto;padding:7px 12px;font-size:11px;border-radius:6px;border:1px solid rgba(255,255,255,.15);background:rgba(0,0,0,.4);color:var(--muted);cursor:pointer">Reset</button>
  </div>
  <div class="gpl-ext-note" style="font-size:10px;margin-top:4px">Drag to preview live. Click Save when perfect. Persisted until Reset.</div>
</div>

<div class="gpl-preview" id="gpl-preview-modal">
  <div class="gpl-preview-box">
    <div class="gpl-preview-hdr">
      <span class="gpl-title" style="font-size:16px">Assembled LLM Prompt</span>
      <button type="button" class="gpl-preview-close" id="gpl-preview-close" title="Close">×</button>
    </div>
    <div class="gpl-preview-meta" id="gpl-preview-meta"></div>
    <div class="gpl-preview-tabs">
      <button type="button" class="gpl-preview-tab on" data-pane="system">System</button>
      <button type="button" class="gpl-preview-tab" data-pane="user">User</button>
    </div>
    <div class="gpl-preview-body">
      <textarea class="gpl-preview-ta" id="gpl-preview-ta" readonly spellcheck="false"></textarea>
    </div>
  </div>
</div>

<!-- Scenario Editor Modal -->
<div class="gpl-preview" id="gpl-scn-edit-modal" style="z-index: 500;">
  <div class="gpl-preview-box" style="max-width: 720px;">
    <div class="gpl-preview-hdr">
      <span class="gpl-title" style="font-size:16px">Edit Scenario</span>
      <button type="button" class="gpl-preview-close" id="gpl-scn-edit-close" title="Close">×</button>
    </div>
    <div style="margin: 8px 0 4px; font: 600 11px 'JetBrains Mono', monospace; color: var(--muted);">Key: <span id="gpl-scn-edit-key" style="color:var(--text);"></span></div>
    <div style="margin-bottom: 8px;">
      <div style="font: 600 11px 'JetBrains Mono', monospace; color: var(--muted); margin-bottom: 2px;">Setup</div>
      <textarea id="gpl-scn-edit-setup" style="width:100%; height: 70px; background:#0d0716; color:#f0ebff; border:1px solid #3a2a4a; border-radius:6px; padding:6px; font: 12px 'JetBrains Mono', monospace; resize: vertical;"></textarea>
    </div>
    <div>
      <div style="font: 600 11px 'JetBrains Mono', monospace; color: var(--muted); margin-bottom: 2px;">Choreography</div>
      <textarea id="gpl-scn-edit-choreo" style="width:100%; height: 160px; background:#0d0716; color:#f0ebff; border:1px solid #3a2a4a; border-radius:6px; padding:6px; font: 12px 'JetBrains Mono', monospace; resize: vertical;"></textarea>
    </div>
    <div style="display:flex; gap:8px; margin-top:10px;">
      <button type="button" id="gpl-scn-edit-save" class="gpl-cog-save" style="flex:1;">Save (persists to scenarios_ld.py)</button>
      <button type="button" id="gpl-scn-edit-cancel" style="flex:0 0 auto; padding:9px 14px; border-radius:7px; border:1px solid rgba(255,255,255,.15); background:rgba(0,0,0,.4); color:var(--muted); cursor:pointer;">Cancel</button>
    </div>
    <div style="font-size:10px; color:#8a7fa8; margin-top:6px;">Changes are saved directly to the .py file and hot-reloaded.</div>
  </div>
</div>
`;

    const uiWidget = node.addDOMWidget("pfld_ui", "div", container, { serialize: false });
    // Debug margins (from cog) control the inset from cyan node border. rootPad is base default only.
    if (uiWidget.element) {
      uiWidget.element.style.margin = "0";
      uiWidget.element.style.width = "100%";
      uiWidget.element.style.boxSizing = "border-box";
    }

    container.style.setProperty('--pfld-pad', LAYOUT.rootPad + 'px');
    container.style.setProperty('--res-hero-basis', LAYOUT.heroResBasis + 'px');
    container.style.setProperty('--res-stage-w', LAYOUT.heroStageW + 'px');
    container.style.setProperty('--hero-h', '210px');
    container.style.setProperty('--res-control-scale', '1');

    // Early sync apply of any saved debug layout (so first paint matches last tweak)
    // Current perfect defaults (from user screenshot): T=-7 R=17 B=13 L=-3 , hero 224/96/196 , pad 12, floor 584
    try {
      const pr = localStorage.getItem('pfld_debug_pad');
      const lr = localStorage.getItem('pfld_debug_layout');
      let p = null, d = null;
      if (pr) p = JSON.parse(pr);
      if (lr) d = JSON.parse(lr);

      if (p) {
        _debugPad = p;
        container.style.marginTop = `${p.t || -7}px`;
        container.style.marginRight = `${p.r || 17}px`;
        container.style.marginBottom = `${p.b || 13}px`;
        container.style.marginLeft = `${p.l || -3}px`;
        const nw = node.size?.[0] || 600;
        const cw = Math.max(180, nw - (p.l||0) - (p.r||0));
        container.style.width = `${cw}px`;
        container.style.maxWidth = `${cw}px`;
      } else {
        // No saved yet — use the perfect insets for first paint
        container.style.marginTop = `-7px`;
        container.style.marginRight = `17px`;
        container.style.marginBottom = `13px`;
        container.style.marginLeft = `-3px`;
        const nw = node.size?.[0] || 600;
        const cw = Math.max(180, nw - (-3) - 17);
        container.style.width = `${cw}px`;
        container.style.maxWidth = `${cw}px`;
      }

      if (d) {
        _debugLayout = d;
        const hb = d.heroResBasis || LAYOUT.heroResBasis;
        const sw = d.heroStageW || LAYOUT.heroStageW;
        const hh = d.heroH || 196;
        const cp = d.contentPad || 12;
        const bx = d.boxOffsetX || 0;
        const by = d.boxOffsetY || 0;
        container.style.setProperty('--res-hero-basis', `${hb}px`);
        container.style.setProperty('--res-stage-w', `${sw}px`);
        container.style.setProperty('--hero-h', `${hh}px`);
        container.style.padding = `${cp}px ${cp}px ${Math.round(cp * 1.33)}px ${cp}px`;
        if (d.floorMin) container.style.minHeight = `${d.floorMin}px`;
        LAYOUT.heroResBasis = hb;
        LAYOUT.heroStageW = sw;
        LAYOUT.heroMinH = hh;
        if (d.floorMin) LAYOUT.floorMin = d.floorMin;
      } else {
        container.style.setProperty('--res-hero-basis', `224px`);
        container.style.setProperty('--res-stage-w', `96px`);
        container.style.setProperty('--hero-h', `196px`);
        container.style.setProperty('--res-control-scale', `1`);
        container.style.setProperty('--text-scale', `1`);
        container.style.padding = `12px 12px 16px 12px`;
        container.style.minHeight = `584px`;
      }

      // Early theme
      const earlyTheme = localStorage.getItem('pfld_theme') || 'default';
      const et = THEMES[earlyTheme] || THEMES.default;
      Object.entries(et).forEach(([k, v]) => container.style.setProperty(k, v));
    } catch (e) {}

    const $ = (sel) => container.querySelector(sel);
    const setSt = (m) => { if ($("#gpl-st")) $("#gpl-st").textContent = m || ""; };

    // Use the actual node title (so it matches the ComfyUI node title / user-renamed title)
    const titleEl = container.querySelector(".gpl-title");
    if (titleEl) {
      titleEl.textContent = node.title || "✦ PromptForge LD";
      // Keep it in sync if the user renames the node later
      const origTitleChange = node.onTitleChange;
      node.onTitleChange = function (newTitle) {
        if (titleEl) titleEl.textContent = newTitle || "✦ PromptForge LD";
        if (origTitleChange) origTitleChange.call(this, newTitle);
      };
    }

    // Keyboard: Ctrl/Cmd+Enter triggers Generate (convenience, no impact on dialogue controls)
    container.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        const btn = $("#gpl-gen");
        if (btn) btn.click();
      }
    });

    function widgetTopOffset() {
      const y = uiWidget.last_y ?? uiWidget.y ?? 0;
      return (typeof y === "number" && y > 0 && y < 400) ? y : 0;
    }
    function nodeNeeded() { return _floor + widgetTopOffset() + 10; }
    function snapNodeHeight() {
      if (!node.size) return;
      const need = nodeNeeded();
      const dbgFloor = (_debugLayout && _debugLayout.floorMin != null) ? _debugLayout.floorMin : _FLOOR_MIN;
      // The workflow-saved / user-dragged height is authoritative. Early
      // measurements (before CSS + fonts settle) produce a spuriously large
      // floor, and the grow-only logic below made that inflation permanent
      // on every reload. Pin instead of growing.
      if (node._savedH) {
        if (Math.abs(node.size[1] - node._savedH) > 1) {
          node.setSize([node.size[0], node._savedH]);
        }
        return;
      }
      const hardMin = Math.max(need, dbgFloor);
      if (node.size[1] < hardMin) {
        node.setSize([node.size[0], hardMin]);
      } else if (node.size[1] > need + 28 && !node._userResized) {
        node.setSize([node.size[0], need]);
      }
    }
    function measureFloor() {
      const prev = container.style.height;
      container.style.height = "auto";
      const h = container.scrollHeight;
      container.style.height = prev;
      const effectiveFloor = (_debugLayout && _debugLayout.floorMin != null) ? _debugLayout.floorMin : _FLOOR_MIN;
      if (h > 50) _floor = Math.max(effectiveFloor, h + 6);
      snapNodeHeight();
    }
    function heroHeight() {
      const nw = node.size?.[0] || 600;
      // If user set explicit Hero Height slider, use it directly (this is what controls the visual area)
      if (_debugLayout && _debugLayout.heroH != null) return _debugLayout.heroH;
      const minH = (_debugLayout && _debugLayout.heroMinH != null) ? _debugLayout.heroMinH :
                   (LAYOUT.heroMinH != null ? LAYOUT.heroMinH : 210);
      // Slightly taller hero area now that res side has more allocation — still restrained.
      return Math.round(Math.min(300, Math.max(minH, nw * 0.37)));
    }
    function syncHeroScale() {
      const row = container.querySelector(".gpl-hero-row");
      if (!row) return;
      const hh = heroHeight();
      row.style.height = `${hh}px`;
    }
    function fitContainer() {
      syncHeroScale();
      const h = (node.size?.[1] || nodeNeeded()) - widgetTopOffset() - 10;
      container.style.height = Math.max(_floor - 6, h) + "px";
    }
    const scheduleLayout = () => requestAnimationFrame(() => {
      measureFloor();
      fitContainer();
      resMaster?.resync?.();
      imageCarousel?.resync?.();
      app.graph?.setDirtyCanvas(false, true);
    });

    uiWidget.computeSize = (w) => [Math.max(10, (node.size?.[0] || w || 600) - 4), _floor];
    node._userW = node._userW || 600;
    if (node.size && node.size[0] < LAYOUT.minNodeW) node.setSize([LAYOUT.minNodeW, node.size[1]]);
    node.onResize = (size) => {
      size[0] = Math.max(size[0], LAYOUT.minNodeW);
      node._userW = size[0];
      const dbgF = (_debugLayout && _debugLayout.floorMin != null) ? _debugLayout.floorMin : 0;
      size[1] = Math.max(size[1], nodeNeeded(), dbgF);
      node._userResized = size[1] > nodeNeeded() + 28;
      node._savedH = size[1]; // manual resize becomes the new sticky height
      fitContainer();
      resMaster?.resync?.();
      imageCarousel?.resync?.();
    };
    const pinW = () => {
      let sub = (LAYOUT.rootPad || 12) * 2;
      if (_debugPad) {
        sub = (_debugPad.l || 0) + (_debugPad.r || 0);
        // keep debug margins sticky (in case of external style resets)
        container.style.marginTop = `${_debugPad.t || 0}px`;
        container.style.marginRight = `${_debugPad.r || 0}px`;
        container.style.marginBottom = `${_debugPad.b || 0}px`;
        container.style.marginLeft = `${_debugPad.l || 0}px`;
      }
      const w = Math.max(10, (node.size?.[0] || 600) - sub);
      container.style.width = container.style.maxWidth = w + "px";
      node._wSync = requestAnimationFrame(pinW);
    };
    node._wSync = requestAnimationFrame(pinW);

    function isInputWired(n) { return node.inputs?.find((i) => i.name === n)?.link != null; }
    function getLinkedVal(n, fb) {
      const inp = node.inputs?.find((i) => i.name === n);
      if (inp?.link == null) return gw(n)?.value ?? fb;
      const resolve = (lid, d) => {
        if (!lid || d > 8) return null;
        const link = app.graph?.links?.[lid];
        const src = link && app.graph?.getNodeById(link.origin_id);
        if (!src) return null;
        for (const w of src.widgets || []) {
          const v = w.value;
          if (v != null && v !== "" && !isNaN(parseFloat(v))) return parseFloat(v);
        }
        for (const si of src.inputs || []) {
          if (si.link != null) { const u = resolve(si.link, d + 1); if (u != null) return u; }
        }
        return null;
      };
      const v = resolve(inp.link, 0);
      return v != null ? v : (gw(n)?.value ?? fb);
    }
    const getDur = () => parseFloat(getLinkedVal("duration_s", 12)) || 12;
    const getFps = () => parseInt(getLinkedVal("fps", 24), 10) || 24;

    function syncLive() {
      const el = $("#gpl-live");
      if (!el) return;
      const wired = isInputWired("duration_s") || isInputWired("fps");
      el.textContent = `${getDur().toFixed(1)}s · ${getFps()}fps`;
      el.classList.toggle("wired", wired);
      el.title = wired ? "Duration/fps wired from input nodes" : "Connect duration_s / fps inputs to override";
    }

    function applyRes(w, h, scale) {
      if (Number.isFinite(w) && w > 0) rmW = Math.round(w);
      if (Number.isFinite(h) && h > 0) rmH = Math.round(h);
      if (Number.isFinite(scale)) resScale = scale;
      sw("rm_w", rmW); sw("rm_h", rmH);
    }

    function fillSelect(sel, wn) {
      const w = gw(wn);
      if (!w?.options || !sel) return;
      sel.innerHTML = "";
      for (const o of w.options.values) {
        const opt = document.createElement("option");
        opt.value = o; opt.textContent = o;
        sel.appendChild(opt);
      }
      sel.value = w.value;
      sel.onchange = () => sw(wn, sel.value);
    }
    fillSelect($("#gpl-cam"), "camera_move");
    fillSelect($("#gpl-scn"), "scenario");
    fillSelect($("#gpl-env"), "environment");
    fillSelect($("#gpl-music"), "music");

    function savedModel() {
      return localStorage.getItem("pfld_model_file") || gw("model_file")?.value || "";
    }
    function savedMmproj() {
      return localStorage.getItem("pfld_mmproj_file") || gw("mmproj_file")?.value || "";
    }
    function syncModels() {
      const m = $("#gpl-model")?.value;
      const mm = $("#gpl-mm")?.value;
      if (m) { sw("model_file", m); localStorage.setItem("pfld_model_file", m); }
      if (mm) { sw("mmproj_file", mm); localStorage.setItem("pfld_mmproj_file", mm); }
    }
    function fillModels(gguf, mmproj) {
      const fill = (sel, list, prefer) => {
        if (!sel || !list) return;
        sel.innerHTML = "";
        const prev = prefer || sel.value;
        for (const o of list) {
          const opt = document.createElement("option");
          opt.value = o; opt.textContent = o;
          if (o === prev) opt.selected = true;
          sel.appendChild(opt);
        }
        if (prev && list.includes(prev)) sel.value = prev;
      };
      fill($("#gpl-model"), gguf, savedModel());
      fill($("#gpl-mm"), mmproj, savedMmproj());
      syncModels();
    }
    function paintBackend() {
      const managed = llmBackend === GPL_BACKENDS.MANAGED;
      $("#gpl-backend-row")?.querySelectorAll(".gpl-be-btn").forEach((b) => {
        b.classList.toggle("on", b.dataset.be === llmBackend);
      });
      const ext = $("#gpl-external-block");
      const man = $("#gpl-managed-block");
      if (ext) ext.style.display = managed ? "none" : "block";
      if (man) man.style.display = managed ? "block" : "none";
    }
    fillModels(gw("model_file")?.options?.values, gw("mmproj_file")?.options?.values);
    $("#gpl-model")?.addEventListener("change", syncModels);
    $("#gpl-mm")?.addEventListener("change", syncModels);

    function backendReady() {
      if (llmBackend === GPL_BACKENDS.MANAGED) {
        if (($("#gpl-model")?.value || "None") === "None") {
          setSt("Select a model first.");
          return false;
        }
      } else if (!($("#gpl-remote-model")?.value || "").trim()) {
        setSt("Enter the model name LM Studio reports (or local).");
        return false;
      }
      return true;
    }
    async function probeConn() {
      const hintEl = $("#gpl-conn-hint");
      try {
        const j = await (await fetch("/pfld/health")).json();
        $("#gpl-conn-dot")?.classList.toggle("ok", !!j.ok);
        if (hintEl) {
          hintEl.textContent = j.hint || (j.ok ? "Server reachable." : "Server not reachable — check URL.");
          hintEl.style.color = j.ok ? "var(--cyan)" : "#c96";
        }
        return j;
      } catch {
        $("#gpl-conn-dot")?.classList.remove("ok");
        if (hintEl) { hintEl.textContent = "Cannot reach /pfld/health"; hintEl.style.color = "#c96"; }
        return { ok: false };
      }
    }
    async function saveConn() {
      const body = {
        backend: llmBackend,
        server_url: $("#gpl-server-url")?.value?.trim(),
        remote_model: ($("#gpl-remote-model")?.value || "local").trim() || "local",
        models_dir: $("#gpl-models-dir")?.value?.trim(),
        llama_exe: $("#gpl-llama-exe")?.value?.trim(),
      };
      localStorage.setItem("pfld_backend", llmBackend);
      localStorage.setItem("pfld_server_url", body.server_url || "");
      localStorage.setItem("pfld_remote_model", body.remote_model);
      localStorage.setItem("pfld_models_dir", body.models_dir || "");
      localStorage.setItem("pfld_llama_exe", body.llama_exe || "");
      syncModels();
      try {
        await fetch("/pfld/set_backend", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      } catch { /* */ }
      return probeConn();
    }
    llmBackend = localStorage.getItem("pfld_backend") || GPL_BACKENDS.MANAGED;
    $("#gpl-server-url").value = localStorage.getItem("pfld_server_url") || GPL_DEFAULT_PORTS[llmBackend] || GPL_DEFAULT_PORTS[GPL_BACKENDS.MANAGED];
    $("#gpl-remote-model").value = localStorage.getItem("pfld_remote_model") || "local";
    $("#gpl-models-dir").value = localStorage.getItem("pfld_models_dir") || "C:\\models";
    $("#gpl-llama-exe").value = localStorage.getItem("pfld_llama_exe") || "C:\\llama\\llama-server.exe";
    paintBackend();
    saveConn();

    function showPreviewPane(pane) {
      $("#gpl-preview-modal")?.querySelectorAll(".gpl-preview-tab").forEach((t) => {
        t.classList.toggle("on", t.dataset.pane === pane);
      });
      const ta = $("#gpl-preview-ta");
      if (ta) ta.value = pane === "user" ? previewCache.user_text : previewCache.system;
    }
    function closePreview() { $("#gpl-preview-modal")?.classList.remove("open"); }
    $("#gpl-preview-close")?.addEventListener("click", closePreview);
    $("#gpl-preview-modal")?.addEventListener("click", (e) => {
      if (e.target?.id === "gpl-preview-modal") closePreview();
    });
    $("#gpl-preview-modal")?.querySelectorAll(".gpl-preview-tab").forEach((t) => {
      t.onclick = () => showPreviewPane(t.dataset.pane || "system");
    });

    // ── Scenario Editor (live edit next to dropdown) ────────────────────────────
    const scnEditModal = $("#gpl-scn-edit-modal");
    const scnEditKey = $("#gpl-scn-edit-key");
    const scnEditSetup = $("#gpl-scn-edit-setup");
    const scnEditChoreo = $("#gpl-scn-edit-choreo");

    function closeScnEdit() { scnEditModal?.classList.remove("open"); }

    $("#gpl-edit-scn")?.addEventListener("click", async () => {
      const sel = $("#gpl-scn");
      const key = sel?.value;
      if (!key || key.startsWith("None") || key === "🎲 Random — seed picks") {
        alert("Cannot edit sentinel entries (None / Random).");
        return;
      }
      try {
        const r = await fetch(`/pfld/get_scenario?key=${encodeURIComponent(key)}`);
        const j = await r.json();
        if (!j.ok) throw new Error(j.error || "failed");
        scnEditKey.textContent = key;
        scnEditSetup.value = j.setup || "";
        scnEditChoreo.value = j.choreography || "";
        scnEditModal?.classList.add("open");
      } catch (e) {
        alert("Failed to load scenario: " + e.message);
      }
    });

    $("#gpl-scn-edit-close")?.addEventListener("click", closeScnEdit);
    $("#gpl-scn-edit-cancel")?.addEventListener("click", closeScnEdit);
    scnEditModal?.addEventListener("click", (e) => {
      if (e.target?.id === "gpl-scn-edit-modal") closeScnEdit();
    });

    $("#gpl-scn-edit-save")?.addEventListener("click", async () => {
      const key = scnEditKey.textContent;
      if (!key) return;
      const setup = scnEditSetup.value;
      const choreo = scnEditChoreo.value;
      try {
        const r = await fetch("/pfld/save_scenario", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ key, setup, choreography: choreo })
        });
        const j = await r.json();
        if (!j.ok) throw new Error(j.error || "save failed");
        closeScnEdit();
        // Give a hint that it is live
        setSt("Scenario saved. Will be used on next Generate.");
        setTimeout(() => setSt(""), 1800);
      } catch (e) {
        alert("Save failed: " + e.message);
      }
    });

    function buildComposeBody() {
      return {
        model_file: llmBackend === GPL_BACKENDS.MANAGED ? (gw("model_file")?.value || "None") : "None",
        mmproj_file: llmBackend === GPL_BACKENDS.MANAGED ? (gw("mmproj_file")?.value || "None (text-only)") : "None (text-only)",
        video_mode: videoMode,
        duration_s: getDur(),
        fps: getFps(),
        dialogue_tier: dlgTier,
        intensity: parseInt($("#gpl-int").value, 10) || 6,
        user_intent: ($("#gpl-intent")?.value || "").trim(),
        image_b64: "",
        pov: povMode !== "off",
        pov_gender: povMode === "male" ? "male" : "female",
        environment: $("#gpl-env")?.value,
        scenario: $("#gpl-scn")?.value,
        camera_move: $("#gpl-cam")?.value,
        music: ($("#gpl-music")?.value || "").trim(),
      };
    }

    async function previewCompose() {
      const intent = ($("#gpl-intent")?.value || "").trim();
      if (!intent) { setSt("Write intent first."); return; }
      if (videoMode === "i2v" && !hasImage()) { setSt("I2V preview needs an image."); return; }
      setSt("Assembling preview…");
      const body = buildComposeBody();
      try {
        if (videoMode === "i2v") body.image_b64 = await visionB64ForCompose();
        const j = await (await fetch("/pfld/assemble_preview", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        })).json();
        if (!j.ok) throw new Error(j.error || "preview failed");
        previewCache = { system: j.system || "", user_text: j.user_text || "" };
        const meta = $("#gpl-preview-meta");
        if (meta) {
          meta.textContent = `system ${j.system_chars} chars · user ${j.user_chars} chars · max_tokens ${j.max_tokens} · explicit ${j.explicit}`;
        }
        showPreviewPane("system");
        $("#gpl-preview-modal")?.classList.add("open");
        setSt("Preview ready — Generate when happy.");
      } catch (e) {
        setSt("Preview error: " + e.message);
      }
    }
    $("#gpl-preview")?.addEventListener("click", previewCompose);

    // Copy LTX script (small convenient UX win)
    $("#gpl-copy")?.addEventListener("click", () => {
      const ta = $("#gpl-out");
      if (ta && ta.value && ta.value.trim()) {
        navigator.clipboard.writeText(ta.value.trim())
          .then(() => setSt("Copied to clipboard"))
          .catch(() => setSt("Copy failed (permissions?)"));
      } else {
        setSt("Nothing to copy yet.");
      }
    });

    $("#gpl-cog")?.addEventListener("click", (e) => { e.stopPropagation(); $("#gpl-cogpanel")?.classList.toggle("open"); probeConn(); });
    document.addEventListener("click", (e) => {
      const p = $("#gpl-cogpanel"), c = $("#gpl-cog");
      if (p?.classList.contains("open") && !p.contains(e.target) && !c?.contains(e.target)) p.classList.remove("open");
    });
    $("#gpl-backend-row")?.querySelectorAll(".gpl-be-btn").forEach((btn) => {
      btn.onclick = () => {
        llmBackend = btn.dataset.be || GPL_BACKENDS.MANAGED;
        const savedUrl = localStorage.getItem(`pfld_url_${llmBackend}`);
        const urlEl = $("#gpl-server-url");
        if (urlEl && (savedUrl || GPL_DEFAULT_PORTS[llmBackend])) {
          urlEl.value = savedUrl || GPL_DEFAULT_PORTS[llmBackend];
        }
        paintBackend();
        saveConn();
      };
    });
    $("#gpl-probe")?.addEventListener("click", saveConn);
    $("#gpl-save-conn")?.addEventListener("click", async () => {
      const prevUrl = $("#gpl-server-url")?.value?.trim();
      if (prevUrl) localStorage.setItem(`pfld_url_${llmBackend}`, prevUrl);
      await saveConn();
      setSt("Settings saved.");
    });
    $("#gpl-scan")?.addEventListener("click", async () => {
      await saveConn();
      try {
        const j = await (await fetch("/pfld/scan_models", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ models_dir: $("#gpl-models-dir")?.value }) })).json();
        if (j.ok) fillModels(j.gguf, j.mmproj);
      } catch { /* */ }
    });
    $("#gpl-remote-model")?.addEventListener("change", saveConn);
    ["gpl-server-url", "gpl-models-dir", "gpl-llama-exe"].forEach((id) => {
      $(`#${id}`)?.addEventListener("change", () => {
        const u = $("#gpl-server-url")?.value?.trim();
        if (u) localStorage.setItem(`pfld_url_${llmBackend}`, u);
        saveConn();
      });
    });
    $("#gpl-temp")?.addEventListener("input", () => { /* temp read at generate time */ });

    // === Node Layout debug via sliders in cog. Live preview on drag.
    // "Save Layout" persists to localStorage. Reset clears.
    // This makes widths + heights (hero area + overall floor) controllable.
    function applyDebug(save = false) {
      // Read current slider values (live)
      const t = parseInt($("#sl-t")?.value, 10) || -7;
      const r = parseInt($("#sl-r")?.value, 10) || 17;
      const b = parseInt($("#sl-b")?.value, 10) || 13;
      const l = parseInt($("#sl-l")?.value, 10) || -3;

      _debugPad = { t, r, b, l };

      // === Insets (margins around the dark panel to reach the cyan node border)
      container.style.marginTop = `${t}px`;
      container.style.marginRight = `${r}px`;
      container.style.marginBottom = `${b}px`;
      container.style.marginLeft = `${l}px`;

      const nodeW = node.size?.[0] || 600;
      const contentW = Math.max(180, nodeW - l - r);
      container.style.width = `${contentW}px`;
      container.style.maxWidth = `${contentW}px`;

      // === Hero area
      const heroBasis = parseInt($("#sl-basis")?.value, 10) || 224;
      const stageW = parseInt($("#sl-stage")?.value, 10) || 96;
      const heroH = parseInt($("#sl-hero-h")?.value, 10) || 196;

      // === BBox placement offsets (live nudge of the cyan box)
      const boxX = parseInt($("#sl-box-x")?.value, 10) || 0;
      const boxY = parseInt($("#sl-box-y")?.value, 10) || 0;

      // Text scale (only text, not layout sizes)
      const textScale = parseFloat($("#sl-text-scale")?.value) || 1.0;
      container.style.setProperty('--text-scale', textScale);

      // Specific scale for the left ResMaster panel's internal controls
      // (MP target slider + AR preset buttons) so they don't get dwarfed
      const resControlScale = parseFloat($("#sl-res-scale")?.value) || 1.0;
      container.style.setProperty('--res-control-scale', resControlScale);

      container.style.setProperty('--res-hero-basis', `${heroBasis}px`);
      container.style.setProperty('--res-stage-w', `${stageW}px`);
      container.style.setProperty('--hero-h', `${heroH}px`);

      // Force the hero row and the ResMaster hero containers (the 188px fixed is now var-driven + explicit)
      const row = container.querySelector('.gpl-hero-row');
      if (row) {
        row.style.height = `${heroH}px`;
        row.style.minHeight = `${heroH}px`;
      }
      container.querySelectorAll('.gpl-rm-hero, .gpl-rm-hero-stage').forEach((el) => {
        el.style.height = `${heroH}px`;
        el.style.minHeight = `${heroH}px`;
        el.style.maxHeight = `${heroH}px`;
      });
      // Help the mid zone breathe with the new hero height
      const midEl = container.querySelector('#gpl-mid');
      if (midEl) {
        midEl.style.minHeight = `${Math.max(180, heroH + 40)}px`;
      }

      // === Overall + internal content padding
      const cpad = parseInt($("#sl-cpad")?.value, 10) || 12;
      const floorMin = parseInt($("#sl-floor")?.value, 10) || 584;

      // Internal breathing room inside the dark box
      container.style.padding = `${cpad}px ${cpad}px ${Math.round(cpad * 1.33)}px ${cpad}px`;

      // Floor min controls overall node/widget height
      container.style.minHeight = `${floorMin}px`;

      _debugLayout = {
        heroResBasis: heroBasis,
        heroStageW: stageW,
        heroH,
        contentPad: cpad,
        floorMin,
        boxOffsetX: boxX,
        boxOffsetY: boxY,
        textScale,
        resControlScale
      };

      // Keep LAYOUT in sync for other code
      LAYOUT.heroResBasis = heroBasis;
      LAYOUT.heroStageW = stageW;
      LAYOUT.heroMinH = heroH;
      LAYOUT.floorMin = floorMin;

      if (save) {
        try {
          localStorage.setItem('pfld_debug_pad', JSON.stringify(_debugPad));
          localStorage.setItem('pfld_debug_layout', JSON.stringify(_debugLayout));
        } catch (e) {}
      }

      // Force everything to update + resync the bbox (critical for height changes)
      if (typeof scheduleLayout === 'function') {
        scheduleLayout();
      } else if (typeof fitContainer === 'function') {
        fitContainer();
      }
      resMaster?.resync?.();

      // Apply bbox offset if available (live move of the cyan resolution box)
      if (resMaster && typeof resMaster.setBoxOffset === 'function') {
        resMaster.setBoxOffset(boxX, boxY);
      }

      // Extra resync + size nudge for hero height + floor to take effect
      requestAnimationFrame(() => {
        resMaster?.resync?.();
        if (node && node.size) {
          const base = (typeof nodeNeeded === 'function') ? nodeNeeded() : 450;
          const targetH = Math.max(floorMin, base + Math.max(0, t) + Math.max(0, b));
          if (node.size[1] < targetH) {
            node.setSize([Math.max(node.size[0], LAYOUT.minNodeW || 580), targetH]);
            node._savedH = targetH; // sliders set the new authoritative height
          }
          if (typeof fitContainer === 'function') fitContainer();
        }
      });

      // Also keep pinW happy
      requestAnimationFrame(() => { /* pinW loop will maintain width/margins */ });
    }

    // Update a val badge next to slider + live preview (no save)
    function bindSlider(sliderId, valId) {
      const s = $(`#${sliderId}`);
      const v = $(`#${valId}`);
      if (!s) return;
      const handler = () => {
        if (v) v.textContent = s.value;
        applyDebug(false);   // live preview only
      };
      s.addEventListener('input', handler);
      // initialize val badge
      if (v) v.textContent = s.value;
    }

    // Bind all sliders for live preview
    bindSlider('sl-t', 'val-t');
    bindSlider('sl-r', 'val-r');
    bindSlider('sl-b', 'val-b');
    bindSlider('sl-l', 'val-l');
    bindSlider('sl-basis', 'val-basis');
    bindSlider('sl-stage', 'val-stage');
    bindSlider('sl-hero-h', 'val-hero-h');
    bindSlider('sl-res-scale', 'val-res-scale');
    bindSlider('sl-box-x', 'val-box-x');
    bindSlider('sl-box-y', 'val-box-y');
    bindSlider('sl-text-scale', 'val-text-scale');
    bindSlider('sl-cpad', 'val-cpad');
    bindSlider('sl-floor', 'val-floor');

    // Save = persist current slider values
    $("#gpl-save-layout")?.addEventListener("click", () => {
      applyDebug(true);
      const btn = $("#gpl-save-layout");
      if (btn) {
        const old = btn.textContent;
        btn.textContent = "Saved ✓";
        setTimeout(() => { if (btn) btn.textContent = old; }, 1200);
      }
    });

    $("#gpl-reset-layout")?.addEventListener("click", () => {
      try {
        localStorage.removeItem('pfld_debug_pad');
        localStorage.removeItem('pfld_debug_layout');
      } catch (e) {}

      // Reset sliders + badges to sensible defaults (current perfect from user screenshot)
      const defaults = { t:-7, r:17, b:13, l:-3, basis:224, stage:96, 'hero-h':196, 'res-scale':1.0, 'box-x':0, 'box-y':0, 'text-scale':1.0, cpad:12, floor:584 };
      Object.keys(defaults).forEach((k) => {
        const el = $(`#sl-${k}`);
        const vl = $(`#val-${k}`);
        if (el) el.value = defaults[k];
        if (vl) vl.textContent = defaults[k];
      });

      // Clear forced styles
      container.style.marginTop = container.style.marginRight = container.style.marginBottom = container.style.marginLeft = '';
      container.style.width = container.style.maxWidth = '';
      container.style.padding = '';
      container.style.minHeight = '';
      container.style.setProperty('--res-hero-basis', '390px');
      container.style.setProperty('--res-stage-w', '135px');
      container.style.setProperty('--hero-h', '210px');
      container.style.setProperty('--res-control-scale', '1');
      container.style.setProperty('--text-scale', '1');

      _debugPad = null;
      _debugLayout = null;
      node._savedH = null;      // release the height pin so layout can re-snap
      node._userResized = false;

      LAYOUT.heroResBasis = 390;
      LAYOUT.heroStageW = 135;
      LAYOUT.heroMinH = 210;
      LAYOUT.floorMin = 680;

      // Re-apply defaults visually (live)
      applyDebug(false);
      applyTheme('default', false);
      scheduleLayout?.();
    });

    // Theme handling (swap colors only, layout stays identical)
    function applyTheme(name, save = true) {
      const theme = THEMES[name] || THEMES.default;
      Object.entries(theme).forEach(([k, v]) => {
        container.style.setProperty(k, v);
      });
      const sel = $("#gpl-theme");
      if (sel) sel.value = name;
      if (save) {
        try { localStorage.setItem('pfld_theme', name); } catch (e) {}
      }
    }

    $("#gpl-theme")?.addEventListener("change", (e) => {
      applyTheme(e.target.value, true);
    });

    // Load saved sliders on startup (after DOM + a tick)
    setTimeout(() => {
      let pad = null, lay = null;
      try {
        const pr = localStorage.getItem('pfld_debug_pad');
        if (pr) pad = JSON.parse(pr);
        const lr = localStorage.getItem('pfld_debug_layout');
        if (lr) lay = JSON.parse(lr);
      } catch (e) {}

      if (pad) {
        if ($("#sl-t")) $("#sl-t").value = pad.t ?? -7;
        if ($("#sl-r")) $("#sl-r").value = pad.r ?? 17;
        if ($("#sl-b")) $("#sl-b").value = pad.b ?? 13;
        if ($("#sl-l")) $("#sl-l").value = pad.l ?? -3;
      }
      if (lay) {
        if ($("#sl-basis")) $("#sl-basis").value = lay.heroResBasis ?? 224;
        if ($("#sl-stage")) $("#sl-stage").value = lay.heroStageW ?? 96;
        if ($("#sl-hero-h")) $("#sl-hero-h").value = lay.heroH ?? 196;
        if ($("#sl-res-scale")) $("#sl-res-scale").value = lay.resControlScale ?? 1.0;
        if ($("#sl-box-x")) $("#sl-box-x").value = lay.boxOffsetX ?? 0;
        if ($("#sl-box-y")) $("#sl-box-y").value = lay.boxOffsetY ?? 0;
        if ($("#sl-text-scale")) $("#sl-text-scale").value = lay.textScale ?? 1.0;
        if ($("#sl-cpad")) $("#sl-cpad").value = lay.contentPad ?? 12;
        if ($("#sl-floor")) $("#sl-floor").value = lay.floorMin ?? 584;
      }

      // Refresh all val badges from current slider values
      ['t','r','b','l','basis','stage','hero-h','res-scale','box-x','box-y','text-scale','cpad','floor'].forEach((k) => {
        const s = $(`#sl-${k}`);
        const v = $(`#val-${k}`);
        if (s && v) v.textContent = s.value;
      });

      // Apply whatever is in the sliders now (live, no extra save)
      applyDebug(false);

      // Load saved theme
      const savedTheme = localStorage.getItem('pfld_theme') || 'default';
      applyTheme(savedTheme, false);
    }, 160);

    function bindChips(id, onPick) {
      $(`#${id}`)?.querySelectorAll(".gpl-chip").forEach((b) => {
        b.onclick = () => {
          $(`#${id}`).querySelectorAll(".gpl-chip").forEach((x) => x.classList.remove("on"));
          b.classList.add("on");
          onPick(b.dataset.v);
        };
      });
    }
    const setDlg = (t) => { dlgTier = t; localStorage.setItem("pfld_dlg", t); sw("dialogue_tier", t); };
    const paintPov = (m) => {
      const pov = m || "off";
      $("#gpl-pov")?.querySelectorAll(".gpl-chip").forEach((b) => {
        b.classList.toggle("on", b.dataset.v === pov);
      });
    };
    const setPov = (m) => {
      povMode = m;
      localStorage.setItem("pfld_pov", m);
      sw("pov", m !== "off");
      sw("pov_gender", m === "male" ? "male" : "female");
      paintPov(m);
    };
    bindChips("gpl-dlg", setDlg);
    bindChips("gpl-pov", setPov);
    setDlg(gw("dialogue_tier")?.value || dlgTier);
    setPov(povMode || "off");

    function setVideoMode(mode) {
      videoMode = mode === "t2v" ? "t2v" : "i2v";
      sw("video_mode", videoMode);
      localStorage.setItem("pfld_video_mode", videoMode);
      $("#gpl-mode-tabs")?.querySelectorAll(".gpl-tab").forEach((t) => {
        t.classList.toggle("on", t.dataset.mode === videoMode);
      });
      mountRes();
      scheduleLayout();
    }
    $("#gpl-mode-tabs")?.querySelectorAll(".gpl-tab").forEach((tab) => {
      tab.onclick = () => setVideoMode(tab.dataset.mode);
    });
    const intEl = $("#gpl-int");
    const energyLabel = (v) => v <= 3 ? "low" : v <= 7 ? "medium" : "high";
    const syncInt = () => { const v = parseInt(intEl?.value, 10) || 5; if ($("#gpl-int-val")) $("#gpl-int-val").textContent = `${v} · ${energyLabel(v)}`; sw("intensity", v); };
    intEl?.addEventListener("input", syncInt);
    syncInt();
    function downscaleDataUrl(src, maxSide) {
      return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
          const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
          const w = Math.max(1, Math.round(img.width * scale));
          const h = Math.max(1, Math.round(img.height * scale));
          const c = document.createElement("canvas");
          c.width = w; c.height = h;
          c.getContext("2d").drawImage(img, 0, 0, w, h);
          resolve(c.toDataURL("image/jpeg", 0.82));
        };
        img.onerror = () => resolve(src);
        img.src = src;
      });
    }

    function hasImage() { return !!(imgFilename || imgPreviewUrl); }

    function setImage(previewUrl, w, h, filename = "") {
      imgPreviewUrl = previewUrl || null;
      imgW = w || 0; imgH = h || 0; imgFilename = filename || "";

      // For manually loaded images (browse/drop), store the b64 so the node can use it in I2V
      // For gallery images we prefer filename (server side)
      if (previewUrl && previewUrl.startsWith('data:')) {
        sw("image_b64", previewUrl);
        sw("image_filename", "");   // clear filename so Python falls back to b64
      } else {
        sw("image_b64", "");
        sw("image_filename", imgFilename);
      }
      if (resMaster) {
        // Always pass the preview (data or thumb url) so the bbox stage can display it
        if (previewUrl && imgW) resMaster.setImage(imgW, imgH, previewUrl);
        else resMaster.clearImage();
        const st = resMaster.getState();
        applyRes(st.w, st.h, resScale);
      }

      // Carousel selection
      if (!imgFilename || imgFilename === NO_IMAGE_NAME) {
        imageCarousel?.setFocus(NO_IMAGE_NAME, false);
      } else if (imgFilename) {
        if (previewUrl && previewUrl.startsWith('data:')) {
          imageCarousel?.setCustomImage(imgFilename, previewUrl);
        } else {
          imageCarousel?.setFocus(imgFilename, false);
        }
      }
      scheduleLayout();
    }

    function loadFile(file) {
      if (!file?.type?.startsWith("image/")) return;
      const r = new FileReader();
      r.onload = async () => {
        const img = new Image();
        img.onload = async () => {
          const preview = await downscaleDataUrl(r.result, 480);
          setImage(preview, img.width, img.height, file.name || "");
        };
        img.src = r.result;
      };
      r.readAsDataURL(file);
    }
    function pickFile() {
      const inp = document.createElement("input");
      inp.type = "file"; inp.accept = "image/*";
      inp.onchange = () => { if (inp.files?.[0]) loadFile(inp.files[0]); };
      inp.click();
    }
    function pickFolder() {
      const p = prompt("Paste image folder path:", $("#gpl-folder-path")?.value || inputFolder || "");
      if (p != null && p.trim()) applyFolder(p.trim());
    }
    async function applyFolder(path) {
      inputFolder = path;
      localStorage.setItem("pfld_input_folder", path);
      if ($("#gpl-folder-path")) $("#gpl-folder-path").value = path;
      try {
        await fetch("/pfld/set_input_folder", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ path }) });
      } catch { /* */ }
      refreshGallery();
    }
    $("#gpl-folder-apply")?.addEventListener("click", () => applyFolder($("#gpl-folder-path")?.value?.trim() || ""));
    if (inputFolder) { $("#gpl-folder-path").value = inputFolder; applyFolder(inputFolder); }

    function thumbUrl(name, max = 360) {
      return `/pfld/thumb?name=${encodeURIComponent(name)}&max=${max}`;
    }

    async function loadGalleryImage(name) {
      if (name === NO_IMAGE_NAME) {
        setImage(null, 0, 0, "");
        return;
      }
      try {
        const info = await (await fetch(`/pfld/image_info?name=${encodeURIComponent(name)}`)).json();
        if (!info.ok) throw new Error("missing");
        setImage(thumbUrl(name, 480), info.w, info.h, name);
        imageCarousel?.setFocus(name, false);
      } catch { setSt("Could not load " + name); }
    }

    async function visionB64ForCompose() {
      if (imgFilename) {
        const j = await (await fetch(`/pfld/preview_b64?name=${encodeURIComponent(imgFilename)}&max=1024`)).json();
        if (j.ok && j.b64) return j.b64;
      }
      if (imgPreviewUrl) return downscaleDataUrl(imgPreviewUrl, 1024);
      return "";
    }
    async function refreshGallery() {
      try {
        const j = await (await fetch("/pfld/list_images?limit=40")).json();
        if (j.input_dir && $("#gpl-folder-path")) $("#gpl-folder-path").value = inputFolder || j.input_dir;
        if (j.input_dir && $("#gpl-folder-path") && !$("#gpl-folder-path").value) $("#gpl-folder-path").value = j.input_dir;

        let list = j.images || [];
        if (videoMode === "t2v") {
          // Always provide "No image" option at the **start and the end** of the carousel for T2V.
          // This is the default selection and always exists (independent of the pointed folder).
          // When selected, it tells ResMaster to output a custom-sized black frame
          // using the current resolution/bbox settings (no reference image used).
          list = list.filter(n => n !== NO_IMAGE_NAME);
          list = [NO_IMAGE_NAME, ...list, NO_IMAGE_NAME];
        }
        const current = imgFilename || (videoMode === "t2v" ? NO_IMAGE_NAME : "");
        imageCarousel?.setImages(list, current);
      } catch { /* gallery offline */ }
    }

    function mountRes() {
      if (resMaster) { try { resMaster.destroy(); } catch { /* */ } resMaster = null; }
      if (imageCarousel) { try { imageCarousel.destroy(); } catch { /* */ } imageCarousel = null; }
      const mount = $("#gpl-res");
      if (!mount) return;
      mount.innerHTML = "";
      const i2v = videoMode === "i2v";
      const mid = $("#gpl-mid");
      if (mid) {
        mid.classList.remove("gpl-mid-off");  // always show res area (T2V needs resolution master too)
        mid.style.display = "";
      }
      if (!i2v) {
        // T2V: resolution master + bbox for any shape black frame.
        // Image can be picked as reference (for native aspect / dims) but output is always black.
        const t2vRow = document.createElement("div");
        t2vRow.className = "gpl-hero-row";
        mount.appendChild(t2vRow);
        resMaster = buildResMaster({
          layout: "hero",
          mount: t2vRow,
          aspectLocked: false,
          lockAspectOnImage: false,  // T2V: ref image for starting aspect only; allow any bbox shape for black frame
          imageW: null,
          imageH: null,
          imageUrl: null,
          aspectW: 9,
          aspectH: 16,
          mp: (rmW * rmH) / (1024 * 1024) || 1,
          snapGrid: LTX_SNAP,
          arPresets: LTX_AR_PRESETS,
          gridUnit: 32,
          onPickImage: pickFile,
          onDropFile: loadFile,
          onOpenFolder: pickFolder,
          onClearImage: () => setImage(null, 0, 0),
          onChange: (st) => applyRes(st.w, st.h, 1),
          boxOffsetX: (_debugLayout && _debugLayout.boxOffsetX) || 0,
          boxOffsetY: (_debugLayout && _debugLayout.boxOffsetY) || 0,
        });
        // T2V gets the same image carousel as I2V — here a picked image is a
        // REFERENCE (sets starting aspect/dims); output is still a black frame.
        imageCarousel = buildImageCarousel({
          mount: t2vRow,
          viewUrl: (name) => thumbUrl(name, 360),
          onPickImage: pickFile,
          onOpenFolder: pickFolder,
          onDropFile: loadFile,
          onSelect: (name) => {
            if (name === NO_IMAGE_NAME) {
              setImage(null, 0, 0, "");
            } else {
              loadGalleryImage(name);
            }
          },
        });
        applyRes(resMaster.getState().w, resMaster.getState().h, 1);
        refreshGallery();

        // For T2V without a saved reference image, default to "No image"
        // (black frame at chosen resolution). User can still pick gallery/upload
        // images as optional reference for aspect.
        if (videoMode === "t2v" && !imgFilename) {
          sw("image_b64", "");
          sw("image_filename", "");
          if (resMaster) resMaster.clearImage();
        }

        scheduleLayout();
        return;
      }
      const row = document.createElement("div");
      row.className = "gpl-hero-row";
      mount.appendChild(row);
      resMaster = buildResMaster({
        layout: "hero",
        mount: row,
        aspectLocked: imgW > 0,
        imageW: imgW || null,
        imageH: imgH || null,
        imageUrl: imgPreviewUrl,
        aspectW: imgW || 9,
        aspectH: imgH || 16,
        mp: imgW && imgH ? (imgW * imgH) / (1024 * 1024) : 1,
        snapGrid: LTX_SNAP,
        arPresets: LTX_AR_PRESETS,
        gridUnit: 32,
        onPickImage: pickFile,
        onDropFile: loadFile,
        onOpenFolder: pickFolder,
        onClearImage: () => setImage(null, 0, 0),
        onChange: (st) => {
          const nmp = imgW && imgH ? (imgW * imgH) / (1024 * 1024) : null;
          applyRes(st.w, st.h, nmp ? st.mp / nmp : 1);
        },
        boxOffsetX: (_debugLayout && _debugLayout.boxOffsetX) || 0,
        boxOffsetY: (_debugLayout && _debugLayout.boxOffsetY) || 0,
      });
      imageCarousel = buildImageCarousel({
        mount: row,
        viewUrl: (name) => thumbUrl(name, 360),
        onPickImage: pickFile,
        onOpenFolder: pickFolder,
        onDropFile: loadFile,
        onSelect: (name) => loadGalleryImage(name),
      });
      applyRes(resMaster.getState().w, resMaster.getState().h, resScale);
      refreshGallery();
      scheduleLayout();
    }

    $("#gpl-intent")?.addEventListener("input", () => sw("user_intent", $("#gpl-intent").value.trim()));
    $("#gpl-out")?.addEventListener("input", () => {
      draftPrompt = $("#gpl-out").value;
      sw("confirmed_prompt", draftPrompt);
    });

    function commitOutput(text) {
      const t = (text || "").trim();
      sw("confirmed_prompt", t);
      return t;
    }

    async function compose() {
      if (generating) { abortCtrl?.abort(); return; }
      const intent = ($("#gpl-intent")?.value || "").trim();
      if (!intent) { setSt("Write intent first."); return; }
      if (!backendReady()) return;
      if (videoMode === "i2v" && !hasImage()) { setSt("I2V needs an image."); return; }

      // Instant visual acknowledgement — flip the button and show a pulsing
      // status the moment the click is validated, BEFORE the (slow) image
      // encode + saveConn run, so there's no dead 3s where nothing changes.
      generating = true;
      const btn = $("#gpl-gen");
      btn.textContent = "Stop";
      btn.classList.add("stop");
      setSt(videoMode === "i2v" ? "Preparing image…" : "Starting…");
      if ($("#gpl-st")) $("#gpl-st").classList.add("working");

      syncModels();
      await saveConn();
      sw("user_intent", intent);
      sw("image_b64", "");
      sw("scenario", $("#gpl-scn")?.value);
      sw("environment", $("#gpl-env")?.value);
      sw("camera_move", $("#gpl-cam")?.value);
      if (!isInputWired("duration_s")) sw("duration_s", getDur());
      if (resMaster) applyRes(resMaster.getState().w, resMaster.getState().h, resScale);

      abortCtrl = new AbortController();
      $("#gpl-out").value = "";
      let text = "";

      const body = {
        ...buildComposeBody(),
        refine: false,
        prior_prompt: "",
        user_intent: intent,
        temperature: parseFloat($("#gpl-temp")?.value) || 0.55,
      };

      try {
        setSt("Connecting…");
        body.image_b64 = videoMode === "i2v" ? await visionB64ForCompose() : "";
        if (videoMode === "i2v" && !body.image_b64) {
          generating = false;
          btn.textContent = "Generate";
          btn.classList.remove("stop");
          if ($("#gpl-st")) $("#gpl-st").classList.remove("working");
          setSt("I2V needs an image.");
          return;
        }
        const resp = await fetch("/pfld/generate_stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
          signal: abortCtrl.signal,
        });
        if (!resp.ok || !resp.body) {
          let msg = `HTTP ${resp.status}`;
          try {
            const j = await resp.json();
            if (typeof j.error === "string") msg = j.error;
            else if (j.error?.message) msg = j.error.message;
          } catch { /* stream may not be JSON */ }
          throw new Error(msg);
        }
        const reader = resp.body.getReader();
        const dec = new TextDecoder();
        let buf = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += dec.decode(value, { stream: true });
          let i;
          while ((i = buf.indexOf("\n\n")) >= 0) {
            const ln = buf.slice(0, i).trim();
            buf = buf.slice(i + 2);
            if (!ln.startsWith("data:")) continue;
            let ev;
            try { ev = JSON.parse(ln.slice(5)); } catch { continue; }
            if (ev.type === "status") setSt(ev.msg);
            else if (ev.type === "delta") {
              text += ev.text;
              $("#gpl-out").value = text;
              setSt(`${text.length} chars…`);
            }
            else if (ev.type === "error") throw new Error(ev.msg);
          }
        }
        draftPrompt = text.trim();
        $("#gpl-out").value = draftPrompt;
        const committed = commitOutput(draftPrompt);
        setSt(committed ? `✦ ${committed.length} chars → pack output` : "Empty.");
      } catch (e) {
        if (e.name !== "AbortError") setSt("Error: " + e.message);
        else setSt("Stopped.");
      } finally {
        generating = false;
        btn.textContent = "Generate";
        btn.classList.remove("stop");
        if ($("#gpl-st")) $("#gpl-st").classList.remove("working");
        scheduleLayout();
      }
    }

    $("#gpl-gen").onclick = compose;

    function restoreSession() {
      const cp = gw("confirmed_prompt")?.value;
      if (cp) { $("#gpl-out").value = cp; draftPrompt = cp; }
      const ui = gw("user_intent")?.value;
      if (ui) $("#gpl-intent").value = ui;
      const vm = gw("video_mode")?.value;
      if (vm) videoMode = vm;
      const fn = (gw("image_filename")?.value || "").trim();
      if (fn) imgFilename = fn;
      setVideoMode(videoMode);
      if (imgFilename && imgFilename !== NO_IMAGE_NAME) loadGalleryImage(imgFilename);
      syncLive();
    }
    restoreSession();

    // nodeCreated runs BEFORE ComfyUI restores widgets_values from the saved
    // workflow — hook onConfigure so the UI re-syncs after real values land.
    const _origConfigure = node.onConfigure;
    node.onConfigure = function (info) {
      _origConfigure?.apply(this, arguments);
      setTimeout(() => {
        restoreSession();
        // Honor the size saved in the workflow — stop auto-layout inflating it.
        const s = (info && info.size) || node.size;
        if (s && s[1] > 100) {
          node._userW = Math.max(s[0], LAYOUT.minNodeW);
          node._savedH = s[1];
          node._userResized = true;
          node.setSize([node._userW, s[1]]);
        }
        scheduleLayout();
      }, 0);
    };

    const tick = setInterval(() => {
      if (node._userW && node.size && node.size[0] < node._userW - 1) node.setSize([node._userW, node.size[1]]);
      syncLive();
      snapNodeHeight();
    }, 500);

    const origRemoved = node.onRemoved;
    node.onRemoved = function () {
      clearInterval(tick);
      if (resMaster) try { resMaster.destroy(); } catch { /* */ }
      if (node._wSync) cancelAnimationFrame(node._wSync);
      if (origRemoved) origRemoved.apply(this, arguments);
    };

    requestAnimationFrame(() => { measureFloor(); fitContainer(); });
    setTimeout(scheduleLayout, 400);
    } catch (err) {
      console.error("[PromptForgeLD] UI init failed:", err);
    }
  },
});