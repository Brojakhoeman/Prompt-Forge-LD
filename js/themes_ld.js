/**
 * Shared visual themes for PromptForge LD + LoraForge LD.
 * Same keys + matching hues so both nodes feel like one product.
 *
 * Each theme:
 *   name   — UI label
 *   pf     — CSS vars for .gpl-root (PromptForge)
 *   lf     — tokens for LoraForge cups / chrome
 *   node   — Comfy node shell colors (LiteGraph title bar)
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
  // Minimal / dull — get the job done, no candy
  "slate",
  "graphite",
  "concrete",
];

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

  mono: {
    name: "Mono",
    pf: {
      "--bg": "#0a0a0c",
      "--panel": "rgba(20, 20, 24, 0.94)",
      "--text": "#ececef",
      "--muted": "#888890",
      "--gold": "#c8c8d0",
      "--cyan": "#a0a0a8",
      "--violet": "#909098",
      "--rose": "#b0b0b8",
      "--mint": "#9898a0",
      "--line": "rgba(255,255,255,.10)",
      "--glow-a": "rgba(200,200,210,.08)",
      "--glow-b": "rgba(160,160,170,.06)",
    },
    lf: {
      str: "#c8c8d0",
      v: "#a0a0a8",
      a: "#909098",
      on: "#d0d0d8",
      off: "#a06060",
      accent: "#c8c8d0",
      bg: "#0a0a0c",
      panel: "rgba(255,255,255,.03)",
      text: "#ececef",
      muted: "#888890",
      line: "rgba(255,255,255,.10)",
    },
    node: { color: "#1a1a1e", bgcolor: "#0c0c0e" },
  },

  // ── Minimal / dull (Comfy-stack energy — workbench, not candy) ───────────
  slate: {
    name: "Slate",
    pf: {
      "--bg": "#1a1a1a",
      "--panel": "rgba(36, 36, 36, 0.96)",
      "--text": "#d0d0d0",
      "--muted": "#6e6e6e",
      "--gold": "#9a9a9a",
      "--cyan": "#8a8a8a",
      "--violet": "#7a7a7a",
      "--rose": "#8e8e8e",
      "--mint": "#858585",
      "--line": "rgba(255,255,255,.07)",
      "--glow-a": "rgba(0,0,0,.0)",
      "--glow-b": "rgba(0,0,0,.0)",
    },
    lf: {
      str: "#9a9a9a",
      v: "#8a8a8a",
      a: "#7a7a7a",
      on: "#b0b0b0",
      off: "#6a6a6a",
      accent: "#9a9a9a",
      bg: "#1a1a1a",
      panel: "rgba(255,255,255,.04)",
      text: "#d0d0d0",
      muted: "#6e6e6e",
      line: "rgba(255,255,255,.07)",
    },
    node: { color: "#2a2a2a", bgcolor: "#161616" },
  },

  graphite: {
    name: "Graphite",
    pf: {
      "--bg": "#121214",
      "--panel": "rgba(28, 28, 32, 0.96)",
      "--text": "#c8c8cc",
      "--muted": "#5c5c64",
      "--gold": "#8b8b94",
      "--cyan": "#7a7a84",
      "--violet": "#6e6e78",
      "--rose": "#82828a",
      "--mint": "#767680",
      "--line": "rgba(255,255,255,.06)",
      "--glow-a": "rgba(0,0,0,.0)",
      "--glow-b": "rgba(0,0,0,.0)",
    },
    lf: {
      str: "#8b8b94",
      v: "#7a7a84",
      a: "#6e6e78",
      on: "#a0a0a8",
      off: "#5a5a62",
      accent: "#8b8b94",
      bg: "#121214",
      panel: "rgba(255,255,255,.035)",
      text: "#c8c8cc",
      muted: "#5c5c64",
      line: "rgba(255,255,255,.06)",
    },
    node: { color: "#222226", bgcolor: "#0e0e10" },
  },

  concrete: {
    name: "Concrete",
    pf: {
      "--bg": "#1c1b1a",
      "--panel": "rgba(40, 38, 36, 0.96)",
      "--text": "#c4c0ba",
      "--muted": "#6a6660",
      "--gold": "#908880",
      "--cyan": "#807870",
      "--violet": "#787068",
      "--rose": "#888078",
      "--mint": "#7c746c",
      "--line": "rgba(255,255,255,.06)",
      "--glow-a": "rgba(0,0,0,.0)",
      "--glow-b": "rgba(0,0,0,.0)",
    },
    lf: {
      str: "#908880",
      v: "#807870",
      a: "#787068",
      on: "#a09890",
      off: "#5c5850",
      accent: "#908880",
      bg: "#1c1b1a",
      panel: "rgba(255,255,255,.035)",
      text: "#c4c0ba",
      muted: "#6a6660",
      line: "rgba(255,255,255,.06)",
    },
    node: { color: "#2c2a28", bgcolor: "#141312" },
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
