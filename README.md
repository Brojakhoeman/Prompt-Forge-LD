<img width="424" height="619" alt="Screenshot 2026-07-14 162333" src="https://github.com/user-attachments/assets/da24ea88-e997-4f65-870e-af52d22ad5be" />


https://github.com/user-attachments/assets/901c891e-15da-4815-ac7a-7b4956558b8a







# PromptForge LD

Slimline LTX Video 2.3 prompt node. **His UI, your brain, less of everything.**

Ground-up rebuild that fixes the core problem with the older nodes: *we were
doing too much*. Micro-detail stacking, flavour-bank dumps, per-beat continuity
nagging and 15k-char system prompts were cluttering the box and hurting the
generations. This node ships **one strong doctrine and gets out of the way.**

## What it is

- **LTX 2.3 video only** — `i2v` and `t2v`. No image mode, no Krea, no Ideogram.
- **The CANON** — the literal-language doctrine (mechanism-not-outcome, render-safe
  body verbs, no vibe words, trust the model). This is the whole engine.
- **The POV CONTRACT** — the four-channel window doctrine (view / hands / sound /
  consequence), distilled. This is the part that was already better than Grok's.
- **Action sections, no timestamps.** The shot is a list of action sections
  separated by blank lines — shot-script structure *without* the clock. Each
  section is one action and carries its motion, an optional inline spoken line,
  and (only when they change) a camera/sound note. **Sections scale with the
  action** — a big move earns a paragraph, a glance is one line. A busy 20s shot
  can run 8–12 sections; a calm one runs 3–4.
- **Emotion brackets for dialogue.** Spoken lines land inline where the mouth
  opens, with a delivery bracket: `he lifts his chin and says (scarily): "you
  are next"`. The bracket steers the voice, it isn't rendered as text.
- **Real dialogue budget.** Talkative aims for ~1 spoken word per second across
  several natural lines — no more "3 words in 15 seconds". Standard is a few
  lines where they fit; Silent is breath/moans only.
- Environments + scenarios are **short shape-hints**, not preset walls of prose.
  For I2V the frame is truth, so the environment is a nudge only.

## UI (from Grok Prompt Lab, kept because it's good)

- Coverflow image carousel (wheel-scroll, centre card scales) + folder browse.
- ResMaster resolution widget with LTX aspect presets.
- Live SSE streaming into the script box, ghost-beat film strip, Preview pane.
- 3 backends: managed **llama.cpp**, **LM Studio**, **Ollama**.

## Controls

`i2v / t2v` · Silent / Standard / Talkative · Off / POV♀ / POV♂ · Energy 1–10 ·
Scenario · Environment. Explicit is **auto-detected** from your intent — no
toggle. No Solo/Duo, no density knob: it's just your intent + length. Fewer
knobs, less clutter, better output.

## Deliberately NOT included (this is the point)

- No 13k-line vocal-enhancement bank, no facial-performance / physical-continuity
  JSON dumps. Motion + sound carry the clip.
- No Grok gold-reference verbatim templates / clause-grafting. That overfits to a
  handful of memorised scenes and is SD-anchor thinking, not LTX flow-matching.
- No per-beat micro-cue requirements (knuckle-whitening, hair strands). They
  clutter the frame and cause failures.
- No camera-move dropdown, no doctrine profiles. Fewer knobs, better output.

## Files

- `brain_ld.py` — the whole brain (CANON + POV contract + formats). ~350 lines.
- `generation_core.py` — one backend-agnostic streaming path.
- `environments_ld.py` / `scenarios_ld.py` — short LTX-smart anchors.
- `llama_manager.py` — 3-backend server lifecycle (from PromptNodething v2brain).
- `api.py` — `/pfld/*` routes. `node.py` — ComfyUI node + unpack.
- `js/` — carousel, res-master, main UI.

Wire: **PromptForge LD → PromptForge Unpack → (image, positive, negative, w, h)**.
