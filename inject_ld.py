"""
inject_ld.py — scenario/environment picklists → SHORT nudge blocks.

Deliberately light for simple scenarios; SHOT RECIPES get full stakes + dialogue shape.
Presets bias setting and arrangement; the user's words lead.
Optional lead_gender rewrites she/he choreography so male-lead clips don't fight the banks.
"""

from __future__ import annotations

import re

try:
    from .scenarios_ld import resolve_scenario, scenario_is_explicit
    from .environments_ld import ENVIRONMENT_PRESETS, _ENV_RANDOM_POOL
except ImportError:
    from scenarios_ld import resolve_scenario, scenario_is_explicit
    from environments_ld import ENVIRONMENT_PRESETS, _ENV_RANDOM_POOL


def _seed_rng(seed=0):
    """Always deterministic for a given seed (including seed=0)."""
    import random
    try:
        s = int(seed) & 0x7FFFFFFF
    except (TypeError, ValueError):
        s = 0
    return random.Random(s)


def resolve_env_key(env_key, seed=0) -> str:
    """Return concrete environment key (RANDOM → picked). Empty/None sentinels unchanged."""
    k = (env_key or "").strip()
    if not k:
        return k
    val = ENVIRONMENT_PRESETS.get(k)
    if val == "RANDOM" or k in ("🎲 Random — seed picks", "RANDOM"):
        return _seed_rng(seed).choice(_ENV_RANDOM_POOL)
    return k


def _resolve_env(env_key, seed=0):
    concrete = resolve_env_key(env_key, seed)
    val = ENVIRONMENT_PRESETS.get(concrete) if concrete else None
    if val == "RANDOM":
        return None
    return val if isinstance(val, tuple) else None


def env_block(env_key, mode="t2v", seed=0):
    val = _resolve_env(env_key, seed)
    if not val:
        return ""
    loc = val[0] if len(val) > 0 else ""
    light = val[1] if len(val) > 1 else ""
    sound = val[2] if len(val) > 2 else ""
    if (mode or "").lower() == "i2v":
        return (
            "━━ ENVIRONMENT (I2V — nudge only) ━━\n"
            f"If it fits the frame, lean the light and mood toward: {loc}. "
            "Never contradict what the image already shows.\n"
        )
    return (
        "━━ ENVIRONMENT ━━\n"
        f"Setting: {loc}\n"
        f"Light: {light}\n"
        f"Sound bed: {sound}\n"
        "Place the action inside this location and let one visible detail of it show through the "
        "sections — the named light on skin, or a feature behind the subject. Don't let the setting "
        "replace the action.\n"
    )


def _rewrite_lead(text: str, lead_gender: str) -> str:
    """Best-effort she↔he rewrite for choreography banks."""
    g = (lead_gender or "auto").lower()
    if not text or g in ("", "auto", "none", "default", "female", "woman", "f"):
        return text
    if g in ("neutral", "they", "nb"):
        s = text
        s = re.sub(r"\bShe\b", "They", s)
        s = re.sub(r"\bshe\b", "they", s)
        s = re.sub(r"\bHer\b", "Their", s)
        s = re.sub(r"\bher\b", "their", s)
        s = re.sub(r"\bhers\b", "theirs", s)
        s = re.sub(r"\bHe\b", "They", s)
        s = re.sub(r"\bhe\b", "they", s)
        s = re.sub(r"\bHis\b", "Their", s)
        s = re.sub(r"\bhis\b", "their", s)
        s = re.sub(r"\bhim\b", "them", s)
        return s
    if g in ("male", "man", "m"):
        s = text
        s = re.sub(r"\bShe's\b", "He's", s)
        s = re.sub(r"\bshe's\b", "he's", s)
        s = re.sub(r"\bShe\b", "He", s)
        s = re.sub(r"\bshe\b", "he", s)
        s = re.sub(r"\bhers\b", "his", s)
        s = re.sub(r"\bHers\b", "His", s)
        s = re.sub(r"\bHer\b", "His", s)
        s = re.sub(
            r"\bher\b(?=\s+(?:dress|skirt|hair|hips|lips|eyes|hand|hands|body|"
            r"back|waist|chest|shoulders|legs|thighs|knees|feet|face|mouth|"
            r"bra|panties|jeans|shirt|top|jacket|weight|forearms?|arms?|fingers?))",
            "his",
            s,
            flags=re.I,
        )
        s = re.sub(r"\bher\b", "him", s)
        return s
    return text


def scenario_block(scn_key, seed=0, lead_gender="auto", mode=None):
    d = resolve_scenario(scn_key, seed=seed, mode=mode)
    if not d:
        return ""
    tag = (d.get("tag") or "SFW").upper()
    setup = _rewrite_lead(d.get("setup") or "", lead_gender)
    choreo = _rewrite_lead(d.get("choreography") or "", lead_gender)
    stakes = _rewrite_lead(d.get("stakes") or "", lead_gender)
    dlg_shape = d.get("dialogue_shape") or ""

    if tag == "RECIPE":
        block = (
            "━━ SHOT RECIPE — T2V DEEP PACK (mandatory structure) ━━\n"
            f"Setup: {setup}\n"
            f"Section plan / choreography:\n{choreo}\n"
        )
        if stakes:
            block += f"Stakes (name these in dialogue): {stakes}\n"
        if dlg_shape:
            block += f"Dialogue shape: {dlg_shape}\n"
        if d.get("cast_hint"):
            block += f"Cast hint from recipe: {d['cast_hint']} — still honour the node's cast control.\n"
        if d.get("motion"):
            block += f"Recipe motion lean: {d['motion']} (node body intensity still wins if set).\n"
        if d.get("mouth_heat"):
            block += f"Recipe mouth-heat lean: {d['mouth_heat']} (node mouth heat still wins if set).\n"
        block += (
            "Follow the section plan beat-for-beat. User intent outranks wardrobe/identity fluff, "
            "but stakes + section order are mandatory. Blank line between every section.\n"
        )
    else:
        block = (
            "━━ SCENARIO — the action of the clip ━━\n"
            f"Setup: {setup}\n"
            f"Choreography: {choreo}\n"
            "This is WHAT HAPPENS — the subject performs this. If an environment is also set, that's just "
            "WHERE it happens. The user's words still govern identity/look when they conflict with fluff, "
            "but the scenario's structure (including any JUMP CUT) is mandatory.\n"
        )

    if tag == "JUMP":
        block += (
            "━━ JUMP CUT (mandatory structure) ━━\n"
            "1) First 2–4 action sections = SETUP only (greeting / talk / light motion). "
            "Honour the start image in I2V for those sections. At least TWO spoken lines in setup "
            "if dialogue is not silent. Setup stays clothed/pose-true to the still.\n"
            "2) Then ONE dedicated HARD CUT section that OPENS with a clear state leap — "
            "start it with 'Hard cut.' then restate the NEW pose/act in mechanism language. "
            "Do NOT bleed undress steps across the cut.\n"
            "3) WARDROBE AFTER THE CUT (important — do not default to full nude):\n"
            "   • ORAL / BLOWJOB / kneeling head: KEEP clothes from setup/start image unless the "
            "user's intent clearly asks for naked/topless/stripped. Clothed blowjob is correct and preferred.\n"
            "   • FACE-SIT / oral-on-her: lower access only (skirt up, panties aside) — full nude only if intent asks.\n"
            "   • PENETRATIVE SEX (doggy, cowgirl, wall fuck, counter, mating press, etc.): "
            "naked or clothes shoved aside for real access — the cut may leap wardrobe here.\n"
            "   • STRIP / dance-to-topless / solo fingers: wardrobe change is the point of the cut.\n"
            "   Never invent full nudity on a blowjob jump just because it's explicit.\n"
            "4) All remaining sections stay in the post-cut reality until the end. "
            "If talkative and mouths are FREE post-cut: most remaining spoken lines land after the cut. "
            "If post-cut is oral/blowjob: giver = wet throat sounds only mid-act (≤1–2 words total free-mouth); "
            "POV/partner free mouths carry the talk — do NOT pack dialogue into bobbing sections.\n"
            "5) Layout: blank line between every section so the cut is obvious on the page.\n"
            "6) BANNED in spoken quotes: 'after the cut', 'this scene', 'hard cut', 'jump cut', "
            "'in this video' — characters only talk in-world. Prose MAY use 'Hard cut.' once to mark the leap.\n"
        )
    if tag in ("NSFW", "JUMP") or d.get("explicit"):
        block += (
            "Explicit: where the act requires it (especially AFTER any jump cut), name cock, pussy, "
            "ass, mouth, penetration plainly — coy phrasing renders nothing.\n"
        )
    if tag == "SFW":
        block += (
            "Motion: one action per section, continuous physical order, head+torso turn together. "
            "No teleporting within a section.\n"
        )
    if (mode or "").lower() == "i2v" and tag != "JUMP":
        block += (
            "I2V note: never fight the start image. If this scenario would restage the still, "
            "adapt the choreography to the pose already in the frame.\n"
        )
    return block


def scenario_forces_explicit(scn_key, seed=0, mode=None):
    """Picking an NSFW scenario turns the explicit gate on even if the typed prompt was tame."""
    try:
        return bool(scenario_is_explicit(scn_key, seed=seed, mode=mode))
    except Exception:
        return False
