# -*- coding: utf-8 -*-
"""
intent_traits_ld.py — carry user intent body/age keywords into the identity open.

Problem: T2V accent look-seeds open as "A Japanese woman with long black hair…"
and soft intent cues (petite, small breasts, age) get ignored in section 1 even
though intent is in the user message.

Fix:
  • Extract body/build/breast/height tags from intent
  • Age: honour user age if named; else seed-pick 19–28 (looks different than plain "woman")
  • Emit a short CHARACTER FACTS block + a ready OPEN LIKE string for T2V
  • I2V: only enforce tags the user named (never invent age/build vs the still)
"""
from __future__ import annotations

import random
import re

# Auto age band when user does not specify (inclusive)
AGE_LO, AGE_HI = 19, 28

# Ordered (priority) body/build extractors — (regex, canonical phrase)
_BODY_PATTERNS: list[tuple[re.Pattern, str]] = [
    # breasts / chest
    (re.compile(r"\b(?:very\s+)?small\s+(?:breasts?|boobs?|tits?|chest)\b", re.I), "small breasts"),
    (re.compile(r"\b(?:tiny|petite)\s+(?:breasts?|boobs?|tits?|chest)\b", re.I), "small breasts"),
    (re.compile(r"\bflat\s+chest\b", re.I), "flat chest"),
    (re.compile(r"\b(?:large|big|huge|heavy)\s+(?:breasts?|boobs?|tits?|chest)\b", re.I), "large breasts"),
    (re.compile(r"\bfull\s+(?:breasts?|chest)\b", re.I), "full breasts"),
    # overall build
    (re.compile(r"\bpetite\b", re.I), "petite"),
    (re.compile(r"\b(?:slim|slender|willowy)\b", re.I), "slim"),
    (re.compile(r"\b(?:skinny|thin)\b", re.I), "slim"),
    (re.compile(r"\b(?:athletic|toned|fit)\b", re.I), "athletic"),
    (re.compile(r"\b(?:curvy|voluptuous|hourglass)\b", re.I), "curvy"),
    (re.compile(r"\b(?:chubby|soft\s+body|plush)\b", re.I), "soft plush body"),
    (re.compile(r"\b(?:muscular|ripped)\b", re.I), "muscular"),
    (re.compile(r"\btall\b", re.I), "tall"),
    (re.compile(r"\bshort\b(?!\s+hair)", re.I), "short stature"),
    # hair colour/length if named (intent wins over seed look)
    (re.compile(r"\b(?:long|short|shoulder[- ]length)\s+(?:black|dark|brown|blonde|red|pink|silver|white)\s+hair\b", re.I), None),  # capture full
    (re.compile(r"\b(?:black|dark|brown|blonde|red|pink)\s+hair\b", re.I), None),
    # wardrobe hints that belong in open if named early
    (re.compile(r"\b(?:lingerie|lace\s+bra|bralette|silk\s+panties|sheer|thigh[- ]highs|stockings)\b", re.I), None),
]

_AGE_PATTERNS = [
    re.compile(r"\b(\d{1,2})\s*(?:years?\s*old|yo|y/o|yr\.?\s*old)\b", re.I),
    re.compile(r"\bage[d\s:]*(\d{1,2})\b", re.I),
    re.compile(r"\b(\d{1,2})\s*yr\b", re.I),
]


def extract_age(intent: str) -> int | None:
    """User-named age if present and plausible."""
    blob = intent or ""
    for rx in _AGE_PATTERNS:
        m = rx.search(blob)
        if not m:
            continue
        try:
            n = int(m.group(1))
        except (TypeError, ValueError):
            continue
        if 18 <= n <= 80:
            return n
    # word ages (light)
    words = {
        "eighteen": 18, "nineteen": 19, "twenty": 20, "twenty one": 21,
        "twenty two": 22, "twenty three": 23, "twenty four": 24,
        "twenty five": 25, "twenty six": 26, "twenty seven": 27,
        "twenty eight": 28, "twenty nine": 29, "thirty": 30,
    }
    low = blob.lower()
    for w, n in words.items():
        if re.search(rf"\b{re.escape(w)}\s*(?:years?\s*old|yo)?\b", low):
            return n
    return None


def pick_age(intent: str = "", seed: int = 0, *, auto: bool = True) -> tuple[int | None, str]:
    """
    Returns (age_or_None, source).
    source: 'intent' | 'seed' | 'none'
    """
    named = extract_age(intent)
    if named is not None:
        return named, "intent"
    if not auto:
        return None, "none"
    rng = random.Random(int(seed or 0) ^ 0xA6E)
    return rng.randint(AGE_LO, AGE_HI), "seed"


def extract_body_traits(intent: str) -> list[str]:
    """Canonical body/look phrases found in intent (order preserved, de-duped)."""
    blob = intent or ""
    out, seen = [], set()
    for rx, canon in _BODY_PATTERNS:
        m = rx.search(blob)
        if not m:
            continue
        phrase = (canon if canon is not None else m.group(0).strip().lower())
        phrase = re.sub(r"\s+", " ", phrase).strip()
        if not phrase or phrase in seen:
            continue
        # skip bare "short" if clearly "short hair"
        if phrase == "short stature" and re.search(r"\bshort\s+hair\b", blob, re.I):
            continue
        seen.add(phrase)
        out.append(phrase)
    return out[:12]


def extract_action_keywords(intent: str) -> list[str]:
    """Light action tags that should survive into choreography (not identity)."""
    blob = (intent or "").lower()
    tags = []
    pairs = [
        (r"\bstrip\s*tease\b|\bslow\s+strip\b", "slow strip tease"),
        (r"\bdirty\s+talk\b|\btalks?\s+dirty\b", "dirty talk"),
        (r"\bteas(?:e|es|ing)\b", "tease"),
        (r"\bgrwth\b|\bgrowth\b|\bgrows?\b", "growth"),
        (r"\bundress\b|\bstrips?\b", "undress"),
    ]
    for rx, lab in pairs:
        if re.search(rx, blob) and lab not in tags:
            tags.append(lab)
    return tags[:8]


def build_open_phrase(
    *,
    accent_adj: str = "",
    person: str = "woman",
    age: int | None = None,
    body_traits: list[str] | None = None,
    look_seed: str = "",
) -> str:
    """
    'A Japanese woman, 23, petite with small breasts, with long black hair…'
    """
    adj = (accent_adj or "").strip()
    person = (person or "woman").strip()
    art = "An" if (adj[:1].lower() in "aeiou" if adj else person[:1].lower() in "aeiou") else "A"
    core = f"{art} {adj} {person}".replace("  ", " ").strip() if adj else f"{art} {person}"

    bits = []
    if age is not None:
        bits.append(f"{int(age)}")
    traits = list(body_traits or [])
    # Prefer build traits before generic look seed
    build = [t for t in traits if t in (
        "petite", "slim", "athletic", "curvy", "soft plush body", "muscular",
        "tall", "short stature",
    )]
    chest = [t for t in traits if "breast" in t or "chest" in t]
    other = [t for t in traits if t not in build and t not in chest]

    body_bit = ""
    if build or chest:
        parts = []
        if build:
            parts.append(" ".join(build[:2]))
        if chest:
            parts.append(" with " + " and ".join(chest[:2]) if not build else ", " + " and ".join(chest[:2]))
        body_bit = "".join(parts).strip(" ,")
        # "petite with small breasts"
        if build and chest:
            body_bit = f"{' '.join(build[:2])} with {' and '.join(chest[:2])}"
        elif build:
            body_bit = " ".join(build[:2])
        elif chest:
            body_bit = " and ".join(chest[:2])

    hair_ward = [t for t in other if "hair" in t or any(
        w in t for w in ("lingerie", "bralette", "panties", "lace", "sheer", "stockings", "bra")
    )]

    # Assemble
    # A Japanese woman, 23, petite with small breasts, with long black hair, in lace lingerie
    mid = []
    if age is not None:
        mid.append(str(int(age)))
    if body_bit:
        mid.append(body_bit)

    if mid:
        open_ = f"{core}, " + ", ".join(mid)
    else:
        open_ = core

    if look_seed and not any(
        k in (look_seed or "").lower() for k in ("petite", "small breast", "large breast", "athletic", "curvy")
    ):
        # keep seed hair/skin if intent didn't already name hair
        if not any("hair" in t for t in traits):
            open_ += f", with {look_seed}"
        else:
            # intent hair wins — still allow non-hair portion of seed lightly skipped
            open_ += f", with {look_seed}"
    elif look_seed and not body_bit:
        open_ += f" with {look_seed}"

    if hair_ward:
        # wardrobe / hair from intent
        for t in hair_ward[:2]:
            if t not in open_.lower():
                if any(w in t for w in ("lingerie", "bralette", "panties", "lace", "sheer", "bra", "stockings")):
                    open_ += f", in {t}"
                else:
                    open_ += f", {t}"

    return open_


def traits_block(
    intent: str = "",
    *,
    seed: int = 0,
    mode: str = "t2v",
    lead_gender: str = "auto",
    accent_key: str = "",
    look_seed: str = "",
) -> str:
    """System doctrine: character facts that MUST land in the first identity section."""
    mode = (mode or "t2v").lower()
    is_i2v = mode == "i2v"
    age, age_src = pick_age(intent, seed, auto=not is_i2v)
    # I2V: only use age if user named it
    if is_i2v and age_src != "intent":
        age, age_src = None, "none"

    body = extract_body_traits(intent)
    actions = extract_action_keywords(intent)

    if is_i2v and not body and age is None and not actions:
        return ""  # nothing to force

    try:
        from .accents_ld import identity_label, _person_noun
    except ImportError:
        from accents_ld import identity_label, _person_noun

    adj = identity_label(accent_key) if accent_key else ""
    person = _person_noun(lead_gender, role="lead")
    open_like = build_open_phrase(
        accent_adj=adj, person=person, age=age, body_traits=body, look_seed=look_seed or "",
    )

    lines = [
        "\n━━ CHARACTER FACTS — INTENT FIRST, SEED FILLS GAPS ━━",
        "User intent is law. These facts MUST appear in the FIRST identity section as physical description",
        "(not only later dialogue). Accent look-seeds and auto-age only fill what intent left blank.",
    ]
    if age is not None:
        if age_src == "intent":
            lines.append(
                f"  • AGE: {age} (USER NAMED — do not change) — write \"{age}\" or \"{age}-year-old\" in the open."
            )
        else:
            lines.append(
                f"  • AGE: {age} (gap-fill only — seed in {AGE_LO}–{AGE_HI}; intent named no age)."
            )
            lines.append(
                "    Numbered age reads different than plain \"a woman\". Never invent an age that fights intent."
            )
    if body:
        lines.append("  • BODY / BUILD from USER INTENT (must appear in open — not optional seasoning):")
        lines.append("    " + " · ".join(body))
    if actions:
        lines.append("  • ACTION PATH from USER INTENT (choreography must hit these): " + " · ".join(actions))
    if is_i2v:
        lines.append(
            "  • I2V: start image wins on face/hair. Only force age/body tags the USER named;"
            " never invent a conflicting ethnicity or wardrobe."
        )
    else:
        lines.append(f"  • ★ OPEN LIKE (intent baked in; seed only where blank): \"{open_like} stands…\"")
        lines.append(
            "  • BAD: drop intent body tags for a generic accent look-seed "
            "(\"A woman with long black hair…\" when intent said petite + small breasts)."
        )
    lines.append(
        "  • Later sections do not re-list full identity — but the open must lock intent facts once."
    )
    lines.append("")
    return "\n".join(lines)


def traits_remember_line(intent: str = "", *, seed: int = 0, mode: str = "t2v") -> str:
    """One-liner for the user REMEMBER checklist."""
    age, src = pick_age(intent, seed, auto=(mode or "t2v").lower() != "i2v")
    if (mode or "").lower() == "i2v" and src != "intent":
        age = None
    body = extract_body_traits(intent)
    bits = []
    if age is not None:
        bits.append(f"age {age}")
    if body:
        bits.append(", ".join(body[:4]))
    if not bits:
        return ""
    return "• CHARACTER OPEN must include: " + " · ".join(bits) + " (from intent/seed — not only dialogue)."
