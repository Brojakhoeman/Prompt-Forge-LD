"""
intensity_ld.py — Qualitative motion + mouth-heat bands (no magic numbers in the UI).

UI labels (same vocabulary for both axes):
  ASMR · Soft · Normal · Intense · Aggressive

Two independent axes:
  • motion / body  — how hard the physical performance goes
  • mouth_heat     — how filthy / loud / degraded speech gets (dialect heat)

Legacy numeric intensity 1–10 still coerces cleanly for old workflows.
"""

from __future__ import annotations

LEVELS = ("asmr", "soft", "normal", "intense", "aggressive")

# Human labels for chips / dropdowns
LEVEL_LABELS = {
    "asmr": "ASMR",
    "soft": "Soft",
    "normal": "Normal",
    "intense": "Intense",
    "aggressive": "Aggressive",
}

# Internal energy used by accent heat tiers + legacy code paths
_LEVEL_ENERGY = {
    "asmr": 2,
    "soft": 3,
    "normal": 5,
    "intense": 7,
    "aggressive": 10,
}

# Accept common aliases from UI / old saves
_ALIASES = {
    "as mr": "asmr",
    "a.s.m.r": "asmr",
    "whisper": "asmr",
    "gentle": "soft",
    "low": "soft",
    "calm": "soft",
    "medium": "normal",
    "mid": "normal",
    "default": "normal",
    "high": "intense",
    "hot": "intense",
    "hard": "aggressive",
    "filthy": "aggressive",
    "max": "aggressive",
    "extreme": "aggressive",
    "raw": "aggressive",
}


def coerce_level(value, default: str = "normal") -> str:
    """Any user/API value → one of LEVELS."""
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return energy_to_level(int(value))
    s = str(value).strip().lower()
    if s in LEVELS:
        return s
    if s in _ALIASES:
        return _ALIASES[s]
    # numeric string
    try:
        return energy_to_level(int(float(s)))
    except (TypeError, ValueError):
        pass
    # "ASMR" / "Soft" etc.
    for k, lab in LEVEL_LABELS.items():
        if s == lab.lower():
            return k
    return default


def energy_to_level(energy: int) -> str:
    e = max(1, min(10, int(energy or 5)))
    if e <= 2:
        return "asmr"
    if e <= 3:
        return "soft"
    if e <= 6:
        return "normal"
    if e <= 8:
        return "intense"
    return "aggressive"


def level_to_energy(level) -> int:
    return _LEVEL_ENERGY[coerce_level(level)]


def resolve_axes(
    *,
    motion=None,
    mouth_heat=None,
    intensity=None,
    energy=None,
) -> tuple[str, str, int, int]:
    """
    Returns (motion_level, mouth_level, motion_energy, mouth_energy).

    Priority:
      motion / mouth_heat labels if provided
      else shared intensity/energy (legacy single slider)
      else normal/normal
    """
    shared = None
    if motion is None and mouth_heat is None:
        if intensity is not None and intensity != "":
            shared = intensity
        elif energy is not None and energy != "":
            shared = energy

    if motion is None or motion == "":
        motion = shared if shared is not None else "normal"
    if mouth_heat is None or mouth_heat == "":
        mouth_heat = shared if shared is not None else motion

    m = coerce_level(motion)
    h = coerce_level(mouth_heat)
    return m, h, level_to_energy(m), level_to_energy(h)


def motion_block(level) -> str:
    lv = coerce_level(level)
    if lv == "asmr":
        body = (
            "MOTION: feather-light — fingertips drift, almost no weight transfer; "
            "long holds; one micro-motion settles before anything else begins. "
            "Never shove, slam, or stack hard impacts.\n"
            "ARC: stays low and hypnotic the whole clip.\n"
        )
        band = "ASMR"
    elif lv == "soft":
        body = (
            "MOTION: unhurried and light — hands settle, trace, guide; weight shifts slowly; "
            "clear pauses between moves.\n"
            "ARC: stays low — it breathes, it never spikes into force.\n"
        )
        band = "SOFT"
    elif lv == "intense":
        body = (
            "MOTION: forceful and driven — grips drag, bodies push and pin with real weight; "
            "motions stack and overlap; impact rhythm carries the clip. Stay render-safe: "
            "force from weight and speed words, never banned deform verbs.\n"
            "ARC: opens already moving, climbs, peak holds in the last third.\n"
        )
        band = "INTENSE"
    elif lv == "aggressive":
        body = (
            "MOTION: maximum force — pinning, driving rhythm, stacked motion; "
            "render-safe verbs only (no twists/writhes/snaps).\n"
            "ARC: high from the open; peak holds through the end.\n"
        )
        band = "AGGRESSIVE"
    else:  # normal
        body = (
            "MOTION: deliberate and grounded — hands grip, pull, press with real weight; "
            "each section adds one new motion; contact and breath stay synced.\n"
            "ARC: opens measured, builds section by section, arrives driven in the final third.\n"
        )
        band = "NORMAL"
    return f"\n━━ BODY INTENSITY: {band} ━━\n{body}"


def mouth_block(level, *, explicit: bool = False) -> str:
    """How people talk — independent of body force. Feeds dialect heat language."""
    lv = coerce_level(level)
    if lv == "asmr":
        heat = (
            "MOUTH HEAT asmr: close-mic whisper / breath; almost no volume; "
            "soft words only; no degradation; cursing rare or absent."
        )
        voice = (
            "VOICE: whispered, trailing, sibilant — brackets like (whispering) (breathy) "
            "(close to the mic). Long pauses between short phrases."
        )
        band = "ASMR"
    elif lv == "soft":
        heat = (
            "MOUTH HEAT soft: gentle intimate words; no degradation; "
            "soft / good / more / please / stay — never barked orders."
        )
        voice = (
            "VOICE: quiet — murmured, soft brackets; words close to the ear, never raised."
        )
        band = "SOFT"
    elif lv == "intense":
        heat = (
            "MOUTH HEAT intense: when explicit, filthy dirty talk is welcome — "
            "take it / filthy / slut / whore / fuckin' — still varied, still in character voice; "
            "when not explicit, heated urgent language without full porn vocabulary."
        )
        voice = (
            "VOICE: loud and raw — shouted, snarled, gasped, breathless brackets; "
            "short hard lines over the sound of contact."
        )
        band = "INTENSE"
    elif lv == "aggressive":
        heat = (
            "MOUTH HEAT aggressive: when explicit, MAX degradation + graphic sex talk; "
            "almost every line is raw; still variety — no same slur twice in a row; "
            "when not explicit, barked urgency without full porn vocab."
        )
        voice = (
            "VOICE: broken / barked / snarled; short hard lines; impact rhythm in the delivery."
        )
        band = "AGGRESSIVE"
    else:  # normal
        heat = (
            "MOUTH HEAT normal: natural conversational heat; "
            "fuck/more/harder when the scene is explicit; no heavy degradation unless asked."
        )
        voice = (
            "VOICE: full and engaged — steady, warm, heated brackets; conversational volume "
            "that can lean urgent as the clip builds."
        )
        band = "NORMAL"

    if not explicit and lv in ("intense", "aggressive"):
        heat += " Scene is NOT flagged explicit — keep heat in language/urgency, skip graphic anatomy spam."

    return (
        f"\n━━ MOUTH / DIALECT HEAT: {band} ━━\n"
        f"{voice}\n"
        f"{heat}\n"
        "Speech filth and volume track THIS band, not body intensity. "
        "A soft body can still talk filthy if mouth heat is high, and vice versa.\n"
    )


def combined_energy_block(motion_level, mouth_level, *, explicit: bool = False) -> str:
    return motion_block(motion_level) + mouth_block(mouth_level, explicit=explicit)


def level_options() -> list[str]:
    """UI option list in display order."""
    return [LEVEL_LABELS[k] for k in LEVELS]


def level_keys() -> list[str]:
    return list(LEVELS)
