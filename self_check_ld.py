# -*- coding: utf-8 -*-
"""
self_check_ld.py — optional post-draft QA pass (before the box commits)

Toggle OFF by default. When ON, the model re-reads its own script against a
checklist of questions (user-selected chips + auto context chips) and either:
  • report — emit pass/fail notes only (script unchanged)
  • fix    — rewrite once to fix FAILs, then re-scrub

Smart layer (automatic):
  • Parse USER INTENT into concrete beats (bullets, dash lists, spoken lines, music cues)
  • Lexically scan the draft for each beat (HIT / MISS) and feed that to the QA model
  • Duration/pacing: compare beat-count + section density to write length

Never runs on silent stream mid-tokens — only after first finalize.
"""
from __future__ import annotations

import json
import re
from typing import Iterable

# Chip id → question the model must answer pass/fail
CHECK_CATALOG: dict[str, dict] = {
    "intent_beats": {
        "label": "Intent beats",
        "q": "Does the script actually perform every concrete beat extracted from the user's intent?",
    },
    "pacing": {
        "label": "Pacing / density",
        "q": "Does the script density fit the clip length — not too sparse, not cramming impossible action stacks?",
    },
    "i2v_lock": {
        "label": "I2V lock",
        "q": "I2V: first line is the start-image anchor; wardrobe/hair/place match the start image; no invented location jump?",
    },
    "talk_floor": {
        "label": "Enough talk",
        "q": "Is there enough quoted spoken dialogue for the dialogue tier (talkative = many short lines with emotion brackets; standard = a few real lines)?",
    },
    "silent_ok": {
        "label": "Silent clean",
        "q": "Silent tier: ZERO quoted speech and no 'says/murmurs/whispers' speech frames?",
    },
    "pov_clean": {
        "label": "POV clean",
        "q": "POV mode: viewpoint is hands/view/sound only — no I/me/my body prose outside dialogue quotes?",
    },
    "body_unit": {
        "label": "Body unit",
        "q": "Head and torso reorient together; no neck-only head turns; rises use body units?",
    },
    "hard_triggers": {
        "label": "LoRA triggers",
        "q": "Any HARD LoRA trigger tokens from the user appear at least once (exact spelling, not spoken as 'LoRA triggers:')?",
    },
    "camera_alive": {
        "label": "Camera hunts",
        "q": "Camera reframes across sections (new angle / close-up / push) — not one frozen medium shot?",
    },
    "no_meta": {
        "label": "No meta speech",
        "q": "No dialogue about cuts, cameras, scenes, clips, or the prompt itself?",
    },
    "sections": {
        "label": "Sections",
        "q": "Blank-line sections with one clear action beat each — not a wall of text?",
    },
    "gravure_voice": {
        "label": "Gravure voice",
        "q": "Gravure: accented mixed-English Asian L2 voice (not flat native English); soft breathy short lines?",
    },
    "music_plant": {
        "label": "Music plant",
        "q": (
            "Music preset is ON: does the FIRST body section (identity/pose open, after any I2V anchor) "
            "name the track already playing (genre/bass/kick/pulse/under the room)? "
            "Is the score re-touched mid-clip and later (not only once near the end)? "
            "If Background/quiet mode: soft continuous score + normal speech — no 'shouted over the music' / loud-room blast prose?"
        ),
    },
    "dance_tease": {
        "label": "Dance / tease",
        "q": (
            "Intent asks for dance and/or tease choreography: do named body mechanisms land "
            "(hip rolls, steps, isolations, fabric peels, gestures) across sections — not a static pose with vibe words? "
            "If music is also on: at least some motion lands with the pulse without turning every line into dance spam?"
        ),
    },
    "sing_vocal": {
        "label": "Singing",
        "q": (
            "Intent asks for singing/song/karaoke/vocals: does the script use sings/croons/sings along "
            "(or clear hums) with short complete lyric phrases — not only says(…) talk lines? "
            "Mouth free for lyrics; no fake phonetic spelling; not one token sing then all dialogue?"
        ),
    },
}

# UI default chips when user hasn't customized
DEFAULT_CHIPS = ["intent_beats", "talk_floor", "body_unit", "sections", "no_meta"]

# ── Smart intent beat extraction ─────────────────────────────────────────────

# Stop fluff that is not a checkable action
_BEAT_STOP = re.compile(
    r"^(?:please|thanks|thank you|make it|write|generate|continue|scene|clip|"
    r"around\s+\d+\s*sec(?:ond)?s?|for\s+\d+\s*sec(?:ond)?s?|"
    r"\d+\s*s(?:ec(?:ond)?s?)?)$",
    re.I,
)

# Synonym bags so "cum on her face" hits "semen" / "jets" / "face"
_BEAT_SYNONYMS: list[tuple[re.Pattern, tuple[str, ...]]] = [
    (re.compile(r"\b(?:suck|sucks|sucking|blowjob|bj|deepthroat|deep.?throat)\b", re.I),
     ("suck", "mouth", "cock", "shaft", "throat", "oral", "lips")),
    (re.compile(r"\b(?:gag|gagging|gagged)\b", re.I),
     ("gag", "gluk", "chok", "throat", "wet")),
    (re.compile(r"\b(?:cum|come)\b.*\b(?:face|facial)\b|\bfacial\b|\bcum\s+on\b", re.I),
     ("cum", "semen", "jet", "splash", "face", "lips", "shot")),
    (re.compile(r"\b(?:guide|push|pull|force).{0,20}\bhead\b|\bhead\b.{0,20}\b(?:down|guide|hands?)\b", re.I),
     ("hand", "grip", "head", "guide", "press", "pull")),
    (re.compile(r"\b(?:look\s+around|looking\s+around|glance|look\s+back|looking\s+back)\b", re.I),
     ("look", "pan", "glance", "around", "back", "view", "rotat")),
    (re.compile(r"\b(?:reggae|radio|music|singing|singer|r&b|edm|techno|bass|soundtrack)\b", re.I),
     ("reggae", "radio", "music", "bass", "sing", "melody", "pulse", "score", "track")),
    (re.compile(r"\b(?:undress|strip|take\s+off|pull\s+off|remove).{0,30}\b", re.I),
     ("pull", "strip", "dress", "bra", "shirt", "fabric", "off")),
    (re.compile(r"\b(?:dance|twerk|grind|hip\s+roll|booty)\b", re.I),
     ("hip", "dance", "step", "roll", "grind", "twerk", "sway")),
]


def _normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def extract_intent_beats(intent: str, *, max_beats: int = 12) -> list[str]:
    """Pull concrete checkable beats from free-form user intent.

    Handles dash/bullet lists, short clauses, quoted speech targets, and
    inline action stacks. Filters pure timing fluff.
    """
    raw = (intent or "").strip()
    if not raw:
        return []

    # Split on newlines, bullets, em/en dashes used as list markers, semicolons
    chunks: list[str] = []
    for line in re.split(r"[\n\r]+", raw):
        line = line.strip()
        if not line:
            continue
        # " - beat" / "• beat" / numbered
        parts = re.split(r"\s*[-–—•·▪]\s+|\s*;\s+|\s*\d+[.)]\s+", line)
        for p in parts:
            p = _normalize_space(p).strip(" .,-")
            if p:
                chunks.append(p)

    # Also split long "and then" chains if we still have only 1 fat chunk
    if len(chunks) <= 2:
        expanded = []
        for c in chunks:
            bits = re.split(r"\s*(?:,\s*then\b|\.\s+|,\s*and\s+then\b|\s+then\s+)\s*", c, flags=re.I)
            if len(bits) > 1:
                expanded.extend(_normalize_space(b) for b in bits if _normalize_space(b))
            else:
                expanded.append(c)
        chunks = expanded

    beats: list[str] = []
    seen: set[str] = set()
    for c in chunks:
        if len(c) < 6 or len(c) > 180:
            continue
        if _BEAT_STOP.match(c):
            continue
        # Pure duration cue alone
        if re.fullmatch(r"(?:around|about|for)?\s*\d+\s*(?:s|sec|secs|second|seconds)\b.*", c, re.I):
            # Keep if it also names speech/action after the time
            if not re.search(r"\b(?:say|says|speak|tell|cum|come|look|guide|music)\b", c, re.I):
                continue
        key = c.lower()
        # de-dupe near-identical
        if key in seen:
            continue
        seen.add(key)
        beats.append(c)
        if len(beats) >= max_beats:
            break

    # Pull quoted target lines as beats if not already covered
    for m in re.finditer(r'["\u201c]([^"\u201d]{3,80})["\u201d]', raw):
        q = _normalize_space(m.group(1))
        if q.lower() not in seen and len(beats) < max_beats:
            seen.add(q.lower())
            beats.append(f'say: "{q}"')

    return beats


def _beat_tokens(beat: str) -> list[str]:
    """Content tokens from a beat (drop tiny function words)."""
    stop = {
        "a", "an", "the", "my", "her", "his", "their", "she", "he", "i", "me", "im",
        "i'm", "as", "on", "in", "at", "to", "of", "and", "or", "with", "from",
        "for", "then", "briefly", "quietly", "around", "that", "this", "it", "is",
        "are", "be", "been", "was", "were", "do", "does", "did", "making", "make",
    }
    words = re.findall(r"[a-z0-9']+", (beat or "").lower())
    return [w for w in words if len(w) > 2 and w not in stop]


def scan_beat_in_script(beat: str, script: str) -> tuple[bool, str]:
    """Cheap lexical engagement check. Returns (hit, how)."""
    blob = (script or "").lower()
    if not beat or not blob:
        return False, "empty"

    # Quoted speech target
    qm = re.search(r'say:\s*["\'](.+?)["\']', beat, re.I)
    if qm:
        frag = qm.group(1).lower().strip()
        # require ~half the content words
        toks = _beat_tokens(frag)
        if toks:
            hits = sum(1 for t in toks if t in blob)
            if hits >= max(1, (len(toks) + 1) // 2):
                return True, "speech"
        if frag[:12] in blob or frag in blob:
            return True, "speech"

    # Synonym bags
    for rx, syns in _BEAT_SYNONYMS:
        if rx.search(beat):
            if sum(1 for s in syns if s in blob) >= 2:
                return True, "synonym"

    toks = _beat_tokens(beat)
    if not toks:
        return False, "no-tokens"
    hits = [t for t in toks if t in blob]
    # Need majority of distinctive tokens, or 2+ strong content hits
    need = 1 if len(toks) == 1 else max(2, (len(toks) + 1) // 2)
    if len(hits) >= need:
        return True, "tokens:" + ",".join(hits[:5])
    # Soft: two multi-char stems
    if len(hits) >= 2:
        return True, "partial:" + ",".join(hits[:5])
    return False, "miss"


def scan_intent_beats(intent: str, script: str) -> dict:
    """Extract beats + HIT/MISS vs draft. Used to make QA concrete."""
    beats = extract_intent_beats(intent)
    rows = []
    for b in beats:
        hit, how = scan_beat_in_script(b, script)
        rows.append({"beat": b, "hit": hit, "how": how})
    hits = sum(1 for r in rows if r["hit"])
    return {
        "beats": rows,
        "total": len(rows),
        "hits": hits,
        "misses": len(rows) - hits,
        "miss_list": [r["beat"] for r in rows if not r["hit"]],
    }


def pacing_assessment(
    *,
    duration_s: float = 12.0,
    intent: str = "",
    script: str = "",
    beat_count: int | None = None,
) -> dict:
    """Rough density vs time — advisory for the QA model (not a hard clock)."""
    try:
        dur = max(2.0, float(duration_s or 12.0))
    except (TypeError, ValueError):
        dur = 12.0
    if beat_count is None:
        beat_count = len(extract_intent_beats(intent))
    sections = [p for p in re.split(r"\n\s*\n", (script or "").strip()) if p.strip()]
    # drop pure I2V anchor
    if sections and re.search(r"use the provided start image", sections[0], re.I):
        sections = sections[1:]
    n_sec = len(sections)
    quotes = len(re.findall(r'["\u201c][^"\u201d]+["\u201d]', script or ""))
    chars = len((script or "").strip())

    # Heuristics: ~1.2–2.0s per action section; ~3–6 intent beats per 10s is fine
    sec_lo = max(2, int(dur / 2.2))
    sec_hi = max(sec_lo + 1, int(dur / 1.0) + 2)
    beat_hi = max(4, int(dur * 0.7) + 2)  # too many named beats for the clock
    char_lo = int(dur * 18)
    char_hi = int(dur * 95)

    flags = []
    if beat_count >= beat_hi:
        flags.append(
            f"INTENT HEAVY: ~{beat_count} named beats for ~{dur:.0f}s — risk of rushed cram; "
            "keep every beat but shorten each section (1 mechanism each)."
        )
    if n_sec and n_sec < sec_lo and chars < char_lo:
        flags.append(
            f"SPARSE: only ~{n_sec} action sections / {chars} chars for ~{dur:.0f}s — under-written."
        )
    if n_sec > sec_hi or chars > char_hi:
        flags.append(
            f"DENSE: ~{n_sec} sections / {chars} chars for ~{dur:.0f}s — may overcrowd; "
            "merge only if redundant, never drop intent beats."
        )
    if beat_count >= 5 and n_sec and n_sec < beat_count:
        flags.append(
            f"BEAT vs SECTIONS: {beat_count} intent beats but only {n_sec} sections — "
            "some beats may be fused or missing; prefer one beat per section when possible."
        )

    verdict = "ok"
    if any(f.startswith("SPARSE") for f in flags):
        verdict = "sparse"
    elif any(f.startswith("INTENT HEAVY") or f.startswith("DENSE") for f in flags):
        verdict = "tight"
    elif flags:
        verdict = "watch"

    return {
        "duration_s": dur,
        "beat_count": beat_count,
        "sections": n_sec,
        "quotes": quotes,
        "chars": chars,
        "flags": flags,
        "verdict": verdict,
        "guide": (
            f"Write-length ~{dur:.0f}s → aim roughly {sec_lo}–{sec_hi} action sections; "
            f"each intent beat should appear as visible mechanism or spoken line."
        ),
    }


def parse_chip_list(raw) -> list[str]:
    """Accept list, JSON string, or comma-separated ids."""
    if raw is None:
        return list(DEFAULT_CHIPS)
    if isinstance(raw, (list, tuple)):
        ids = [str(x).strip() for x in raw if str(x).strip()]
    else:
        s = str(raw).strip()
        if not s:
            return list(DEFAULT_CHIPS)
        if s.startswith("["):
            try:
                arr = json.loads(s)
                ids = [str(x).strip() for x in arr if str(x).strip()]
            except Exception:
                ids = [p.strip() for p in s.split(",") if p.strip()]
        else:
            ids = [p.strip() for p in re.split(r"[,|;]+", s) if p.strip()]
    out, seen = [], set()
    for i in ids:
        if i in CHECK_CATALOG and i not in seen:
            seen.add(i)
            out.append(i)
    return out or list(DEFAULT_CHIPS)


def auto_chips(
    *,
    mode: str = "t2v",
    dialogue_tier: str = "standard",
    pov: bool = False,
    video_style: str = "",
    lora_triggers: str = "",
    music_key: str = "",
    intent: str = "",
    scenario: str = "",
    duration_s: float | None = None,
    base: Iterable[str] | None = None,
) -> list[str]:
    """Merge user chips with context-required questions.

    Always forces intent_beats (smart keyword pass). Pacing auto when duration known
    or intent is beat-heavy.
    """
    chips = list(base) if base is not None else list(DEFAULT_CHIPS)
    seen = set(chips)
    def add(cid: str):
        if cid in CHECK_CATALOG and cid not in seen:
            chips.append(cid)
            seen.add(cid)

    # Smart core — always on when self-check runs
    add("intent_beats")
    # Put intent_beats first so the model grades story before style nits
    if "intent_beats" in chips:
        chips = ["intent_beats"] + [c for c in chips if c != "intent_beats"]

    if (mode or "").lower() == "i2v":
        add("i2v_lock")
    tier = (dialogue_tier or "standard").lower()
    if tier in ("none", "silent", "off"):
        add("silent_ok")
        # talk_floor is wrong for silent
        chips = [c for c in chips if c != "talk_floor"]
        seen.discard("talk_floor")
    elif tier in ("talkative", "chatty", "dense", "rich"):
        add("talk_floor")
    if pov:
        add("pov_clean")
    if lora_triggers and str(lora_triggers).strip():
        add("hard_triggers")
    vs = (video_style or "").lower()
    if "gravure" in vs:
        add("camera_alive")
        add("gravure_voice")
    # Music preset selected (not None / empty)
    mk = (music_key or "").strip()
    if mk and not re.match(r"^none\b", mk, re.I):
        add("music_plant")
    # Intent-named music even if dropdown is None
    if re.search(
        r"\b(?:music|reggae|radio|soundtrack|edm|techno|r&b|hip-?hop|bass playing|"
        r"song plays|singing quietly)\b",
        intent or "",
        re.I,
    ):
        add("music_plant")
    # Dance / tease choreography from intent or scenario keywords
    try:
        from .dance_ld import is_active as dance_active
    except ImportError:
        try:
            from dance_ld import is_active as dance_active
        except ImportError:
            dance_active = None
    if dance_active and dance_active(intent or "", scenario or ""):
        add("dance_tease")
    # Singing / vocal performance from intent keywords
    try:
        from .sing_ld import wants_sing as sing_wants
    except ImportError:
        try:
            from sing_ld import wants_sing as sing_wants
        except ImportError:
            sing_wants = None
    if sing_wants and sing_wants(intent or "", scenario or "", video_style=video_style or ""):
        add("sing_vocal")

    # Pacing: auto when we know duration, or intent is dense with beats
    n_beats = len(extract_intent_beats(intent or ""))
    try:
        dur = float(duration_s) if duration_s is not None else None
    except (TypeError, ValueError):
        dur = None
    if dur is not None or n_beats >= 4:
        add("pacing")
    return chips


def _truthy(v, default=False) -> bool:
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() not in ("0", "false", "off", "no", "")


def is_self_check_on(body: dict) -> bool:
    return _truthy(body.get("self_check", body.get("selfcheck")), default=False)


def self_check_mode(body: dict) -> str:
    m = str(body.get("self_check_mode") or body.get("selfcheck_mode") or "fix").lower().strip()
    return "report" if m in ("report", "report_only", "qa", "check") else "fix"


def resolve_chips(body: dict, **ctx) -> list[str]:
    base = parse_chip_list(body.get("self_check_chips") or body.get("selfcheck_chips"))
    dur = ctx.get("duration_s")
    if dur is None:
        dur = body.get("duration_s") or body.get("duration")
    return auto_chips(
        mode=ctx.get("mode") or body.get("video_mode") or "t2v",
        dialogue_tier=ctx.get("dialogue_tier") or body.get("dialogue_tier") or "standard",
        pov=bool(ctx.get("pov") if ctx.get("pov") is not None else body.get("pov")),
        video_style=ctx.get("video_style") or body.get("video_style") or body.get("style") or "",
        lora_triggers=ctx.get("lora_triggers") or body.get("lora_triggers") or "",
        music_key=ctx.get("music_key") if ctx.get("music_key") is not None else (body.get("music") or ""),
        intent=ctx.get("intent") if ctx.get("intent") is not None else (body.get("intent") or ""),
        scenario=ctx.get("scenario") if ctx.get("scenario") is not None else (body.get("scenario") or ""),
        duration_s=dur,
        base=base,
    )


def _music_question(*, music_key: str = "", music_background: bool = False) -> str:
    """Context-aware music checklist line."""
    mk = (music_key or "").strip() or "selected preset"
    if music_background:
        return (
            f"Music BACKGROUND/quiet is ON ({mk}): FIRST body section after any I2V anchor must include "
            "identity/pose AND a soft score plant (faint/low/under the room) in that same open; "
            "re-touch the quiet pulse mid-clip and late. FAIL if music first appears mid/late only. "
            "FAIL if dialogue is 'shouted over the music/bass' or the track is described as loud/room-shaking."
        )
    return (
        f"Music IN THE MIX is ON ({mk}): FIRST body section after any I2V anchor must include "
        "identity/pose AND the track already playing (kick/bass/groove) in that same open; "
        "re-mention pulse/bass mid-clip and later. FAIL if music is missing from the open or only appears once at the end. "
        "Track must stay continuous under speech (talk/shout over OK in loud mix)."
    )


def _dance_question(*, intent: str = "", scenario: str = "", music_on: bool = False) -> str:
    base = (
        "Intent/scenario asks for dance and/or tease choreography: the script must show concrete "
        "body mechanisms across multiple sections (steps, hip rolls, isolations, fabric peels, "
        "named tease gestures) — not a frozen pose + vibe words. FAIL if choreography is only implied."
    )
    if music_on:
        base += (
            " Music is also on: land at least some motion with the pulse/bass without making every section a dance essay."
        )
    return base


def _intent_beats_question(scan: dict) -> str:
    if not scan.get("total"):
        return (
            "Re-read USER INTENT for every named action, prop, place, music cue, and spoken line. "
            "FAIL if any concrete ask is missing from the draft (not just vibe)."
        )
    lines = [
        "AUTO-EXTRACTED intent beats — each must be engaged in the draft (visible mechanism or spoken line):",
    ]
    for r in scan.get("beats") or []:
        mark = "HIT?" if r.get("hit") else "MISS?"
        lines.append(f"  • [{mark}] {r.get('beat')}")
    if scan.get("miss_list"):
        lines.append(
            f"Lexical pre-scan found {scan['misses']} possible MISS(es). "
            "Confirm each; FAIL intent_beats if any real beat is absent. Fix by writing the missing beat, do not invent new plot."
        )
    else:
        lines.append(
            "Lexical pre-scan thinks all beats appear — still FAIL if a beat is only vaguely implied, not performed."
        )
    return " ".join(lines) if len(lines) == 1 else "\n".join(lines)


def _pacing_question(pace: dict) -> str:
    bits = [
        pace.get("guide") or "Match section density to clip length.",
        f"Draft stats: ~{pace.get('sections', 0)} sections, {pace.get('chars', 0)} chars, "
        f"{pace.get('quotes', 0)} quoted lines, {pace.get('beat_count', 0)} intent beats, "
        f"~{pace.get('duration_s', 12):.0f}s write-length.",
    ]
    for f in pace.get("flags") or []:
        bits.append(f"FLAG: {f}")
    if pace.get("verdict") == "sparse":
        bits.append("Likely FAIL if the draft is thin — add missing intent beats / fill time with mechanism, not fluff.")
    elif pace.get("verdict") == "tight":
        bits.append(
            "Tight clock: PASS only if every intent beat is present without impossible simultaneous stacks; "
            "shorten prose, keep beats."
        )
    else:
        bits.append("PASS if density feels filmable for the duration and no intent beat is dropped.")
    return " ".join(bits)


def build_self_check_messages(
    *,
    script: str,
    intent: str,
    chips: list[str],
    mode: str = "t2v",
    dialogue_tier: str = "standard",
    pov: bool = False,
    lora_triggers: str = "",
    fix: bool = True,
    music_key: str = "",
    music_background: bool = False,
    scenario: str = "",
    duration_s: float | None = None,
) -> list[dict]:
    """Build a short system+user for the QA pass (not the full brain doctrine)."""
    mk = (music_key or "").strip()
    music_on = bool(mk) and not re.match(r"^none\b", mk, re.I)
    scan = scan_intent_beats(intent or "", script or "")
    try:
        dur = float(duration_s) if duration_s is not None else 12.0
    except (TypeError, ValueError):
        dur = 12.0
    pace = pacing_assessment(
        duration_s=dur, intent=intent or "", script=script or "",
        beat_count=scan.get("total"),
    )

    questions = []
    for i, cid in enumerate(chips, 1):
        meta = CHECK_CATALOG.get(cid)
        if not meta:
            continue
        if cid == "music_plant":
            q = _music_question(music_key=mk, music_background=bool(music_background))
        elif cid == "dance_tease":
            q = _dance_question(intent=intent, scenario=scenario, music_on=music_on)
        elif cid == "intent_beats":
            q = _intent_beats_question(scan)
        elif cid == "pacing":
            q = _pacing_question(pace)
        else:
            q = meta["q"]
        questions.append(f"{i}. [{cid}] {q}")

    q_block = "\n".join(questions) if questions else "1. [intent_beats] Does the script match the intent?"

    system = (
        "You are a ruthless LTX shot-script QA editor. "
        "Read the DRAFT script and answer ONLY the checklist questions.\n"
        "Rules:\n"
        "• INTENT IS LAW: the AUTO-EXTRACTED beat list is your primary checklist — every beat must be engaged.\n"
        "• Be concrete — cite what's missing (e.g. 'no look-around beat', 'cum line missing', 'music missing from open').\n"
        "• Do NOT invent praise. FAIL when unsure.\n"
        "• Keep I2V honesty, head+torso units, blank-line sections if you rewrite.\n"
        "• Never add meta speech about cameras/cuts/clips inside dialogue.\n"
        "• Never dump 'LoRA triggers:' as prose.\n"
        "• Music FAIL fixes: plant score in the identity open + light through-line; honour Background vs in-the-mix.\n"
        "• Dance/tease FAIL fixes: add real mechanism choreography beats (not vibe adjectives).\n"
        "• Pacing: never drop intent beats to 'fit time' — compress wording; if intent is heavy, short sharp sections.\n"
        "• Lexical HIT/MISS is a hint only — a HIT can still FAIL if the action is wrong; a MISS should almost always FAIL.\n"
    )
    if fix:
        system += (
            "OUTPUT FORMAT (exact):\n"
            "1) One line per checklist item: PASS|FAIL|SKIP · id · short reason\n"
            "2) A line with only: ---SCRIPT---\n"
            "3) The FULL revised shot script (all sections). "
            "If everything PASSed, repeat the draft unchanged after ---SCRIPT---.\n"
            "Fix every FAIL. Do not shrink the script into a summary.\n"
        )
    else:
        system += (
            "OUTPUT FORMAT (exact):\n"
            "One line per checklist item: PASS|FAIL|SKIP · id · short reason\n"
            "Do NOT rewrite the script. No ---SCRIPT--- block.\n"
        )

    music_line = "(none)"
    if music_on:
        music_line = f"{mk} · {'BACKGROUND quiet' if music_background else 'IN THE MIX'}"
    # Intent-only music still noted
    elif re.search(r"\b(?:music|reggae|radio|soundtrack)\b", intent or "", re.I):
        music_line = "named in INTENT (no Music dropdown preset)"

    beat_block = "(no structured beats extracted — grade freeform intent carefully)"
    if scan.get("beats"):
        beat_lines = []
        for r in scan["beats"]:
            tag = "HIT" if r["hit"] else "MISS"
            beat_lines.append(f"  [{tag}] {r['beat']}")
        beat_block = "\n".join(beat_lines)

    pace_block = pace.get("guide", "")
    if pace.get("flags"):
        pace_block += "\n" + "\n".join(f"  ! {f}" for f in pace["flags"])

    user = (
        f"MODE: {mode} · DIALOGUE TIER: {dialogue_tier} · POV: {bool(pov)}\n"
        f"WRITE-LENGTH: ~{dur:.0f}s · PACING: {pace.get('verdict', 'ok')}\n"
        f"MUSIC: {music_line}\n"
        f"LORA TRIGGERS: {(lora_triggers or '').strip() or '(none)'}\n\n"
        f"USER INTENT:\n{(intent or '').strip()}\n\n"
        f"AUTO BEAT SCAN ({scan.get('hits', 0)}/{scan.get('total', 0)} lexical hits):\n"
        f"{beat_block}\n\n"
        f"PACING NOTES:\n{pace_block}\n\n"
        f"CHECKLIST:\n{q_block}\n\n"
        f"DRAFT SCRIPT:\n{(script or '').strip()}\n"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


_LINE_RE = re.compile(
    r"^\s*(PASS|FAIL|SKIP)\s*[·|:.\-–—]\s*([a-z0-9_]+)\s*[·|:.\-–—]?\s*(.*)$",
    re.I,
)


def parse_self_check_response(text: str, *, fix: bool = True) -> dict:
    """Parse model QA response into verdicts + optional revised script."""
    raw = (text or "").strip()
    script_part = ""
    report_part = raw
    if fix and "---SCRIPT---" in raw:
        report_part, script_part = raw.split("---SCRIPT---", 1)
        script_part = script_part.strip()
        # drop markdown fences if model wraps
        script_part = re.sub(r"^```\w*\s*", "", script_part)
        script_part = re.sub(r"\s*```\s*$", "", script_part).strip()

    verdicts = []
    fails = []
    for line in report_part.splitlines():
        m = _LINE_RE.match(line.strip())
        if not m:
            continue
        status = m.group(1).upper()
        cid = m.group(2).lower()
        reason = (m.group(3) or "").strip()
        row = {"id": cid, "status": status, "reason": reason}
        verdicts.append(row)
        if status == "FAIL":
            fails.append(row)

    summary = ", ".join(
        f"{v['id']}:{v['status']}" + (f"({v['reason'][:40]})" if v.get("reason") and v["status"] == "FAIL" else "")
        for v in verdicts
    ) or "no structured verdicts"

    return {
        "verdicts": verdicts,
        "fails": fails,
        "fail_count": len(fails),
        "pass_count": sum(1 for v in verdicts if v["status"] == "PASS"),
        "summary": summary,
        "revised": script_part,
        "raw": raw,
    }


def format_status(result: dict, *, fixed: bool, elapsed_s: float | None = None) -> str:
    n_fail = result.get("fail_count") or 0
    n_pass = result.get("pass_count") or 0
    bits = [f"Self-check {n_pass} pass / {n_fail} fail"]
    if fixed and n_fail:
        bits.append("fixed → committed")
    elif fixed and not n_fail:
        bits.append("clean")
    elif not fixed:
        bits.append("report only")
    if elapsed_s is not None:
        bits.append(f"+{elapsed_s:.1f}s")
    # first fail reason for glance
    fails = result.get("fails") or []
    if fails:
        f0 = fails[0]
        bits.append(f"{f0.get('id')}: {(f0.get('reason') or 'fail')[:48]}")
    return " · ".join(bits)


def catalog_for_ui() -> list[dict]:
    """Chip metadata for the settings panel / optional API."""
    return [
        {"id": cid, "label": meta["label"], "q": meta["q"]}
        for cid, meta in CHECK_CATALOG.items()
    ]
