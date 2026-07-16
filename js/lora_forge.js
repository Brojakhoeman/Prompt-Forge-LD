/**
 * LoraForge LD — DOM-widget port of the LTX LoRA controller, styled to match PromptForge LD.
 *
 * Rewritten from the canvas version so it behaves like the PromptForge node:
 *   - real HTML/CSS UI (addDOMWidget) => native ComfyUI corner-resize works
 *   - LoRA picker is a searchable dropdown (type-to-filter, like the old loader)
 *   - STR / V× / A× render as "cup of water" level boxes:
 *       hover a box + scroll wheel  -> raises / lowers the fill (and the value)
 *       click a box                 -> type a value manually
 *   - Themes shared with PromptForge (themes_ld.js) — same names & hues
 */
import { app } from "../../../scripts/app.js";
import {
  THEME_KEYS,
  resolveTheme,
  loadSharedThemeKey,
  saveSharedThemeKey,
  applyComfyAccentVars,
  ensureComfyNativeShell,
  COMFY_DEFAULT_NODE_COLOR,
  COMFY_DEFAULT_NODE_BG,
} from "./themes_ld.js";

const THEME_ORDER = THEME_KEYS.slice();

/* ----------------------------------------------------------------- helpers */
const keyCache = {};
let LORA_LIST = null;          // cached list from the API
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const round2 = v => Math.round(v * 100) / 100;
const STEP = 0.05;
const RANGES = { str: [-2, 2], vs: [0, 2], as: [0, 2] };
const shortName = (lora) =>
  lora === "None" ? "None" : lora.split(/[\\/]/).pop().replace(/\.safetensors$/i, "");

/* ----------------------------------------------------------------- styles */
const STYLE_ID = "lfld-styles-v6";
function ensureStyles() {
  // Replace older injects so theme CSS updates after reload
  ["lfld-styles", "lfld-styles-v3", "lfld-styles-v4", "lfld-styles-v5"].forEach((id) => {
    const old = document.getElementById(id);
    if (old) old.remove();
  });
  if (document.getElementById(STYLE_ID)) return;
  const el = document.createElement("style");
  el.id = STYLE_ID;
  el.textContent = `
.lfld-root {
  --bg:#07040e; --panel:rgba(255,255,255,.03); --text:#f0ebff; --muted:#7d7394;
  --gold:#ffc857; --cyan:#5ce1e6; --violet:#a855f7; --line:rgba(255,255,255,.08);
  --str:#ffc857; --vc:#5ce1e6; --ac:#a855f7; --accent:#5ce1e6;
  --on-color:#5ce1e6;
  width:100%; box-sizing:border-box; display:flex; flex-direction:column; gap:8px;
  font-family:'Outfit',system-ui,sans-serif; color:var(--text);
  background:
    radial-gradient(120% 80% at 0% 0%, color-mix(in srgb, var(--accent) 14%, transparent), transparent 50%),
    radial-gradient(90% 60% at 100% 0%, color-mix(in srgb, var(--vc) 10%, transparent), transparent 45%),
    var(--bg);
  padding:12px; border-radius:10px;
  border:1px solid var(--line);
  transition: background .25s ease, color .2s ease, border-color .2s ease;
}
.lfld-head { display:flex; align-items:center; justify-content:space-between; gap:8px; flex-wrap:wrap; }
.lfld-tools { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }
.lfld-theme-btn, .lfld-native-btn {
  font:600 11px 'JetBrains Mono',monospace; color:var(--accent);
  padding:5px 12px; border-radius:99px; cursor:pointer; white-space:nowrap;
  background:color-mix(in srgb, var(--accent) 12%, transparent);
  border:1px solid color-mix(in srgb, var(--accent) 40%, transparent);
  user-select:none;
}
.lfld-native-btn.on {
  color:#e0e0e0;
  background:#3d3a4a;
  border-color:#6b6280;
}
.lfld-mini {
  width:26px; height:26px; border-radius:7px; cursor:pointer;
  font:700 15px 'JetBrains Mono',monospace; line-height:1;
  display:flex; align-items:center; justify-content:center;
  background:color-mix(in srgb, var(--accent) 12%, transparent);
  border:1px solid color-mix(in srgb, var(--accent) 40%, transparent);
  color:var(--accent);
}
.lfld-mini.rm { background:rgba(255,107,107,.12); border-color:rgba(255,107,107,.4); color:#ff8f8f; }
.lfld-mini:hover { filter:brightness(1.25); }

/* ── ComfyUI native look — match PromptForge shell accent (not blue) ── */
.lfld-root.lfld-comfy-native {
  --bg:#1a1a1a; --panel:#252525; --text:#ececec; --muted:#a8a8a8;
  --gold:#7c6bb0; --cyan:#7c6bb0; --violet:#7c6bb0; --rose:#7c6bb0; --mint:#7c6bb0;
  --line:rgba(255,255,255,.14);
  --str:#7c6bb0; --vc:#7c6bb0; --ac:#7c6bb0; --accent:#7c6bb0; --on-color:#7c6bb0;
  --comfy-accent:#7c6bb0; --comfy-on:#7c6bb0; --comfy-off:#f07178;
  font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif !important;
  background:#1a1a1a !important;
  border:1px solid color-mix(in srgb, var(--violet, #7c6bb0) 55%, #3a3a3a) !important;
  border-radius:4px !important;
  box-shadow:inset 0 2px 0 0 color-mix(in srgb, var(--violet, #7c6bb0) 70%, transparent) !important;
}
.lfld-root.lfld-comfy-native .lfld-title {
  background:none !important; -webkit-background-clip:unset !important; background-clip:unset !important;
  color:color-mix(in srgb, var(--violet, #7c6bb0) 55%, #e8e8e8) !important; filter:none !important;
  font:600 16px system-ui,sans-serif !important;
}
/* Idle chrome = same grey as PF chips */
.lfld-root.lfld-comfy-native .lfld-theme-btn,
.lfld-root.lfld-comfy-native .lfld-native-btn,
.lfld-root.lfld-comfy-native .lfld-mini,
.lfld-root.lfld-comfy-native .lfld-on,
.lfld-root.lfld-comfy-native .lfld-pick-btn {
  font-family:system-ui,sans-serif !important;
  border-radius:3px !important;
  background:#333 !important;
  border:1px solid #4a4a4a !important;
  color:#ccc !important;
  box-shadow:none !important;
}
/* Selected / active = same purple mix as PF .gpl-chip.on */
.lfld-root.lfld-comfy-native .lfld-native-btn.on,
.lfld-root.lfld-comfy-native .lfld-on.on,
.lfld-root.lfld-comfy-native .lfld-mini {
  background:color-mix(in srgb, var(--violet, #7c6bb0) 58%, #222) !important;
  border-color:var(--violet, #7c6bb0) !important;
  color:#f5f2ff !important;
  box-shadow:none !important;
}
.lfld-root.lfld-comfy-native .lfld-theme-btn { opacity:0.4; pointer-events:none; }
/* OFF / remove stay red so disabled ≠ selected */
.lfld-root.lfld-comfy-native .lfld-on.off {
  color:#ffd0d0 !important;
  background:color-mix(in srgb, var(--comfy-off, #f07178) 28%, #1e1e1e) !important;
  border-color:var(--comfy-off, #f07178) !important;
  box-shadow:none !important;
}
.lfld-root.lfld-comfy-native .lfld-mini.rm {
  color:#ffd0d0 !important;
  border-color:var(--comfy-off, #f07178) !important;
  background:color-mix(in srgb, var(--comfy-off, #f07178) 28%, #1e1e1e) !important;
}
/* Row = same panel tint as PF Shot/Scene/Voice */
.lfld-root.lfld-comfy-native .lfld-row {
  background:color-mix(in srgb, var(--violet, #7c6bb0) 10%, #252525) !important;
  border:1px solid color-mix(in srgb, var(--violet, #7c6bb0) 38%, #3a3a3a) !important;
  border-radius:3px !important;
  color:#e8e8e8 !important;
}
.lfld-root.lfld-comfy-native .lfld-pick-btn {
  background:#1a1a1a !important;
  border-color:color-mix(in srgb, var(--violet, #7c6bb0) 28%, #444) !important;
  color:#e8e8e8 !important;
}
.lfld-root.lfld-comfy-native .lfld-menu {
  background:#252525 !important;
  border:1px solid color-mix(in srgb, var(--violet, #7c6bb0) 38%, #3a3a3a) !important;
}
.lfld-root.lfld-comfy-native .lfld-menu-search {
  background:#1a1a1a !important; color:#ddd !important; font-family:system-ui,sans-serif !important;
}
.lfld-root.lfld-comfy-native .lfld-menu-item:hover,
.lfld-root.lfld-comfy-native .lfld-menu-item.active {
  background:color-mix(in srgb, var(--violet, #7c6bb0) 48%, #2a2a2a) !important; color:#f5f2ff !important;
}
.lfld-root.lfld-comfy-native .lfld-cup {
  border-color:color-mix(in srgb, var(--violet, #7c6bb0) 30%, #555) !important;
  background:#1a1a1a !important;
}
.lfld-root.lfld-comfy-native .lfld-keys { color:#888 !important; font-family:system-ui,sans-serif !important; }
.lfld-root.lfld-comfy-native .lfld-keys .kv,
.lfld-root.lfld-comfy-native .lfld-keys .ka {
  color:color-mix(in srgb, var(--violet, #7c6bb0) 40%, #aaa) !important;
}

.lfld-rows { display:flex; flex-direction:column; gap:6px; }
.lfld-row {
  display:grid;
  grid-template-columns:52px 1fr 70px 58px 58px 44px;
  gap:6px; align-items:center;
  background:var(--panel); border:1px solid var(--line);
  border-radius:8px; padding:6px;
  transition: border-color .2s ease, background .2s ease;
}
.lfld-title {
  font:700 20px 'Outfit',sans-serif;
  background: linear-gradient(90deg, var(--accent), var(--vc));
  -webkit-background-clip: text; background-clip: text;
  color: transparent;
  filter: drop-shadow(0 0 12px color-mix(in srgb, var(--accent) 35%, transparent));
}
.lfld-on {
  font:700 10px 'JetBrains Mono',monospace; letter-spacing:.04em;
  border:none; border-radius:6px; padding:8px 0; cursor:pointer; text-align:center;
  background:rgba(0,0,0,.3);
}
.lfld-on.on  { color:var(--on-color, var(--cyan)); box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--on-color,var(--cyan)) 45%,transparent); }
.lfld-on.off { color:#ff6b6b; box-shadow:inset 0 0 0 1px rgba(255,107,107,.4); }

.lfld-pick { position:relative; min-width:0; }
.lfld-pick-btn {
  width:100%; box-sizing:border-box; text-align:left; cursor:pointer;
  background:rgba(0,0,0,.3); border:1px solid var(--line); border-radius:6px;
  color:var(--text); padding:8px 10px; font:600 12px 'Outfit',sans-serif;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
.lfld-pick-btn.empty { color:var(--muted); }
.lfld-pick-btn:hover { border-color:color-mix(in srgb,var(--accent) 50%,transparent); }

.lfld-menu {
  position:absolute; top:calc(100% + 4px); left:0; z-index:9999;
  width:min(420px,60vw); background:#0d0716; border:1px solid var(--line);
  border-radius:8px; box-shadow:0 12px 40px rgba(0,0,0,.6); overflow:hidden; display:none;
}
.lfld-menu.open { display:block; }
.lfld-menu-search {
  width:100%; box-sizing:border-box; background:#120a1c; color:var(--accent);
  border:none; border-bottom:1px solid var(--line);
  padding:9px 12px; font:600 12px 'JetBrains Mono',monospace; outline:none;
}
.lfld-menu-search::placeholder { color:var(--muted); }
.lfld-menu-list { max-height:280px; overflow-y:auto; }
.lfld-menu-item {
  padding:8px 12px; cursor:pointer; font:500 12px 'Outfit',sans-serif;
  color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
.lfld-menu-item:hover, .lfld-menu-item.active { background:color-mix(in srgb,var(--accent) 18%,transparent); color:#fff; }
.lfld-menu-item.none { color:var(--muted); font-style:italic; }
.lfld-menu-list::-webkit-scrollbar { width:8px; }
.lfld-menu-list::-webkit-scrollbar-thumb { background:rgba(255,255,255,.14); border-radius:8px; }

.lfld-cup {
  position:relative; height:38px; border-radius:6px; cursor:ns-resize;
  overflow:hidden; user-select:none; background:rgba(0,0,0,.35);
  border:1px solid color-mix(in srgb, var(--cup) 45%, transparent);
}
.lfld-cup-fill {
  position:absolute; left:0; right:0; bottom:0;
  background:color-mix(in srgb, var(--cup) 32%, transparent);
  border-top:1px solid color-mix(in srgb, var(--cup) 85%, transparent);
  transition:height .06s linear; pointer-events:none;
}
.lfld-cup-lbl {
  position:absolute; top:3px; left:5px; z-index:2; pointer-events:none;
  font:700 7px 'JetBrains Mono',monospace; letter-spacing:.06em; color:var(--cup); opacity:.9;
}
.lfld-cup-val {
  position:absolute; left:0; right:0; bottom:3px; z-index:2; text-align:center; pointer-events:none;
  font:700 12px 'JetBrains Mono',monospace; color:var(--cup); text-shadow:0 1px 3px rgba(0,0,0,.8);
}
.lfld-cup.zero { opacity:.55; }
.lfld-cup-input {
  position:absolute; inset:0; z-index:5; width:100%; box-sizing:border-box;
  background:#0d0716; border:1px solid var(--cup); border-radius:6px;
  color:var(--cup); text-align:center; font:700 13px 'JetBrains Mono',monospace; outline:none; display:none;
}
.lfld-cup-input.show { display:block; }

.lfld-keys { font:600 8px 'JetBrains Mono',monospace; line-height:1.35; text-align:right; color:var(--muted); overflow:hidden; }
.lfld-keys .kv { color:color-mix(in srgb,var(--vc) 80%,#fff); }
.lfld-keys .ka { color:color-mix(in srgb,var(--ac) 80%,#fff); }
`;
  document.head.appendChild(el);
}

/* ----------------------------------------------------------------- extension */
app.registerExtension({
  name: "LoraForge.LTX2.DOM",

  // capture the hidden lora list as a fallback
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData.name !== "LoraForgeLD") return;
    try {
      const h = nodeData?.input?.hidden?.available_loras?.[0];
      if (Array.isArray(h) && h.length && !LORA_LIST) LORA_LIST = h.slice();
    } catch {}
  },

  async nodeCreated(node) {
    if (node.comfyClass !== "LoraForgeLD") return;
    ensureStyles();

    // Drop experimental sockets (trigger_words / loaded_keys_info) left from older builds
    // Current Python only returns model + clip.
    const stripExtraOutputs = () => {
      if (!node.outputs?.length) return;
      for (let i = node.outputs.length - 1; i >= 0; i--) {
        const n = String(node.outputs[i]?.name || "").toLowerCase();
        if (n === "model" || n === "clip") continue;
        try {
          // Prefer LiteGraph API if present
          if (typeof node.removeOutput === "function") node.removeOutput(i);
          else node.outputs.splice(i, 1);
        } catch {
          try { node.outputs.splice(i, 1); } catch { /* */ }
        }
      }
      try { node.setDirtyCanvas?.(true, true); } catch { /* */ }
    };
    stripExtraOutputs();
    // Again after configure (workflow restore can re-add ghost links)
    setTimeout(stripExtraOutputs, 0);
    setTimeout(stripExtraOutputs, 200);

    node.properties = node.properties || {};
    // Prefer shared PromptForge theme; map legacy a/b/c via resolveTheme
    if (!node.properties.theme) {
      node.properties.theme = loadSharedThemeKey();
    } else {
      node.properties.theme = resolveTheme(node.properties.theme).id;
    }
    let comfyNative = localStorage.getItem("pfld_comfy_native") === "1";
    let _lfColorWatch = null;
    let _lfLastColorKey = "";
    {
      if (comfyNative) {
        ensureComfyNativeShell(node);
      } else {
        const { theme: bootT } = resolveTheme(node.properties.theme);
        if (bootT.node) {
          node.color = bootT.node.color;
          node.bgcolor = bootT.node.bgcolor;
        }
      }
    }
    if (!node.properties.stack_data) {
      node.properties.stack_data = JSON.stringify([{ on: true, lora: "None", str: 1.0, vs: 1.0, as: 1.0 }]);
    }

    const gw = (n) => node.widgets?.find((w) => w.name === n);
    let dataWidget = gw("stack_data");
    if (!dataWidget) dataWidget = node.addWidget("text", "stack_data", node.properties.stack_data, () => {});
    dataWidget.value = node.properties.stack_data;
    dataWidget.computeSize = () => [0, -4];
    dataWidget.draw = () => {};

    if (!document.getElementById("lfld-fonts")) {
      const lf = document.createElement("link");
      lf.id = "lfld-fonts";
      lf.rel = "stylesheet";
      lf.href = "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Outfit:wght@400;600;700&display=swap";
      document.head.appendChild(lf);
    }

    /* ---------- data helpers */
    const getData = () => {
      try { return JSON.parse(node.properties.stack_data); }
      catch { return [{ on: true, lora: "None", str: 1.0, vs: 1.0, as: 1.0 }]; }
    };
    const commit = (data) => {
      node.properties.stack_data = JSON.stringify(data);
      dataWidget.value = node.properties.stack_data;
      node.setDirtyCanvas(true, true);
    };

    /* ---------- lora list (API first, hidden-input fallback) */
    const ensureLoras = () => {
      if (LORA_LIST) return;
      LORA_LIST = ["None"];
      fetch("/pfld/lora_list")
        .then(r => r.json())
        .then(d => { if (Array.isArray(d.loras) && d.loras.length) { LORA_LIST = d.loras; } })
        .catch(() => {});
    };
    ensureLoras();
    const loraList = () => LORA_LIST || ["None"];

    /* ---------- container */
    const container = document.createElement("div");
    container.className = "lfld-root";

    const syncLfComfyAccents = () => {
      if (!comfyNative) return;
      const c = node.color || COMFY_DEFAULT_NODE_COLOR;
      const bg = node.bgcolor || COMFY_DEFAULT_NODE_BG;
      const key = `${c}|${bg}`;
      if (key === _lfLastColorKey) return;
      _lfLastColorKey = key;
      applyComfyAccentVars(container, c, bg);
    };
    const startLfColorWatch = () => {
      stopLfColorWatch();
      syncLfComfyAccents();
      _lfColorWatch = setInterval(syncLfComfyAccents, 250);
    };
    const stopLfColorWatch = () => {
      if (_lfColorWatch) { clearInterval(_lfColorWatch); _lfColorWatch = null; }
      _lfLastColorKey = "";
    };

    const applyThemeVars = () => {
      container.classList.toggle("lfld-comfy-native", comfyNative);
      if (comfyNative) {
        // Follow Comfy colour dots; near-black theme leftovers → default purple
        try {
          ensureComfyNativeShell(node);
        } catch { /* */ }
        _lfLastColorKey = ""; // force accent re-apply
        syncLfComfyAccents();
        startLfColorWatch();
        return;
      }
      stopLfColorWatch();
      const { id, theme } = resolveTheme(node.properties.theme);
      node.properties.theme = id;
      const t = theme.lf;
      container.style.setProperty("--str", t.str);
      container.style.setProperty("--vc", t.v);
      container.style.setProperty("--ac", t.a);
      container.style.setProperty("--accent", t.accent);
      container.style.setProperty("--on-color", t.on);
      container.style.setProperty("--bg", t.bg);
      container.style.setProperty("--panel", t.panel);
      container.style.setProperty("--text", t.text);
      container.style.setProperty("--muted", t.muted);
      container.style.setProperty("--line", t.line);
      container.style.setProperty("--gold", t.str);
      container.style.setProperty("--cyan", t.v);
      container.style.setProperty("--violet", t.a);
      if (theme.node) {
        node.color = theme.node.color;
        node.bgcolor = theme.node.bgcolor;
      }
    };

    const setComfyNative = (on, save = true) => {
      comfyNative = !!on;
      if (save) {
        try { localStorage.setItem("pfld_comfy_native", comfyNative ? "1" : "0"); } catch { /* */ }
        try {
          window.dispatchEvent(new CustomEvent("pfld-comfy-native", { detail: { on: comfyNative } }));
        } catch { /* */ }
      }
      build();
      try { node.setDirtyCanvas(true, true); } catch { /* */ }
    };

    // Stay in sync when PromptForge toggles native look (same tab + other tabs)
    window.addEventListener("storage", (e) => {
      if (e.key === "pfld_comfy_native") {
        comfyNative = e.newValue === "1";
        build();
      }
      if (e.key === "pfld_theme" && e.newValue && !comfyNative) {
        node.properties.theme = e.newValue;
        build();
      }
    });
    window.addEventListener("pfld-comfy-native", (e) => {
      const on = !!(e?.detail?.on);
      if (on === comfyNative) return;
      comfyNative = on;
      build();
    });

    const build = () => {
      const { id, theme } = resolveTheme(node.properties.theme);
      node.properties.theme = id;
      const t = theme;
      const data = getData();
      applyThemeVars();

      container.innerHTML = `
<div class="lfld-head">
  <span class="lfld-title">✦ LoraForge LD</span>
  <div class="lfld-tools">
    <div class="lfld-native-btn${comfyNative ? " on" : ""}" id="lfld-native" title="Stock Comfy dark widgets — same toggle as PromptForge">Comfy native${comfyNative ? " ✓" : ""}</div>
    <div class="lfld-theme-btn" id="lfld-theme" title="Cycle theme (matches PromptForge; off while Comfy native)">THEME: ${t.name}</div>
    <div class="lfld-mini" id="lfld-add" title="Add slot">+</div>
    ${data.length > 1 ? `<div class="lfld-mini rm" id="lfld-del" title="Remove last slot">−</div>` : ""}
  </div>
</div>
<div class="lfld-rows" id="lfld-rows"></div>`;

      const rowsEl = container.querySelector("#lfld-rows");

      data.forEach((row, i) => {
        const rowEl = document.createElement("div");
        rowEl.className = "lfld-row";

        const onBtn = document.createElement("div");
        onBtn.className = "lfld-on " + (row.on ? "on" : "off");
        onBtn.textContent = row.on ? "✔ ON" : "✖ OFF";
        onBtn.onclick = () => { const d = getData(); d[i].on = !d[i].on; commit(d); build(); };
        rowEl.appendChild(onBtn);

        rowEl.appendChild(makePicker(i, row));
        rowEl.appendChild(makeCup(i, "str", "STR", row.str ?? 1.0, "var(--str)"));
        rowEl.appendChild(makeCup(i, "vs", "V×", row.vs ?? 1.0, "var(--vc)"));
        rowEl.appendChild(makeCup(i, "as", "A×", row.as ?? 1.0, "var(--ac)"));

        const keys = document.createElement("div");
        keys.className = "lfld-keys";
        if (row.lora !== "None") {
          const c = keyCache[row.lora];
          if (c) keys.innerHTML = `<div class="kv">V:${c.v}</div><div class="ka">A:${c.a}</div>`;
          else { keys.innerHTML = `<div>…</div>`; fetchKeys(row.lora); }
        }
        rowEl.appendChild(keys);

        rowsEl.appendChild(rowEl);
      });

      container.querySelector("#lfld-native").onclick = () => {
        setComfyNative(!comfyNative, true);
      };
      container.querySelector("#lfld-theme").onclick = () => {
        if (comfyNative) return; // disabled in native mode
        const cur = resolveTheme(node.properties.theme).id;
        const idx = Math.max(0, THEME_ORDER.indexOf(cur));
        const next = THEME_ORDER[(idx + 1) % THEME_ORDER.length];
        node.properties.theme = next;
        saveSharedThemeKey(next);
        build();
        try { node.setDirtyCanvas(true, true); } catch { /* */ }
      };
      container.querySelector("#lfld-add").onclick = () => {
        const d = getData(); d.push({ on: true, lora: "None", str: 1.0, vs: 1.0, as: 1.0 });
        commit(d); build(); relayout();
      };
      const del = container.querySelector("#lfld-del");
      if (del) del.onclick = () => { const d = getData(); if (d.length > 1) d.pop(); commit(d); build(); relayout(); };
    };

    /* ---------- searchable LoRA picker */
    function makePicker(i, row) {
      const wrap = document.createElement("div");
      wrap.className = "lfld-pick";

      const btn = document.createElement("div");
      btn.className = "lfld-pick-btn" + (row.lora === "None" ? " empty" : "");
      btn.textContent = shortName(row.lora);
      btn.title = row.lora;
      wrap.appendChild(btn);

      const menu = document.createElement("div");
      menu.className = "lfld-menu";
      const search = document.createElement("input");
      search.className = "lfld-menu-search";
      search.placeholder = "Search LoRAs…";
      search.spellcheck = false;
      const list = document.createElement("div");
      list.className = "lfld-menu-list";
      menu.appendChild(search); menu.appendChild(list); wrap.appendChild(menu);

      let items = [], activeIdx = -1;
      const renderList = (term) => {
        list.innerHTML = ""; items = [];
        const lo = term.toLowerCase();
        loraList()
          .filter(v => v === "None" || shortName(v).toLowerCase().includes(lo) || v.toLowerCase().includes(lo))
          .forEach(v => {
            const it = document.createElement("div");
            it.className = "lfld-menu-item" + (v === "None" ? " none" : "");
            it.textContent = shortName(v);
            it.title = v;
            it.onclick = () => { const d = getData(); d[i].lora = v; commit(d); close(); build(); };
            list.appendChild(it); items.push(it);
          });
      };
      const setActive = (n) => {
        if (!items.length) return;
        activeIdx = (n + items.length) % items.length;
        items.forEach((el, k) => el.classList.toggle("active", k === activeIdx));
        items[activeIdx].scrollIntoView({ block: "nearest" });
      };
      const close = () => { menu.classList.remove("open"); document.removeEventListener("mousedown", onDocDown, true); };
      const onDocDown = (ev) => { if (!wrap.contains(ev.target)) close(); };

      btn.onclick = () => {
        const open = menu.classList.contains("open");
        container.querySelectorAll(".lfld-menu.open").forEach(m => m.classList.remove("open"));
        if (open) { close(); return; }
        renderList(""); activeIdx = -1;
        menu.classList.add("open"); search.value = "";
        setTimeout(() => search.focus(), 10);
        document.addEventListener("mousedown", onDocDown, true);
      };
      search.addEventListener("input", (e) => { renderList(e.target.value); activeIdx = -1; });
      search.addEventListener("keydown", (e) => {
        if (e.key === "ArrowDown") { e.preventDefault(); setActive(activeIdx + 1); }
        else if (e.key === "ArrowUp") { e.preventDefault(); setActive(activeIdx - 1); }
        else if (e.key === "Enter") { e.preventDefault(); if (activeIdx >= 0) items[activeIdx].click(); }
        else if (e.key === "Escape") { close(); }
      });
      return wrap;
    }

    /* ---------- cup-of-water level box */
    function makeCup(i, field, label, val, colorVar) {
      const [lo, hi] = RANGES[field];
      const cup = document.createElement("div");
      cup.className = "lfld-cup" + (val === 0 ? " zero" : "");
      cup.style.setProperty("--cup", colorVar);

      const fill = document.createElement("div"); fill.className = "lfld-cup-fill";
      const lbl = document.createElement("div"); lbl.className = "lfld-cup-lbl"; lbl.textContent = label;
      const valEl = document.createElement("div"); valEl.className = "lfld-cup-val"; valEl.textContent = val.toFixed(2);
      const input = document.createElement("input"); input.className = "lfld-cup-input"; input.type = "text";
      cup.append(fill, lbl, valEl, input);

      const setFill = (v) => {
        fill.style.height = clamp((v - lo) / (hi - lo), 0, 1) * 100 + "%";
        valEl.textContent = v.toFixed(2);
        cup.classList.toggle("zero", v === 0);
      };
      setFill(val);

      cup.addEventListener("wheel", (e) => {
        e.preventDefault();
        const d = getData();
        const dir = e.deltaY < 0 ? 1 : -1;
        const next = round2(clamp((d[i][field] ?? 1.0) + dir * STEP, lo, hi));
        d[i][field] = next; commit(d); setFill(next);
      }, { passive: false });

      cup.addEventListener("click", () => {
        const d = getData();
        input.value = (d[i][field] ?? 1.0).toFixed(2);
        input.classList.add("show"); input.focus(); input.select();
      });
      const applyInput = () => {
        const d = getData(); const parsed = parseFloat(input.value);
        if (!isNaN(parsed)) { const next = round2(clamp(parsed, lo, hi)); d[i][field] = next; commit(d); setFill(next); }
        input.classList.remove("show");
      };
      input.addEventListener("blur", applyInput);
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") { e.preventDefault(); applyInput(); }
        else if (e.key === "Escape") { input.classList.remove("show"); }
      });
      return cup;
    }

    /* ---------- key-count fetch */
    function fetchKeys(lora) {
      if (keyCache[lora + "_p"]) return;
      keyCache[lora + "_p"] = true;
      fetch(`/pfld/lora_keycounts?lora=${encodeURIComponent(lora)}`)
        .then(r => r.json())
        .then(d => { keyCache[lora] = { v: d.v, a: d.a }; build(); })
        .catch(() => { keyCache[lora] = { v: "?", a: "?" }; build(); });
    }

    /* ---------- DOM widget + sizing */
    const uiWidget = node.addDOMWidget("lfld_ui", "div", container, { serialize: false });
    if (uiWidget.element) {
      uiWidget.element.style.margin = "0";
      uiWidget.element.style.width = "100%";
      uiWidget.element.style.boxSizing = "border-box";
    }

    const MIN_W = 460, HEADER = 34;
    // Measure the real content height from the header + rows, NOT the container
    // (the container is stretched to the widget, so scrollHeight feeds back and grows).
    const contentH = () => {
      const head = container.querySelector(".lfld-head");
      let h = 24; // root padding top+bottom
      if (head) h += head.offsetHeight + 8;   // + gap
      // Sum row heights individually (offsetHeight ignores overflow), so the
      // absolutely-positioned search dropdown can't inflate the measurement —
      // rows.scrollHeight included the open menu and left a ghost gap behind.
      container.querySelectorAll(".lfld-row").forEach((r) => { h += r.offsetHeight + 6; });
      return Math.max(120, h);
    };
    // What the node needs to show everything, once.
    const needed = () => HEADER + contentH() + 8;

    // computeSize is what ComfyUI reserves for the widget. Report content height only.
    uiWidget.computeSize = () => [MIN_W, contentH()];

    // Snap node to fit content exactly (used after add/remove/build).
    function relayout() {
      node.setSize([Math.max(node.size[0], MIN_W), needed()]);
      node.setDirtyCanvas(true, true);
    }

    // Only enforce the minimum on manual resize — never force it larger,
    // so the user can freely drag and it won't bounce back up.
    node.onResize = (size) => {
      size[0] = Math.max(size[0], MIN_W);
      size[1] = Math.max(size[1], HEADER + 120);
    };

    const pinW = () => {
      const w = Math.max(10, (node.size?.[0] || 600) - 24);
      container.style.width = container.style.maxWidth = w + "px";
      node._lfldPin = requestAnimationFrame(pinW);
    };
    node._lfldPin = requestAnimationFrame(pinW);

    const _onRemoved = node.onRemoved;
    node.onRemoved = function () {
      if (node._lfldPin) cancelAnimationFrame(node._lfldPin);
      stopLfColorWatch();
      _onRemoved?.apply(this, arguments);
    };

    build();
    // One-time snap to content once the DOM has measured. Preserve user width.
    // Skipped for nodes loaded from a workflow — onConfigure handles those and
    // this snap used to stomp the saved size.
    setTimeout(() => {
      if (node._lfldConfigured) return;
      node.setSize([Math.max(node.size?.[0] || 700, MIN_W), needed()]);
      node.setDirtyCanvas(true, true);
    }, 30);

    // nodeCreated runs BEFORE ComfyUI restores properties/widgets_values from
    // the saved workflow, so the UI built above only shows the default single
    // row. Re-sync + rebuild once the real data lands ("+" no longer needed
    // to make saved LoRAs appear).
    const _origConfigure = node.onConfigure;
    node.onConfigure = function (info) {
      _origConfigure?.apply(this, arguments);
      node._lfldConfigured = true;
      setTimeout(() => {
        const pickValid = (s) => {
          if (typeof s !== "string" || !s.trim()) return "";
          try { const a = JSON.parse(s); return Array.isArray(a) && a.length ? s : ""; }
          catch { return ""; }
        };
        const w = node.widgets?.find((x) => x.name === "stack_data");
        node.properties.stack_data =
          pickValid(node.properties?.stack_data) ||
          pickValid(w?.value) ||
          JSON.stringify([{ on: true, lora: "None", str: 1.0, vs: 1.0, as: 1.0 }]);
        if (w) w.value = node.properties.stack_data;
        stripExtraOutputs();
        build();
        // Keep the workflow-saved size; only grow if restored rows truly don't fit.
        const savedW = Math.max(node.size?.[0] || MIN_W, MIN_W);
        const savedH = node.size?.[1] || 0;
        setTimeout(() => {
          node.setSize([savedW, Math.max(savedH, needed())]);
          node.setDirtyCanvas(true, true);
        }, 20);
      }, 0);
    };
  },
});
