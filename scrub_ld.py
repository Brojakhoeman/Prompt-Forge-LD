"""
scrub_ld.py — post-generation CANON enforcement.

The system prompt teaches the model. This module cleans residual slips from
weaker local models without rewriting the whole script. Conservative: only
known-bad tokens / patterns, never "creative rewrite".
"""

from __future__ import annotations

import re

# Teleport / deform verbs → render-safe substitutes (word-boundary, case-preserving)
_VERB_MAP = {
    r"\bsnaps?\b": "turns fast",
    r"\bsnapping\b": "turning fast",
    r"\bsuddenly\b": "",
    r"\binstantly\b": "",
    r"\ball at once\b": "in one continuous motion",
    r"\bjerks?\b": "pulls sharp",
    r"\bjerking\b": "pulling sharp",
    r"\bwhips?\b": "swings",
    r"\bwhipping\b": "swinging",
    r"\btwists?\b": "turns",
    r"\btwisting\b": "turning",
    r"\bcontorts?\b": "arches",
    r"\bcontorting\b": "arching",
    r"\bwrithes?\b": "shifts",
    r"\bwrithing\b": "shifting",
    r"\bconvulses?\b": "shudders",
    r"\bconvulsing\b": "shuddering",
    r"\bthrashes?\b": "pushes hard",
    r"\bthrashing\b": "pushing hard",
    r"\bspasms?\b": "trembles",
    r"\bspasming\b": "trembling",
    r"\bwrenches?\b": "pulls",
    r"\bwrenching\b": "pulling",
}

# Pure vibe adjectives/adverbs that paint nothing on LTX
_VIBE = re.compile(
    r"\b(?:beautifully|gorgeously|stunningly|perfectly|sensually|seductively|"
    r"teasingly|passionately|elegantly|alluringly|erotically|sexily)\b",
    re.I,
)

# Micro-detail spam that clogs LTX (outside quotes)
_MICRO = re.compile(
    r"\b(?:knuckles? whitening|hair strands?|thumb rims?|a small smile on (?:her|his|their) face|"
    r"shadow stretching across the ground)\b",
    re.I,
)

# Lone head-turn patterns → torso+head unit.
# Do NOT rewrite "look back over shoulder" when torso is already mentioned nearby
# (that produced doubled phrases in Gemma outputs).
_HEAD_ONLY = [
    (re.compile(r"\bturns? (?:her|his|their) head\b", re.I),
     "rotates torso and head together"),
    (re.compile(r"\bturning (?:her|his|their) head\b", re.I),
     "rotating torso and head together"),
    (re.compile(r"\btwists? (?:her|his|their) (?:head|neck)\b", re.I),
     "rotates torso and head together"),
    (re.compile(r"\bswivels? (?:her|his|their) (?:head|neck)\b", re.I),
     "rotates torso and head together"),
    (re.compile(r"\bcranes? (?:her|his|their) neck\b", re.I),
     "leans upper body and head together"),
    (re.compile(r"\bsnaps? (?:her|his|their) head\b", re.I),
     "turns upper body and head together fast"),
    (re.compile(r"\bwhips? (?:her|his|their) head\b", re.I),
     "turns upper body and head together fast"),
]


def _fix_rise_getup(s: str) -> str:
    """LTX fails stand-ups that only say 'rises to her feet' with no torso/head unit.

    Prefer adding a short unit clause rather than rewriting the whole beat.
    Skip if torso/shoulders/upper body already in the same sentence (before OR after the rise).
    Never rewrite non-person rises (steam rises, dust rises, sun rises).
    """
    def repl(m):
        full = m.group(0)
        # Non-person subjects: steam/dust/smoke/sun/fog/temperature — leave alone
        pre = s[max(0, m.start() - 48):m.start()].lower()
        if re.search(
            r"\b(?:steam|dust|smoke|mist|fog|vapor|sun|moon|heat|temperature|"
            r"chest|breath|voice|sound|music|camera|volume|tide|dough|bread|"
            r"level|number|price|stock|anger|tension)\s+$",
            pre,
        ) or re.search(
            r"\b(?:steam|dust|smoke|mist|fog|vapor|sun|moon)\s+$",
            pre,
        ):
            return full
        sent_start = max(s.rfind(".", 0, m.start()), s.rfind("\n", 0, m.start()), s.rfind("!", 0, m.start()), s.rfind("?", 0, m.start()))
        # End of sentence after the match — so trailing "torso and head moving…" is seen
        tail = s[m.end():]
        end_rel = len(tail)
        for sep in (".", "\n", "!", "?"):
            i = tail.find(sep)
            if i != -1:
                end_rel = min(end_rel, i)
        sent_end = m.end() + end_rel
        window = s[sent_start + 1:sent_end].lower()
        if any(w in window for w in (
            "torso", "shoulder", "upper body", "waist", "spine", "as one unit",
            "rising together", "moving upward together", "lifting together",
        )):
            return full
        return full.rstrip(".,; ") + ", torso and head rising together as one unit"

    # Person get-up only — require she/he/they OR explicit "to her/his feet"
    # (bare "rises" alone matched "Steam rises" and polluted ASMR scripts)
    s = re.sub(
        r"\b(?:(?:she|he|they)\s+rises?(?:\s+to\s+(?:her|his|their)\s+feet)?|"
        r"rises?\s+to\s+(?:her|his|their)\s+feet|"
        r"(?:she|he|they)\s+stands?\s+up|"
        r"stands?\s+up(?:\s+to\s+(?:her|his|their)\s+feet)?|"
        r"stands?\s+to\s+(?:her|his|their)\s+feet|"
        r"(?:she|he|they)\s+gets?\s+up(?:\s+to\s+(?:her|his|their)\s+feet)?|"
        r"gets?\s+up\s+to\s+(?:her|his|their)\s+feet)\b",
        repl,
        s,
        flags=re.I,
    )
    s = re.sub(
        r"(torso and head rising together as one unit)(?:,?\s*torso and head rising together as one unit)+",
        r"\1",
        s,
        flags=re.I,
    )
    return s


def _fix_lone_lookback(s: str) -> str:
    """Only expand look-back when the clause has no torso/shoulder unit already."""
    def repl(m):
        start = max(0, m.start() - 48)
        window = s[start:m.start()].lower()
        if "torso" in window or "shoulder" in window and "rotat" in window:
            return m.group(0)  # already correct enough
        return "rotates torso and head together to look back over the shoulder"
    return re.sub(
        r"\blooks? back over (?:her|his|their) shoulder\b",
        repl,
        s,
        flags=re.I,
    )


def _fix_facing_jump(s: str) -> str:
    """If earlier text is back/ass/crouch-to-camera and a later line teleports to
    'facing the view' without a turn/shoulders beat nearby, insert a turn clause.

    Gold LTX clips (gym strip) always had an explicit turn section before face-front.
    """
    low = s.lower()
    backish = bool(re.search(
        r"\b(?:back to (?:the )?(?:camera|view|lens)|ass (?:to|toward|towards) (?:the )?(?:camera|view|lens)|"
        r"facing away|kneels? on .{0,40}back|crouch(?:es|ing)? .{0,30}back|"
        r"hips? (?:toward|towards|to) (?:the )?(?:camera|lens|view))\b",
        low,
    ))
    if not backish:
        return s
    # Already has a proper reorient somewhere
    if re.search(
        r"\b(?:turns? (?:her|his|their) upper body|rotates? (?:her|his|their) (?:upper body|torso)|"
        r"turns? at the waist|shoulders following|pivot(?:s|ing)? (?:upper body|at the waist))\b",
        low,
    ):
        return s

    def repl(m):
        clause = m.group(0)
        # Don't double-fix
        if re.search(r"turn|rotat|shoulder|waist", clause, re.I):
            return clause
        return (
            "She turns at the waist to face the camera, upper body and head rotating together, "
            "shoulders following. " + clause
        )

    # Jump patterns: stands … facing / now faces / fully upright facing
    s2 = re.sub(
        r"\b(?:She|He|They)\s+(?:stands?\s+(?:fully\s+)?upright,?\s+facing|"
        r"stands?\s+tall,?\s+facing|"
        r"stands?,?\s+facing|"
        r"is\s+(?:now\s+)?facing|"
        r"now\s+faces?)\s+(?:the\s+)?(?:view|camera|lens)\b[^.!\n]*[.!]?",
        repl,
        s,
        count=1,
        flags=re.I,
    )
    return s2


def _fix_bra_waist_incomplete(s: str) -> str:
    """Prefer full top take-off path over stopping at the waist when undress is happening."""
    if not re.search(r"\b(?:bra|sports bra|top|crop top|shirt|blouse)\b", s, re.I):
        return s
    # Only when there's an undress pull-up nearby
    if not re.search(
        r"\b(?:pulls?|slides?|lifts?|grips?)\b.{0,80}\b(?:bra|top|hem|shirt)\b|"
        r"\b(?:bra|top|hem|shirt)\b.{0,80}\b(?:pulls?|slides?|lifts?)\b",
        s,
        re.I,
    ):
        return s
    s = re.sub(
        r"\blets? the (?:black |sports |white )?(?:bra|top|shirt) fall to (?:her |his )?waist\b[^.!\n]*",
        "lifts the garment over her head and lets it fall to the floor",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"\b(?:bra|top|shirt) (?:falls?|drops?) to (?:her |his )?waist\b",
        "garment clears her head and drops to the floor",
        s,
        flags=re.I,
    )
    # "fully naked" after only a top remove — soften when bottoms still implied
    if re.search(r"\b(?:briefs?|panties|jeans|skirt|leggings|shorts|trousers|pants)\b", s, re.I):
        s = re.sub(
            r"\bstands? fully naked\b",
            "stands with the top gone",
            s,
            flags=re.I,
        )
    return s

_I2V_ANCHOR = "Use the provided start image exactly as the first frame."

_POV_SELF = re.compile(
    r"\b(?:I |I'm |I've |I'd |me |my |myself |mine )\b",
)


def _apply_verb_map(s: str) -> str:
    out = s
    for pat, rep in _VERB_MAP.items():
        def _sub(m, r=rep):
            if not r:
                return ""
            g = m.group(0)
            if g[0].isupper():
                return r[:1].upper() + r[1:]
            return r
        out = re.sub(pat, _sub, out, flags=re.I)
    # collapse double spaces left by deletions
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r" +([,.;:])", r"\1", out)
    return out


def _scrub_star_adlibs(s: str) -> str:
    """Turn *stage-direction* markers into plain prose (LTX must not see markdown)."""
    def repl(m):
        inner = (m.group(1) or "").strip()
        if not inner:
            return ""
        # common bank forms
        low = inner.lower()
        table = {
            "soft hum": "she hums soft",
            "quiet laugh": "she laughs quiet",
            "giggle": "she giggles",
            "slow exhale": "she exhales slow",
            "sharp inhale": "she inhales sharp",
            "breath catches": "her breath catches",
            "shaky breath": "her breath shakes",
            "gasp": "she gasps",
            "sigh": "she sighs",
            "low hum": "a low hum",
            "bright hum": "a bright hum",
            "playful hum": "a playful hum",
            "content sigh": "she sighs",
            "quiet mmm": "she hums",
        }
        if low in table:
            return table[low]
        # generic: drop stars, keep words as a short breath note
        return inner
    s = re.sub(r"\*([^*]{1,40})\*", repl, s)
    return s


_ACTION_START = re.compile(
    r"^(?:"
    r"She|He|They|The view|A hand|Hands|Both hands|"
    r"Eye-level|Use the provided|"
    r"The (?:man|woman|view|crowd)|"
    r"A (?:woman|man|person|muscular)|An "
    r")\b",
    re.I,
)

# Next beat often starts with these (model frequently omits the period before them)
_ACTION_BOUNDARY = re.compile(
    r"(?<=[\"\u201d.!?])\s+(?="
    r"(?:She|He|They|The view|A hand|Hands|Both hands|Eye-level|Use the provided|"
    r"The (?:man|woman|view)|A (?:woman|man|person|muscular))"
    r"\b)",
    re.I,
)
# Missing punctuation: `"quote" She does` or `goes" The woman`
_QUOTE_THEN_ACTION = re.compile(
    r'(["\u201d])\s*(?=(?:She|He|They|The view|A hand|Hands|The (?:man|woman|view)|A (?:woman|man))\b)',
    re.I,
)


def _split_sentences(block: str) -> list:
    """Split a paragraph into sentences without breaking inside quotes."""
    block = (block or "").strip()
    if not block:
        return []
    out, buf, in_q = [], [], False
    i, n = 0, len(block)
    while i < n:
        ch = block[i]
        if ch in '"\u201c\u201d':
            in_q = not in_q
            buf.append(ch)
            i += 1
            continue
        buf.append(ch)
        if not in_q and ch in ".!?":
            nxt = block[i + 1] if i + 1 < n else ""
            if nxt == "" or nxt.isspace():
                sent = "".join(buf).strip()
                if sent:
                    out.append(sent)
                buf = []
                while i + 1 < n and block[i + 1].isspace():
                    i += 1
        i += 1
    tail = "".join(buf).strip()
    if tail:
        out.append(tail)
    return out


def _split_on_actions(block: str) -> list:
    """Split a long line on action-subject boundaries (She/He/The view/…)."""
    block = (block or "").strip()
    if not block:
        return []
    # Inject breaks where the model forgot a period after a quote/sentence
    t = _QUOTE_THEN_ACTION.sub(r"\1\n", block)
    t = _ACTION_BOUNDARY.sub("\n", t)
    parts = [p.strip() for p in t.split("\n") if p.strip()]
    if len(parts) <= 1:
        return _split_sentences(block) or [block]
    # Further sentence-split any still-huge chunk
    out = []
    for p in parts:
        if len(p) > 220:
            out.extend(_split_sentences(p) or [p])
        else:
            out.append(p)
    return out


def _ensure_section_breaks(s: str) -> str:
    """Restore old shot-script layout: one action beat per paragraph, blank line between.

    Critical: do NOT flatten existing newlines into spaces first — that was the
    bug. Streamed text often has good single-line breaks; final scrub used to
    destroy them, then fail to re-split when the model omitted periods.
    """
    s = (s or "").strip().replace("\r\n", "\n")
    if not s:
        return s

    # 1) Promote existing structure: blank lines + single newlines that start beats
    rough_lines = []
    for chunk in re.split(r"\n+", s):
        line = " ".join(chunk.split()).strip()  # tidy spaces inside a line only
        if line:
            rough_lines.append(line)

    # 2) Expand any line that still packs multiple actions
    sentences = []
    for line in rough_lines:
        multi = bool(_QUOTE_THEN_ACTION.search(line) or _ACTION_BOUNDARY.search(line))
        short_single = (
            len(line) < 160
            and not multi
            and line.count(". ") < 1
        )
        if short_single:
            sentences.append(line)
        else:
            sentences.extend(_split_on_actions(line))

    if not sentences:
        return s

    sections = []
    i = 0
    if re.search(r"use the provided start image", sentences[0], re.I):
        sections.append(sentences[0])
        i = 1
        if i < len(sentences) and re.match(r"^Eye-level\b", sentences[i], re.I):
            open_bits = [sentences[i]]
            i += 1
            if i < len(sentences) and re.match(
                r"^(?:A |An |The )?(?:woman|man|person|girl|guy|blonde|figure|muscular)\b",
                sentences[i], re.I,
            ):
                open_bits.append(sentences[i])
                i += 1
            sections.append(" ".join(open_bits))

    while i < len(sentences):
        sent = sentences[i]
        is_speech_only = bool(re.match(
            r"^(?:She|He|They)\s+(?:says|murmurs|whispers|shouts|yells|asks|answers|laughs|breathes|groans|moans|whimpers|gasps)\b",
            sent, re.I,
        )) and ('"' in sent or "\u201c" in sent)
        is_action = bool(_ACTION_START.match(sent)) or is_speech_only
        if sections and is_speech_only and '"' not in sections[-1] and "\u201c" not in sections[-1]:
            sections[-1] = sections[-1].rstrip() + " " + sent
        elif is_action or not sections:
            sections.append(sent)
        else:
            sections[-1] = sections[-1].rstrip() + " " + sent
        i += 1

    cleaned = []
    for sec in sections:
        sec = re.sub(r",\s*\.", ".", sec)
        sec = re.sub(r"\.\s*\.", ".", sec)
        sec = re.sub(r"[ \t]{2,}", " ", sec).strip()
        if sec:
            cleaned.append(sec)

    return "\n\n".join(cleaned)


_ORAL_OCCUPY_RE = re.compile(
    r"\b(?:bobs?|bobbing|sucks?|sucking|deepthroats?|deep-throats?|gags?|gagging|"
    r"mouths? (?:on|around|full of)|lips? (?:around|sealed on)|"
    r"takes? (?:him|it|the cock) (?:into|in) (?:her|his) mouth|"
    r"cock (?:in|into) (?:her|his) mouth|throat (?:full|stuffed)|"
    r"slurps?|slurping|glucks?|gluk)\b",
    re.I,
)
_FREE_MOUTH_BEAT_RE = re.compile(
    r"\b(?:pulls? off|pulls? (?:him|it) out|comes? up for air|comes? off|"
    r"breaks? (?:the )?kiss|lowers? (?:the )?(?:cup|glass|drink)|"
    r"takes? (?:a |her |his )?breath|mouth free|lets? (?:it|him|her) (?:go|out)|"
    r"releases? (?:him|it)|pops? off)\b",
    re.I,
)
_ONSCREEN_SPEECH_RE = re.compile(
    r"\b((?:she|he)\s+)"
    r"(says|murmurs|whispers|asks|adds|moans|gasps)\s*"
    r"(?:\([^)]*\))?\s*:\s*\"[^\"]*\"",
    re.I,
)
_POV_VOICE_SPEECH_RE = re.compile(
    r"\b(?:voice|from just behind|behind the view|unseen)\b",
    re.I,
)


def _scrub_occupied_mouth_talk(s: str) -> str:
    """Clear speech while mouth is busy — same-clause and same-section oral.

    Oral giver: no quoted lines mid-act without an explicit free-mouth beat.
    POV / off-screen voice lines are kept (receiver can talk during oral).
    """
    # Same clause: bobbing/sucking ... says "words" without pull-off between
    s = re.sub(
        r"\b((?:bobs?|bobbing|sucks?|sucking|deepthroats?|gags?|gagging|"
        r"mouths? (?:on|around|full of)|lips? (?:around|sealed on)|"
        r"slurps?|slurping)"
        r"[^.!\n]{0,100}?)\s+"
        r"((?:and\s+)?(?:she|he|they)\s+)?"
        r"(says|murmurs|whispers|asks|adds|moans|gasps)\s*(\([^)]*\))?\s*:\s*\"([^\"]*)\"",
        r"\1, wet throat sounds only — mouth still occupied.",
        s,
        flags=re.I,
    )
    # Same blank-line section: oral action + on-screen quoted speech, no free beat
    parts = re.split(r"(\n\n+)", s)
    out = []
    for part in parts:
        if part.startswith("\n") or not part.strip():
            out.append(part)
            continue
        if (
            _ORAL_OCCUPY_RE.search(part)
            and _ONSCREEN_SPEECH_RE.search(part)
            and not _FREE_MOUTH_BEAT_RE.search(part)
        ):
            def _drop_onscreen(m, _part=part):
                # Keep if this speech is clearly POV/unseen voice enrichment
                window = _part[max(0, m.start() - 80):m.start()]
                if _POV_VOICE_SPEECH_RE.search(window):
                    return m.group(0)
                return f"{m.group(1)}makes wet throat sounds only — mouth still full."
            part = _ONSCREEN_SPEECH_RE.sub(_drop_onscreen, part)
        out.append(part)
    # Scrub rewrites can glue into the next sentence — force a clean break
    s = "".join(out)
    s = re.sub(
        r"(mouth still (?:full|occupied))\.?\s*(?=[A-Z\"])",
        r"\1. ",
        s,
    )
    s = re.sub(
        r"(wet throat sounds only[^.!\n]{0,40})\s+(A low voice)",
        r"\1. \2",
        s,
        flags=re.I,
    )
    return s


def _scrub_false_pov_voice(s: str, *, pov: bool) -> str:
    """Strip densify-invented 'voice from just behind the view' when POV is off."""
    if pov:
        return s
    # Drop whole speech-act clauses that invent unseen POV receiver voice
    patterns = [
        r"(?:\.|,)?\s*A low voice from just behind the view says\s*"
        r"(?:\([^)]*\))?\s*:\s*\"[^\"]*\"\.?",
        r"(?:\.|,)?\s*(?:The voice|A voice) from just behind the view says\s*"
        r"(?:\([^)]*\))?\s*:\s*\"[^\"]*\"\.?",
        r"(?:\.|,)?\s*From just behind the view,?\s*a low voice says\s*"
        r"(?:\([^)]*\))?\s*:\s*\"[^\"]*\"\.?",
        r"(?:\.|,)?\s*From just behind the view,?\s*(?:a |the )?voice says\s*"
        r"(?:\([^)]*\))?\s*:\s*\"[^\"]*\"\.?",
    ]
    for pat in patterns:
        s = re.sub(pat, ".", s, flags=re.I)
    s = re.sub(r"\.\s*\.", ".", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    return s


_PULL_AIR_RE = re.compile(
    r"\b(?:pulls? off|pulls? (?:him|it|the cock) out|comes? up for air|comes? off|"
    r"pops? off|pulls? (?:her |his )?head back|gasps? for air|pulls? back|"
    r"string of saliva|saliva (?:thread|string)|for air|breath catching)\b",
    re.I,
)
_AFTERCARE_RE = re.compile(
    r"\b(?:water|glass of|towel|jaw|aftercare|wipes?|kisses? (?:her|his) forehead|"
    r"lies? (?:down|back)|cuddle|beside)\b",
    re.I,
)


def _scrub_oral_pull_off_wordiness(s: str) -> str:
    """Across an oral sequence, long on-screen pull-off speech → ≤2 words.

    Tracks oral state across blank-line sections so a pull-off section without
    the word 'suck' still gets micro-capped. Aftercare (water/jaw/towel) ends the
    sequence and allows real talk again.
    """
    parts = re.split(r"(\n\n+)", s)
    out = []
    in_oral_seq = False

    def _micro(m):
        who, verb, br, quote = m.group(1), m.group(2), m.group(3) or "", m.group(4)
        words = re.findall(r"[A-Za-z']+", quote)
        if len(words) <= 2:
            return m.group(0)
        # Prefer content words — avoid "it's so" / "cock is" fragments that LTX prints weird
        stop = {
            "i", "i'm", "im", "it's", "its", "the", "a", "an", "so", "this", "that",
            "you", "your", "oh", "uh", "um", "just", "really", "very",
            "is", "are", "was", "were", "be", "been", "am", "to", "of", "for", "my", "me",
        }
        content = [w for w in words if w.lower() not in stop]
        pick = content[:2] if content else words[:1]
        micro = " ".join(pick).lower()
        br_s = f" {br}" if br else ""
        return f'{who}{verb}{br_s}: "{micro}"'

    for part in parts:
        if part.startswith("\n") or not part.strip():
            out.append(part)
            continue
        if _ORAL_OCCUPY_RE.search(part):
            in_oral_seq = True
        elif in_oral_seq and _AFTERCARE_RE.search(part) and not _ORAL_OCCUPY_RE.search(part):
            in_oral_seq = False

        if in_oral_seq:
            # Cap long on-screen lines during oral sequence (mid-act or air pull)
            # Skip if clearly only partner/POV voice (no she/he says)
            part = re.sub(
                r"\b((?:she|he)\s+)"
                r"(says|murmurs|whispers|gasps|asks|adds)\s*"
                r"(\([^)]*\))?\s*:\s*\"([^\"]+)\"",
                _micro,
                part,
                flags=re.I,
            )
            # Also: "and says (x): \"long\"" forms without she/he repeated
            part = re.sub(
                r"\b(and\s+)(says|murmurs|whispers|gasps)\s*"
                r"(\([^)]*\))?\s*:\s*\"([^\"]+)\"",
                lambda m: (
                    m.group(0)
                    if len(re.findall(r"[A-Za-z']+", m.group(4))) <= 2
                    else f'{m.group(1)}{m.group(2)}{m.group(3) or ""}: '
                         f'"{" ".join(re.findall(r"[A-Za-z\']+", m.group(4))[:2]).lower()}"'
                ),
                part,
                flags=re.I,
            )
        out.append(part)
    return "".join(out)


def _fix_dialogue_caps(s: str) -> str:
    """Capitalize first letter in spoken quotes; add terminal punct if missing.

    Intent paste often leaks 'i only…' and models drop the closing period.
    """
    def repl(m):
        q = m.group(1)
        if not q:
            return m.group(0)
        for i, ch in enumerate(q):
            if ch.isalpha():
                if ch.islower():
                    q = q[:i] + ch.upper() + q[i + 1:]
                break
        # Ensure terminal . ! ? … (skip pure interjections already punctuated)
        stripped = q.rstrip()
        if stripped and stripped[-1] not in ".!?…\"'":
            # Don't add period to trailing ellipsis-ish or emoji-only
            if re.search(r"[A-Za-z0-9]$", stripped):
                q = stripped + "."
        return f'"{q}"'

    # ASCII double quotes (primary LTX form)
    s = re.sub(r'"([^"]*)"', repl, s)
    return s


# Soft-trigger / SD-tag paste that models still dump as prose labels
_META_QUALITY = [
    (re.compile(r"\bCinematic lighting\b", re.I), "Light"),
    (re.compile(r"\bDetailed skin\b", re.I), "Her skin"),
    (re.compile(r"\bRealistic skin\b", re.I), "Skin"),
    (re.compile(r"\bSkin texture\b", re.I), "Skin"),
    (re.compile(r"\bUltra detailed\b", re.I), ""),
    (re.compile(r"\bHigh quality\b", re.I), ""),
    (re.compile(r"\bBest quality\b", re.I), ""),
    (re.compile(r"\bMasterpiece\b", re.I), ""),
    (re.compile(r"\bSharp focus\b", re.I), ""),
    (re.compile(r"\bRaw photo\b", re.I), ""),
    (re.compile(r"\bVolumetric lighting\b", re.I), "Volumetric light"),
    (re.compile(r"\bStudio lighting\b", re.I), "Studio light"),
    (re.compile(r"\bDramatic lighting\b", re.I), "Dramatic light"),
    (re.compile(r"\bSoft lighting\b", re.I), "Soft light"),
    (re.compile(r"\bNatural lighting\b", re.I), "Natural light"),
    (re.compile(r"\bFilm grain\b", re.I), "grain"),
]


def _scrub_meta_quality_tags(s: str) -> str:
    """Rewrite SD/quality tag paste outside dialogue quotes (soft LoRA field leftovers)."""
    parts = re.split(r'("[^"]*")', s)
    for i, part in enumerate(parts):
        if part.startswith('"') and part.endswith('"'):
            continue
        for rx, rep in _META_QUALITY:
            part = rx.sub(rep, part)
        # tidy double spaces after empty replacements
        part = re.sub(r"[ \t]{2,}", " ", part)
        part = re.sub(r" \.", ".", part)
        parts[i] = part
    return "".join(parts)


def _fix_quote_terminal_punct(s: str) -> str:
    """Move sentence period inside closing quote when model wrote: \"line\". → \"line.\""""
    s = re.sub(r'"([^"\n]{1,200}?)"\s*\.', r'"\1."', s)
    return s


def _scrub_speech_verb_glitches(s: str) -> str:
    """Fix double speech-verb artifacts: 'saying says (warm)' from bare-bracket inject."""
    s = re.sub(
        r"\b(saying|sayin'?)(\s+)says\b",
        r"\1",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"\b(murmuring|whispering|asking|adding|growling|moaning|gasping|"
        r"snarling|breathing)(\s+)(?:says|murmurs|whispers|asks|adds)\b",
        r"\1",
        s,
        flags=re.I,
    )
    # saying (warm): → says (warm):
    s = re.sub(
        r"\bsaying\s+(\([^)]{1,40}\)\s*:)",
        r"says \1",
        s,
        flags=re.I,
    )
    return s


def _fix_bare_emotion_brackets(s: str) -> str:
    """Bare (soft): \"hi\" → says (soft): \"hi\" — only when no speech verb already present.

    Must not turn 'saying (warm):' into 'saying says (warm):'.
    """
    speech_verb_tail = re.compile(
        r"\b(?:says|saying|sayin'?|murmurs|murmuring|whispers|whispering|"
        r"asks|asking|adds|adding|growls|growling|moans|moaning|"
        r"gasps|gasping|snarls|snarling|breathes|breathing)\s*$",
        re.I,
    )

    def repl(m: re.Match) -> str:
        start = m.start()
        pre = s[max(0, start - 28):start]
        if speech_verb_tail.search(pre):
            return m.group(0)
        return f"says ({m.group(1)}): {m.group(2)}"

    return re.sub(
        r"\((\w[\w\s,]{0,40})\)\s*:\s*(\")",
        repl,
        s,
    )


def _scrub_meta_speech(s: str) -> str:
    """Kill fourth-wall / edit-aware spoken lines that LTX would print literally."""
    # Rewrite common meta quotes into empty removal (drop the quote clause)
    meta_in_quotes = re.compile(
        r'"[^"]*\b(?:after the cut|hard cut|jump cut|this (?:scene|clip|video|shot|prompt)|'
        r'as the (?:clip|video|scene) continues|in this (?:video|scene|clip)|'
        r'the camera|the prompt|ltx)\b[^"]*"',
        re.I,
    )
    s = meta_in_quotes.sub('""', s)
    # Clean empty speech acts left after meta quote strip (keep the section intact)
    s = re.sub(
        r'\b(?:says|murmurs|whispers|growls|snarls|gasps|barks|adds|asks|moans|groans)\s*'
        r'(?:\([^)]*\))?\s*:\s*""\s*',
        'breathes a quiet sound. ',
        s,
        flags=re.I,
    )
    s = re.sub(r'\.\s*\.', '.', s)
    s = re.sub(r'breathes a quiet sound\.\s*\.', 'breathes a quiet sound.', s, flags=re.I)
    # Prose meta (keep newlines — never use \s which eats section breaks)
    s = re.sub(r'\b(?:after|before)\s+the\s+(?:hard\s+)?(?:jump\s+)?cut\b[^.!\n]{0,40}', '', s, flags=re.I)
    s = re.sub(r'[^\S\n]{2,}', ' ', s)  # horizontal whitespace only
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s


def _scrub_garment_one_shot(s: str) -> str:
    """Soften 'in one motion' full-garment removals that fight CANON."""
    s = re.sub(
        r'\bpulls?\s+(?:her|his|the)\s+(\w+)\s+(?:up\s+)?over\s+(?:her|his)\s+head\s+in\s+one\s+(?:motion|go|pull)\b',
        r'grips the hem of the \1 and pulls it up past the ribs, then off the arms',
        s,
        flags=re.I,
    )
    s = re.sub(
        r'\bin\s+one\s+(?:motion|go|pull)\b',
        'in a steady continuous motion',
        s,
        flags=re.I,
    )
    s = re.sub(
        r'\b(?:clothes|clothing)\s+(?:are|is)\s+gone\b',
        'garments lie discarded',
        s,
        flags=re.I,
    )
    return s


def _dedupe_spoken_loops(s: str) -> str:
    """If the same 3+ word chunk appears in multiple quoted lines, lightly
    diversify later occurrences by dropping the repeated chunk from the quote.
    Conservative — only exact multi-word repeats inside quotes."""
    quotes = re.findall(r'"([^"]+)"', s)
    if len(quotes) < 3:
        return s
    # find 3-word phrases that appear in 3+ different quotes
    from collections import Counter
    phrase_hits = Counter()
    for q in quotes:
        words = re.findall(r"[A-Za-z']+", q.lower())
        for i in range(len(words) - 2):
            phrase_hits[" ".join(words[i:i + 3])] += 1
    bad = {p for p, n in phrase_hits.items() if n >= 3 and len(p) >= 10}
    if not bad:
        return s

    seen_phrase = {p: 0 for p in bad}

    def fix_quote(m):
        inner = m.group(1)
        low = inner.lower()
        for p in bad:
            if p in low:
                seen_phrase[p] += 1
                if seen_phrase[p] > 1:
                    # strip this occurrence of the loop phrase
                    inner = re.sub(re.escape(p), "", inner, count=1, flags=re.I)
                    inner = re.sub(r"\s{2,}", " ", inner).strip(" ,.")
        if not inner:
            return m.group(0)
        return f'"{inner}"'

    return re.sub(r'"([^"]+)"', fix_quote, s)


_CUT_MARK_RE = re.compile(
    r"\bhard cut\b|\bjump cut\b|\binstant cut\b|\bhard-cut\b|"
    r"\bclothes gone\b|\bnow naked\b|\bnaked on (?:her|his) knees\b|"
    r"\bon her knees\b.*\b(?:sucks?|mouth|cock)\b|\bkneeling\b.*\b(?:sucks?|blow)\b",
    re.I,
)
_POST_CUT_ACT_RE = re.compile(
    r"\b(?:sucks?|sucking|blowjob|deepthroat|fucks?|fucking|penetration|"
    r"cowgirl|doggy|missionary|cock in|takes (?:him|it) (?:into|in)|"
    r"rides?|riding|bobs?|bobbing|gags?|facesit|face.?sit)\b",
    re.I,
)


def ensure_jump_hard_cut(s: str, *, intent: str = "", scenario: str = "") -> str:
    """If this is a JUMP scene and the script never marks a cut, inject one.

    Conservative: only when JUMP is clearly requested and no cut mark exists.
    Inserts 'Hard cut.' at the start of the first post-setup section that looks
    like the act leap (oral/sex), else at ~1/3 of sections.
    """
    blob = f"{intent or ''} {scenario or ''}".lower()
    scn = scenario or ""
    is_jump = (
        "⚡" in scn
        or "jump:" in blob
        or "jump cut" in blob
        or "hard cut" in blob
        or re.search(r"\bjump\b.*\b(blowjob|doggy|cowgirl|wall|sink|backseat|facesit|oral)\b", blob)
        or re.search(r"\b(hello|chat|kiss|talk).*(→|->|then).*(blowjob|doggy|fuck|sex|oral)\b", blob)
    )
    if not is_jump:
        return s
    if _CUT_MARK_RE.search(s or ""):
        return s

    parts = re.split(r"(\n\n+)", s or "")
    # Build list of content section indices (even positions if split keeps seps)
    content_idxs = [i for i, p in enumerate(parts) if p.strip() and not re.match(r"^\n+$", p)]
    if len(content_idxs) < 3:
        return s

    # Skip I2V anchor / eye-level open as setup
    start_i = 0
    for j, idx in enumerate(content_idxs):
        low = parts[idx].lower()
        if re.search(r"use the provided start image|eye-level", low):
            start_i = j + 1
            continue
        break
    setup_end = min(len(content_idxs) - 1, max(start_i + 1, start_i + max(1, (len(content_idxs) - start_i) // 3)))

    # Prefer first post-setup section that already looks like the act
    inject_at = content_idxs[setup_end]
    for idx in content_idxs[setup_end:]:
        if _POST_CUT_ACT_RE.search(parts[idx]):
            inject_at = idx
            break

    body = parts[inject_at].lstrip()
    if _CUT_MARK_RE.search(body):
        return s
    # Don't put Hard cut inside a pure dialogue quote-only line
    parts[inject_at] = "Hard cut. " + body
    return "".join(parts)


def _scrub_silent_speech(s: str) -> str:
    """SILENT tier: strip quoted dialogue and 'says (…):' speech frames."""
    # Drop "says (bracket): \"...\"" / murmurs / whispers / etc. whole clause
    s = re.sub(
        r"\s*(?:and\s+)?(?:"
        r"says?|said|murmurs?|murmured|whispers?|whispered|mutters?|muttered|"
        r"asks?|asked|replies?|replied|calls?|called|yells?|yelled|shouts?|shouted|"
        r"breathes?|breathed|hisses?|hissed|growls?|growled|moans?|moaned"
        r")\s*(?:\([^)]{0,40}\))?\s*:\s*[\"\u201c][^\"\u201d]*[\"\u201d]",
        "",
        s,
        flags=re.I,
    )
    # Remaining bare quotes (curly or straight)
    s = re.sub(r'[\"\u201c][^\"\u201d]{0,240}[\"\u201d]', "", s)
    # Orphan speech verbs left behind
    s = re.sub(
        r"\s*(?:and\s+)?(?:"
        r"says?|murmurs?|whispers?|mutters?|asks?|replies?"
        r")\s*(?:\([^)]{0,40}\))?\s*:?\s*$",
        "",
        s,
        flags=re.I | re.M,
    )
    # Collapse empty sections / double spaces (keep blank-line layout)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = re.sub(r" +\.", ".", s)
    s = re.sub(r" +,", ",", s)
    return s.strip()


def scrub(text: str, *, mode: str = "i2v", pov: bool = False,
          intent: str = "", scenario: str = "", dialogue_tier: str = "standard") -> str:
    """Clean a finished script. Returns stripped text."""
    s = (text or "").strip()
    if not s:
        return s

    s = re.sub(r"<think>.*?</think>", "", s, flags=re.DOTALL)
    s = re.sub(r"^```\w*\s*", "", s)
    s = re.sub(r"\s*```\s*$", "", s)
    s = s.strip()

    s = _scrub_star_adlibs(s)
    s = _apply_verb_map(s)
    s = _VIBE.sub("", s)
    # Only strip micro-details / felt-sensation prose outside of spoken quotes
    parts = re.split(r'("[^"]*")', s)
    for i, part in enumerate(parts):
        if not (part.startswith('"') and part.endswith('"')):
            part = _MICRO.sub("", part)
            part = re.sub(r"\b(?:she|he|they|you) feels?\b[^.\n]{0,40}", "", part, flags=re.I)
            parts[i] = part
    s = "".join(parts)
    for rx, rep in _HEAD_ONLY:
        s = rx.sub(rep, s)
    s = _fix_lone_lookback(s)
    s = _fix_rise_getup(s)
    s = _fix_facing_jump(s)
    s = _fix_bra_waist_incomplete(s)
    # De-spam identical torso phrase spam (keep first style variety later via brain)
    s = re.sub(
        r"(rotates? (?:her |his |their )?torso and head together(?: as one unit)?(?: to face[^.!\n]*)?[.!]?\s*){3,}",
        lambda m: m.group(0),  # leave for now; collapse only true doubles below
        s,
        flags=re.I,
    )
    # Collapse accidental doubled torso phrases from model+scrub collisions
    s = re.sub(
        r"(rotates? (?:her |his |their )?torso and head together(?: as one unit)?)"
        r"(?:\s+to)?\s+\1",
        r"\1",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"to rotates torso and head together to",
        "to",
        s,
        flags=re.I,
    )
    # "pulls her torso and head together" is nonsensical body language from over-applying the rule
    s = re.sub(
        r"\bpulls? (?:her|his|their) torso and head together\b",
        "pulls her close",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"\bpulling (?:her|his|their) torso and head together\b",
        "pulling her close",
        s,
        flags=re.I,
    )
    # Broken fragments only: "his ," (space before comma = missing noun), not normal "her, and"
    s = re.sub(r"\b(his|her|their)\s+,\s*", r"\1 hands ", s, flags=re.I)
    s = re.sub(r"\b(his|her|their)\s+against\b", r"\1 body against", s, flags=re.I)
    s = re.sub(r"\bhands settle,\s*\.", ".", s, flags=re.I)
    s = re.sub(r",\s*\.", ".", s)
    s = re.sub(r"\s+,", ",", s)
    s = re.sub(r",\s*,+", ",", s)
    s = re.sub(r"\.\s*\.", ".", s)
    # NEVER use \s{2,} here — it eats newlines and kills section layout
    s = re.sub(r"[ \t]{2,}", " ", s)

    # Tidy whitespace again after vibe wipe (preserve blank-line sections)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r" *\n *", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = _ensure_section_breaks(s)
    s = ensure_jump_hard_cut(s, intent=intent, scenario=scenario)
    s = _dedupe_spoken_loops(s)
    s = _scrub_meta_speech(s)
    s = _scrub_garment_one_shot(s)
    s = _scrub_occupied_mouth_talk(s)
    s = _scrub_oral_pull_off_wordiness(s)
    s = _scrub_false_pov_voice(s, pov=bool(pov))
    s = _scrub_speech_verb_glitches(s)
    s = _fix_dialogue_caps(s)
    s = _fix_quote_terminal_punct(s)
    s = _scrub_meta_quality_tags(s)
    # SILENT tier wins — strip any quoted speech the model still wrote
    if (dialogue_tier or "").lower() in ("none", "silent", "off"):
        s = _scrub_silent_speech(s)
    # Glued consecutive quotes from stream collisions: "foo""bar" → two lines
    s = re.sub(r'"\s*"', '"\n\n"', s)
    # Voice-setup sentence accidentally quoted as speech — unquote into prose
    s = re.sub(
        r'["\u201c]((?:His|Her|Their) voice:\s*English with a heavy[^"\u201d]{10,160})["\u201d]',
        r"\1",
        s,
        flags=re.I,
    )

    if (mode or "").lower() == "i2v":
        if not re.search(r"use the provided start image", s, re.I):
            s = _I2V_ANCHOR + "\n" + s.lstrip()
        else:
            # Ensure it is literally the first line
            lines = s.splitlines()
            if lines and not re.search(r"use the provided start image", lines[0], re.I):
                # pull any anchor line to front
                rest = []
                anchor = _I2V_ANCHOR
                for ln in lines:
                    if re.search(r"use the provided start image", ln, re.I):
                        anchor = ln.strip()
                    else:
                        rest.append(ln)
                s = anchor + "\n" + "\n".join(rest).lstrip()

    # Bare emotion-bracket speech without a verb: (soft): "hi" → says (soft): "hi"
    # Global — accent/talkative scripts hit this too, not only POV
    s = _fix_bare_emotion_brackets(s)
    s = _scrub_speech_verb_glitches(s)

    if pov:
        # Soft warn via rewrite of common collapse: "I grab" → "a hand grabs"
        s = re.sub(r"\bI grab\b", "a hand grabs", s, flags=re.I)
        s = re.sub(r"\bI reach\b", "a hand reaches", s, flags=re.I)
        s = re.sub(r"\bI pull\b", "a hand pulls", s, flags=re.I)
        s = re.sub(r"\bI push\b", "a hand pushes", s, flags=re.I)
        s = re.sub(r"\bmy hand\b", "a hand", s, flags=re.I)
        s = re.sub(r"\bmy hands\b", "hands", s, flags=re.I)
        # Hands are not a speaking mouth — common Gemma slip
        s = re.sub(
            r"\b([Hh]ands?[^.!\n]{0,80}?)\s+and says\b",
            r"\1. She says",
            s,
        )
        s = re.sub(
            r"\b([Tt]he view[^.!\n]{0,60}?)\s+and says\b",
            r"\1. She says",
            s,
        )

    return s.strip()
