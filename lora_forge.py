"""
LoraForge LD — LTX 2.3 LoRA controller with audio/visual split.
Ported from Loradaddyloaderltx-main and restyled to match PromptForgeLD.
"""

import os
import json
import folder_paths
import comfy.utils
import comfy.lora

try:
    from comfy.lora import load_lora_for_models as _load_lora
except (ImportError, AttributeError):
    from comfy.sd import load_lora_for_models as _load_lora

NUM_SLOTS = 10

def _is_audio_key(k):
    return "audio" in k.lower()

def _apply_slot(model, clip, lora_name, lora_str, vs, as_):
    lora_path = folder_paths.get_full_path("loras", lora_name)
    if not lora_path or not os.path.isfile(lora_path):
        print(f"[LoraForgeLD] LoRA not found: {lora_name}")
        return model, clip

    weights = comfy.utils.load_torch_file(lora_path, safe_load=True)

    video_weights = {k: v for k, v in weights.items() if not _is_audio_key(k)}
    audio_weights = {k: v for k, v in weights.items() if _is_audio_key(k)}

    v_final = lora_str * vs
    a_final = lora_str * as_

    print(f"[LoraForgeLD] '{lora_name}' V:{len(video_weights)}@{v_final:.2f}  A:{len(audio_weights)}@{a_final:.2f}")

    if video_weights and v_final != 0.0:
        model, clip = _load_lora(model, clip, video_weights, v_final, v_final)
    if audio_weights and a_final != 0.0:
        model, clip = _load_lora(model, clip, audio_weights, a_final, a_final)

    return model, clip


class LoraForgeLD:
    """✦ LoraForge LD — 10-slot LTX 2.3 LoRA controller (video/audio split)."""

    @classmethod
    def INPUT_TYPES(s):
        lora_list = ["None"] + folder_paths.get_filename_list("loras")
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "stack_data": ("STRING", {"default": "[]", "multiline": False}),
            },
            "hidden": {"available_loras": (lora_list,)}
        }

    # Outputs: model + clip only. (No trigger_words / loaded_keys_info — experiments removed.)
    RETURN_TYPES = ("MODEL", "CLIP")
    RETURN_NAMES = ("model", "clip")
    FUNCTION = "apply_stack"
    CATEGORY = "LD/PromptForge"

    def apply_stack(self, model, clip, stack_data, available_loras=None):
        m, c = model, clip
        try:
            data = json.loads(stack_data or "[]")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"[LoraForgeLD] bad stack_data: {e}")
            return (m, c)
        if not isinstance(data, list):
            return (m, c)
        for row in data:
            if not row.get("on") or row.get("lora") in ("None", "", None):
                continue
            lora_str = float(row.get("str", 1.0))
            vs = float(row.get("vs", 1.0))
            as_ = float(row.get("as", 1.0))
            m, c = _apply_slot(m, c, row["lora"], lora_str, vs, as_)
        return (m, c)


NODE_CLASS_MAPPINGS = {"LoraForgeLD": LoraForgeLD}
NODE_DISPLAY_NAME_MAPPINGS = {"LoraForgeLD": "✦ LoraForge LD"}
