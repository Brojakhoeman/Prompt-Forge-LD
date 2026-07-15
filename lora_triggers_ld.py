# -*- coding: utf-8 -*-
"""
LoRA trigger tokens for PromptForge LD.

Users paste activation keywords (e.g. grwth, sks person) separate from free intent.
We:
  1) teach the LLM to keep short activation tokens visible in the shot script
  2) guarantee missing SHORT tokens are injected into the final positive
  3) long English phrases are treated as soft guidance, not hard tags
     (so "her height increases…" does not get appended as "LoRA triggers: …")
"""

from __future__ import annotations

import re


def _norm_match(s: str) -> str:
    """Lowercase + strip most punctuation for containment checks."""
    s = (s or "").lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parse_triggers(raw) -> list[str]:
    """Split a free-form trigger field into unique tokens (order preserved)."""
    if raw is None:
        return []
    s = str(raw).strip()
    if not s:
        return []
    # Split on commas, semicolons, pipes, newlines — keep multi-word phrases
    parts = re.split(r"[,;|\n]+", s)
    out, seen = [], set()
    for p in parts:
        t = re.sub(r"\s+", " ", p).strip()
        t = re.sub(r"^(?:trigger|lora|kw|keyword)s?\s*[:=]\s*", "", t, flags=re.I).strip()
        # trim trailing sentence punctuation
        t = t.strip(" .;:!?")
        if not t or len(t) > 80:
            continue
        key = t.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(t)
    return out[:24]


# English quality / lighting phrases users paste as "triggers" — soft only.
# (Old bug: 2-word English like "detailed skin" was treated HARD and force-woven.)
_SOFT_AESTHETIC = re.compile(
    r"^(?:"
    r"detailed(?:\s+skin)?|cinematic(?:\s+lighting)?|beautiful(?:\s+detailed)?|"
    r"high(?:\s+quality)?|soft(?:\s+(?:lighting|focus|skin))?|natural(?:\s+light(?:ing)?)?|"
    r"dramatic(?:\s+lighting)?|volumetric(?:\s+lighting)?|ambient(?:\s+light(?:ing)?)?|"
    r"studio(?:\s+lighting)?|film(?:\s+grain)?|depth(?:\s+of\s+field)?|"
    r"8k|4k|masterpiece|best\s+quality|ultra\s+detailed|raw\s+photo|"
    r"skin\s+texture|realistic\s+skin|sharp\s+focus"
    r")$",
    re.I,
)

# Multi-word activation prefixes that stay hard (ohwx woman, sks person, …)
_HARD_MULTI_PREFIX = frozenset({
    "sks", "ohwx", "nzl", "emb", "lora", "trigger", "tok", "pt",
})


def is_hard_trigger(token: str) -> bool:
    """Short activation tags only (not full instruction sentences).

    Examples hard: grwth, sks, ohwx woman, giantess_v2
    Soft (doctrine only): "her height increases…", "detailed skin", "cinematic lighting"
    """
    t = (token or "").strip()
    if not t:
        return False
    words = t.split()
    if len(t) > 48 or len(words) > 3:
        return False
    # Pure aesthetic English → never hard-append
    if _SOFT_AESTHETIC.match(t):
        return False
    # Underscore / slash / versioned LoRA names → hard
    if re.search(r"[_\d/\\]", t):
        return True
    # One token — always hard (including weird spellings like grwth)
    if len(words) == 1:
        return True
    # Clause / instruction English → soft
    if re.search(
        r"\b(?:increases?|becomes?|grows?|turns?|gets?|makes?|should|must|will|into)\b",
        t,
        re.I,
    ):
        return False
    # Known multi-word activation ("ohwx woman") → hard
    if words[0].lower() in _HARD_MULTI_PREFIX:
        return True
    # Two+ plain dictionary-looking English words (lighting, skin, …) → soft
    if len(words) >= 2 and all(re.fullmatch(r"[A-Za-z][A-Za-z\-']*", w) for w in words):
        # Rare short code-like first token without vowels can still be hard
        w0 = words[0].lower()
        if len(w0) <= 5 and not re.search(r"[aeiou]", w0):
            return True
        return False
    # Three short words max, no clause verbs — possible multi-word tag
    if len(words) <= 3 and len(t) <= 40:
        return True
    return False


def hard_triggers(raw) -> list[str]:
    return [t for t in parse_triggers(raw) if is_hard_trigger(t)]


def soft_phrases(raw) -> list[str]:
    return [t for t in parse_triggers(raw) if not is_hard_trigger(t)]


def triggers_present(token: str, script: str) -> bool:
    """True if token (or punctuation-insensitive form) already appears in script."""
    if not token:
        return True
    n = _norm_match(token)
    if not n:
        return True
    body = _norm_match(script)
    if n in body:
        return True
    # single weird token: also allow as whole word
    if " " not in n and re.search(r"(?<![a-z0-9])" + re.escape(n) + r"(?![a-z0-9])", body):
        return True
    return False


def triggers_block(raw) -> str:
    """System doctrine when triggers are set (empty string if none)."""
    hard = hard_triggers(raw)
    soft = soft_phrases(raw)
    if not hard and not soft:
        return ""

    parts = [
        "\n━━ LORA / ACTIVATION TOKENS ━━\n",
    ]
    if hard:
        listed = ", ".join(f'"{t}"' for t in hard)
        parts.append(
            f"HARD TRIGGERS (exact strings — must appear in the script at least once): {listed}.\n"
            "  • Keep spelling exact. Do not expand or 'correct' them into normal English.\n"
            "  • Prefer early in the first action section; may repeat later if useful.\n"
            "  • Weave as tags next to the subject if needed — not as spoken dialogue unless intent asks.\n"
        )
    if soft:
        listed = "; ".join(soft)
        parts.append(
            f"SOFT GROWTH / EFFECT / QUALITY PHRASES (meaning, not tags): {listed}.\n"
            "  • Describe this effect in natural mechanism language — do NOT paste the phrase as a LoRA tag line.\n"
            "  • Never write meta prompt-speak like 'detailed skin' or 'cinematic lighting' as labels — "
            "show light/skin in concrete visible terms (sheen, window light, pores only if Detailer on).\n"
            "  • Do not invent extra random LoRA tags beyond the HARD list.\n"
        )
    if hard:
        parts.append("Missing any HARD trigger token is a failure for this generate.\n")
    return "".join(parts)


def ensure_triggers_in_script(script: str, raw) -> str:
    """Append only missing HARD trigger tokens so the pack positive still activates LoRAs.

    Soft English phrases are never force-appended (avoids 'LoRA triggers: her height…').
    """
    hard = hard_triggers(raw)
    if not hard:
        return script or ""
    s = script or ""
    missing = [t for t in hard if not triggers_present(t, s)]
    if not missing:
        return s
    line = "LoRA triggers: " + ", ".join(missing) + "."
    s = s.rstrip()
    if s:
        return s + "\n\n" + line + "\n"
    return line + "\n"
