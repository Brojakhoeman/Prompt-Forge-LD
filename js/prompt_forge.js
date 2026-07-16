/**
 * PromptForge LD — top toggles · hero canvas · prompt I/O
 */
import { app } from "../../scripts/app.js";
import { buildResMaster, LTX_AR_PRESETS } from "./res_master.js";
import { buildImageCarousel } from "./image_carousel.js";
import {
  THEMES as SHARED_THEMES,
  THEME_KEYS,
  resolveTheme,
  themeOptionsHtml,
  loadSharedThemeKey,
  saveSharedThemeKey,
  applyComfyAccentVars,
  ensureComfyNativeShell,
  COMFY_DEFAULT_NODE_COLOR,
  COMFY_DEFAULT_NODE_BG,
} from "./themes_ld.js";

const HIDE = [
  "model_file", "mmproj_file", "video_mode", "environment", "scenario",
  "camera_move", "music", "pov", "pov_gender", "dialogue_tier", "cast",
  "lead_gender", "video_style", "accent_mode", "accent_partner", "intensity",
  "motion_level", "mouth_heat",
  "user_intent", "confirmed_prompt", "continuity_state",
  "image_b64", "image_filename", "rm_w", "rm_h", "duration_s", "fps",
];

const HISTORY_KEY = "pfld_history_v2";
const HISTORY_MAX = 24;

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
  // Node shell — default tall so Intent + Generate are visible; min is free-drag floor
  defaultNodeW: 920,
  defaultNodeH: 1400,
  minNodeH: 720,   // corner-drag can shrink to this (content scrolls inside)
  maxNodeH: 2400,
};

let _debugPad = null; // for the temp UI padding debug in cog
let _debugLayout = null; // layout sizes exposed in cog for live resize tweaks (no bars)

/** Flatten shared themes → CSS vars map (PromptForge panel). */
const THEMES = Object.fromEntries(
  THEME_KEYS.map((k) => [k, SHARED_THEMES[k].pf])
);

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
  // Bust cache: native shell vs inner accents
  link.href += (link.href.includes("?") ? "&" : "?") + "v=voice-stack1";
  document.head.appendChild(link);
}

/**
 * Custom tooltips — native `title` rarely shows inside Comfy LiteGraph DOM widgets.
 * Use data-tip="…" on elements. Also migrates existing title → data-tip.
 */
// Style options: hover shows what they do + a tiny example intent
const STYLE_PICKS = [
  {
    v: "None — off (no style path)",
    short: "None — off",
    tip: "No style path — zero extra tokens. Your intent only.",
  },
  {
    v: "✨ Gravure — slow body tease (close & personal)",
    short: "✨ Gravure — slow body tease",
    tip: "Sexy lingerie / sheer · soft Asian idol slow tease.\n\nEx: a Korean woman in red sheer lingerie by a window",
  },
  {
    v: "📱 Handheld phone vlog — arm's-length selfie",
    short: "📱 Handheld phone vlog",
    tip: "Selfie phone · talk to the lens while doing stuff.\n\nEx: girl shows her messy kitchen morning coffee",
  },
  {
    v: "👻 Horror — dread & unease",
    short: "👻 Horror",
    tip: "Dread path · invents scary beats around your place.\n\nEx: a woman alone in a foggy graveyard",
  },
  {
    v: "🎵 Music-video performance",
    short: "🎵 Music-video performance",
    tip: "Performance clip · hooks the Music dropdown groove.\n\nEx: dancer in neon alley hits the chorus",
  },
  {
    v: "🎞 Found-footage / security cam energy",
    short: "🎞 Found footage",
    tip: "Security / camcorder energy · observational.\n\nEx: hallway cam catches someone at 3am",
  },
  {
    v: "☕ Slice-of-life cinema",
    short: "☕ Slice of life",
    tip: "Quiet realism · props and small stakes.\n\nEx: couple miss the last bus in the rain",
  },
  {
    v: "👗 Fashion editorial / lookbook",
    short: "👗 Fashion editorial",
    tip: "Lookbook path · garment and pose are the star.\n\nEx: model in a black coat on wet marble steps",
  },
  {
    v: "🎤 Late-night confessional",
    short: "🎤 Late-night confessional",
    tip: "Soft lamp · private talk to the view.\n\nEx: she apologises alone on her bed at 2am",
  },
  {
    v: "🏃 Athletic / training diary",
    short: "🏃 Athletic training",
    tip: "Gym kit · sweat · form and reps.\n\nEx: woman finishes deadlift sets in a night gym",
  },
  {
    v: "🌃 Night-drive / neon city",
    short: "🌃 Night drive / neon",
    tip: "Car + neon · late city mood.\n\nEx: man drives wet neon streets after midnight",
  },
  {
    v: "😌 Soft romance",
    short: "😌 Soft romance",
    tip: "Tender pair · closeness, almost-kiss energy.\n\nEx: they share an umbrella after the cinema",
  },
  {
    v: "🔥 Explicit heat — slow filth",
    short: "🔥 Explicit heat — slow filth",
    tip: "Adult slow heat · lingerie-to-skin, mechanism-first.\n\nEx: hotel room, she peels a silk slip for him",
  },
  {
    v: "⛓ BDSM power exchange",
    short: "⛓ BDSM power exchange",
    tip: "Dom/sub path · collar/leather · command voice.\nPairs with POV Mistress / POV Sub recipes.\n\nEx: she orders him to kneel; collar tug; cool yes-Ma'am",
  },
];

/**
 * Custom tooltips — native `title` is flaky in Comfy node DOM.
 * Use data-tip="…" on labels/chips/buttons (not textareas / res master).
 */
function wireTooltips(root) {
  if (!root || root._pfldTipsWired) return;
  root._pfldTipsWired = true;

  let tip = document.getElementById("pfld-float-tip");
  if (!tip) {
    tip = document.createElement("div");
    tip.id = "pfld-float-tip";
    tip.className = "pfld-float-tip";
    tip.setAttribute("role", "tooltip");
    document.body.appendChild(tip);
  }

  // Migrate native title → data-tip (skip textareas / res master zone)
  root.querySelectorAll("[title]").forEach((el) => {
    if (el.closest?.("#gpl-res") || el.matches?.("textarea")) {
      el.removeAttribute("title");
      return;
    }
    const t = (el.getAttribute("title") || "").trim();
    if (t && !el.getAttribute("data-tip")) el.setAttribute("data-tip", t);
    el.removeAttribute("title");
  });

  let hideTimer = null;
  let activeEl = null;

  const place = (e) => {
    if (!tip.classList.contains("on")) return;
    const pad = 14;
    const tw = tip.offsetWidth || 220;
    const th = tip.offsetHeight || 48;
    let x = e.clientX + pad;
    let y = e.clientY + pad;
    if (x + tw > window.innerWidth - 8) x = Math.max(8, e.clientX - tw - pad);
    if (y + th > window.innerHeight - 8) y = Math.max(8, e.clientY - th - pad);
    tip.style.left = `${Math.round(x)}px`;
    tip.style.top = `${Math.round(y)}px`;
  };

  const show = (el, e) => {
    if (el.closest?.("#gpl-res") || el.matches?.("textarea")) return;
    const text = (el.getAttribute("data-tip") || "").trim();
    if (!text) return;
    clearTimeout(hideTimer);
    activeEl = el;
    tip.textContent = text;
    tip.classList.add("on");
    place(e);
  };

  const hide = () => {
    hideTimer = setTimeout(() => {
      tip.classList.remove("on");
      activeEl = null;
    }, 60);
  };

  root.addEventListener("pointerover", (e) => {
    const el = e.target?.closest?.("[data-tip]");
    if (!el || !root.contains(el)) return;
    if (el.closest?.("#gpl-res") || el.matches?.("textarea")) return;
    show(el, e);
  }, true);

  root.addEventListener("pointermove", (e) => {
    if (activeEl) place(e);
  }, true);

  root.addEventListener("pointerout", (e) => {
    const el = e.target?.closest?.("[data-tip]");
    if (!el) return;
    const to = e.relatedTarget;
    if (to && el.contains(to)) return;
    if (to && to.closest && to.closest("[data-tip]") === el) return;
    hide();
  }, true);

  // Don't kill tip on every click inside style menu (hover tips while browsing)
  root.addEventListener("pointerdown", (e) => {
    if (e.target?.closest?.(".gpl-style-menu")) return;
    tip.classList.remove("on");
    activeEl = null;
  }, true);
}

/** Custom Style picker so each option can show a rich hover tip (native <option> cannot). */
function wireStylePicker(root) {
  const sel = root.querySelector("#gpl-style");
  const btn = root.querySelector("#gpl-style-btn");
  const menu = root.querySelector("#gpl-style-menu");
  if (!sel || !btn || !menu) return;

  // Hidden native select keeps .value working for generate body
  sel.innerHTML = "";
  sel.classList.add("gpl-style-native");
  STYLE_PICKS.forEach((p) => {
    const o = document.createElement("option");
    o.value = p.v;
    o.textContent = p.short;
    sel.appendChild(o);
  });

  menu.innerHTML = "";
  STYLE_PICKS.forEach((p) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "gpl-style-opt";
    b.dataset.v = p.v;
    b.setAttribute("data-tip", p.tip);
    b.textContent = p.short;
    b.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      sel.value = p.v;
      btn.textContent = p.short;
      btn.setAttribute("data-tip", p.tip);
      menu.querySelectorAll(".gpl-style-opt").forEach((o) => {
        o.classList.toggle("on", o.dataset.v === p.v);
      });
      menu.classList.remove("open");
      btn.setAttribute("aria-expanded", "false");
      sel.dispatchEvent(new Event("change", { bubbles: true }));
    });
    menu.appendChild(b);
  });

  const syncBtn = () => {
    const pick = STYLE_PICKS.find((p) => p.v === sel.value) || STYLE_PICKS[0];
    if (sel.value !== pick.v) sel.value = pick.v;
    btn.textContent = pick.short;
    btn.setAttribute("data-tip", pick.tip);
    menu.querySelectorAll(".gpl-style-opt").forEach((o) => {
      o.classList.toggle("on", o.dataset.v === pick.v);
    });
  };
  syncBtn();
  // If something sets sel.value later, keep button in sync
  sel.addEventListener("change", syncBtn);

  // Park menu on body so Comfy node overflow/transform never clips it
  if (menu.parentElement !== document.body) {
    document.body.appendChild(menu);
  }

  const placeMenu = () => {
    const r = btn.getBoundingClientRect();
    const maxH = Math.min(280, window.innerHeight - r.bottom - 12);
    menu.style.position = "fixed";
    menu.style.left = `${Math.round(r.left)}px`;
    menu.style.width = `${Math.round(Math.max(160, r.width))}px`;
    menu.style.top = `${Math.round(r.bottom + 4)}px`;
    menu.style.right = "auto";
    menu.style.bottom = "auto";
    menu.style.maxHeight = `${Math.max(120, maxH)}px`;
    if (maxH < 140 && r.top > 160) {
      menu.style.top = "auto";
      menu.style.bottom = `${Math.round(window.innerHeight - r.top + 4)}px`;
      menu.style.maxHeight = `${Math.min(280, r.top - 12)}px`;
    }
  };

  const closeMenu = () => {
    menu.classList.remove("open");
    btn.setAttribute("aria-expanded", "false");
  };

  btn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    const willOpen = !menu.classList.contains("open");
    if (willOpen) {
      placeMenu();
      menu.classList.add("open");
      btn.setAttribute("aria-expanded", "true");
    } else {
      closeMenu();
    }
  });

  document.addEventListener("pointerdown", (e) => {
    if (!menu.classList.contains("open")) return;
    if (menu.contains(e.target) || btn.contains(e.target)) return;
    closeMenu();
  }, true);

  window.addEventListener("resize", () => {
    if (menu.classList.contains("open")) placeMenu();
  });

  // Expose helper for restoreSession
  sel._pfldSyncStyleBtn = syncBtn;
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

/**
 * Capture Comfy Queue / Run: free managed LLM *before* the graph starts so LTX
 * can load. Generate leaves the model warm; this is the hand-off.
 *
 * CRITICAL: do NOT await a full unload_all_models here — that stalls the click
 * 5–10s when VRAM is packed. Fast kill = process only (+ light CUDA clear),
 * capped wait so Queue always proceeds quickly. node.run() also free()s.
 */
function installPfldQueueKillHook() {
  if (typeof window !== "undefined" && window.__pfldQueueKillHook) return;
  if (typeof window !== "undefined") window.__pfldQueueKillHook = true;

  function sleep(ms) {
    return new Promise((r) => setTimeout(r, ms));
  }

  async function killBeforeQueue(reason) {
    try { window.__pfldVideoTookVram = true; } catch { /* */ }
    try {
      console.log(`[PromptForgeLD] ${reason} → fast free LLM (no full unload wait)`);
      // Fire fast kill; never block Queue more than ~1.2s even if server is slow
      const killP = fetch("/pfld/kill", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fast: true }),
      }).catch((e) => console.warn("[PromptForgeLD] pre-queue kill failed:", e));
      await Promise.race([killP, sleep(1200)]);
    } catch (e) {
      console.warn("[PromptForgeLD] pre-queue kill error:", e);
    }
  }

  function wrapFn(obj, name) {
    if (!obj || typeof obj[name] !== "function") return false;
    const orig = obj[name];
    if (orig.__pfldKillWrapped) return true;
    const wrapped = async function (...args) {
      await killBeforeQueue(`Comfy ${name}`);
      return orig.apply(this, args);
    };
    wrapped.__pfldKillWrapped = true;
    obj[name] = wrapped;
    return true;
  }

  // app.queuePrompt is the classic UI path
  wrapFn(app, "queuePrompt");
  // Newer frontends also go through api.queuePrompt
  try {
    import("../../scripts/api.js")
      .then((mod) => {
        const api = mod?.api || mod?.default;
        if (api) wrapFn(api, "queuePrompt");
      })
      .catch(() => { /* api path optional */ });
  } catch { /* */ }
}

app.registerExtension({
  name: "LD.PromptForge",

  async setup() {
    installPfldQueueKillHook();
  },

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
    // Ensure hook exists even if setup order was weird
    installPfldQueueKillHook();
    try {
    for (const w of node.widgets || []) hideWidget(w);

    // Shell colour owned by look mode (Comfy native defaults / theme pack).
    // Do NOT hardcode near-black here — that made native accents stay grey.

    const gw = (n) => node.widgets?.find((w) => w.name === n);
    /** Write a hidden widget AND keep Comfy's widgets_values / graph in sync.
     *  Bare `w.value = x` can leave Queue on a stale pack/image until something
     *  else (e.g. re-clicking a carousel card) rewrites the widget. */
    const sw = (n, v) => {
      const w = gw(n);
      if (!w) return;
      w.value = v;
      try {
        const idx = node.widgets?.indexOf(w);
        if (idx >= 0) {
          if (!Array.isArray(node.widgets_values)) node.widgets_values = [];
          node.widgets_values[idx] = v;
        }
      } catch { /* */ }
      try { w.callback?.(v); } catch { /* */ }
      try {
        node.setDirtyCanvas?.(true, true);
        app.graph?.setDirtyCanvas?.(true, true);
      } catch { /* */ }
    };
    sw("image_b64", "");

    let imgPreviewUrl = null, imgW = 0, imgH = 0, imgFilename = "";
    const savedName = (gw("image_filename")?.value || "").trim();
    if (savedName) {
      imgFilename = savedName;
      imgW = 0;
      imgH = 0;
    }
    let draftPrompt = "", generating = false, abortCtrl = null;
    // Intent string used for the last successful Generate (not Refine) — drives Re-roll UI
    let lastGenIntent = "";
    let povMode = localStorage.getItem("pfld_pov") || "off";
    let dlgTier = localStorage.getItem("pfld_dlg") || "standard";
    let castMode = localStorage.getItem("pfld_cast") || "pair";
    let leadGender = localStorage.getItem("pfld_lead") || "auto";
    let accentMode = localStorage.getItem("pfld_accent") || "auto";
    let accentPartner = localStorage.getItem("pfld_accent_partner") || "off";
    let motionLevel = localStorage.getItem("pfld_motion") || "normal";
    let mouthHeat = localStorage.getItem("pfld_mouth") || "normal";
    // Default ON: leave local LLM loaded after Generate until Comfy Queue/Run kills it.
    // Explicit "0" turns the old free-after-gen behaviour back on.
    let keepWarm = localStorage.getItem("pfld_keep_warm") !== "0";
    let carryNext = localStorage.getItem("pfld_carry") !== "0"; // default on
    let detailerOn = localStorage.getItem("pfld_detailer") === "1"; // default off (zero tokens)
    // Post-repair scrub (CANON head/torso, silent strip, facing jump…). Default ON.
    let repairOn = localStorage.getItem("pfld_repair") !== "0";
    // Music background (quiet under) — only meaningful when a music preset is selected
    let musicBgOn = localStorage.getItem("pfld_music_bg") === "1";
    // Self-check QA pass (extra LLM pass). Default OFF — optional polish.
    let selfCheckOn = localStorage.getItem("pfld_self_check") === "1";
    let selfCheckMode = (localStorage.getItem("pfld_self_check_mode") || "fix").toLowerCase();
    if (selfCheckMode !== "report" && selfCheckMode !== "fix") selfCheckMode = "fix";
    const SELF_CHECK_CHIPS = [
      { id: "intent_beats", label: "Intent beats" },
      { id: "i2v_lock", label: "I2V lock" },
      { id: "talk_floor", label: "Enough talk" },
      { id: "silent_ok", label: "Silent clean" },
      { id: "pov_clean", label: "POV clean" },
      { id: "body_unit", label: "Body unit" },
      { id: "hard_triggers", label: "LoRA triggers" },
      { id: "camera_alive", label: "Camera hunts" },
      { id: "no_meta", label: "No meta" },
      { id: "sections", label: "Sections" },
      { id: "gravure_voice", label: "Gravure voice" },
      { id: "music_plant", label: "Music plant" },
      { id: "dance_tease", label: "Dance / tease" },
      { id: "sing_vocal", label: "Singing" },
      { id: "pacing", label: "Pacing / density" },
    ];
    const SELF_CHECK_DEFAULT = ["intent_beats", "talk_floor", "body_unit", "sections", "no_meta"];
    let selfCheckChips = (() => {
      try {
        const raw = localStorage.getItem("pfld_self_check_chips");
        if (raw) {
          const a = JSON.parse(raw);
          if (Array.isArray(a) && a.length) return a.filter((id) => SELF_CHECK_CHIPS.some((c) => c.id === id));
        }
      } catch { /* */ }
      return SELF_CHECK_DEFAULT.slice();
    })();
    // Seed modes: random (new each gen) · fixed (same) · increment (+1 each gen)
    let seedMode = (localStorage.getItem("pfld_seed_mode") || "").toLowerCase();
    if (!["random", "fixed", "increment"].includes(seedMode)) {
      // migrate old lock checkbox
      seedMode = localStorage.getItem("pfld_seed_lock") === "1" ? "fixed" : "random";
    }
    let lastSeed = parseInt(localStorage.getItem("pfld_seed") || "0", 10);
    if (!Number.isFinite(lastSeed) || lastSeed < 0) lastSeed = Math.floor(Math.random() * 2147483647);

    function paintSeedUI() {
      const val = String(lastSeed >>> 0);
      container.querySelectorAll("#gpl-seed-hd").forEach((el) => {
        if (el && document.activeElement !== el) el.value = val;
      });
      container.querySelectorAll(".gpl-seed-mode-btn").forEach((b) => {
        b.classList.toggle("on", b.dataset.mode === seedMode);
      });
      const lab = $("#gpl-seed-mode-lab");
      if (lab) {
        lab.textContent = seedMode === "fixed" ? "fixed" : seedMode === "increment" ? "+1" : "rand";
      }
    }
    function setSeedMode(mode) {
      if (!["random", "fixed", "increment"].includes(mode)) return;
      seedMode = mode;
      try { localStorage.setItem("pfld_seed_mode", seedMode); } catch { /* */ }
      // keep legacy key in sync for older logic
      try { localStorage.setItem("pfld_seed_lock", seedMode === "fixed" ? "1" : "0"); } catch { /* */ }
      paintSeedUI();
    }
    function rollSeed() {
      lastSeed = Math.floor(Math.random() * 2147483647);
      try { localStorage.setItem("pfld_seed", String(lastSeed)); } catch { /* */ }
      paintSeedUI();
      return lastSeed;
    }
    function readSeed() {
      const n = parseInt($("#gpl-seed-hd")?.value, 10);
      if (Number.isFinite(n) && n >= 0) {
        lastSeed = n >>> 0;
        try { localStorage.setItem("pfld_seed", String(lastSeed)); } catch { /* */ }
        paintSeedUI();
        return lastSeed;
      }
      return rollSeed();
    }
    /** random → new seed · fixed → keep · increment → last+1 */
    function seedForGenerate() {
      const modeBtn = container.querySelector(".gpl-seed-mode-btn.on");
      if (modeBtn?.dataset?.mode) seedMode = modeBtn.dataset.mode;
      if (seedMode === "fixed") return readSeed();
      if (seedMode === "increment") {
        lastSeed = ((readSeed() + 1) >>> 0);
        try { localStorage.setItem("pfld_seed", String(lastSeed)); } catch { /* */ }
        paintSeedUI();
        return lastSeed;
      }
      return rollSeed();
    }
    let localDur = parseFloat(localStorage.getItem("pfld_dur") || "12") || 12;
    const INTENSITY_LEVELS = [
      { k: "asmr", lab: "ASMR" },
      { k: "soft", lab: "Soft" },
      { k: "normal", lab: "Normal" },
      { k: "intense", lab: "Intense" },
      { k: "aggressive", lab: "Aggressive" },
    ];
    const levelToEnergy = (k) => ({ asmr: 2, soft: 3, normal: 5, intense: 7, aggressive: 10 }[k] || 5);
    const energyToLevel = (n) => {
      const v = parseInt(n, 10) || 5;
      if (v <= 2) return "asmr";
      if (v <= 3) return "soft";
      if (v <= 6) return "normal";
      if (v <= 8) return "intense";
      return "aggressive";
    };
    let lastContinuity = (gw("continuity_state")?.value || "").trim();
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
<!-- TOP: header + controls in colour sections -->
<div class="gpl-zone gpl-top">
  <div class="gpl-row-spread gpl-header">
    <div class="gpl-header-left">
      <span class="gpl-title" data-tip="LTX 2.3 shot writer — builds timed multi-section scripts for video">✦ PromptForge LD</span>
      <span class="gpl-badge" id="gpl-live" data-tip="Duration · fps · cast (from slider or wired inputs)">—</span>
    </div>
    <div class="gpl-header-right">
      <div class="gpl-seed-strip" data-tip="Seed for LLM + Random scenario/env. Random = new each Generate · Fixed = same · +1 = increment">
        <span class="gpl-seed-lbl">Seed</span>
        <div class="gpl-seed-modes" id="gpl-seed-modes" role="group" aria-label="Seed mode">
          <button type="button" class="gpl-seed-mode-btn" data-mode="random" data-tip="New random seed every Generate (warm re-rolls)">Rand</button>
          <button type="button" class="gpl-seed-mode-btn" data-mode="fixed" data-tip="Keep this seed — reproduce a script">Fixed</button>
          <button type="button" class="gpl-seed-mode-btn" data-mode="increment" data-tip="Add 1 to the seed each Generate">+1</button>
        </div>
        <input type="number" id="gpl-seed-hd" class="gpl-seed-num" min="0" max="2147483647" step="1" value="0" data-tip="Current seed number">
        <button type="button" id="gpl-seed-roll-hd" class="gpl-seed-dice" data-tip="Roll a new random seed now">🎲</button>
      </div>
      <button type="button" class="gpl-cog" id="gpl-cog" data-tip="Settings: LLM server, model, theme, node size">⚙</button>
    </div>
  </div>

  <!-- Row A: SHOT (full) — mode + chips + energy inline where possible -->
  <div class="gpl-sec gpl-sec-shot">
    <div class="gpl-sec-head"><span class="gpl-sec-dot"></span><span class="gpl-sec-title" data-tip="Shot setup: video mode, dialogue density, POV, cast count">Shot</span>
      <div class="gpl-inline gpl-dur-inline gpl-dur-head">
        <label data-tip="Clip length in seconds (UI). Internal write is 2s shorter so the last word is not cut off.">Dur <input type="range" id="gpl-dur" min="4" max="40" step="0.5" value="12" data-tip="Drag to set clip duration (seconds)"><span class="val" id="gpl-dur-val">12s</span></label>
      </div>
    </div>
    <div class="gpl-shot-bar">
      <div class="gpl-tabs" id="gpl-mode-tabs">
        <button type="button" class="gpl-tab on" data-mode="i2v" data-tip="Image → Video. Start frame is law. JUMP scenarios only in this mode.">I2V</button>
        <button type="button" class="gpl-tab" data-mode="t2v" data-tip="Text → Video. Full recipes + character look seeds + video styles.">T2V</button>
      </div>
      <div class="gpl-chips gpl-chips-inline">
        <div class="gpl-chip-wrap">
          <span class="gpl-chip-lbl" data-tip="How much spoken dialogue the script must carry">Dialogue</span>
          <div class="gpl-chipgrp" id="gpl-dlg">
            <button type="button" class="gpl-chip" data-v="none" data-tip="Silent: no spoken lines — breath, moans, foley only">Silent</button>
            <button type="button" class="gpl-chip on" data-v="standard" data-tip="Standard: a few natural lines where mouths are free">Standard</button>
            <button type="button" class="gpl-chip rose" data-v="talkative" data-tip="Talkative: dense dialogue (Grok floor). Free mouths only — oral stays quiet.">Talkative</button>
          </div>
        </div>
        <div class="gpl-chip-split" aria-hidden="true"></div>
        <div class="gpl-chip-wrap">
          <span class="gpl-chip-lbl" data-tip="Point-of-view camera: view is a body, not a floating camera">POV</span>
          <div class="gpl-chipgrp" id="gpl-pov">
            <button type="button" class="gpl-chip pov-off on" data-v="off" data-tip="Third-person / normal framing — no POV contract">Off</button>
            <button type="button" class="gpl-chip pov-f" data-v="female" data-tip="Female POV: view is her eyes/body; no I/me/my in prose">POV ♀</button>
            <button type="button" class="gpl-chip pov-m" data-v="male" data-tip="Male POV: view is his eyes/body; hands enter from bottom edge">POV ♂</button>
          </div>
        </div>
        <div class="gpl-chip-split" aria-hidden="true"></div>
        <div class="gpl-chip-wrap">
          <span class="gpl-chip-lbl" data-tip="How many people on screen">Cast</span>
          <div class="gpl-chipgrp" id="gpl-cast">
            <button type="button" class="gpl-chip" data-v="solo" data-tip="One person only — no invented partner">Solo</button>
            <button type="button" class="gpl-chip on cyan" data-v="pair" data-tip="Two people — keep identities distinct">Pair</button>
            <button type="button" class="gpl-chip" data-v="group" data-tip="Three or more — role tags, focus on 1–2 bodies per section">Group</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Row B: SCENE | VOICE side by side -->
  <div class="gpl-pair-row">
    <div class="gpl-sec gpl-sec-scene">
      <div class="gpl-sec-head">
        <span class="gpl-sec-dot"></span><span class="gpl-sec-title" data-tip="Where / what structure: camera, scenario, place, music, video style">Scene</span>
        <label class="gpl-check gpl-check-inline" data-tip="Detailer: skin texture + lighting + max 1 new visual detail per section. Off = zero tokens. Helps I2V keep start-image skin."><input type="checkbox" id="gpl-detailer"> Detailer</label>
      </div>
      <div class="gpl-fields gpl-fields-3-tight">
        <div class="gpl-field"><label data-tip="Camera move preset (dolly, orbit…). Separate from Video Style.">Camera</label><select id="gpl-cam" data-tip="Optional camera motion language for the script"></select></div>
        <div class="gpl-field">
          <label id="gpl-scn-label" data-tip="I2V: JUMP cuts only. T2V: deep shot recipes. None = your intent only.">Scenario</label>
          <div class="gpl-field-row">
            <select id="gpl-scn" data-tip="Structure / choreography bank for this mode"></select>
            <button type="button" id="gpl-edit-scn" class="gpl-icon-btn" data-tip="Edit this scenario's setup & choreography (saves to disk)">✎</button>
          </div>
        </div>
        <div class="gpl-field"><label data-tip="Location / set dressing block">Environment</label><select id="gpl-env" data-tip="Where the clip happens — lighting, props, atmosphere"></select></div>
        <div class="gpl-field"><label data-tip="Soundtrack groove. Music-video Style hard-hooks this.">Music</label><select id="gpl-music" data-tip="Music / soundtrack preset. Pairs with Music-video style."></select>
          <label class="gpl-check gpl-check-inline" id="gpl-music-bg-wrap" style="margin-top:4px;display:none" data-tip="Quiet wallpaper score under the scene. Normal speaking voice — music never pauses, but people don't shout over it. Off = loud in-the-mix (club/shout-over)."><input type="checkbox" id="gpl-music-bg"> Background (quiet)</label>
        </div>
        <div class="gpl-field gpl-style-field">
          <label data-tip="Video genre path (not a camera). Hover each style for what it does + an example.">Style</label>
          <div class="gpl-style-wrap">
            <button type="button" class="gpl-style-btn" id="gpl-style-btn" aria-haspopup="listbox" aria-expanded="false" data-tip="Click to pick a video style — hover each row for a short example">None — off</button>
            <div class="gpl-style-menu" id="gpl-style-menu" role="listbox"></div>
            <select id="gpl-style" class="gpl-style-native" aria-hidden="true" tabindex="-1"></select>
          </div>
        </div>
      </div>
    </div>

    <div class="gpl-sec gpl-sec-voice">
      <div class="gpl-sec-head">
        <span class="gpl-sec-dot"></span><span class="gpl-sec-title" data-tip="Who talks how: lead gender + accent locks + continuity carry">Voice</span>
        <label class="gpl-check gpl-check-inline" data-tip="Carry wardrobe/pose state into the next Generate (continuity)"><input type="checkbox" id="gpl-carry" checked> Carry</label>
        <button type="button" id="gpl-carry-clear" class="gpl-icon-btn" data-tip="Clear stored continuity (fresh wardrobe/pose next Generate)" style="margin-left:2px;font-size:10px;padding:2px 6px" title="Clear continuity">✕</button>
      </div>
      <!-- Lead + accents — single compact row -->
      <div class="gpl-fields gpl-fields-voice-3">
        <div class="gpl-field"><label data-tip="Who the primary subject is (she/he/they) — drives identity + accent look seeds">Lead</label>
          <select id="gpl-lead" data-tip="Lead gender for identity lines and accent profiles">
            <option value="auto">Auto</option>
            <option value="female">Female</option>
            <option value="male">Male</option>
            <option value="neutral">Neutral</option>
          </select>
        </div>
        <div class="gpl-field"><label data-tip="Lead speaker accent. T2V also seeds matching look (Scottish freckles ≠ Korean face).">Accent</label>
          <select id="gpl-accent" data-tip="Accent lock for lead: grammar + voice line + look seed (T2V)">
            <option value="auto">Auto</option>
            <option value="off">Off</option>
            <optgroup label="UK / Ireland">
              <option value="cockney">Cockney (London)</option>
              <option value="scottish">Scottish</option>
              <option value="irish">Irish</option>
              <option value="scouse">Scouse (Liverpool)</option>
              <option value="geordie">Geordie (Newcastle)</option>
              <option value="northern_english">Northern English</option>
              <option value="welsh">Welsh English</option>
              <option value="rp_british">RP / Southern British</option>
            </optgroup>
            <optgroup label="Europe">
              <option value="french">French</option>
              <option value="german">German</option>
              <option value="spanish_latin">Spanish (Latin)</option>
              <option value="spanish_castilian">Spanish (Spain)</option>
              <option value="italian">Italian</option>
              <option value="portuguese">Portuguese</option>
              <option value="dutch">Dutch</option>
              <option value="russian">Russian</option>
              <option value="polish">Polish</option>
              <option value="czech">Czech</option>
              <option value="swedish">Swedish</option>
              <option value="norwegian">Norwegian</option>
              <option value="greek">Greek</option>
            </optgroup>
            <optgroup label="Asia">
              <option value="korean">Korean</option>
              <option value="japanese">Japanese</option>
              <option value="mandarin">Mandarin</option>
              <option value="thai">Thai</option>
              <option value="vietnamese">Vietnamese</option>
              <option value="indian_english">Indian English</option>
            </optgroup>
            <optgroup label="Caribbean (listen)">
              <option value="jamaican_rasta">Jamaican / Rasta</option>
              <option value="trinidadian">Trinidadian / Trini</option>
            </optgroup>
            <optgroup label="Africa">
              <option value="nigerian_english">Nigerian English (Naija)</option>
              <option value="ghanaian_english">Ghanaian English</option>
              <option value="south_african_english">South African English</option>
              <option value="swahili">Swahili / East African</option>
            </optgroup>
            <optgroup label="Other English">
              <option value="australian">Australian</option>
              <option value="new_zealand">New Zealand / Kiwi</option>
              <option value="southern_us">Southern US</option>
              <option value="filipino_english">Filipino English</option>
            </optgroup>
            <optgroup label="Middle East">
              <option value="arabic">Arabic</option>
              <option value="hebrew">Hebrew</option>
            </optgroup>
          </select>
        </div>
        <div class="gpl-field"><label data-tip="Second speaker's accent (pair scenes). Stays distinct from lead. Off = same as lead.">Partner</label>
          <select id="gpl-accent-partner" data-tip="Partner accent lock — never blend mid-line with lead. Off = same as lead.">
            <option value="off">Off</option>
            <option value="auto">Auto</option>
            <optgroup label="UK / Ireland">
              <option value="cockney">Cockney</option>
              <option value="scottish">Scottish</option>
              <option value="irish">Irish</option>
              <option value="scouse">Scouse</option>
              <option value="geordie">Geordie</option>
              <option value="northern_english">Northern English</option>
              <option value="welsh">Welsh</option>
              <option value="rp_british">RP British</option>
            </optgroup>
            <optgroup label="Europe">
              <option value="french">French</option>
              <option value="german">German</option>
              <option value="spanish_latin">Spanish (Latin)</option>
              <option value="spanish_castilian">Spanish (Spain)</option>
              <option value="italian">Italian</option>
              <option value="portuguese">Portuguese</option>
              <option value="dutch">Dutch</option>
              <option value="russian">Russian</option>
              <option value="polish">Polish</option>
              <option value="czech">Czech</option>
              <option value="swedish">Swedish</option>
              <option value="norwegian">Norwegian</option>
              <option value="greek">Greek</option>
            </optgroup>
            <optgroup label="Asia">
              <option value="korean">Korean</option>
              <option value="japanese">Japanese</option>
              <option value="mandarin">Mandarin</option>
              <option value="thai">Thai</option>
              <option value="vietnamese">Vietnamese</option>
              <option value="indian_english">Indian English</option>
            </optgroup>
            <optgroup label="Caribbean (listen)">
              <option value="jamaican_rasta">Jamaican / Rasta</option>
              <option value="trinidadian">Trinidadian / Trini</option>
            </optgroup>
            <optgroup label="Africa">
              <option value="nigerian_english">Nigerian English</option>
              <option value="ghanaian_english">Ghanaian English</option>
              <option value="south_african_english">South African English</option>
              <option value="swahili">Swahili / East African</option>
            </optgroup>
            <optgroup label="Other English">
              <option value="australian">Australian</option>
              <option value="new_zealand">New Zealand / Kiwi</option>
              <option value="southern_us">Southern US</option>
              <option value="filipino_english">Filipino English</option>
            </optgroup>
            <optgroup label="Middle East">
              <option value="arabic">Arabic</option>
              <option value="hebrew">Hebrew</option>
            </optgroup>
          </select>
        </div>
      </div>
    </div>
  </div>

  <!-- Row C: ENERGY full width but single compact row -->
  <div class="gpl-sec gpl-sec-energy">
    <div class="gpl-sec-head gpl-sec-head-inline">
      <span class="gpl-sec-dot"></span><span class="gpl-sec-title" data-tip="Two independent axes: Body motion force ≠ Mouth / dialogue heat">Energy</span>
      <div class="gpl-intensity-inline">
        <span class="gpl-energy-lbl-sm" data-tip="How hard the body moves (ASMR soft → aggressive slam)">Body</span>
        <div class="gpl-chipgrp" id="gpl-motion">
          <button type="button" class="gpl-chip" data-v="asmr" data-tip="Body: micro motion, whisper-scale movement">ASMR</button>
          <button type="button" class="gpl-chip" data-v="soft" data-tip="Body: gentle continuous motion">Soft</button>
          <button type="button" class="gpl-chip on" data-v="normal" data-tip="Body: natural everyday force">Normal</button>
          <button type="button" class="gpl-chip" data-v="intense" data-tip="Body: strong, forceful motion">Intense</button>
          <button type="button" class="gpl-chip rose" data-v="aggressive" data-tip="Body: hard, aggressive physical energy">Aggressive</button>
        </div>
        <span class="gpl-energy-lbl-sm" data-tip="How filthy / heated the dialogue is (independent of body)">Mouth</span>
        <div class="gpl-chipgrp" id="gpl-mouth">
          <button type="button" class="gpl-chip" data-v="asmr" data-tip="Mouth: soft whispers, almost no filth">ASMR</button>
          <button type="button" class="gpl-chip" data-v="soft" data-tip="Mouth: gentle warm talk">Soft</button>
          <button type="button" class="gpl-chip on" data-v="normal" data-tip="Mouth: natural heat">Normal</button>
          <button type="button" class="gpl-chip" data-v="intense" data-tip="Mouth: dirty / heated dialect">Intense</button>
          <button type="button" class="gpl-chip rose" data-v="aggressive" data-tip="Mouth: full filth / degradation band (when explicit)">Aggressive</button>
        </div>
        <input type="hidden" id="gpl-int" value="5">
      </div>
    </div>
  </div>
</div>

<!-- MIDDLE: image hero -->
<div class="gpl-zone gpl-mid gpl-sec-media" id="gpl-mid">
  <div class="gpl-sec-head gpl-sec-head-media"><span class="gpl-sec-dot"></span><span class="gpl-sec-title">Frame</span></div>
  <div id="gpl-res"></div>
  <div class="gpl-folder">
    <input id="gpl-folder-path" placeholder="Image folder (default: ComfyUI/input)" spellcheck="false">
    <button type="button" id="gpl-folder-apply" data-tip="Load images from this folder into the carousel">Apply</button>
  </div>
</div>

<!-- BOTTOM: intent → output -->
<div class="gpl-zone gpl-bot">
  <div class="gpl-write-col">
    <div class="gpl-lbl-row">
      <div class="gpl-lbl gpl-lbl-intent">Intent</div>
    </div>
    <div class="gpl-lora-trig-row" data-tip="Activation keywords for LoRAs on the graph (e.g. grwth). Kept out of free intent; injected into the writer + guaranteed in the final script if missing.">
      <label class="gpl-lora-trig-lbl" for="gpl-lora-trig">LoRA triggers</label>
      <input type="text" id="gpl-lora-trig" class="gpl-lora-trig" placeholder="short tags only — e.g. grwth   (put growth description in Intent below)" spellcheck="false" autocomplete="off">
    </div>
    <textarea class="gpl-prompt gpl-intent" id="gpl-intent" placeholder="What happens… e.g. she grows rapidly into a giantess, steps out of the car…"></textarea>
  </div>

  <div class="gpl-write-col gpl-write-out">
    <div class="gpl-lbl-row">
      <div class="gpl-lbl gpl-lbl-script">LTX Script</div>
      <select id="gpl-history" class="gpl-history" data-tip="Reload a previous generated script">
        <option value="">History…</option>
      </select>
    </div>
    <textarea class="gpl-prompt gpl-out" id="gpl-out" placeholder="Generate fills here…  ·  Refine rewrites this in place"></textarea>
    <div class="gpl-cont-strip" id="gpl-cont-strip" data-tip="Continuity (wardrobe/pose) when Carry is on">—</div>
    <div class="gpl-actions">
      <button type="button" class="gpl-btn-prev" id="gpl-preview" data-tip="Show the full system + user prompt the LLM would receive (no generate)">Preview</button>
      <button type="button" class="gpl-btn-prev" id="gpl-copy" data-tip="Copy LTX script to clipboard">Copy</button>
      <button type="button" class="gpl-btn-refine" id="gpl-refine" data-tip="Rewrite current script using Intent as the revision request">Refine</button>
      <button type="button" class="gpl-btn gpl-btn-gen" id="gpl-gen" data-tip="Generate a new LTX script from all controls + intent. Same intent again → Re-roll (new seed, model stays warm).">Generate</button>
    </div>
    <div class="gpl-st" id="gpl-st" data-tip="Status: writing, densifying, errors, elapsed"></div>
  </div>
</div>

<div class="gpl-cogpanel" id="gpl-cogpanel">
  <div class="clbl" data-tip="Where the LLM lives — Local managed, LM Studio, or Ollama">LLM Server <span class="gpl-conn-dot" id="gpl-conn-dot" data-tip="Connection status: green = healthy"></span></div>
  <div class="gpl-be-row" id="gpl-backend-row">
    <button type="button" class="gpl-be-btn on" data-be="llama.cpp (managed)" data-tip="Managed llama-server.exe on this machine">🖥 Local<span class="gpl-be-sub">llama.cpp</span></button>
    <button type="button" class="gpl-be-btn" data-be="LM Studio (OpenAI-compatible)" data-tip="Connect to LM Studio OpenAI API (usually :1234)">🔌 LM Studio<span class="gpl-be-sub">connect</span></button>
    <button type="button" class="gpl-be-btn" data-be="Ollama" data-tip="Connect to Ollama HTTP API (usually :11434)">🦙 Ollama<span class="gpl-be-sub">connect</span></button>
  </div>
  <div class="gpl-cogrow"><input id="gpl-server-url" placeholder="http://127.0.0.1:8080" data-tip="Server base URL"><button type="button" id="gpl-probe" data-tip="Test if the LLM server is reachable">⟳</button></div>
  <div id="gpl-external-block" style="display:none">
    <div class="clbl" data-tip="Model id the remote server expects">Model name <span style="opacity:.55;font-weight:400">(as server reports)</span></div>
    <input id="gpl-remote-model" placeholder="local" data-tip="Exact model id from LM Studio / Ollama">
    <div class="gpl-ext-note" id="gpl-conn-hint">Start LM Studio with a model loaded — this only connects (model name: local or exact id).</div>
  </div>
  <div id="gpl-managed-block">
    <div class="clbl" data-tip="Path to llama-server.exe">llama-server.exe</div>
    <input id="gpl-llama-exe" placeholder="C:\\llama\\llama-server.exe" data-tip="Full path to llama-server executable">
    <div class="clbl" data-tip="Folder containing GGUF models">Models folder</div>
    <div class="gpl-cogrow"><input id="gpl-models-dir" placeholder="C:\\models" data-tip="Scan this folder for .gguf files"><button type="button" id="gpl-scan" data-tip="Rescan models folder">⟳</button></div>
    <div class="clbl" data-tip="Text / multimodal GGUF to load">Model (GGUF)</div>
    <select id="gpl-model" data-tip="GGUF model file for generation"></select>
    <div class="clbl" data-tip="Vision projector for I2V image understanding">Vision mmproj</div>
    <select id="gpl-mm" data-tip="mmproj for I2V (text-only if None)"></select>
  </div>
  <button type="button" class="gpl-cog-save" id="gpl-save-conn" data-tip="Persist server URL, backend, and model choices">Save connection &amp; models</button>
  <div class="clbl" data-tip="LLM sampling temperature (0 = deterministic, higher = freer)">Sampler temp</div>
  <input type="number" id="gpl-temp" min="0" max="1.5" step="0.05" value="0.55" data-tip="Temperature for script generation">

  <div class="clbl" style="margin-top:10px;border-top:1px solid rgba(255,255,255,.12);padding-top:10px" data-tip="Look &amp; feel of this node panel">Look</div>
  <label class="gpl-check cog" data-tip="ON = stock Comfy look. Colour dots paint the NODE SHELL; selected chips/Generate use that colour as accent. OFF = theme packs."><input type="checkbox" id="gpl-comfy-native"> ComfyUI native look</label>
  <div style="font:500 10px system-ui,sans-serif;color:#888;margin:0 0 8px;line-height:1.35">
    Colour dots → node shell + chip/Generate accents. Inner boxes stay dark so text stays readable (same on LoraForge).
  </div>
  <div class="clbl" style="margin-top:4px" data-tip="Colour themes (ignored while ComfyUI native look is ON)">Theme pack</div>
  <select id="gpl-theme" data-tip="Shared with LoraForge — disabled while ComfyUI native look is on">
    ${themeOptionsHtml()}
  </select>

  <div class="clbl" style="margin-top:10px;border-top:1px solid rgba(255,255,255,.12);padding-top:10px" data-tip="LLM stays loaded after Generate until you press Comfy Queue/Run">Session</div>
  <label class="gpl-check cog" data-tip="ON (default): LLM stays loaded after Generate/Refine so you can iterate. Comfy Queue/Run kills it and frees VRAM for LTX. OFF = free immediately after each Generate (old behaviour)."><input type="checkbox" id="gpl-keep-warm" checked> Keep LLM warm until Queue/Run</label>
  <label class="gpl-check cog" data-tip="After the model finishes, run CANON repair (head+torso, silent strip, facing jumps, bra path, and when Music→Background: kill shout-over-music + loud-score lines). Turn OFF to keep raw model text. Streaming already shows raw; this controls the final committed script."><input type="checkbox" id="gpl-repair" checked> Post-repair scrub (final pass)</label>
  <div style="font:500 10px JetBrains Mono;color:#8a7fa8;margin:0 0 8px;line-height:1.35">
    Stream = raw tokens. When scrub is <b>on</b>, the finished box is repaired. When <b>off</b>, the box keeps raw model output.
  </div>

  <div class="clbl" style="margin-top:10px;border-top:1px solid rgba(255,200,87,.28);padding-top:10px;color:var(--gold)" data-tip="Optional extra LLM pass that grades the draft against your checklist before the box commits">✦ Self-check (optional extra pass)</div>
  <label class="gpl-check cog" data-tip="OFF by default. When ON: after draft (+ densify/scrub), the model re-reads the script and answers your checklist. Adds a few seconds."><input type="checkbox" id="gpl-self-check"> Self-check before commit</label>
  <div style="font:500 10px JetBrains Mono;color:#8a7fa8;margin:2px 0 6px;line-height:1.35">
    Off = normal generate. On = model asks itself your questions, then either <b>fixes</b> fails or <b>reports</b> only.
  </div>
  <div class="gpl-inline" style="margin:4px 0;gap:8px;flex-wrap:wrap">
    <label style="font:600 10px JetBrains Mono;color:var(--muted)">Mode</label>
    <select id="gpl-self-check-mode" style="flex:1;min-width:10em" data-tip="Fix = rewrite fails then commit. Report = show pass/fail in status, keep draft.">
      <option value="fix">Fix fails → commit</option>
      <option value="report">Report only (no rewrite)</option>
    </select>
  </div>
  <div style="font:600 9px JetBrains Mono;color:#8a7fa8;margin:6px 0 4px">Checklist chips (selected = questions)</div>
  <div id="gpl-self-check-chips" style="display:flex;flex-wrap:wrap;gap:5px;margin:0 0 8px"></div>
  <div style="font:500 9px JetBrains Mono;color:#6a6080;margin:0 0 8px;line-height:1.35">
    Smart: re-reads Intent into beats + HIT/MISS scan, auto music/dance/pacing. Also auto I2V / silent / POV / triggers / gravure. Status shows pass·fail after generate.
  </div>

  <button type="button" class="gpl-cog-save" id="gpl-kill-llm" style="margin-top:8px;background:rgba(180,40,60,.25);border-color:rgba(255,80,100,.35)" data-tip="Stop llama-server and free VRAM">Kill LLM / free VRAM</button>

  <details class="gpl-adv" id="gpl-adv-layout">
    <summary class="gpl-adv-sum" data-tip="Node size, insets, hero area, typography — collapsed by default">
      Advanced · node size &amp; layout
    </summary>
    <div class="gpl-adv-body">
      <div class="clbl" style="margin-top:8px;color:var(--gold)" data-tip="Pinned node shell — drag corner freely (grow + shrink). Default 1400, min 720.">✦ NODE SIZE (drag corner both ways)</div>
      <div style="font:500 10px JetBrains Mono;color:#8a7fa8;margin:2px 0 6px;line-height:1.35">
        Drag the node corner to grow or shrink. Size is saved; content scrolls if shorter than the UI.
      </div>
      <div class="gpl-inline" style="margin:4px 0">
        <label style="min-width:4.5em">Height <span class="val" id="val-node-h">1400</span></label>
        <input type="range" id="sl-node-h" min="720" max="2400" step="10" value="1400" style="flex:1;accent-color:#ffc857">
      </div>
      <div class="gpl-inline" style="margin:4px 0">
        <label style="min-width:4.5em">Width <span class="val" id="val-node-w">920</span></label>
        <input type="range" id="sl-node-w" min="580" max="1200" step="10" value="920" style="flex:1;accent-color:#ffc857">
      </div>
      <div style="display:flex;gap:6px;margin:6px 0 10px">
        <button type="button" class="gpl-cog-save" id="gpl-apply-size" style="flex:1;font-size:11px;padding:8px">Apply size</button>
        <button type="button" id="gpl-size-compact" style="flex:0 0 auto;padding:8px 12px;font-size:11px;border-radius:6px;border:1px solid rgba(255,200,87,.35);background:rgba(255,200,87,.1);color:var(--gold);cursor:pointer" title="Reset to default 920×1400">Default size</button>
      </div>

      <div class="clbl" style="margin-top:8px;border-top:1px solid rgba(255,255,255,.12);padding-top:8px">Fine layout (optional)</div>
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
      <div class="gpl-inline" style="margin:1px 0"><label title="Does NOT resize the Comfy node — use NODE SIZE above">Content pad floor <span class="val" id="val-floor">584</span></label><input type="range" id="sl-floor" min="520" max="980" step="4" value="584" style="flex:1;accent-color:#ffc857"></div>

      <div style="display:flex; gap:6px; margin-top:8px;">
        <button type="button" class="gpl-cog-save" id="gpl-save-layout" style="flex:1;font-size:11px;padding:7px">Save Layout</button>
        <button type="button" id="gpl-reset-layout" style="flex:0 0 auto;padding:7px 12px;font-size:11px;border-radius:6px;border:1px solid rgba(255,255,255,.15);background:rgba(0,0,0,.4);color:var(--muted);cursor:pointer">Reset</button>
      </div>
      <div class="gpl-ext-note" style="font-size:10px;margin-top:4px">Drag to preview live. Click Save when perfect. Persisted until Reset.</div>
    </div>
  </details>
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
    // Custom style menu (per-option tips) + floating tooltips
    wireStylePicker(container);
    wireTooltips(container);

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
        // Do not apply floorMin as minHeight — that blocked corner shrink
        container.style.minHeight = "0";
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
        container.style.minHeight = "0";
      }

      // Early look: Comfy native OR theme pack
      const earlyNative = localStorage.getItem("pfld_comfy_native") === "1";
      if (earlyNative) {
        container.classList.add("gpl-comfy-native");
        // Near-black theme shells → default purple; user palette picks kept
        const shell = ensureComfyNativeShell(node);
        applyComfyAccentVars(container, shell.color, shell.bgcolor);
      } else {
        const { theme: earlyT } = resolveTheme(loadSharedThemeKey());
        Object.entries(earlyT.pf || {}).forEach(([k, v]) => container.style.setProperty(k, v));
        if (earlyT.node) {
          node.color = earlyT.node.color;
          node.bgcolor = earlyT.node.bgcolor;
        }
      }
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

    // Sticky size: free corner resize both ways. Soft floor only (minNodeH).
    const SIZE_H_KEY = "pfld_node_h";
    const SIZE_W_KEY = "pfld_node_w";
    const NODE_MIN_H = LAYOUT.minNodeH || 720;
    const NODE_MAX_H = LAYOUT.maxNodeH || 2400;
    const NODE_DEF_H = LAYOUT.defaultNodeH || 1400;
    const NODE_DEF_W = LAYOUT.defaultNodeW || 920;
    function clampNodeH(h) {
      const n = Math.round(Number(h) || NODE_DEF_H);
      return Math.min(NODE_MAX_H, Math.max(NODE_MIN_H, n));
    }
    function loadPinnedSize() {
      try {
        let h = parseInt(localStorage.getItem(SIZE_H_KEY), 10);
        let w = parseInt(localStorage.getItem(SIZE_W_KEY), 10);
        // Honor any saved pin in the free-resize range (no force-up to 1400)
        if (Number.isFinite(h) && h >= 400) {
          node._savedH = clampNodeH(h);
          node._userResized = true;
        } else {
          node._savedH = NODE_DEF_H;
        }
        if (Number.isFinite(w) && w >= LAYOUT.minNodeW) {
          node._userW = Math.min(Math.max(w, LAYOUT.minNodeW), 1200);
        } else {
          node._userW = NODE_DEF_W;
        }
      } catch (_) {
        node._savedH = NODE_DEF_H;
        node._userW = NODE_DEF_W;
      }
    }
    function savePinnedSize() {
      try {
        if (node._savedH) localStorage.setItem(SIZE_H_KEY, String(Math.round(node._savedH)));
        if (node._userW) localStorage.setItem(SIZE_W_KEY, String(Math.round(node._userW)));
      } catch (_) { /* */ }
    }
    loadPinnedSize();

    function paintSizeSliders() {
      const h = clampNodeH(node._savedH || node.size?.[1] || NODE_DEF_H);
      const w = node._userW || node.size?.[0] || NODE_DEF_W;
      const sh = $("#sl-node-h"), swEl = $("#sl-node-w");
      const vh = $("#val-node-h"), vw = $("#val-node-w");
      if (sh) sh.value = String(Math.round(h));
      if (swEl) swEl.value = String(Math.round(w));
      if (vh) vh.textContent = String(Math.round(h));
      if (vw) vw.textContent = String(Math.round(w));
    }

    /** Manual size only — NEVER grows from content measure. Soft floor = minNodeH. */
    function applyNodeSize(w, h, persist = true) {
      w = Math.max(LAYOUT.minNodeW, Math.round(Number(w) || NODE_DEF_W));
      h = clampNodeH(h || NODE_DEF_H);
      node._userW = w;
      node._savedH = h;
      node._userResized = true;
      node.setSize([w, h]);
      // Widget body = remaining space inside pin (scroll if content taller)
      const bodyH = Math.max(280, h - widgetTopOffset() - 18);
      _floor = Math.max(280, h - widgetTopOffset() - 14);
      if (container) {
        container.style.height = `${bodyH}px`;
        container.style.maxHeight = `${bodyH}px`;
        // Never force content taller than the pin (that blocked corner shrink)
        container.style.minHeight = "0";
        container.style.overflowY = "auto";
      }
      if (persist) savePinnedSize();
      paintSizeSliders();
      try { app.graph?.setDirtyCanvas(true, true); } catch (_) { /* */ }
    }

    function snapNodeHeight() {
      if (!node.size) return;
      // Hold the user pin only — never content-driven growth.
      const h = clampNodeH(node._savedH || NODE_DEF_H);
      const w = node._userW || node.size[0] || NODE_DEF_W;
      node._savedH = h;
      if (Math.abs(node.size[1] - h) > 1 || Math.abs(node.size[0] - w) > 1) {
        node.setSize([w, h]);
      }
    }
    function measureFloor() {
      // Does NOT resize the node. Only sets internal widget floor to fit the pin.
      if (node._savedH) {
        _floor = Math.max(280, node._savedH - widgetTopOffset() - 14);
      } else {
        _floor = _FLOOR_MIN;
      }
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
      // Fill pinned node; scroll inside if content is taller — never push node height.
      const pinH = clampNodeH(node._savedH || node.size?.[1] || NODE_DEF_H);
      const bodyH = Math.max(280, pinH - widgetTopOffset() - 18);
      container.style.height = `${bodyH}px`;
      container.style.maxHeight = `${bodyH}px`;
      container.style.minHeight = "0";
      container.style.overflowY = "auto";
    }
    const scheduleLayout = () => requestAnimationFrame(() => {
      // No measure-driven resize — only fit UI inside current pin.
      if (node._savedH) {
        _floor = Math.max(280, node._savedH - widgetTopOffset() - 14);
      }
      fitContainer();
      resMaster?.resync?.();
      imageCarousel?.resync?.();
      app.graph?.setDirtyCanvas(false, true);
    });

    // CRITICAL: report only the soft min height. If we report the pinned height,
    // Comfy/LiteGraph refuses corner-drag shrink (min size = current size).
    uiWidget.computeSize = (w) => {
      const width = Math.max(10, (node.size?.[0] || w || NODE_DEF_W) - 4);
      const minBody = Math.max(280, NODE_MIN_H - widgetTopOffset() - 12);
      return [width, minBody];
    };
    node._userW = node._userW || NODE_DEF_W;
    node._savedH = clampNodeH(node._savedH || NODE_DEF_H);
    // Open at pinned/default size; user can freely grow or shrink after
    applyNodeSize(node._userW || NODE_DEF_W, node._savedH, true);
    node.onResize = (size) => {
      // User corner drag = new pin in either direction (soft floor only).
      size[0] = Math.max(size[0], LAYOUT.minNodeW);
      size[1] = clampNodeH(size[1]);
      node._userW = size[0];
      node._savedH = size[1];
      node._userResized = true;
      savePinnedSize();
      paintSizeSliders();
      // Keep body inside the new shell so DOM min-height can't fight the drag
      const bodyH = Math.max(280, size[1] - widgetTopOffset() - 18);
      _floor = Math.max(280, size[1] - widgetTopOffset() - 14);
      if (container) {
        container.style.height = `${bodyH}px`;
        container.style.maxHeight = `${bodyH}px`;
        container.style.minHeight = "0";
        container.style.overflowY = "auto";
      }
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
    // Priority: wired duration_s/fps inputs win. Else Dur slider (localDur).
    // Badge + slider always show the same effective values so they never fight.
    const getDur = () => {
      if (isInputWired("duration_s")) {
        const v = parseFloat(getLinkedVal("duration_s", localDur));
        return Number.isFinite(v) && v > 0 ? v : localDur;
      }
      return localDur;
    };
    const getFps = () => {
      if (isInputWired("fps")) {
        const v = parseInt(getLinkedVal("fps", 24), 10);
        return Number.isFinite(v) && v > 0 ? v : 24;
      }
      return 24;
    };

    function paintDurSlider() {
      const durEl = $("#gpl-dur");
      const valEl = $("#gpl-dur-val");
      const wrap = durEl?.closest?.(".gpl-dur-inline") || durEl?.parentElement;
      const d = getDur();
      const wiredDur = isInputWired("duration_s");
      if (durEl) {
        durEl.value = String(d);
        durEl.disabled = wiredDur;
        durEl.title = wiredDur
          ? "Locked — duration_s is wired (disconnect the input to use this slider)"
          : "Clip length used for Generate (when duration_s is not wired)";
      }
      if (valEl) {
        valEl.textContent = wiredDur ? `${d.toFixed(1)}s · wired` : `${d.toFixed(1)}s`;
      }
      if (wrap) wrap.classList.toggle("gpl-dur-wired", wiredDur);
    }

    function syncLive() {
      const el = $("#gpl-live");
      if (!el) return;
      const wired = isInputWired("duration_s") || isInputWired("fps");
      const warm = keepWarm ? " · warm" : "";
      const d = getDur();
      const f = getFps();
      // Compact live chip — seed lives in its own strip now
      el.textContent = `${d.toFixed(1)}s · ${f}fps · ${castMode}${warm}`;
      el.classList.toggle("wired", wired);
      el.title = wired
        ? "Duration/fps from wired inputs (slider locked while duration_s is connected)"
        : "Duration from Dur slider — wire duration_s / fps to override";
      paintDurSlider();
      paintSeedUI();
      const strip = $("#gpl-cont-strip");
      if (strip) {
        strip.textContent = lastContinuity
          ? `Continuity: ${lastContinuity.slice(0, 140)}${lastContinuity.length > 140 ? "…" : ""}`
          : "Continuity: (empty — generate once to lock state)";
        strip.classList.toggle("has", !!lastContinuity);
      }
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
    function syncMusicBgVisibility() {
      const wrap = $("#gpl-music-bg-wrap");
      const sel = $("#gpl-music");
      const v = (sel?.value || "").trim();
      const on = v && !/^none/i.test(v);
      if (wrap) wrap.style.display = on ? "" : "none";
      if ($("#gpl-music-bg")) $("#gpl-music-bg").checked = musicBgOn;
    }
    syncMusicBgVisibility();
    $("#gpl-music")?.addEventListener("change", () => {
      syncMusicBgVisibility();
    });
    $("#gpl-music-bg")?.addEventListener("change", () => {
      musicBgOn = !!$("#gpl-music-bg")?.checked;
      try { localStorage.setItem("pfld_music_bg", musicBgOn ? "1" : "0"); } catch { /* */ }
      setSt(musicBgOn ? "Music → background (quiet under speech)" : "Music → in the mix (shout-over OK)");
    });
    refreshScenarioList();

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
      leadGender = $("#gpl-lead")?.value || leadGender || "auto";
      accentMode = $("#gpl-accent")?.value || accentMode || "auto";
      accentPartner = $("#gpl-accent-partner")?.value || accentPartner || "off";
      keepWarm = !!$("#gpl-keep-warm")?.checked;
      carryNext = !!$("#gpl-carry")?.checked;
      detailerOn = !!$("#gpl-detailer")?.checked;
      repairOn = $("#gpl-repair") ? !!$("#gpl-repair").checked : repairOn;
      selfCheckOn = $("#gpl-self-check") ? !!$("#gpl-self-check").checked : selfCheckOn;
      selfCheckMode = $("#gpl-self-check-mode")?.value || selfCheckMode || "fix";
      const energy = levelToEnergy(motionLevel);
      return {
        model_file: llmBackend === GPL_BACKENDS.MANAGED ? (gw("model_file")?.value || "None") : "None",
        mmproj_file: llmBackend === GPL_BACKENDS.MANAGED ? (gw("mmproj_file")?.value || "None (text-only)") : "None (text-only)",
        video_mode: videoMode,
        duration_s: getDur(),
        fps: getFps(),
        dialogue_tier: dlgTier,
        // qualitative axes (primary) + legacy numeric for old paths
        motion_level: motionLevel,
        mouth_heat: mouthHeat,
        intensity: energy,
        user_intent: ($("#gpl-intent")?.value || "").trim(),
        lora_triggers: ($("#gpl-lora-trig")?.value || "").trim(),
        image_b64: "",
        pov: povMode !== "off",
        pov_gender: povMode === "male" ? "male" : "female",
        cast: castMode,
        lead_gender: leadGender,
        accent_mode: accentMode,
        accent_partner: accentPartner,
        video_style: ($("#gpl-style")?.value || "None — off (no style path)"),
        continuity_state: carryNext ? (lastContinuity || (gw("continuity_state")?.value || "")) : "",
        keep_warm: keepWarm,
        detailer: detailerOn,
        repair: repairOn,
        self_check: selfCheckOn,
        self_check_mode: selfCheckMode,
        self_check_chips: selfCheckChips.slice(),
        seed: seedForGenerate(),
        environment: $("#gpl-env")?.value,
        scenario: $("#gpl-scn")?.value,
        camera_move: $("#gpl-cam")?.value,
        music: ($("#gpl-music")?.value || "").trim(),
        music_bg: (() => {
          const v = ($("#gpl-music")?.value || "").trim();
          if (!v || /^none/i.test(v)) return false;
          return !!$("#gpl-music-bg")?.checked || musicBgOn;
        })(),
      };
    }

    function styleSelfCheckChip(b, on) {
      b.classList.toggle("on", !!on);
      b.style.cssText = "font:600 10px JetBrains Mono;padding:4px 8px;border-radius:999px;cursor:pointer;"
        + (on
          ? "border:1px solid rgba(255,200,87,.55);background:rgba(255,200,87,.14);color:var(--gold)"
          : "border:1px solid rgba(255,255,255,.12);background:rgba(0,0,0,.25);color:var(--muted)");
    }

    function paintSelfCheckChips() {
      const host = $("#gpl-self-check-chips");
      if (!host) return;
      // Only rebuild once — toggling updates the existing button in place so the
      // cog panel does not lose the click target and close via document handler.
      if (host.dataset.built === "1") {
        host.querySelectorAll("button[data-id]").forEach((b) => {
          styleSelfCheckChip(b, selfCheckChips.includes(b.dataset.id));
        });
        return;
      }
      host.innerHTML = "";
      SELF_CHECK_CHIPS.forEach((c) => {
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = c.label;
        b.dataset.id = c.id;
        b.title = c.label + " — toggle question";
        styleSelfCheckChip(b, selfCheckChips.includes(c.id));
        const keepOpen = (e) => { e.preventDefault(); e.stopPropagation(); };
        b.addEventListener("mousedown", keepOpen);
        b.addEventListener("pointerdown", keepOpen);
        b.addEventListener("click", (e) => {
          e.preventDefault();
          e.stopPropagation();
          if (selfCheckChips.includes(c.id)) {
            selfCheckChips = selfCheckChips.filter((x) => x !== c.id);
          } else {
            selfCheckChips = selfCheckChips.concat([c.id]);
          }
          if (!selfCheckChips.length) selfCheckChips = SELF_CHECK_DEFAULT.slice();
          try { localStorage.setItem("pfld_self_check_chips", JSON.stringify(selfCheckChips)); } catch { /* */ }
          styleSelfCheckChip(b, selfCheckChips.includes(c.id));
        });
        host.appendChild(b);
      });
      host.dataset.built = "1";
    }

    async function applyRecipeHints(key) {
      if (!key || !String(key).includes("Recipe")) return;
      try {
        const r = await fetch(`/pfld/get_scenario?key=${encodeURIComponent(key)}`);
        const j = await r.json();
        if (!j.ok) return;
        if (j.cast_hint && ["solo", "pair", "group"].includes(j.cast_hint)) {
          castMode = j.cast_hint;
          localStorage.setItem("pfld_cast", castMode);
          $("#gpl-cast")?.querySelectorAll(".gpl-chip").forEach((b) => {
            b.classList.toggle("on", b.dataset.v === castMode);
          });
          sw("cast", castMode);
        }
        if (j.motion) setMotionLevel(String(j.motion).toLowerCase());
        if (j.mouth_heat) setMouthHeat(String(j.mouth_heat).toLowerCase());
        if (j.duration_hint && !isInputWired("duration_s")) {
          localDur = parseFloat(j.duration_hint) || localDur;
          localStorage.setItem("pfld_dur", String(localDur));
          if ($("#gpl-dur")) $("#gpl-dur").value = String(localDur);
          if ($("#gpl-dur-val")) $("#gpl-dur-val").textContent = `${localDur}s`;
          sw("duration_s", localDur);
        }
        if (j.dialogue_tier_hint) {
          const t = j.dialogue_tier_hint === "none" ? "none"
            : (j.dialogue_tier_hint === "talkative" ? "talkative" : "standard");
          dlgTier = t;
          localStorage.setItem("pfld_dlg", dlgTier);
          $("#gpl-dlg")?.querySelectorAll(".gpl-chip").forEach((b) => {
            b.classList.toggle("on", b.dataset.v === dlgTier);
          });
          sw("dialogue_tier", dlgTier);
        }
        if (j.pov_hint === "female" || j.pov_hint === "male") {
          povMode = j.pov_hint;
          localStorage.setItem("pfld_pov", povMode);
          $("#gpl-pov")?.querySelectorAll(".gpl-chip").forEach((b) => {
            b.classList.toggle("on", b.dataset.v === povMode);
          });
          sw("pov", true);
          sw("pov_gender", povMode);
        }
        setSt("Recipe hints applied (cast / intensity / dur / talk) — tweak freely.");
        setTimeout(() => setSt(""), 2200);
      } catch (_) { /* ignore */ }
    }

    async function refreshScenarioList() {
      const sel = $("#gpl-scn");
      if (!sel) return;
      const prev = sel.value;
      const label = $("#gpl-scn-label");
      if (label) {
        label.textContent = videoMode === "t2v" ? "T2V shot recipe" : "I2V scenario";
      }
      try {
        const r = await fetch(`/pfld/scenario_keys?mode=${encodeURIComponent(videoMode)}`);
        const j = await r.json();
        const keys = (j.ok && j.keys) ? j.keys : null;
        if (keys && keys.length) {
          sel.innerHTML = "";
          keys.forEach((k) => {
            const opt = document.createElement("option");
            opt.value = k;
            opt.textContent = k;
            sel.appendChild(opt);
          });
          if (keys.includes(prev)) sel.value = prev;
          else sel.selectedIndex = 0;
          sw("scenario", sel.value);
          return;
        }
      } catch (e) { /* fall through to widget values */ }
      // Fallback: all widget options (unfiltered)
      fillSelect(sel, "scenario");
      if (prev) sel.value = prev;
    }

    function loadHistory() {
      try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]"); }
      catch { return []; }
    }
    function saveHistory(list) {
      try { localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, HISTORY_MAX))); }
      catch { /* quota */ }
    }
    function pushHistory(intent, script) {
      const s = (script || "").trim();
      if (!s) return;
      const entry = {
        t: Date.now(),
        intent: (intent || "").slice(0, 120),
        script: s,
        continuity: lastContinuity || "",
      };
      const list = loadHistory().filter((x) => x.script !== s);
      list.unshift(entry);
      saveHistory(list);
      paintHistory();
    }
    function paintHistory() {
      const sel = $("#gpl-history");
      if (!sel) return;
      const list = loadHistory();
      const cur = sel.value;
      sel.innerHTML = `<option value="">History (${list.length})…</option>`;
      list.forEach((e, i) => {
        const opt = document.createElement("option");
        opt.value = String(i);
        const when = new Date(e.t).toLocaleString();
        opt.textContent = `${when} · ${(e.intent || "—").slice(0, 40)} · ${e.script.length}c`;
        sel.appendChild(opt);
      });
      if (cur) sel.value = cur;
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

    $("#gpl-cog")?.addEventListener("click", (e) => {
      e.stopPropagation();
      const p = $("#gpl-cogpanel");
      const opening = !p?.classList.contains("open");
      p?.classList.toggle("open");
      if (opening) {
        paintSelfCheckChips();
        probeConn();
      } else {
        // Persist checklist when cog closes (also saved live on each chip click)
        try { localStorage.setItem("pfld_self_check_chips", JSON.stringify(selfCheckChips)); } catch { /* */ }
      }
    });
    document.addEventListener("click", (e) => {
      const p = $("#gpl-cogpanel"), c = $("#gpl-cog");
      if (!p?.classList.contains("open")) return;
      // Stay open for any click inside the panel (chips, selects, etc.)
      if (p.contains(e.target) || c?.contains(e.target)) return;
      p.classList.remove("open");
      try { localStorage.setItem("pfld_self_check_chips", JSON.stringify(selfCheckChips)); } catch { /* */ }
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

      // Content floor is cosmetic only — never force DOM taller than the pin
      // (that used to block corner-drag shrink). Scroll inside instead.
      const pinH = clampNodeH(node._savedH || node.size?.[1] || NODE_DEF_H);
      const bodyCap = Math.max(280, pinH - widgetTopOffset() - 18);
      container.style.minHeight = "0";
      container.style.height = `${bodyCap}px`;
      container.style.maxHeight = `${bodyCap}px`;
      container.style.overflowY = "auto";

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

      // Refit UI inside the *existing* pin — never setSize from layout sliders.
      if (typeof fitContainer === 'function') {
        fitContainer();
      } else if (typeof scheduleLayout === 'function') {
        scheduleLayout();
      }
      resMaster?.resync?.();

      // Apply bbox offset if available (live move of the cyan resolution box)
      if (resMaster && typeof resMaster.setBoxOffset === 'function') {
        resMaster.setBoxOffset(boxX, boxY);
      }

      requestAnimationFrame(() => {
        resMaster?.resync?.();
        imageCarousel?.resync?.();
        // Hold pin steady (in case LiteGraph nudged during resync)
        if (typeof snapNodeHeight === 'function') snapNodeHeight();
        if (typeof fitContainer === 'function') fitContainer();
        if (typeof paintSizeSliders === 'function') paintSizeSliders();
      });
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

    // ★ Node size sliders — explicit, no auto-grow
    const bindNodeSizeSliders = () => {
      const sh = $("#sl-node-h");
      const swEl = $("#sl-node-w");
      const live = () => {
        const h = parseInt(sh?.value, 10) || NODE_DEF_H;
        const w = parseInt(swEl?.value, 10) || NODE_DEF_W;
        if ($("#val-node-h")) $("#val-node-h").textContent = String(h);
        if ($("#val-node-w")) $("#val-node-w").textContent = String(w);
        applyNodeSize(w, h, true);
      };
      sh?.addEventListener("input", live);
      swEl?.addEventListener("input", live);
      $("#gpl-apply-size")?.addEventListener("click", live);
      $("#gpl-size-compact")?.addEventListener("click", () => {
        if (sh) sh.value = String(NODE_DEF_H);
        if (swEl) swEl.value = String(NODE_DEF_W);
        live();
        setSt(`Node size → default ${NODE_DEF_W}×${NODE_DEF_H}`);
      });
      paintSizeSliders();
    };
    bindNodeSizeSliders();

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
      // Persist insets/hero only — do NOT change node.size / _savedH
      applyDebug(true);
      snapNodeHeight();
      paintSizeSliders();
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
        localStorage.removeItem(SIZE_H_KEY);
        localStorage.removeItem(SIZE_W_KEY);
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
      node._savedH = NODE_DEF_H;
      node._userResized = true;
      try {
        localStorage.removeItem(SIZE_H_KEY);
        localStorage.removeItem(SIZE_W_KEY);
      } catch (_) { /* */ }
      // Reset to default tall shell (1400)
      applyNodeSize(NODE_DEF_W, NODE_DEF_H, true);

      LAYOUT.heroResBasis = 390;
      LAYOUT.heroStageW = 135;
      LAYOUT.heroMinH = 210;
      LAYOUT.floorMin = 680;

      // Re-apply defaults visually (live)
      applyDebug(false);
      if (!comfyNative) applyTheme("default", false);
      scheduleLayout?.();
    });

    // ── Look modes ──────────────────────────────────────────────────────────
    // comfyNative = full stock-Comfy chrome (class-driven CSS). Not a colour pack.
    // Theme packs only apply when native is OFF.
    // When native is ON: Comfy's colour dots (node.color) drive button accents.
    let comfyNative = localStorage.getItem("pfld_comfy_native") === "1";
    let _comfyColorWatch = null;
    let _lastComfyColorKey = "";

    function syncComfyAccentsFromNode() {
      if (!comfyNative) return;
      const c = node.color || COMFY_DEFAULT_NODE_COLOR;
      const bg = node.bgcolor || COMFY_DEFAULT_NODE_BG;
      const key = `${c}|${bg}`;
      if (key === _lastComfyColorKey) return;
      _lastComfyColorKey = key;
      applyComfyAccentVars(container, c, bg);
    }

    function startComfyColorWatch() {
      stopComfyColorWatch();
      syncComfyAccentsFromNode();
      // Comfy palette dots set node.color with no event — light poll while native is on
      _comfyColorWatch = setInterval(syncComfyAccentsFromNode, 250);
    }
    function stopComfyColorWatch() {
      if (_comfyColorWatch) {
        clearInterval(_comfyColorWatch);
        _comfyColorWatch = null;
      }
      _lastComfyColorKey = "";
    }

    function applyComfyNative(on, save = true) {
      comfyNative = !!on;
      container.classList.toggle("gpl-comfy-native", comfyNative);
      if ($("#gpl-comfy-native")) $("#gpl-comfy-native").checked = comfyNative;
      const themeSel = $("#gpl-theme");
      if (themeSel) {
        themeSel.disabled = comfyNative;
        themeSel.title = comfyNative
          ? "Theme packs disabled while ComfyUI native look is on — use the node colour dots"
          : "Colour theme pack";
      }
      if (comfyNative) {
        // Outer shell = Comfy colour dots. Near-black theme leftovers → default
        // purple so native mode never looks stuck grey. User palette picks kept.
        try {
          ensureComfyNativeShell(node);
        } catch { /* */ }
        _lastComfyColorKey = ""; // force accent re-apply
        startComfyColorWatch();
      } else {
        stopComfyColorWatch();
        applyTheme(loadSharedThemeKey(), false);
      }
      if (save) {
        try { localStorage.setItem("pfld_comfy_native", comfyNative ? "1" : "0"); } catch { /* */ }
        // Same-tab LoraForge listens via custom event (storage event is cross-tab only)
        try {
          window.dispatchEvent(new CustomEvent("pfld-comfy-native", { detail: { on: comfyNative } }));
        } catch { /* */ }
      }
      try { app.graph?.setDirtyCanvas(true, true); } catch { /* */ }
    }

    // Theme handling (swap colors only, layout stays identical).
    // Keys are shared with LoraForge via themes_ld.js + localStorage pfld_theme.
    function applyTheme(name, save = true) {
      if (comfyNative) {
        // Still remember the pick for when user leaves native mode
        const { id } = resolveTheme(name);
        const sel = $("#gpl-theme");
        if (sel) sel.value = id;
        if (save) saveSharedThemeKey(id);
        return;
      }
      const { id, theme } = resolveTheme(name);
      const pf = theme.pf || THEMES.default;
      Object.entries(pf).forEach(([k, v]) => {
        container.style.setProperty(k, v);
      });
      // Comfy node chrome (title bar) matches panel
      if (theme.node) {
        try {
          node.color = theme.node.color;
          node.bgcolor = theme.node.bgcolor;
          node.setDirtyCanvas?.(true, true);
        } catch { /* */ }
      }
      const sel = $("#gpl-theme");
      if (sel) sel.value = id;
      if (save) saveSharedThemeKey(id);
    }

    $("#gpl-theme")?.addEventListener("change", (e) => {
      applyTheme(e.target.value, true);
    });
    $("#gpl-comfy-native")?.addEventListener("change", () => {
      applyComfyNative(!!$("#gpl-comfy-native")?.checked, true);
      setSt(comfyNative
        ? "Look → ComfyUI native (stock dark widgets)"
        : "Look → PromptForge themed chrome");
    });
    // Advanced layout accordion — collapsed by default; remember if user opens it
    {
      const adv = $("#gpl-adv-layout");
      if (adv) {
        try {
          if (localStorage.getItem("pfld_adv_layout_open") === "1") adv.open = true;
        } catch { /* */ }
        adv.addEventListener("toggle", () => {
          try {
            localStorage.setItem("pfld_adv_layout_open", adv.open ? "1" : "0");
          } catch { /* */ }
        });
      }
    }
    // If LoraForge cycles the shared theme in another node, pick it up
    window.addEventListener("storage", (e) => {
      if (e.key === "pfld_theme" && e.newValue) applyTheme(e.newValue, false);
      if (e.key === "pfld_comfy_native") {
        applyComfyNative(e.newValue === "1", false);
      }
    });
    window.addEventListener("pfld-comfy-native", (e) => {
      const on = !!(e?.detail?.on);
      if (on === comfyNative) return;
      applyComfyNative(on, false);
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

      // Load look mode + theme pack
      applyComfyNative(localStorage.getItem("pfld_comfy_native") === "1", false);
      if (!comfyNative) applyTheme(loadSharedThemeKey(), false);
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
    const setDlg = (t) => {
      dlgTier = t || "standard";
      localStorage.setItem("pfld_dlg", dlgTier);
      sw("dialogue_tier", dlgTier);
      // Keep chip paint honest (widget restore must not leave Silent unselected)
      $("#gpl-dlg")?.querySelectorAll(".gpl-chip").forEach((b) => {
        b.classList.toggle("on", b.dataset.v === dlgTier);
      });
    };
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
    const setCast = (c) => {
      castMode = c || "pair";
      localStorage.setItem("pfld_cast", castMode);
      sw("cast", castMode);
      $("#gpl-cast")?.querySelectorAll(".gpl-chip").forEach((b) => {
        b.classList.toggle("on", b.dataset.v === castMode);
      });
      syncLive();
    };
    bindChips("gpl-dlg", setDlg);
    bindChips("gpl-pov", setPov);
    bindChips("gpl-cast", setCast);
    // Prefer UI/localStorage tier over widget default ("standard") so Silent survives reload
    {
      const wDlg = gw("dialogue_tier")?.value;
      const lsDlg = localStorage.getItem("pfld_dlg");
      const pick = (lsDlg && ["none", "standard", "talkative"].includes(lsDlg))
        ? lsDlg
        : (wDlg && ["none", "standard", "talkative"].includes(wDlg) ? wDlg : (dlgTier || "standard"));
      setDlg(pick);
    }
    setPov(povMode || "off");
    setCast(gw("cast")?.value || castMode || "pair");

    // Duration slider = local fallback. Wired duration_s always wins (slider locks).
    const durEl = $("#gpl-dur");
    if (durEl) {
      durEl.value = String(localDur);
      const onDurSlide = () => {
        if (isInputWired("duration_s")) {
          // Ignore drags while locked — snap UI back to wire
          paintDurSlider();
          return;
        }
        localDur = parseFloat(durEl.value) || 12;
        localStorage.setItem("pfld_dur", String(localDur));
        // Keep hidden widget in sync when Comfy exposes it (forceInput may omit it)
        try { sw("duration_s", localDur); } catch (_) { /* no widget */ }
        syncLive();
      };
      durEl.addEventListener("input", onDurSlide);
      paintDurSlider();
    }
    if ($("#gpl-lead")) {
      $("#gpl-lead").value = gw("lead_gender")?.value || leadGender || "auto";
      $("#gpl-lead").addEventListener("change", () => {
        leadGender = $("#gpl-lead").value || "auto";
        localStorage.setItem("pfld_lead", leadGender);
        sw("lead_gender", leadGender);
      });
    }
    if ($("#gpl-style")) {
      const vs0 = gw("video_style")?.value;
      const applyStyleVal = (v) => {
        if (!v) return;
        try {
          $("#gpl-style").value = v;
          $("#gpl-style")._pfldSyncStyleBtn?.();
        } catch (_) { /* */ }
      };
      if (vs0) applyStyleVal(vs0);
      $("#gpl-style").addEventListener("change", () => {
        try { sw("video_style", $("#gpl-style").value); } catch (_) {}
        localStorage.setItem("pfld_style", $("#gpl-style").value || "");
        $("#gpl-style")._pfldSyncStyleBtn?.();
      });
      try {
        const saved = localStorage.getItem("pfld_style");
        if (saved && !vs0) applyStyleVal(saved);
      } catch (_) {}
    }
    if ($("#gpl-accent")) {
      $("#gpl-accent").value = accentMode || "auto";
      $("#gpl-accent").addEventListener("change", () => {
        accentMode = $("#gpl-accent").value || "auto";
        localStorage.setItem("pfld_accent", accentMode);
        sw("accent_mode", accentMode);
      });
    }
    if ($("#gpl-keep-warm")) {
      $("#gpl-keep-warm").checked = keepWarm;
      $("#gpl-keep-warm").addEventListener("change", () => {
        keepWarm = !!$("#gpl-keep-warm").checked;
        localStorage.setItem("pfld_keep_warm", keepWarm ? "1" : "0");
        setSt(keepWarm
          ? "LLM stays warm after Generate — freed on Comfy Queue/Run"
          : "LLM free after each Generate (old)");
        syncLive();
      });
    }
    if ($("#gpl-repair")) {
      $("#gpl-repair").checked = repairOn;
      $("#gpl-repair").addEventListener("change", () => {
        repairOn = !!$("#gpl-repair").checked;
        localStorage.setItem("pfld_repair", repairOn ? "1" : "0");
        setSt(repairOn ? "Post-repair scrub ON" : "Post-repair scrub OFF — raw model text kept");
      });
    }
    if ($("#gpl-self-check")) {
      $("#gpl-self-check").checked = selfCheckOn;
      $("#gpl-self-check").addEventListener("change", () => {
        selfCheckOn = !!$("#gpl-self-check").checked;
        localStorage.setItem("pfld_self_check", selfCheckOn ? "1" : "0");
        setSt(selfCheckOn
          ? `Self-check ON (${selfCheckMode}) — extra QA pass after draft`
          : "Self-check OFF — normal generate");
      });
    }
    if ($("#gpl-self-check-mode")) {
      $("#gpl-self-check-mode").value = selfCheckMode;
      $("#gpl-self-check-mode").addEventListener("change", () => {
        selfCheckMode = $("#gpl-self-check-mode").value === "report" ? "report" : "fix";
        localStorage.setItem("pfld_self_check_mode", selfCheckMode);
        setSt(`Self-check mode → ${selfCheckMode}`);
      });
    }
    paintSelfCheckChips();
    if ($("#gpl-carry")) {
      $("#gpl-carry").checked = carryNext;
      $("#gpl-carry").addEventListener("change", () => {
        carryNext = !!$("#gpl-carry").checked;
        localStorage.setItem("pfld_carry", carryNext ? "1" : "0");
      });
    }
    $("#gpl-carry-clear")?.addEventListener("click", () => {
      lastContinuity = "";
      try { sw("continuity_state", ""); } catch (_) {}
      syncLive();
      setSt("Continuity cleared");
    });
    if ($("#gpl-detailer")) {
      $("#gpl-detailer").checked = detailerOn;
      $("#gpl-detailer").addEventListener("change", () => {
        detailerOn = !!$("#gpl-detailer").checked;
        localStorage.setItem("pfld_detailer", detailerOn ? "1" : "0");
      });
    }
    // Seed: header strip only (cog duplicate removed)
    paintSeedUI();
    container.querySelectorAll(".gpl-seed-mode-btn").forEach((b) => {
      b.addEventListener("click", () => {
        setSeedMode(b.dataset.mode || "random");
        setSt(`Seed mode → ${seedMode}`);
      });
    });
    const onSeedEdit = () => {
      const n = parseInt($("#gpl-seed-hd")?.value, 10);
      if (Number.isFinite(n) && n >= 0) {
        lastSeed = n >>> 0;
        try { localStorage.setItem("pfld_seed", String(lastSeed)); } catch { /* */ }
        paintSeedUI();
      }
    };
    $("#gpl-seed-hd")?.addEventListener("change", onSeedEdit);
    $("#gpl-seed-hd")?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") { e.preventDefault(); onSeedEdit(); }
    });
    const rollClick = () => {
      const s = rollSeed();
      setSt(`Seed → ${s}`);
    };
    $("#gpl-seed-roll-hd")?.addEventListener("click", rollClick);
    $("#gpl-kill-llm")?.addEventListener("click", async () => {
      try {
        // Cog button: full free (unload Comfy models too)
        await fetch("/pfld/kill", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ full: true }),
        });
        setSt("LLM killed · VRAM flushed");
      } catch (e) {
        setSt("Kill failed: " + e.message);
      }
    });
    paintHistory();
    $("#gpl-history")?.addEventListener("change", () => {
      const i = parseInt($("#gpl-history").value, 10);
      if (Number.isNaN(i)) return;
      const e = loadHistory()[i];
      if (!e) return;
      $("#gpl-out").value = e.script;
      draftPrompt = e.script;
      commitOutput(e.script);
      if (e.intent) $("#gpl-intent").value = e.intent;
      if (e.continuity) {
        lastContinuity = e.continuity;
        sw("continuity_state", lastContinuity);
      }
      setSt(`Restored history · ${e.script.length} chars`);
      syncLive();
    });

    function setVideoMode(mode) {
      videoMode = mode === "t2v" ? "t2v" : "i2v";
      sw("video_mode", videoMode);
      localStorage.setItem("pfld_video_mode", videoMode);
      $("#gpl-mode-tabs")?.querySelectorAll(".gpl-tab").forEach((t) => {
        t.classList.toggle("on", t.dataset.mode === videoMode);
      });
      refreshScenarioList();
      mountRes();
      scheduleLayout();
    }
    $("#gpl-mode-tabs")?.querySelectorAll(".gpl-tab").forEach((tab) => {
      tab.onclick = () => setVideoMode(tab.dataset.mode);
    });
    // Body intensity + mouth heat — qualitative chips (no magic numbers)
    const paintLevelChips = (rootId, current) => {
      $(`#${rootId}`)?.querySelectorAll(".gpl-chip").forEach((btn) => {
        btn.classList.toggle("on", btn.dataset.v === current);
      });
    };
    const setMotionLevel = (k) => {
      motionLevel = k || "normal";
      localStorage.setItem("pfld_motion", motionLevel);
      paintLevelChips("gpl-motion", motionLevel);
      const e = levelToEnergy(motionLevel);
      sw("intensity", e);
      try { sw("motion_level", INTENSITY_LEVELS.find((x) => x.k === motionLevel)?.lab || "Normal"); } catch (_) {}
      if ($("#gpl-int")) $("#gpl-int").value = String(e);
    };
    const setMouthHeat = (k) => {
      mouthHeat = k || "normal";
      localStorage.setItem("pfld_mouth", mouthHeat);
      paintLevelChips("gpl-mouth", mouthHeat);
      try { sw("mouth_heat", INTENSITY_LEVELS.find((x) => x.k === mouthHeat)?.lab || "Normal"); } catch (_) {}
    };
    $("#gpl-motion")?.querySelectorAll(".gpl-chip").forEach((btn) => {
      btn.addEventListener("click", () => setMotionLevel(btn.dataset.v));
    });
    $("#gpl-mouth")?.querySelectorAll(".gpl-chip").forEach((btn) => {
      btn.addEventListener("click", () => setMouthHeat(btn.dataset.v));
    });
    // Migrate legacy intensity widget → levels once
    if (!localStorage.getItem("pfld_motion")) {
      const legacy = parseInt(gw("intensity")?.value, 10);
      if (legacy) motionLevel = energyToLevel(legacy);
    }
    setMotionLevel(motionLevel);
    setMouthHeat(mouthHeat);

    // Shot recipes can auto-lean cast / intensity / duration / talk
    $("#gpl-scn")?.addEventListener("change", () => {
      const key = $("#gpl-scn")?.value || "";
      sw("scenario", key);
      applyRecipeHints(key);
    });

    // Partner accent
    if ($("#gpl-accent-partner")) {
      $("#gpl-accent-partner").value = accentPartner || "off";
      $("#gpl-accent-partner").addEventListener("change", () => {
        accentPartner = $("#gpl-accent-partner").value || "off";
        localStorage.setItem("pfld_accent_partner", accentPartner);
        try { sw("accent_partner", accentPartner); } catch (_) {}
      });
    }
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
        // Save the ORIGINAL file into the input folder so the node can
        // resolve it at queue time (image_b64 never serializes to Python).
        let savedName = "";
        try {
          const resp = await fetch("/pfld/upload_image", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: file.name || "upload.png", b64: r.result }),
          });
          const j = await resp.json();
          if (j.ok && j.name) savedName = j.name;
        } catch { /* offline — fall back to preview-only below */ }

        if (savedName) {
          await refreshGallery(true);
          loadGalleryImage(savedName);
          imageCarousel?.setFocus(savedName);
          return;
        }
        // Fallback (upload route unreachable): preview-only, queue will
        // fail for I2V but the LLM can still see the image.
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
      path = (path || "").trim();
      inputFolder = path;
      localStorage.setItem("pfld_input_folder", path);
      if ($("#gpl-folder-path")) $("#gpl-folder-path").value = path;
      setSt(path ? "Switching image folder…" : "Resetting image folder…");
      let ok = true;
      let errMsg = "";
      try {
        const r = await fetch("/pfld/set_input_folder", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path }),
        });
        const j = await r.json().catch(() => ({}));
        if (!r.ok || j.ok === false) {
          ok = false;
          errMsg = j.error || `HTTP ${r.status}`;
        } else if (j.path) {
          inputFolder = j.path;
          if ($("#gpl-folder-path")) $("#gpl-folder-path").value = j.path;
        }
      } catch (e) {
        ok = false;
        errMsg = e.message || "network";
      }
      // Always hard-reset carousel so same filenames in a new folder don't keep stale thumbs.
      _galleryKey = null;
      _galleryCacheKey = "";
      await refreshGallery(true, { hard: true, status: ok });
      if (!ok) setSt("Folder apply failed: " + errMsg);
    }
    $("#gpl-folder-apply")?.addEventListener("click", () => applyFolder($("#gpl-folder-path")?.value?.trim() || ""));
    if (inputFolder) { $("#gpl-folder-path").value = inputFolder; applyFolder(inputFolder); }

    let _galleryCacheKey = "";
    function thumbUrl(name, max = 360) {
      let u = `/pfld/thumb?name=${encodeURIComponent(name)}&max=${max}`;
      if (_galleryCacheKey) u += `&v=${encodeURIComponent(_galleryCacheKey)}`;
      return u;
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
    let _galleryKey = null;
    async function refreshGallery(force = true, opts = {}) {
      const hard = !!(opts && opts.hard);
      const showStatus = !!(opts && opts.status);
      try {
        const j = await (await fetch("/pfld/list_images?limit=40&_=" + Date.now())).json();
        if (j.input_dir && $("#gpl-folder-path")) {
          // Prefer live server path after Apply; keep typed path if user is mid-edit only when empty
          if (inputFolder) $("#gpl-folder-path").value = inputFolder;
          else if (!$("#gpl-folder-path").value) $("#gpl-folder-path").value = j.input_dir;
        }
        if (j.cache_key) _galleryCacheKey = String(j.cache_key);

        let list = j.images || [];
        if (videoMode === "t2v") {
          // Always provide "No image" option at the **start and the end** of the carousel for T2V.
          // This is the default selection and always exists (independent of the pointed folder).
          // When selected, it tells ResMaster to output a custom-sized black frame
          // using the current resolution/bbox settings (no reference image used).
          list = list.filter(n => n !== NO_IMAGE_NAME);
          list = [NO_IMAGE_NAME, ...list, NO_IMAGE_NAME];
        }
        // Auto-poll calls with force=false: skip the rebuild when nothing
        // changed, so the carousel never resets focus or churns the DOM.
        const key = (j.cache_key || j.input_dir || "") + "::" + list.join("|");
        const folderChanged = hard || (force && _galleryKey && _galleryKey.split("::")[0] !== key.split("::")[0]);
        if (!force && !hard && key === _galleryKey) return;
        const needHard = hard || folderChanged || force;
        _galleryKey = key;
        const current = imgFilename || (videoMode === "t2v" ? NO_IMAGE_NAME : "");
        // Drop selection if it isn't in the new folder (except T2V "No image")
        const pick = (current && list.includes(current)) ? current
          : (videoMode === "t2v" ? NO_IMAGE_NAME : (list[0] || ""));
        if (current && current !== NO_IMAGE_NAME && !list.includes(current)) {
          // Old focus file gone — clear hero so we don't keep a stale path
          if (imgFilename === current) setImage(null, 0, 0, "");
        }
        if (imageCarousel) {
          imageCarousel.setImages(list, pick, { hardReset: needHard });
          // Rebind every card src with cache-busted thumb URLs (new folder / new mtimes)
          if (typeof imageCarousel.rebindSrcs === "function") {
            imageCarousel.rebindSrcs((name) => thumbUrl(name, 360));
          }
        }
        if (showStatus || hard) {
          const n = typeof j.count === "number" ? j.count : (j.images || []).length;
          const dir = j.input_dir || inputFolder || "folder";
          setSt(n ? `Loaded ${n} image${n === 1 ? "" : "s"} · ${dir}` : `No images in ${dir}`);
        }
      } catch (e) {
        if (showStatus || hard) setSt("Gallery refresh failed" + (e?.message ? ": " + e.message : ""));
      }
    }

    // Watch the input folder — new/removed images appear without a manual refresh.
    const galleryTick = setInterval(() => {
      if (document.hidden) return;   // don't poll from background tabs
      refreshGallery(false);
    }, 5000);

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
          onRefresh: () => refreshGallery(true, { hard: true, status: true }),
        });
        applyRes(resMaster.getState().w, resMaster.getState().h, 1);
        refreshGallery(true, { hard: true });

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
        onRefresh: () => refreshGallery(true, { hard: true, status: true }),
      });
      applyRes(resMaster.getState().w, resMaster.getState().h, resScale);
      refreshGallery(true, { hard: true });
      scheduleLayout();
    }

    /**
     * Intent box only — independent height grip (localStorage).
     * LTX Script fills leftover space and tracks node resize (no own grip).
     */
    function wireIntentResize(ta, storageKey, opts = {}) {
      if (!ta || ta.dataset.pfldResize === "1") return;
      const minH = opts.minH ?? 64;
      const maxH = opts.maxH ?? 600;
      const defH = opts.defH ?? 110;
      let h = defH;
      try {
        const saved = parseInt(localStorage.getItem(storageKey), 10);
        if (Number.isFinite(saved) && saved >= minH) h = Math.min(maxH, saved);
      } catch { /* */ }

      const wrap = document.createElement("div");
      wrap.className = "gpl-ta-wrap gpl-ta-wrap-intent";
      ta.parentNode.insertBefore(wrap, ta);
      wrap.appendChild(ta);

      const grip = document.createElement("div");
      grip.className = "gpl-ta-grip";
      grip.title = "Drag to resize Intent height";
      grip.setAttribute("data-tip", "Drag up/down to resize Intent only — LTX Script follows the node size");
      grip.setAttribute("aria-label", "Resize Intent box");
      wrap.appendChild(grip);

      const applyH = (px, save) => {
        const v = Math.max(minH, Math.min(maxH, Math.round(px)));
        ta.style.height = `${v}px`;
        ta.style.minHeight = `${v}px`;
        ta.style.maxHeight = "none";
        ta.style.flex = "none";
        if (save) {
          try { localStorage.setItem(storageKey, String(v)); } catch { /* */ }
        }
        return v;
      };
      applyH(h, false);
      ta.dataset.pfldResize = "1";

      let drag = null;
      const onMove = (ev) => {
        if (!drag) return;
        ev.preventDefault();
        const y = ev.clientY ?? ev.touches?.[0]?.clientY;
        if (y == null) return;
        applyH(drag.startH + (y - drag.startY), false);
      };
      const onUp = () => {
        if (!drag) return;
        wrap.classList.remove("dragging");
        const finalH = parseInt(ta.style.height, 10) || defH;
        applyH(finalH, true);
        drag = null;
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
        window.removeEventListener("pointercancel", onUp);
      };
      grip.addEventListener("pointerdown", (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        const startH = ta.offsetHeight || defH;
        drag = { startY: ev.clientY, startH };
        wrap.classList.add("dragging");
        try { grip.setPointerCapture(ev.pointerId); } catch { /* */ }
        window.addEventListener("pointermove", onMove);
        window.addEventListener("pointerup", onUp);
        window.addEventListener("pointercancel", onUp);
      });
      grip.addEventListener("dblclick", (ev) => {
        ev.preventDefault();
        applyH(defH, true);
      });
    }
    // Intent: free grip. Script: no grip — height from node (CSS flex fill).
    wireIntentResize($("#gpl-intent"), "pfld_intent_h", { minH: 72, maxH: 600, defH: 110 });
    // Clear any leftover independent height from older builds
    const outTa = $("#gpl-out");
    if (outTa) {
      outTa.style.height = "";
      outTa.style.minHeight = "";
      outTa.style.maxHeight = "";
      outTa.style.flex = "";
      try { localStorage.removeItem("pfld_out_h"); } catch { /* */ }
    }

    $("#gpl-intent")?.addEventListener("input", () => sw("user_intent", $("#gpl-intent").value.trim()));
    // LoRA trigger keywords (separate from free intent)
    try {
      const savedTrig = localStorage.getItem("pfld_lora_triggers") || "";
      if ($("#gpl-lora-trig") && savedTrig) $("#gpl-lora-trig").value = savedTrig;
    } catch { /* */ }
    $("#gpl-lora-trig")?.addEventListener("input", () => {
      const v = ($("#gpl-lora-trig")?.value || "").trim();
      try { localStorage.setItem("pfld_lora_triggers", v); } catch { /* */ }
    });
    $("#gpl-lora-trig")?.addEventListener("change", () => {
      const v = ($("#gpl-lora-trig")?.value || "").trim();
      try { localStorage.setItem("pfld_lora_triggers", v); } catch { /* */ }
    });
    $("#gpl-out")?.addEventListener("input", () => {
      draftPrompt = $("#gpl-out").value;
      sw("confirmed_prompt", draftPrompt);
    });

    /** Old shot-script layout: blank line between action beats.
     *  Never flatten existing newlines first — that caused "looked good then
     *  collapsed to one paragraph" after the final pass. */
    function formatScriptLayout(text) {
      let s = (text || "").replace(/\r\n/g, "\n").trim();
      if (!s) return s;

      // Insert breaks at action boundaries even when the model skips periods
      s = s.replace(
        /(["”])\s*(?=(She|He|They|The view|A hand|Hands|The man|The woman|A woman|A man)\b)/g,
        "$1\n\n"
      );
      s = s.replace(
        /([.!?])\s+(?=(She|He|They|The view|A hand|Hands|The man|The woman|A woman|A man|Eye-level|Use the provided)\b)/g,
        "$1\n\n"
      );

      // Prefer existing line structure (do NOT crush \n into spaces)
      let lines = s.split(/\n+/).map((l) => l.replace(/[ \t]{2,}/g, " ").trim()).filter(Boolean);
      if (lines.length < 2) {
        // true single wall — split on sentences lightly
        const flat = lines[0] || s;
        const parts = [];
        let buf = "", inQ = false;
        for (let i = 0; i < flat.length; i++) {
          const ch = flat[i];
          if (ch === '"') inQ = !inQ;
          buf += ch;
          if (!inQ && (ch === "." || ch === "!" || ch === "?")) {
            const nxt = flat[i + 1] || "";
            if (!nxt || /\s/.test(nxt)) {
              if (buf.trim()) parts.push(buf.trim());
              buf = "";
              while (i + 1 < flat.length && /\s/.test(flat[i + 1])) i++;
            }
          }
        }
        if (buf.trim()) parts.push(buf.trim());
        lines = parts.length ? parts : lines;
      }

      const actionRe = /^(She|He|They|The view|A hand|Hands|Both hands|Eye-level|Use the provided|A (woman|man|person|muscular)|The (man|woman|view))\b/i;
      const speechRe = /^(She|He|They)\s+(says|murmurs|whispers|shouts|yells|asks|answers|laughs|breathes|groans|moans|whimpers|gasps)\b/i;
      const sections = [];
      let i = 0;
      if (lines[0] && /use the provided start image/i.test(lines[0])) {
        sections.push(lines[0]);
        i = 1;
        if (i < lines.length && /^Eye-level\b/i.test(lines[i])) {
          let open = lines[i++];
          if (i < lines.length && /^(A |An |The )?(woman|man|person|muscular)/i.test(lines[i])) {
            open += " " + lines[i++];
          }
          sections.push(open);
        }
      }
      while (i < lines.length) {
        const sent = lines[i];
        const speechOnly = speechRe.test(sent) && sent.includes('"');
        if (sections.length && speechOnly && !sections[sections.length - 1].includes('"')) {
          sections[sections.length - 1] += " " + sent;
        } else if (actionRe.test(sent) || speechOnly || !sections.length) {
          sections.push(sent);
        } else {
          sections[sections.length - 1] += " " + sent;
        }
        i++;
      }
      return sections
        .map((x) => x.replace(/,\s*\./g, ".").replace(/\s{2,}/g, " ").trim())
        .filter(Boolean)
        .join("\n\n");
    }

    function commitOutput(text) {
      const t = formatScriptLayout(text || "");
      sw("confirmed_prompt", t);
      // Re-assert image path with the script so Queue can't pick new text + old image
      if (imgFilename && imgFilename !== NO_IMAGE_NAME) {
        sw("image_filename", imgFilename);
        sw("image_b64", "");
      }
      if ($("#gpl-out") && t) $("#gpl-out").value = t;
      draftPrompt = t;
      return t;
    }

    function isRerollMode() {
      const intent = ($("#gpl-intent")?.value || "").trim();
      const hasScript = !!(draftPrompt || $("#gpl-out")?.value || gw("confirmed_prompt")?.value || "").trim();
      return !!(hasScript && intent && lastGenIntent && intent === lastGenIntent);
    }
    function paintGenBtn() {
      const btn = $("#gpl-gen");
      if (!btn || generating) return;
      if (isRerollMode()) {
        btn.textContent = "Re-roll";
        btn.setAttribute("data-tip", "Same intent — new seed, fresh take. Model stays warm.");
      } else {
        btn.textContent = "Generate";
        btn.setAttribute("data-tip", "Generate a new LTX script from all controls + intent. Same intent again → Re-roll (new seed).");
      }
    }

    async function compose(opts = {}) {
      const refine = !!opts.refine;
      if (generating) { abortCtrl?.abort(); return; }
      const intent = ($("#gpl-intent")?.value || "").trim();
      if (!intent) { setSt(refine ? "Write the revision request in Intent." : "Write intent first."); return; }
      if (!backendReady()) return;
      const prior = (draftPrompt || $("#gpl-out")?.value || gw("confirmed_prompt")?.value || "").trim();
      if (refine && !prior) { setSt("Refine needs an existing script — Generate first."); return; }
      if (videoMode === "i2v" && !hasImage() && !refine) { setSt("I2V needs an image."); return; }

      const reroll = !refine && isRerollMode();
      generating = true;
      const btn = $("#gpl-gen");
      const rbtn = $("#gpl-refine");
      btn.textContent = "Stop";
      btn.classList.add("stop");
      if (rbtn) rbtn.disabled = true;
      setSt(refine
        ? "Preparing refine…"
        : reroll
          ? "Re-roll (new seed)…"
          : (videoMode === "i2v" ? "Preparing image…" : "Starting…"));
      if ($("#gpl-st")) $("#gpl-st").classList.add("working");

      syncModels();
      await saveConn();
      sw("user_intent", intent);
      // image_b64 never serializes to Queue (stripped). Always re-push the
      // carousel selection so I2V pack doesn't use a stale/empty filename until
      // the user re-clicks a card.
      sw("image_b64", "");
      if (imgFilename && imgFilename !== NO_IMAGE_NAME) {
        sw("image_filename", imgFilename);
      } else if (imgPreviewUrl && String(imgPreviewUrl).startsWith("data:")) {
        // Browse fallback still in memory only — keep b64 for Python if present
        sw("image_b64", imgPreviewUrl);
        sw("image_filename", "");
      } else {
        sw("image_filename", "");
      }
      sw("scenario", $("#gpl-scn")?.value);
      sw("environment", $("#gpl-env")?.value);
      sw("camera_move", $("#gpl-cam")?.value);
      sw("cast", castMode);
      sw("lead_gender", $("#gpl-lead")?.value || leadGender);
      try { sw("video_style", $("#gpl-style")?.value || "None — off (no style path)"); } catch (_) {}
      sw("accent_mode", $("#gpl-accent")?.value || accentMode);
      try { sw("accent_partner", $("#gpl-accent-partner")?.value || accentPartner || "off"); } catch (_) {}
      try {
        sw("motion_level", INTENSITY_LEVELS.find((x) => x.k === motionLevel)?.lab || "Normal");
        sw("mouth_heat", INTENSITY_LEVELS.find((x) => x.k === mouthHeat)?.lab || "Normal");
        sw("intensity", levelToEnergy(motionLevel));
      } catch (_) {}
      if (!isInputWired("duration_s")) sw("duration_s", getDur());
      if (resMaster) applyRes(resMaster.getState().w, resMaster.getState().h, resScale);

      abortCtrl = new AbortController();
      if (!refine) $("#gpl-out").value = "";
      let text = refine ? "" : "";

      // After Queue/Run the LLM is dead and LTX may hold VRAM. keep_warm must NOT
      // skip the pre-flush in that case — force_flush + server-side "LLM down → flush".
      let videoTookVram = false;
      try { videoTookVram = !!window.__pfldVideoTookVram; } catch { /* */ }

      const body = {
        ...buildComposeBody(),
        refine,
        prior_prompt: refine ? prior : "",
        user_intent: intent,
        // Leave LLM loaded after THIS gen (re-roll / warm session)
        keep_warm: reroll ? true : keepWarm,
        // After Queue/Run: LTX holds VRAM — force Comfy unload before LLM boot.
        // Server also auto-flushes whenever the LLM health check is down.
        force_flush: !!videoTookVram,
        temperature: parseFloat($("#gpl-temp")?.value) || (refine ? 0.4 : 0.55),
      };
      // Re-roll always forces a NEW seed (even Fixed mode) — after buildComposeBody so it wins
      if (reroll) body.seed = rollSeed();

      try {
        setSt(
          refine
            ? "Revising…"
            : reroll
              ? (videoTookVram
                ? `Re-roll · free LTX VRAM · seed ${body.seed}…`
                : `Re-rolling seed ${body.seed}…`)
              : (videoTookVram ? "Freeing video VRAM · starting LLM…" : "Connecting…"),
        );
        if (videoMode === "i2v" && !refine) {
          body.image_b64 = await visionB64ForCompose();
          if (!body.image_b64) {
            generating = false;
            paintGenBtn();
            btn.classList.remove("stop");
            if (rbtn) rbtn.disabled = false;
            if ($("#gpl-st")) $("#gpl-st").classList.remove("working");
            setSt("I2V needs an image.");
            return;
          }
        } else if (videoMode === "i2v" && refine && hasImage()) {
          // Optional vision on refine — skip to keep fast; prior text is enough
          body.image_b64 = "";
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
        let finalFromDone = "";
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
            else if (ev.type === "replace") {
              // Densify / full rewrite — wipe streamed first pass
              text = (ev.text != null) ? String(ev.text) : "";
              if ($("#gpl-out")) $("#gpl-out").value = text;
            }
            else if (ev.type === "delta") {
              text += ev.text;
              $("#gpl-out").value = text;
              setSt(`${text.length} chars…`);
            }
            else if (ev.type === "done") {
              // Final box = repaired (or raw if scrub off). Stream already showed raw tokens.
              if (ev.prompt) finalFromDone = ev.prompt;
              if (ev.raw_prompt && ev.repaired) {
                // Stash raw so user can compare (status + optional copy via console)
                try { window.__pfldLastRaw = ev.raw_prompt; } catch { /* */ }
              }
              if (ev.continuity) {
                lastContinuity = ev.continuity;
                sw("continuity_state", lastContinuity);
              }
              if (ev.seed != null && Number.isFinite(Number(ev.seed))) {
                lastSeed = Number(ev.seed) >>> 0;
                try { localStorage.setItem("pfld_seed", String(lastSeed)); } catch { /* */ }
                paintSeedUI();
              }
              // Surface Random resolves + repair note
              const rBits = [];
              if (ev.resolved_scenario && ev.scenario_raw
                  && String(ev.resolved_scenario) !== String(ev.scenario_raw)) {
                rBits.push("scn " + String(ev.resolved_scenario).slice(0, 48));
              }
              if (ev.resolved_environment && ev.environment_raw
                  && String(ev.resolved_environment) !== String(ev.environment_raw)) {
                rBits.push("env " + String(ev.resolved_environment).slice(0, 36));
              }
              if (ev.repair === false) rBits.push("raw (no scrub)");
              else if (ev.repaired) rBits.push("scrubbed");
              if (ev.self_check && !ev.self_check.error) {
                const sc = ev.self_check;
                rBits.push(`qa ${sc.pass_count || 0}✓/${sc.fail_count || 0}✗`);
                if (sc.fixed) rBits.push("qa-fixed");
                try { window.__pfldLastSelfCheck = sc; } catch { /* */ }
              }
              if (rBits.length) setSt((rBits[0].startsWith("scn") || rBits[0].startsWith("env") ? "Random → " : "") + rBits.join(" · "));
            }
            else if (ev.type === "self_check") {
              try { window.__pfldLastSelfCheck = ev; } catch { /* */ }
              const nP = ev.pass_count || 0, nF = ev.fail_count || 0;
              setSt(`Self-check ${nP} pass / ${nF} fail${ev.fixed ? " · fixing…" : " · report"}`);
            }
            else if (ev.type === "error") throw new Error(ev.msg);
          }
        }
        draftPrompt = (finalFromDone || text).trim();
        $("#gpl-out").value = draftPrompt;
        const committed = commitOutput(draftPrompt);
        pushHistory(intent, committed);
        if (!refine && committed) lastGenIntent = intent;
        // LLM is back in VRAM — next re-roll can skip LTX flush until Queue again
        try { window.__pfldVideoTookVram = false; } catch { /* */ }
        syncLive();
        const tag = refine ? "refined" : (reroll ? "re-rolled" : "forged");
        const scTag = selfCheckOn ? (selfCheckMode === "report" ? " · qa-report" : " · qa") : "";
        setSt(committed
          ? `✦ ${committed.length} chars ${tag} → pack · seed ${lastSeed}${keepWarm || reroll ? " · warm" : ""}${detailerOn ? " · det" : ""}${repairOn ? "" : " · raw"}${scTag}`
          : "Empty.");
      } catch (e) {
        if (e.name !== "AbortError") setSt("Error: " + e.message);
        else setSt("Stopped.");
      } finally {
        generating = false;
        paintGenBtn();
        btn.classList.remove("stop");
        if (rbtn) rbtn.disabled = false;
        if ($("#gpl-st")) $("#gpl-st").classList.remove("working");
        scheduleLayout();
      }
    }

    $("#gpl-gen").onclick = () => compose({ refine: false });
    $("#gpl-refine")?.addEventListener("click", () => compose({ refine: true }));
    $("#gpl-intent")?.addEventListener("input", () => paintGenBtn());
    $("#gpl-out")?.addEventListener("input", () => paintGenBtn());
    paintGenBtn();

    function restoreSession() {
      const cp = gw("confirmed_prompt")?.value;
      if (cp) { $("#gpl-out").value = cp; draftPrompt = cp; }
      const ui = gw("user_intent")?.value;
      if (ui) $("#gpl-intent").value = ui;
      const vm = gw("video_mode")?.value;
      if (vm) videoMode = vm;
      const fn = (gw("image_filename")?.value || "").trim();
      if (fn) imgFilename = fn;
      const cont = (gw("continuity_state")?.value || "").trim();
      if (cont) lastContinuity = cont;
      const cs = gw("cast")?.value;
      if (cs) setCast(cs);
      const lg = gw("lead_gender")?.value;
      if (lg && $("#gpl-lead")) { $("#gpl-lead").value = lg; leadGender = lg; }
      const vs = gw("video_style")?.value;
      if (vs && $("#gpl-style")) {
        try {
          $("#gpl-style").value = vs;
          $("#gpl-style")._pfldSyncStyleBtn?.();
        } catch (_) {}
      }
      const am = gw("accent_mode")?.value;
      if (am && $("#gpl-accent")) { $("#gpl-accent").value = am; accentMode = am; }
      setVideoMode(videoMode);
      if (imgFilename && imgFilename !== NO_IMAGE_NAME) loadGalleryImage(imgFilename);
      paintHistory();
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
        loadPinnedSize();
        const s = (info && info.size) || node.size;
        // Restore saved pin (free-resize range); prefer localStorage, else workflow size
        const h = clampNodeH(node._savedH || s?.[1] || NODE_DEF_H);
        const w = Math.max(node._userW || s?.[0] || NODE_DEF_W, LAYOUT.minNodeW);
        applyNodeSize(w, h, true);
        paintSizeSliders();
        fitContainer();
      }, 0);
    };

    const tick = setInterval(() => {
      // Hold user pin only — never re-measure content to grow.
      // onResize already wrote _savedH, so this won't fight free shrink/grow.
      if (node.size && node._savedH) {
        const h = clampNodeH(node._savedH);
        const w = node._userW || node.size[0] || NODE_DEF_W;
        if (Math.abs(node.size[1] - h) > 2 || Math.abs(node.size[0] - w) > 2) {
          node.setSize([w, h]);
        }
      }
      syncLive();
    }, 800);

    const origRemoved = node.onRemoved;
    node.onRemoved = function () {
      clearInterval(tick);
      clearInterval(galleryTick);
      if (resMaster) try { resMaster.destroy(); } catch { /* */ }
      if (node._wSync) cancelAnimationFrame(node._wSync);
      if (origRemoved) origRemoved.apply(this, arguments);
    };

    requestAnimationFrame(() => {
      applyNodeSize(node._userW || NODE_DEF_W, clampNodeH(node._savedH || NODE_DEF_H), true);
      fitContainer();
      paintSizeSliders();
    });
    setTimeout(() => {
      applyNodeSize(node._userW || NODE_DEF_W, clampNodeH(node._savedH || NODE_DEF_H), true);
      fitContainer();
      paintSizeSliders();
    }, 400);
    } catch (err) {
      console.error("[PromptForgeLD] UI init failed:", err);
    }
  },
});