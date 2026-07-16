# PromptForge LD

**A serious shot-writer for LTX Video in ComfyUI.**

PromptForge LD is a full creative panel — not a one-line text box. It helps you write clean, render-safe motion scripts for **image-to-video** and **text-to-video**, then packs the result (image, positive, negative, size) for the rest of your graph.

A lot of care went into how it writes: body mechanics that LTX can actually draw, dialogue that stays readable, continuity between clips, accents and styles that only inject when you ask for them, and a gallery that reloads when you change folders. The goal is simple: **better scripts, fewer bad frames, less fighting the model.**

> **SFW note:** This README stays family-friendly. The node itself is a general-purpose shot-writer — you decide the subject matter.

---

## What’s in the pack

| Node | Role |
|------|------|
| **PromptForge LD** | Main writer UI + Generate / Refine |
| **PromptForge Unpack** | Splits the pack into image · positive · negative · width · height |
| **LoraForge LD** | Multi-LoRA stack with **separate video / audio strengths** and mouse-wheel control |

Typical wire:

```
PromptForge LD  →  PromptForge Unpack  →  (your LTX / sampler graph)
LoraForge LD    →  model / clip        (optional)
```

---

## Install (ComfyUI)

1. Copy or clone this folder into:

   ```
   ComfyUI/custom_nodes/PromptForgeLD/
   ```

2. Restart ComfyUI (or reload custom nodes).

3. Find the nodes under **LD / PromptForge**.

4. You’ll also need a **local language model** for Generate (see options below). The node does **not** ship model weights.

---

## Option A — LM Studio (easiest)

Great if you want a simple app with a UI.

### 1. Install LM Studio

Download and install from:

**https://lmstudio.ai/**

### 2. Get a model

**Recommended (tested with this node):**

**HauhauCS · Gemma 4 26B A4B Uncensored Balanced**

- Repo: [HauhauCS/Gemma4-26B-A4B-Uncensored-HauhauCS-Balanced](https://huggingface.co/HauhauCS/Gemma4-26B-A4B-Uncensored-HauhauCS-Balanced/tree/main)

In LM Studio:

1. Open the **Discover / Search** tab (or download GGUF files from Hugging Face and point LM Studio at your models folder).
2. Download a **GGUF** quant that fits your VRAM (start smaller if you’re unsure; step up when it’s stable).
3. Load the model in LM Studio.

### 3. Start the local server

1. In LM Studio, open the **Developer / Local Server** section (wording can vary slightly by version).
2. Load your model.
3. Click **Start server**.
4. Default URL is usually:

   ```
   http://127.0.0.1:1234
   ```

5. Note the **exact model name / id** shown while the server is running (you’ll paste this into the node).

### 4. Connect PromptForge LD

1. On the PromptForge node, open the **gear (⚙) / connection** panel.
2. Set backend to **LM Studio**.
3. Set server URL to `http://127.0.0.1:1234` (or whatever LM Studio shows).
4. Paste the **model name** into the model field so it matches what the server reports.
5. Save connection, then use **Generate**.

**Tip:** Leave the server running while you iterate. Use **Keep LLM warm** in the node if you want faster back-to-back generates.

---

## Option B — llama.cpp (`llama-server`) + CUDA (Windows)

For users who prefer a standalone server and full control.

### 1. Download prebuilt Windows CUDA binaries

Official releases (pick the latest **Windows x64 CUDA** build that matches your CUDA generation):

**https://github.com/ggml-org/llama.cpp/releases**

You’ll typically want:

| File | What it is |
|------|------------|
| `llama-…-bin-win-cuda-…-x64.zip` | The tools, including **`llama-server.exe`** |
| Matching **`cudart-…`** zip (CUDA runtime DLLs) | Runtime libraries the server needs |

Example naming from the releases page (version numbers change over time):

- Windows x64 **CUDA 12** build + **CUDA 12.x** runtime DLLs  
- or Windows x64 **CUDA 13** build + matching runtime DLLs  

Unzip both into the **same folder** (so `llama-server.exe` sits next to the CUDA DLLs).

> Use the CUDA line that matches the drivers / toolkit you already run for ComfyUI. If Comfy is happy on your GPU, match that generation (12 vs 13) when possible.

### 2. Download the model (GGUF)

**Recommended:**

**https://huggingface.co/HauhauCS/Gemma4-26B-A4B-Uncensored-HauhauCS-Balanced/tree/main**

1. Open the repo and download a **`.gguf`** quant that fits your VRAM.
2. Put it in a folder you’ll remember, e.g. `C:\models\`.

For **image-to-video** writing that uses vision, you may also need a matching **mmproj** (vision projector) if you run a multimodal GGUF pair — follow the model card. Text-only writing works with a standard GGUF alone.

### 3. Point PromptForge at llama-server

1. Gear panel → backend **llama.cpp (managed)** (or connect to a server you started yourself).
2. Set path to **`llama-server.exe`**.
3. Set **models folder** to where your GGUF lives.
4. Pick the model (and mmproj if used) from the dropdowns after a scan.
5. Save → Generate.

You can also start `llama-server` yourself and point the node at that URL; the node’s managed path just automates boot/scan for convenience.

---

## Option C — Ollama

If you already use Ollama:

1. Install from **https://ollama.com/**
2. Pull / run a capable chat model.
3. In PromptForge gear: backend **Ollama**, URL usually `http://127.0.0.1:11434`, model name as Ollama lists it.

LM Studio or llama-server + the Gemma build above is the path we test most.

---

## Using PromptForge LD

### Modes

| Mode | Use when |
|------|----------|
| **I2V** | You have a **start image**. The first frame is law — pose, wardrobe, and look should stay honest to that still. |
| **T2V** | No required start image (or a black frame at your chosen size). Full recipes and look seeds available. |

### Shot row

- **Dialogue** — Silent · Standard · Talkative (how much people speak)
- **POV** — Off, or a first-person style camera (female / male)
- **Cast** — Solo · Pair · Group
- **Duration** — Local slider, or wire `duration_s` / `fps` from the graph

### Scene

- **Camera** — Optional camera-motion language  
- **Scenario** — Structure packs (I2V and T2V lists are different on purpose)  
- **Environment** — Place / light / atmosphere  
- **Music** — Soundtrack groove (pairs especially well with music-video style)  
- **Lead** — Who the primary subject is  
- **Style** — Optional **video style path** (e.g. soft fashion, horror mood, music-video energy, slice-of-life…). **None** adds zero extra tokens  
- **Detailer** — Optional quality pass for lighting and surface detail (default off)

### Voice

- **Accent · Lead / Partner** — How people sound (and on T2V, matching look seeds when useful)  
- **Carry** — Remember wardrobe / pose notes into the next Generate  

### Energy

- **Body** — How strong / energetic the physical motion is  
- **Mouth** — How rich or intense the spoken delivery is  

These are **independent**. Soft body + lively speech is allowed.

### Frame

- Resolution / aspect for LTX-friendly sizes  
- **Image gallery** — Point at a folder, **Apply**, scroll the coverflow  
- Upload or pick a still for I2V  
- Folder changes reload immediately (no full page refresh)

### Intent → script

1. Write what should happen in **Intent** (who, where, what motion, any lines you care about).  
2. Press **Generate**.  
3. Read the **LTX script**. Edit if you want.  
4. **Refine** with a short revision note in Intent when you only need a pass of changes.  
5. Queue the graph — only the **committed** script goes out as the positive.

Also:

- **History** — Recent scripts  
- **Preview** — See assembled system/user context (advanced)  
- **Copy** — Clipboard  

### Gear panel (connection & quality)

- Backend: LM Studio · llama.cpp · Ollama  
- **Keep LLM warm** / **Kill LLM** (free VRAM)  
- Sampler temperature  
- **Seed** — Unlock to re-roll every Generate; lock to reproduce  
- **Themes** (shared with LoraForge): Violet · Midnight · Neon · Warm · Terminal · Arctic · Rose · Ember · Ocean · Mono  
- **Node size** (large default so the panel stays usable)

---

## LoraForge LD

A dedicated LoRA stack for video workflows.

- Stack multiple LoRAs on the model / clip path  
- **Separate strengths** for **video** and **audio** where that split matters for your pipeline  
- **Mouse wheel:** hover a strength control and **scroll** to raise or lower it quickly — no need to type tiny numbers for every tweak  
- Built for fast iteration while you audition looks and motion styles  

Wire it upstream of your sampler / LTX stack the same way you’d use a normal multi-LoRA loader, then fine-tune strengths with the wheel.

---

## Design ideas we cared about

These aren’t marketing bullets — they’re the rules the writer tries to obey so LTX fails less often:

1. **Mechanism first** — Clothes move when hands move them; bodies take real paths through space.  
2. **No teleport motion** — Avoid “snap / suddenly” style language that confuses the video model.  
3. **Head and torso turn together** — A common failure mode is a neck that spins alone; the writer and cleanup pass fight that.  
4. **One clear action per beat** — Sections with blank lines, easy to scan and retime.  
5. **Intent wins** — Presets nudge; your words lead.  
6. **Optional layers stay optional** — Style, Detailer, accents: off means almost no extra tokens. Niche dialogue lives in the dialogue bank (only activates on matching intent).
7. **Negatives that match the shot** — Built for graphs that use a NAG-style negative path so the “don’t do this” list actually steers.  
8. **Iterate warm** — Seed unlock + keep-warm so re-rolls stay fast once the model is loaded.

A lot of the work is invisible: cleanup after the model writes, budget rules for talkative scenes, mode-specific scenario lists, gallery cache-busting, continuity carry, dual energy axes, and dozens of small guards so the script stays *filmable*.

---

## Quick start checklist

- [ ] Custom node folder in `ComfyUI/custom_nodes/PromptForgeLD`  
- [ ] Comfy restarted  
- [ ] LM Studio **or** `llama-server` running with a GGUF loaded  
- [ ] Recommended model family: [HauhauCS Gemma 4 26B balanced](https://huggingface.co/HauhauCS/Gemma4-26B-A4B-Uncensored-HauhauCS-Balanced/tree/main)  
- [ ] Server URL + **exact model name** saved in the gear panel  
- [ ] I2V: start image selected · T2V: resolution set  
- [ ] Intent filled → **Generate** → Unpack → rest of graph  

---

## Troubleshooting

| Problem | Try this |
|---------|----------|
| Generate fails / connection error | Confirm LM Studio or llama-server is running; check URL and model name match exactly |
| I2V refuses | Select a start image; for vision paths ensure mmproj is set if your backend needs it |
| Gallery empty after folder change | Click **Apply** on the path; use the refresh control on the carousel |
| Script feels too short for a long duration | Prefer clearer multi-step intent, or Talkative if you need more spoken lines; movement-heavy clips are often intentionally sparse |
| VRAM full | Kill LLM in the gear panel; close other GPU apps; use a smaller GGUF quant |
| Want a different take | Unlock **Seed**, Keep warm on, Generate again |

---

## Privacy & local-first

Generation is designed for **your machine** and **your** LLM server. No cloud account is required for the node itself. You choose the model and whether it ever leaves localhost.

---

## Credits & models

- **PromptForge LD / LoraForge LD** — built for people who care how LTX actually moves  
- **Suggested weights:** [HauhauCS/Gemma4-26B-A4B-Uncensored-HauhauCS-Balanced](https://huggingface.co/HauhauCS/Gemma4-26B-A4B-Uncensored-HauhauCS-Balanced/tree/main)  
- **llama.cpp / llama-server:** [ggml-org/llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases)  
- **LM Studio:** [lmstudio.ai](https://lmstudio.ai/)  

Model licenses and terms are those of their authors — always check the Hugging Face model card.

---

## License

See the repository license file (if provided) or contact the maintainer. Third-party models and tools remain under their own licenses.

---

**Write the shot. Don’t fight the frame.**
