<img width="424" height="619" alt="image" src="https://github.com/user-attachments/assets/42a85a9d-5235-4163-a2d4-a9aed675b1e2" />
<img width="437" height="254" alt="image" src="https://github.com/user-attachments/assets/c0db65a0-4934-4029-880e-6fc43f3b5d34" />


https://github.com/user-attachments/assets/a4db89b0-4d88-4407-b084-04fcd7fdf051



Scroll your mouse wheel to change the lora strenghs. or click to add a number. 
scroll to use the image carousel



# ✦ PromptForgeLD

A powerful ComfyUI node for cinematic **LTX-Video 2.3** prompt engineering and video generation. Built for creative professionals who need fine-grained control over character direction, environment, cinematography, and dialogue in AI video.

## Features

### Core Capabilities
- **Dual Video Modes**: Image-to-Video (I2V) and Text-to-Video (T2V)
- **LLM-Powered Prompt Generation**: Integrates local LLMs (llama.cpp, LM Studio, Ollama) for smart prompt suggestions
- **Vision-Enabled**: Processes reference images with multimodal vision models (Qwen3-VL)
- **Resolution Master**: Responsive aspect ratio controller with LTX 2.3 presets
- **Image Carousel**: Browse and select reference images from your input folder

### Control Interfaces
- **Environment & Scenario Library**: Curated sets for cinematic contexts
- **Camera Movement Presets**: Pan, dolly, push, and tracking motions
- **POV/Dialogue Tiers**: Gender-aware dialogue generation and perspective control
- **LoRA Forge Integration**: 10-slot LoRA loader with video/audio split weighting
- **Music Tags**: Audio mood and style markers for music-aware generation

### Persistence & Quality
- **Live Textarea Persistence**: Intent and output prompts auto-save across restarts
- **Session Restore**: Automatic recovery of last workflow state
- **Backend Health Monitoring**: Real-time connection status for managed and remote LLM servers

## Installation

1. Clone into your ComfyUI custom_nodes:
   ```bash
   cd ComfyUI/custom_nodes
   git clone https://github.com/yourusername/PromptForgeLD.git
   ```

2. Restart ComfyUI

3. The node appears under **LD/PromptForge** category

## Quick Start

### Basic I2V Workflow
1. Load an image into your input folder
2. Create a **✦ PromptForge LD** node
3. Click the **⚙** (cog) to configure LLM backend
   - Managed: Uses built-in llama.cpp
   - Remote: Point to LM Studio or Ollama instance
4. Select environment, scenario, camera move, music
5. Write your intent in the intent textarea
6. Click **Generate** — LLM builds the detailed prompt
7. Review and refine in the output textarea
8. Click the **▶** button or press Enter to commit to workflow

### Advanced: LoRA Control
Connect **LoraForgeLD** downstream:
- Stack up to 10 custom LoRAs
- Split video vs audio strengths independently
- Live enable/disable per slot

## Node Inputs

### Required (Visible in UI)
- **video_mode**: I2V or T2V
- **environment**: Scene context (garden, office, studio, etc.)
- **scenario**: Action framework (monologue, interview, performance, etc.)
- **camera_move**: Motion preset (static, pan_left, dolly_in, etc.)
- **music**: Audio mood tag (ambient, dramatic, upbeat, etc.)
- **pov**: Boolean toggle for perspective mode
- **pov_gender**: female or male (influences dialogue generation)
- **dialogue_tier**: none, standard, or talkative
- **intensity**: 1–10 strength scale for prompt aggressiveness
- **user_intent**: Your creative direction (textarea, auto-saves)
- **confirmed_prompt**: Final prompt for video gen (persisted)
- **image_filename**: I2V reference image (or paste as b64)
- **rm_w / rm_h**: Output resolution from ResMaster
- **model_file / mmproj_file**: Vision model selection

### Optional (Usually Wired)
- **duration_s**: Video length in seconds (default 12.0)
- **fps**: Frame rate (default 24)

### Output
- **pack**: `PFLD_PACK` type containing image, positive prompt, negative prompt, width, height

## Node Outputs

### Primary Output: PFLD Pack
Contains:
- **image**: Prepared reference (I2V) or black frame (T2V)
- **positive**: Finalized prompt string
- **negative**: Auto-generated negative prompt
- **width / height**: Resolution from ResMaster

### Unpack Node: PromptForgeLDUnpack
Splits the pack for downstream connections:
```
PACK → [Unpack] → IMAGE, STRING (positive), STRING (negative), INT, INT
```

## API Routes

For integrations or extending functionality:

| Route | Method | Purpose |
|-------|--------|---------|
| `/pfld/generate_stream` | POST | Stream LLM prompt generation |
| `/pfld/assemble_preview` | POST | Preview without LLM (fast preview) |
| `/pfld/health` | GET | Check LLM backend status |
| `/pfld/scan_models` | POST | Discover GGUF models in folder |
| `/pfld/set_backend` | POST | Switch LLM (managed/remote) |
| `/pfld/list_images` | GET | Browse input folder |
| `/pfld/thumb` | GET | Generate thumbnail |
| `/pfld/lora_list` | GET | Available LoRAs |

## LLM Backend Configuration

### Managed (Built-in)
- Uses `llama.cpp` if available in `C:\llama\` (Windows) or system PATH
- Auto-selects best model from your models folder
- Requires GGUF format models

### LM Studio (Remote)
- Point to `http://localhost:1234` (default)
- Load any model in LM Studio's UI first
- Supports both GGUF and safetensors

### Ollama
- Point to `http://localhost:11434` (default)
- Requires Ollama running locally
- Works with ollama models (llama2, mistral, etc.)

## Architecture

```
PromptForgeLD/
├── __init__.py                 # Package init + WEB_DIRECTORY declaration
├── node.py                     # PromptForgeLD & PromptForgeLDUnpack node classes
├── api.py                      # aiohttp routes for LLM + image serving
├── generation_core.py          # Prompt generation pipeline
├── brain_ld.py                 # LLM prompt composition logic
├── dialogue_ld.py              # Dialogue generation + tier control
├── environments_ld.py          # Scene + scenario libraries
├── camera_ld.py                # Camera move presets
├── music_ld.py                 # Music tag system
├── llama_manager.py            # Backend connection (managed/remote)
├── lora_forge.py               # LoRA loader node (10 slots, video/audio split)
├── pack_ld.py                  # PFLD_PACK serialization
├── js/
│   ├── prompt_forge.js         # Main UI widget + extension registration
│   ├── prompt_forge.css        # Styling (purple/gold LoRa-Daddy theme)
│   ├── lora_forge.js           # LoRA stack UI
│   ├── image_carousel.js       # Image browser widget
│   └── res_master.js           # Resolution/aspect ratio controls
└── README.md
```

## Configuration

### First Launch
1. Open **PromptForgeLD** node in ComfyUI
2. Click **⚙** (settings cog)
3. Select backend:
   - **llama.cpp (managed)**: Auto-finds models
   - **LM Studio**: Enter server URL + load model there
   - **Ollama**: Enter server URL + select model
4. Choose GGUF model and optional vision projection
5. Test with **Health** button

### Persisted Settings
Stored in browser localStorage:
- Selected backend type and server URL
- Model selections (text + vision)
- Layout preferences (panel widths, theme)
- Input folder path
- Video mode (I2V vs T2V)

## Workflows

### Example Workflows Included
- **ltx23I2VWorkflow_v20.json** — Full I2V pipeline with LTXV audio-visual generation

Load in ComfyUI via **Queue** → **Load** (or drag into canvas).

## Theming

Built-in themes in the cog panel:
- **default**: Purple/gold (LoRa-Daddy brand)
- **midnight**: Dark blue/muted gold
- **terminal**: Green matrix aesthetic
- **neon**: Bright cyan/magenta
- **warm**: Sepia/orange

Customize CSS variables in `js/prompt_forge.css`:
```css
--bg: '#07040e',
--text: '#f0ebff',
--gold: '#ffc857',
--cyan: '#5ce1e6',
--violet: '#a855f7',
```

## Troubleshooting

### UI Not Loading
- Clear browser cache or hard refresh (Ctrl+Shift+R)
- Restart ComfyUI server completely
- Check browser console for JavaScript errors

### LLM Connection Fails
- Verify backend is running (LM Studio, Ollama, or llama.cpp)
- Check server URL and port in settings
- Click **Health** probe to see detailed error
- Ensure model is loaded in the backend

### Prompts Not Persisting
- Browser storage must be enabled
- Check ComfyUI's workflow saves (prompts auto-save to widget values)
- Use the **Reset Layout** button if UI feels broken

## Performance Tips

- **Local Vision**: Qwen3-VL-8B runs on 24GB VRAM; consider quantized variants for lower VRAM
- **Remote LLM**: For faster iteration, use LM Studio or Ollama on same/nearby GPU
- **Batch Size**: LoRA loading is sequential; preload static LoRAs outside PromptForgeLD for speed

## Contributing

Issues, PRs, and feature requests welcome. This is an actively developed node suite.

## Credits

**PromptForgeLD** by LoRa-Daddy (paulhaul / Brojakhoeman)
- Core LTX-Video 2.3 integration
- LLM-driven prompt engineering
- Vision model integration

Built on ComfyUI, LM Studio, Ollama, and llama.cpp.

## License

MIT — Use freely in your workflows and forks.

---

**Status**: Active development | **Last Updated**: July 2026
