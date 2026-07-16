/**
 * Shared visual themes for PromptForge LD + LoraForge LD.
 * Same keys + matching hues so both nodes feel like one product.
 *
 * Each theme:
 *   name   — UI label
 *   pf     — CSS vars for .gpl-root (PromptForge)
 *   lf     — tokens for LoraForge cups / chrome
 *   node   — Comfy node shell colors (LiteGraph title bar)
 *
 * Role vars (PF):
 *   --bg --panel --text --muted --line --glow-a --glow-b
 *   --gold  → highlights / energy / intent labels
 *   --cyan  → shot / cool accents
 *   --violet → primary accent (chips on, script box, scene) — NOT always purple
 *   --rose  → voice / POV heat
 *   --mint  → media / detailer / success-ish
 *
 * Minimal themes (slate / graphite / concrete / mono) keep ALL role colours
 * in the grey range so no purple textareas or candy zone fills.
 */
export const THEME_KEYS = [
  "default",
  "midnight",
  "neon",
  "warm",
  "terminal",
  "arctic",
  "rose",
  "ember",
  "ocean",
  "mono",
  // Minimal / dull — workbench, not candy
  "slate",
  "graphite",
  "concrete",
];

/** Pure greyscale role set — graphite/slate-style (no blue cast). */
function monoRoles(base = {}) {
  return {
    "--gold": "#b4b4b4",
    "--cyan": "#a8a8a8",
    "--violet": "#9c9c9c",
    "--rose": "#b0b0b0",
    "--mint": "#a4a4a4",
    "--glow-a": "rgba(0,0,0,0)",
    "--glow-b": "rgba(0,0,0,0)",
    ...base,
  };
}

export const THEMES = {
  default: {
    name: "Violet",
    pf: {
      "--bg": "#07040e",
      "--panel": "rgba(18, 12, 28, 0.92)",
      "--text": "#f0ebff",
      "--muted": "#7d7394",
      "--gold": "#ffc857",
      "--cyan": "#5ce1e6",
      "--violet": "#a855f7",
      "--rose": "#ff6b9d",
      "--mint": "#6ee7b7",
      "--line": "rgba(255,255,255,.08)",
      "--glow-a": "rgba(168,85,247,.14)",
      "--glow-b": "rgba(92,225,230,.10)",
    },
    lf: {
      str: "#ffc857",
      v: "#5ce1e6",
      a: "#a855f7",
      on: "#5ce1e6",
      off: "#ff6b6b",
      accent: "#a855f7",
      bg: "#07040e",
      panel: "rgba(255,255,255,.03)",
      text: "#f0ebff",
      muted: "#7d7394",
      line: "rgba(255,255,255,.08)",
    },
    node: { color: "#1a0f2e", bgcolor: "#0a0614" },
  },

  midnight: {
    name: "Midnight",
    pf: {
      "--bg": "#030208",
      "--panel": "rgba(10, 12, 24, 0.94)",
      "--text": "#d4dcf0",
      "--muted": "#5a6480",
      "--gold": "#c9a86c",
      "--cyan": "#6b9fd4",
      "--violet": "#6b7fd7",
      "--rose": "#8b7ec8",
      "--mint": "#7eb8c9",
      "--line": "rgba(140,160,220,.10)",
      "--glow-a": "rgba(80,100,180,.16)",
      "--glow-b": "rgba(60,90,140,.10)",
    },
    lf: {
      str: "#c9a86c",
      v: "#6b9fd4",
      a: "#6b7fd7",
      on: "#6b9fd4",
      off: "#c07080",
      accent: "#6b7fd7",
      bg: "#030208",
      panel: "rgba(255,255,255,.03)",
      text: "#d4dcf0",
      muted: "#5a6480",
      line: "rgba(140,160,220,.10)",
    },
    node: { color: "#0c1020", bgcolor: "#05060e" },
  },

  neon: {
    name: "Neon",
    pf: {
      "--bg": "#080410",
      "--panel": "rgba(20, 8, 28, 0.94)",
      "--text": "#f5ecff",
      "--muted": "#9a7ab0",
      "--gold": "#ffe066",
      "--cyan": "#00f0ff",
      "--violet": "#ff2d9b",
      "--rose": "#ff4dc4",
      "--mint": "#39ff9a",
      "--line": "rgba(255,80,200,.14)",
      "--glow-a": "rgba(255,45,155,.18)",
      "--glow-b": "rgba(0,240,255,.12)",
    },
    lf: {
      str: "#ff2d9b",
      v: "#00f0ff",
      a: "#bf5fff",
      on: "#39ff9a",
      off: "#ff2d88",
      accent: "#ff2d9b",
      bg: "#080410",
      panel: "rgba(255,255,255,.04)",
      text: "#f5ecff",
      muted: "#9a7ab0",
      line: "rgba(255,80,200,.14)",
    },
    node: { color: "#220818", bgcolor: "#0c0414" },
  },

  warm: {
    name: "Warm",
    pf: {
      "--bg": "#120c08",
      "--panel": "rgba(28, 18, 12, 0.94)",
      "--text": "#f5e6d0",
      "--muted": "#8a7058",
      "--gold": "#ffb347",
      "--cyan": "#d4a574",
      "--violet": "#e07a5f",
      "--rose": "#e8a0a0",
      "--mint": "#c4b58a",
      "--line": "rgba(255,180,100,.12)",
      "--glow-a": "rgba(255,140,60,.14)",
      "--glow-b": "rgba(200,120,60,.08)",
    },
    lf: {
      str: "#ffb347",
      v: "#d4a574",
      a: "#e07a5f",
      on: "#ffb347",
      off: "#c06050",
      accent: "#ffb347",
      bg: "#120c08",
      panel: "rgba(255,255,255,.03)",
      text: "#f5e6d0",
      muted: "#8a7058",
      line: "rgba(255,180,100,.12)",
    },
    node: { color: "#2a1810", bgcolor: "#140c08" },
  },

  terminal: {
    name: "Terminal",
    pf: {
      "--bg": "#060e08",
      "--panel": "rgba(8, 20, 12, 0.94)",
      "--text": "#b8e0b8",
      "--muted": "#5a7a5a",
      "--gold": "#c8b060",
      "--cyan": "#4ade80",
      "--violet": "#6b9b6b",
      "--rose": "#86c080",
      "--mint": "#86efac",
      "--line": "rgba(80,200,100,.12)",
      "--glow-a": "rgba(74,222,128,.12)",
      "--glow-b": "rgba(100,160,80,.08)",
    },
    lf: {
      str: "#c8b060",
      v: "#4ade80",
      a: "#86efac",
      on: "#4ade80",
      off: "#c07060",
      accent: "#4ade80",
      bg: "#060e08",
      panel: "rgba(255,255,255,.03)",
      text: "#b8e0b8",
      muted: "#5a7a5a",
      line: "rgba(80,200,100,.12)",
    },
    node: { color: "#0e1a10", bgcolor: "#060c08" },
  },

  arctic: {
    name: "Arctic",
    pf: {
      "--bg": "#060a10",
      "--panel": "rgba(12, 18, 28, 0.94)",
      "--text": "#e8f2ff",
      "--muted": "#7a90a8",
      "--gold": "#a8c8e0",
      "--cyan": "#7dd3fc",
      "--violet": "#93c5fd",
      "--rose": "#bae6fd",
      "--mint": "#a5f3fc",
      "--line": "rgba(125,211,252,.14)",
      "--glow-a": "rgba(125,211,252,.14)",
      "--glow-b": "rgba(147,197,253,.10)",
    },
    lf: {
      str: "#a8c8e0",
      v: "#7dd3fc",
      a: "#93c5fd",
      on: "#7dd3fc",
      off: "#f09090",
      accent: "#7dd3fc",
      bg: "#060a10",
      panel: "rgba(255,255,255,.03)",
      text: "#e8f2ff",
      muted: "#7a90a8",
      line: "rgba(125,211,252,.14)",
    },
    node: { color: "#101828", bgcolor: "#060a12" },
  },

  rose: {
    name: "Rose",
    pf: {
      "--bg": "#10080c",
      "--panel": "rgba(28, 12, 18, 0.94)",
      "--text": "#ffe8f0",
      "--muted": "#a87890",
      "--gold": "#f0c0a0",
      "--cyan": "#f9a8d4",
      "--violet": "#f472b6",
      "--rose": "#fb7185",
      "--mint": "#fda4af",
      "--line": "rgba(244,114,182,.14)",
      "--glow-a": "rgba(244,114,182,.16)",
      "--glow-b": "rgba(251,113,133,.10)",
    },
    lf: {
      str: "#f0c0a0",
      v: "#f9a8d4",
      a: "#f472b6",
      on: "#f9a8d4",
      off: "#e07070",
      accent: "#f472b6",
      bg: "#10080c",
      panel: "rgba(255,255,255,.03)",
      text: "#ffe8f0",
      muted: "#a87890",
      line: "rgba(244,114,182,.14)",
    },
    node: { color: "#241018", bgcolor: "#12080c" },
  },

  ember: {
    name: "Ember",
    pf: {
      "--bg": "#100806",
      "--panel": "rgba(28, 12, 8, 0.94)",
      "--text": "#ffe8d8",
      "--muted": "#a07058",
      "--gold": "#ff9f43",
      "--cyan": "#ff6b35",
      "--violet": "#e85d04",
      "--rose": "#ff6b6b",
      "--mint": "#f4a261",
      "--line": "rgba(255,120,40,.14)",
      "--glow-a": "rgba(255,107,53,.16)",
      "--glow-b": "rgba(232,93,4,.10)",
    },
    lf: {
      str: "#ff9f43",
      v: "#ff6b35",
      a: "#e85d04",
      on: "#ff9f43",
      off: "#c04040",
      accent: "#ff6b35",
      bg: "#100806",
      panel: "rgba(255,255,255,.03)",
      text: "#ffe8d8",
      muted: "#a07058",
      line: "rgba(255,120,40,.14)",
    },
    node: { color: "#281208", bgcolor: "#120806" },
  },

  ocean: {
    name: "Ocean",
    pf: {
      "--bg": "#040c10",
      "--panel": "rgba(8, 20, 28, 0.94)",
      "--text": "#e0f4f8",
      "--muted": "#5a8890",
      "--gold": "#5eead4",
      "--cyan": "#22d3ee",
      "--violet": "#0ea5e9",
      "--rose": "#67e8f9",
      "--mint": "#2dd4bf",
      "--line": "rgba(34,211,238,.14)",
      "--glow-a": "rgba(34,211,238,.14)",
      "--glow-b": "rgba(14,165,233,.10)",
    },
    lf: {
      str: "#5eead4",
      v: "#22d3ee",
      a: "#0ea5e9",
      on: "#22d3ee",
      off: "#e07070",
      accent: "#22d3ee",
      bg: "#040c10",
      panel: "rgba(255,255,255,.03)",
      text: "#e0f4f8",
      muted: "#5a8890",
      line: "rgba(34,211,238,.14)",
    },
    node: { color: "#0c1c24", bgcolor: "#040e14" },
  },

  // True neutral greys (slight cool edge only)
  mono: {
    name: "Mono",
    pf: {
      "--bg": "#0a0a0a",
      "--panel": "rgba(22, 22, 22, 0.96)",
      "--text": "#ececec",
      "--muted": "#7a7a7a",
      "--line": "rgba(255,255,255,.09)",
      ...monoRoles({
        "--gold": "#c8c8c8",
        "--cyan": "#b0b0b0",
        "--violet": "#a8a8a8",
        "--rose": "#bcbcbc",
        "--mint": "#b4b4b4",
      }),
    },
    lf: {
      str: "#c8c8c8",
      v: "#b0b0b0",
      a: "#a8a8a8",
      on: "#e0e0e0",
      off: "#888888",
      accent: "#c8c8c8",
      bg: "#0a0a0a",
      panel: "rgba(255,255,255,.04)",
      text: "#ececec",
      muted: "#7a7a7a",
      line: "rgba(255,255,255,.09)",
    },
    node: { color: "#1c1c1c", bgcolor: "#0c0c0c" },
  },

  // ── Minimal / dull (Comfy-stack energy — workbench, not candy) ───────────
  slate: {
    name: "Slate",
    pf: {
      "--bg": "#181818",
      "--panel": "rgba(34, 34, 34, 0.97)",
      "--text": "#d2d2d2",
      "--muted": "#6a6a6a",
      "--line": "rgba(255,255,255,.07)",
      ...monoRoles({
        "--gold": "#9e9e9e",
        "--cyan": "#8e8e8e",
        "--violet": "#868686",
        "--rose": "#949494",
        "--mint": "#8a8a8a",
      }),
    },
    lf: {
      str: "#9e9e9e",
      v: "#8e8e8e",
      a: "#868686",
      on: "#b8b8b8",
      off: "#5e5e5e",
      accent: "#9e9e9e",
      bg: "#181818",
      panel: "rgba(255,255,255,.04)",
      text: "#d2d2d2",
      muted: "#6a6a6a",
      line: "rgba(255,255,255,.07)",
    },
    node: { color: "#282828", bgcolor: "#141414" },
  },

  // Graphite = basically black & white (no purple, no blue cast)
  graphite: {
    name: "Graphite",
    pf: {
      "--bg": "#0c0c0c",
      "--panel": "rgba(24, 24, 24, 0.98)",
      "--text": "#e6e6e6",
      "--muted": "#6e6e6e",
      "--line": "rgba(255,255,255,.08)",
      ...monoRoles({
        "--gold": "#b8b8b8",
        "--cyan": "#a8a8a8",
        "--violet": "#9a9a9a",
        "--rose": "#b0b0b0",
        "--mint": "#a4a4a4",
      }),
    },
    lf: {
      str: "#b8b8b8",
      v: "#a8a8a8",
      a: "#9a9a9a",
      on: "#e0e0e0",
      off: "#666666",
      accent: "#b8b8b8",
      bg: "#0c0c0c",
      panel: "rgba(255,255,255,.04)",
      text: "#e6e6e6",
      muted: "#6e6e6e",
      line: "rgba(255,255,255,.08)",
    },
    node: { color: "#1e1e1e", bgcolor: "#0a0a0a" },
  },

  // Warm concrete grey only — still colourless
  concrete: {
    name: "Concrete",
    pf: {
      "--bg": "#141312",
      "--panel": "rgba(32, 30, 28, 0.97)",
      "--text": "#d8d4ce",
      "--muted": "#6e6a64",
      "--line": "rgba(255,255,255,.07)",
      "--gold": "#a8a098",
      "--cyan": "#989088",
      "--violet": "#908880",
      "--rose": "#a09890",
      "--mint": "#948c84",
      "--glow-a": "rgba(0,0,0,0)",
      "--glow-b": "rgba(0,0,0,0)",
    },
    lf: {
      str: "#a8a098",
      v: "#989088",
      a: "#908880",
      on: "#c0b8b0",
      off: "#5c5850",
      accent: "#a8a098",
      bg: "#141312",
      panel: "rgba(255,255,255,.035)",
      text: "#d8d4ce",
      muted: "#6e6a64",
      line: "rgba(255,255,255,.07)",
    },
    node: { color: "#262422", bgcolor: "#100f0e" },
  },
};

export function resolveTheme(key) {
  const k = (key || "default").toLowerCase().trim();
  // Legacy LoraForge keys a/b/c
  const legacy = { a: "default", b: "neon", c: "warm" };
  const id = legacy[k] || (THEMES[k] ? k : "default");
  return { id, theme: THEMES[id] };
}

export function themeOptionsHtml() {
  return THEME_KEYS.map((k) => {
    const n = THEMES[k]?.name || k;
    return `<option value="${k}">${n}</option>`;
  }).join("\n    ");
}

/** Persist shared key so both nodes reopen on the same look. */
export function loadSharedThemeKey() {
  try {
    return localStorage.getItem("pfld_theme") || "default";
  } catch {
    return "default";
  }
}

export function saveSharedThemeKey(key) {
  try {
    localStorage.setItem("pfld_theme", key);
  } catch { /* */ }
}

/* ── Comfy native: derive panel accents from LiteGraph node.color ─────────── */

/** Parse #rgb / #rrggbb / rgb() → {r,g,b} or null. */
export function parseCssColor(c) {
  if (c == null || c === "") return null;
  const s = String(c).trim();
  if (s.startsWith("#")) {
    let h = s.slice(1);
    if (h.length === 3) h = h.split("").map((ch) => ch + ch).join("");
    if (h.length !== 6 || /[^0-9a-f]/i.test(h)) return null;
    return {
      r: parseInt(h.slice(0, 2), 16),
      g: parseInt(h.slice(2, 4), 16),
      b: parseInt(h.slice(4, 6), 16),
    };
  }
  const m = s.match(/rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i);
  if (m) return { r: +m[1], g: +m[2], b: +m[3] };
  return null;
}

function _hex({ r, g, b }) {
  const c = (n) => Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, "0");
  return `#${c(r)}${c(g)}${c(b)}`;
}

function _mix(a, b, t) {
  return {
    r: a.r + (b.r - a.r) * t,
    g: a.g + (b.g - a.g) * t,
    b: a.b + (b.b - a.b) * t,
  };
}

/** Typical Comfy title-bar purple when node has no colour set yet. */
export const COMFY_DEFAULT_NODE_COLOR = "#7c6bb0";
export const COMFY_DEFAULT_NODE_BG = "#1e1e1e";

/** Relative luminance 0–1 (sRGB approx). */
function _luma({ r, g, b }) {
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
}

/**
 * Theme packs paint near-black shells. Those read as "no colour" in native mode
 * (inner UI is also dark → accents look grey). Treat them as unset for native seed.
 */
export function isNearBlackShell(color) {
  const p = parseCssColor(color);
  if (!p) return true;
  return _luma(p) < 0.14;
}

/**
 * Lift a dark shell colour into a mid-bright accent that still keeps the same hue.
 * Comfy dots often set deep title colours; chips need something readable on #252525.
 */
export function liftToAccentColor(rgb, targetLuma = 0.48) {
  if (!rgb) return parseCssColor(COMFY_DEFAULT_NODE_COLOR);
  let { r, g, b } = rgb;
  let L = _luma(rgb);
  if (L >= targetLuma) return rgb;
  // Scale channels up until luminance hits target (preserves hue ratios)
  if (L < 0.02) {
    // Near pure black / unknown → default purple accent
    return parseCssColor(COMFY_DEFAULT_NODE_COLOR);
  }
  const scale = Math.min(4.5, targetLuma / L);
  r = Math.min(255, r * scale);
  g = Math.min(255, g * scale);
  b = Math.min(255, b * scale);
  // If still dark (channel clamp), mix toward white
  let out = { r, g, b };
  let L2 = _luma(out);
  if (L2 < targetLuma) {
    out = _mix(out, { r: 255, g: 255, b: 255 }, Math.min(0.55, (targetLuma - L2) * 1.4));
  }
  return out;
}

/**
 * Ensure LiteGraph shell has a visible colour under native look.
 * - Empty / near-black (theme pack leftovers) → Comfy default purple
 * - User palette pick (mid/bright) → leave alone
 * Returns { color, bgcolor } after any fix.
 */
export function ensureComfyNativeShell(node) {
  if (!node) return { color: COMFY_DEFAULT_NODE_COLOR, bgcolor: COMFY_DEFAULT_NODE_BG };
  const cur = String(node.color || "").trim();
  if (!cur || cur === "null" || cur === "undefined" || isNearBlackShell(cur)) {
    node.color = COMFY_DEFAULT_NODE_COLOR;
  }
  if (!node.bgcolor || isNearBlackShell(node.bgcolor)) {
    // Body stays dark (Comfy-like) but not pure black
    node.bgcolor = COMFY_DEFAULT_NODE_BG;
  }
  try { node.setDirtyCanvas?.(true, true); } catch { /* */ }
  return { color: node.color, bgcolor: node.bgcolor };
}

/**
 * Build CSS vars for native mode.
 *
 * Shell (LiteGraph): node.color / node.bgcolor stay whatever Comfy's colour dots set
 * (we do NOT paint the whole inner UI that colour — unreadable).
 *
 * Inner widgets: always dark readable surfaces.
 * Accents (chips, Generate, borders): lifted from node.color so they actually show.
 * Semantic controls: fixed blue ON / red OFF for clarity.
 *
 * @param {string} nodeColor  LiteGraph node.color (title bar / accent)
 * @param {string} [nodeBg]   LiteGraph node.bgcolor (unused for fills — kept for API)
 */
export function comfyAccentVarsFromNodeColor(nodeColor, nodeBg) {
  const white = { r: 255, g: 255, b: 255 };
  // Prefer title colour; fall back to body colour if title missing
  const raw =
    parseCssColor(nodeColor) ||
    parseCssColor(nodeBg) ||
    parseCssColor(COMFY_DEFAULT_NODE_COLOR);
  // Lift dark theme shells so selected chips / Generate read as real colour
  const base = liftToAccentColor(raw, 0.48);

  const accent = _hex(base);
  const soft = _hex(_mix(base, white, 0.28));
  const pale = _hex(_mix(base, white, 0.45));
  // Fixed semantic colours (always readable on dark panels)
  const onBlue = "#5eb8f0";
  const offRed = "#f07178";

  return {
    // One shell accent for chips + section panels (no cyan/rose/gold mix-up)
    "--violet": accent,
    "--accent": accent,
    "--cyan": accent,
    "--gold": soft,
    "--rose": accent,
    "--mint": soft,
    // Match PromptForge selected chips (shell hue); OFF/remove still red below
    "--on-color": accent,
    "--str": soft,
    "--vc": soft,
    "--ac": accent,
    // INNER UI always dark — never fill boxes with the node shell colour
    "--bg": "#1a1a1a",
    "--panel": "#252525",
    "--line": "rgba(255,255,255,0.14)",
    "--text": "#ececec",
    "--muted": "#a8a8a8",
    "--glow-a": "transparent",
    "--glow-b": "transparent",
    "--comfy-accent": accent,
    "--comfy-accent-soft": soft,
    "--comfy-on": accent,
    "--comfy-off": offRed,
  };
}

/** Apply accent map onto an element (inline style). */
export function applyComfyAccentVars(el, nodeColor, nodeBg) {
  if (!el) return;
  const vars = comfyAccentVarsFromNodeColor(nodeColor, nodeBg);
  Object.entries(vars).forEach(([k, v]) => el.style.setProperty(k, v));
}
