# PromptForgeLD Workflows

Example workflows for LTX-Video 2.3 with PromptForgeLD integration.

## ltx23I2VWorkflow_v20.json

A complete **Image-to-Video + Audio Generation** pipeline featuring:

### Visual Pipeline
- **Reference Image** → PromptForgeLD (I2V mode)
- Dimension control (768×512, configurable via ResMaster)
- LTX-2.3 unet inference
- VAE decode to video frames
- Video export (h264-mp4, 25 FPS)

### Audio Pipeline
- **Dialogue Prompt** → LTX-V Gemma-3 CLIP encoder
- LTXV Audio VAE latent space generation
- Audio decode via vocoder
- Synchronized with video output

### Key Nodes

#### Model Loaders (Toggle via Label comments)
- **Checkpoint Path**: `ltx2310eros1.4.safetensors`
- **CLIP Options**:
  - Safetensors: Gemma-3-12b-it-heretic (v2, fp8)
  - GGUF: Gemma-3-12b-it-Q4_K_S (quantized, faster)
- **Text Projection**: ltx-2.3_text_projection_bf16
- **Vocoder**: ltx-av-step-1751000_vocoder_24K

#### Conditioning
- **Positive**: Your detailed prompt (from PromptForgeLD)
- **Negative**: Auto-generated negatives (from PromptForgeLD)
- **LTXVConditioning**: Frame rate + embedding formatting

#### Sampling
- **KSampler**: Euler sampler (20 steps, configurable)
- **LTXVScheduler**: Shift scheduling (base=0.95, max=2.05)
- **Multimodal Guider**: 
  - Video CFG: 3
  - Audio CFG: 7
  - Stagger (STG): 0
  - Modality scale: 3

#### Latent Handling
- **EmptyLTXVLatentVideo**: 768×512, frame count = 105 (4.2 sec @ 25fps)
- **LTXVEmptyLatentAudio**: Matching audio latent
- **LTXVConcatAVLatent**: Merge video + audio latents
- **SamplerCustomAdvanced**: Unified AV sampling
- **LTXVSeparateAVLatent**: Split output back to video/audio

#### Output
- **VAEDecode**: Video frames
- **LTXVAudioVAEDecode**: Audio waveform
- **VideoCombine**: Merge with MP4 container (h264, CRF=19, metadata=true)

### Workflow Settings

**Frame Configuration**:
- Resolution: 768×512 (9:16 mobile ratio)
- Duration: 105 frames @ 25 FPS = 4.2 seconds
- Adjust `EmptyLTXVLatentVideo` length node to scale

**Sampling**:
- Steps: 20 (balance speed/quality)
- Euler sampler (stable, predictable)
- Noise seed: Randomized (change for variation)

**Conditioning Strength**:
- Video guidance (CFG): 3 (moderate adherence to prompt)
- Audio guidance (CFG): 7 (strong dialogue/audio prompt matching)
- Adjust in GuiderParameters nodes

**Quality**:
- MP4 CRF: 19 (visually lossless; 0=lossless, 51=worst)
- Pixel format: yuv420p (H.264 standard)
- Loop count: 0 (single pass; >0 for repeat)

### Setup Instructions

1. **Models Required**:
   - Ensure checkpoint: `ltx2310eros1.4.safetensors`
   - Ensure vocoder: `ltx-av-step-1751000_vocoder_24K.safetensors`
   - Choose CLIP variant (safetensors OR GGUF, not both)

2. **Load Workflow**:
   - In ComfyUI: **Queue** → **Load** → Select this JSON
   - Or drag JSON onto canvas

3. **Configure PromptForgeLD**:
   - Plug your reference image into PromptForgeLD
   - Write intent in the intent textarea
   - Click **Generate** to build prompt
   - Copy to the **Positive** node's textarea

4. **Queue**:
   - Adjust steps/CFG as needed
   - Press **Queue Prompt**
   - Monitor output folder

### Customization

#### Aspect Ratio
Modify `EmptyLTXVLatentVideo` node:
```
- width: 768 (adjust by 64-pixel increments)
- height: 512 (adjust by 64-pixel increments)
```

Common presets:
- **1:1 (square)**: 512×512
- **9:16 (mobile)**: 576×1024 or 768×1365
- **16:9 (widescreen)**: 1088×613
- **4:3 (classic)**: 832×624

#### Video Length
Modify `INT Constant` node (value 105):
```
Frames = (Duration_seconds × FPS) - 1
Examples:
- 3 sec @ 25 fps = 74 frames
- 6 sec @ 25 fps = 149 frames
- 10 sec @ 25 fps = 249 frames
```

#### Sampling Quality vs Speed
- **Fast** (quality=60): steps=12, CFG_video=2, CFG_audio=5
- **Balanced** (current): steps=20, CFG_video=3, CFG_audio=7
- **Quality** (slow): steps=30, CFG_video=4, CFG_audio=8

#### Audio Focus
Increase `GuiderParameters` audio node CFG to emphasize dialogue:
```
Default: 7
Stronger audio: 10–12
Barely audible: 3–4
```

### Troubleshooting

**Issue**: "Model not found" error
- Check checkpoint filename matches exactly
- Ensure models are in ComfyUI's `models/checkpoints/` folder

**Issue**: Out of VRAM
- Reduce width/height in `EmptyLTXVLatentVideo`
- Reduce steps in `LTXVScheduler`
- Use GGUF CLIP loaders (quantized, smaller)

**Issue**: Audio out of sync
- Check FPS is consistent (25 here)
- Ensure `LTXVConditioning` node has correct frame_rate input
- Try disabling `trim_to_audio` in `VideoCombine`

**Issue**: Low video quality
- Increase CRF (lower = better, but bigger file)
- Increase sampling steps
- Increase video CFG in Guider

### Example Prompts

**Cinematic Dialogue**:
```
A close-up interview shot of a woman in professional lighting,
speaking clearly about project insights. Shallow depth of field,
soft key light, neutral background. Clear, measured speech with
natural pauses. Duration: 4 seconds.
```

**Narrative Scene**:
```
Wide establishing shot: a coffee shop interior with warm amber
lighting, a person sitting at a table looking out the window.
Subtle dolly push inward. Minimal dialogue or ambient background
noise. Moody, introspective tone.
```

**Product Demo**:
```
Product unboxing shot: hands carefully removing a tech gadget
from packaging. Clean white background, bright overhead lighting.
Clear close-ups of details. Narration explains features. Upbeat,
professional tone. Duration: 6 seconds.
```

---

**Tip**: Combine PromptForgeLD's LLM generation with these workflows for end-to-end cinematic AI video production. The node handles prompt refinement; the workflow handles rendering.
