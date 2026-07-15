"""
PromptForge LD — LTX 2.3 prompt node (overhaul).
UI owns the craft surface; this node commits pack outputs to the graph.
"""

from .api import register_routes, _scan_gguf, _models_dir, resolve_input_image
from .environments_ld import ENV_KEYS
from .scenarios_ld import SCENARIO_KEYS as SCN_KEYS
from .camera_ld import KEYS as CAM_KEYS
from .music_ld import MUSIC_KEYS
from .styles_ld import STYLE_KEYS
from .negatives import build as build_negative
from .intensity_ld import LEVELS, LEVEL_LABELS, coerce_level, level_to_energy
from .pack_ld import PFLD_PACK, make_pack, unpack
from .tensors import b64_to_tensor, load_path, make_black, resize

try:
    register_routes()
except Exception as _e:
    print(f"[PromptForgeLD] route registration skipped: {_e}")

# Comfy dropdown labels for qualitative intensity
_INTENSITY_CHOICES = [LEVEL_LABELS[k] for k in LEVELS]


class PromptForgeLD:
    """LTX 2.3 shot-writer — CANON brain, generous talkers, refine-ready."""

    @classmethod
    def INPUT_TYPES(cls):
        gguf, mmproj = _scan_gguf(_models_dir())
        d_gguf = gguf[1] if len(gguf) > 1 else "None"
        d_mm = mmproj[1] if len(mmproj) > 1 else "None (text-only)"
        return {
            "required": {
                "model_file": (gguf, {"default": d_gguf}),
                "mmproj_file": (mmproj, {"default": d_mm}),
                "video_mode": (["i2v", "t2v"], {"default": "i2v"}),
                "environment": (ENV_KEYS, {"default": ENV_KEYS[0]}),
                "scenario": (SCN_KEYS, {"default": SCN_KEYS[0]}),
                "camera_move": (CAM_KEYS, {"default": CAM_KEYS[0]}),
                "music": (MUSIC_KEYS, {"default": MUSIC_KEYS[0]}),
                "pov": ("BOOLEAN", {"default": False}),
                "pov_gender": (["female", "male"], {"default": "female"}),
                "dialogue_tier": (["none", "standard", "talkative"], {"default": "standard"}),
                # Legacy numeric kept for old workflows; UI drives qualitative fields
                "intensity": ("INT", {"default": 5, "min": 1, "max": 10}),
                "user_intent": ("STRING", {"multiline": True, "default": ""}),
                "confirmed_prompt": ("STRING", {"multiline": True, "default": ""}),
                "image_b64": ("STRING", {"default": ""}),
                "image_filename": ("STRING", {"default": ""}),
                "rm_w": ("INT", {"default": 1088, "min": 64, "max": 16384}),
                "rm_h": ("INT", {"default": 1920, "min": 64, "max": 16384}),
            },
            "optional": {
                "cast": (["solo", "pair", "group"], {"default": "pair"}),
                "lead_gender": (["auto", "female", "male", "neutral"], {"default": "auto"}),
                "video_style": (STYLE_KEYS, {"default": STYLE_KEYS[0]}),
                "accent_mode": ("STRING", {"default": "auto"}),
                "accent_partner": ("STRING", {"default": "off"}),
                "motion_level": (_INTENSITY_CHOICES, {"default": "Normal"}),
                "mouth_heat": (_INTENSITY_CHOICES, {"default": "Normal"}),
                "continuity_state": ("STRING", {"multiline": True, "default": ""}),
                "duration_s": ("FLOAT", {"default": 12.0, "min": 1.0, "max": 60.0, "step": 0.5, "forceInput": True}),
                "fps": ("INT", {"default": 24, "min": 8, "max": 60, "forceInput": True}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = (PFLD_PACK,)
    RETURN_NAMES = ("pack",)
    FUNCTION = "run"
    CATEGORY = "LD/PromptForge"
    OUTPUT_NODE = True

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        return True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def run(self, model_file, mmproj_file, video_mode, environment, scenario, camera_move, music, pov,
            pov_gender, dialogue_tier, intensity, user_intent,
            confirmed_prompt, image_b64, image_filename, rm_w, rm_h,
            cast="pair", lead_gender="auto", video_style=None, accent_mode="auto", accent_partner="off",
            motion_level="Normal", mouth_heat="Normal", continuity_state="",
            duration_s=None, fps=None, unique_id=None):
        out_w = max(64, int(rm_w or 1088))
        out_h = max(64, int(rm_h or 1920))

        # Only text committed in the UI (▶ Generate / Refine) reaches the positive pin.
        positive = (confirmed_prompt or "").strip()
        talkative = (dialogue_tier or "").lower() in ("talkative", "chatty", "dense", "rich")
        silent = (dialogue_tier or "").lower() in ("none", "silent", "off")
        m_lv = coerce_level(motion_level)
        h_lv = coerce_level(mouth_heat)
        wants_music = bool(music) and not str(music).startswith("None")

        negative = build_negative(
            pov=bool(pov),
            music=wants_music,
            talkative=talkative,
            silent=silent,
            intent=user_intent or "",
            scenario=str(scenario or ""),
            environment=str(environment or ""),
            music_key=str(music or ""),
            motion_level=m_lv,
            mouth_level=h_lv,
            dialogue_tier=dialogue_tier or "standard",
            cast=str(cast or "pair"),
            video_style=str(video_style or ""),
        )

        if video_mode == "i2v":
            t = load_path(resolve_input_image(image_filename) or "")
            if t is None and (image_b64 or "").strip():
                t = b64_to_tensor(image_b64)
            if t is None:
                raise ValueError("[PromptForgeLD] I2V requires an uploaded image.")
            image_out = resize(t, out_w, out_h)
        else:
            image_out = make_black(out_w, out_h)

        print(
            f"[PromptForgeLD] {video_mode.upper()} → {out_w}×{out_h} | "
            f"pov={pov} cast={cast} dlg={dialogue_tier} "
            f"body={LEVEL_LABELS[m_lv]} mouth={LEVEL_LABELS[h_lv]} music={wants_music} | "
            f"{len(positive)} chars pos / {len(negative)} chars neg"
        )
        return (make_pack(image_out, positive, negative, out_w, out_h),)


class PromptForgeLDUnpack:
    """Split the PFLD pack into image / positive / negative / width / height."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"pack": (PFLD_PACK,)}}

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "INT", "INT")
    RETURN_NAMES = ("image", "positive", "negative", "width", "height")
    FUNCTION = "run"
    CATEGORY = "LD/PromptForge"

    def run(self, pack):
        return unpack(pack)


NODE_CLASS_MAPPINGS = {
    "PromptForgeLD": PromptForgeLD,
    "PromptForgeLDUnpack": PromptForgeLDUnpack,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptForgeLD": "✦ PromptForge LD",
    "PromptForgeLDUnpack": "✦ PromptForge Unpack",
}
