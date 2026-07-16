# -*- coding: utf-8 -*-
"""
sing_ld.py — Singing / vocal performance doctrine for PromptForge LD

Activation (NO BLOAT — same philosophy as dance_ld):
  • Only injects when intent/scenario has clear SING / SONG / KARAOKE cues.
  • Music preset alone does NOT force singing — music only *colours* the vocal.
  • "Music-video" video style alone does NOT force lyrics (performance can be dance-only).
  • Silent dialogue tier → hum / melody only (no quoted lyrics).

Why this exists:
  Accent banks + CANON push spoken "says (soft): …". When the user wants
  singing, the model otherwise softens into talk. This block cuts in and
  tries — LTX-safe short lyric phrases, not arias.
"""
from __future__ import annotations

import random
import re

# ─────────────────────────────────────────────────────────────────────────────
#  ACTIVATION
# ─────────────────────────────────────────────────────────────────────────────

_SING_CUES = (
    "sing", "sings", "singing", "sang", "sung", "singer",
    "song", "songs", "lyrics", "lyric", "chorus", "verse",
    "karaoke", "belt", "belting", "belt out",
    "serenade", "serenades", "serenading",
    "croon", "croons", "crooning",
    "harmonize", "harmonise", "harmony line",
    "toasting", "toast over", "singjay",
    "melisma", "melismatic", "runs and ad-libs",
    "hum a tune", "hums a tune", "humming a song",
    "sings along", "sing along", "singing along",
    "sings the", "sings a", "sings to",
    "musical number", "showtune", "show tune",
    "acapella", "a cappella", "a capella",
    "sings softly", "softly sings", "sings quiet",
    "vocals", "vocal run", "power note", "held note",
    "raps a verse",  # half-sung / vocal performance intent
    "spits a verse",
)

# Soft cues that need a second music/voice hint (avoid "song" as in love song title only)
_SOFT_SING = (
    "hook", "the chorus", "into the mic", "to the microphone",
    "on the mic", "open mic", "covers the song", "cover of",
)

# Anti-false: bare "music" / "soundtrack" without sing words must NOT activate
_FALSE_ALONE = (
    "music", "soundtrack", "bass", "edm", "techno", "score",
)


def _blob(intent: str = "", scenario: str = "", style: str = "") -> str:
    return f"{intent or ''} {scenario or ''} {style or ''}".lower()


def wants_sing(
    intent: str = "",
    scenario: str = "",
    *,
    video_style: str = "",
) -> bool:
    """True when user clearly wants sung / vocal performance."""
    b = _blob(intent, scenario, video_style)
    if not b.strip():
        return False
    if any(c in b for c in _SING_CUES):
        return True
    # Soft: "hook" / "mic" only with music context
    if any(c in b for c in _SOFT_SING):
        if re.search(r"\b(?:music|song|sing|track|karaoke|band|mic)\b", b):
            return True
    return False


def is_active(intent: str = "", scenario: str = "", *, video_style: str = "") -> bool:
    return wants_sing(intent, scenario, video_style=video_style)


# ─────────────────────────────────────────────────────────────────────────────
#  SING PATHS — LTX-safe vocal delivery (mechanism + short lyrics)
# ─────────────────────────────────────────────────────────────────────────────

SING_PATHS: dict[str, dict] = {
    "soft_croon": {
        "name": "Soft croon / close-mic",
        "triggers": (
            "croon", "softly sings", "sings soft", "quiet song", "whisper-sing",
            "sings quietly", "intimate song", "bedroom song",
        ),
        "doctrine": (
            "SOFT CROON: short phrases (4–10 words); breathy delivery named in the bracket "
            "(soft)/(breath)/(low). Mouth visible — lips shape words. One lyric phrase per section; "
            "rest is breath or a soft hum between. Not a full verse dump."
        ),
    },
    "belt_chorus": {
        "name": "Belt / chorus push",
        "triggers": (
            "belt", "belting", "belt out", "big chorus", "power note",
            "sings loud", "full voice", "belt the chorus",
        ),
        "doctrine": (
            "BELT/CHORUS: chest open; jaw drops on open vowels; head+torso lift together on the push. "
            "One short hook line per belted section. Prefer MIX music (not quiet wallpaper) if score is on. "
            "Still complete words — no mid-word cut at section end."
        ),
    },
    "sing_along": {
        "name": "Sing-along to the track",
        "triggers": (
            "sing along", "sings along", "singing along", "sings with the music",
            "sings to the song", "joins the chorus", "karaoke",
        ),
        "doctrine": (
            "SING-ALONG: track is already playing (plant music early if preset on). "
            "They join with short known-hook style lines or placeholder lyric fragments that match the genre. "
            "Eyes can go half-closed; one hand optional on mic/air mic. Mouth free = sing; mouth busy = hum only."
        ),
    },
    "karaoke": {
        "name": "Karaoke / mic performance",
        "triggers": ("karaoke", "on the mic", "into the mic", "microphone", "open mic"),
        "doctrine": (
            "KARAOKE/MIC: hand on mic or stand; weight shift; face the view or screen. "
            "Lyric lines short; optional shy laugh between. Name mic grip once, then sing."
        ),
    },
    "serenade": {
        "name": "Serenade / to a partner",
        "triggers": ("serenade", "sings to her", "sings to him", "sings for her", "sings for him"),
        "doctrine": (
            "SERENADE: eye-line on partner; soft or warm belt; one lyric phrase then a reaction beat "
            "(partner smile/look away). Keep identities stable. Not continuous aria."
        ),
    },
    "rnb_runs": {
        "name": "R&B runs / melisma",
        "triggers": (
            "r&b", "rnb", "melisma", "vocal run", "runs and ad-libs",
            "soul sing", "soul singing",
        ),
        "doctrine": (
            "R&B/RUNS: base line is a short lyric; then optional wordless run (*ooh* / *yeah* melody) "
            "on the same section if mouth free. Do not write fake IPA — use plain *ooh* / *yeah* / held 'oh'."
        ),
    },
    "rap_verse": {
        "name": "Rap / half-sung verse",
        "triggers": (
            "raps", "rapping", "spits a verse", "raps a verse", "rap verse",
            "spits bars", "freestyles",
        ),
        "doctrine": (
            "RAP/VERSE: rhythmic speech on the beat if music on; short bar (one line) per section; "
            "gesture with free hand optional. Accent grammar can colour the English. Not mumbled mush."
        ),
    },
    "dancehall_toast": {
        "name": "Toast / singjay",
        "triggers": ("toasting", "toast over", "singjay", "dancehall sing"),
        "doctrine": (
            "TOAST/SINGJAY: rhythmic call over the riddim; short call-and-response fragments; "
            "optional Jamaican/Caribbean slips if accent locked. Energy up; words still clear."
        ),
    },
    "anthem_rock": {
        "name": "Rock / anthem shout-sing",
        "triggers": (
            "rock sing", "sings rock", "anthem", "sings the chorus loud",
            "gritty vocal", "sings with the band",
        ),
        "doctrine": (
            "ROCK/ANTHEM: gritty full-throated short lines; jaw and chest work visible; "
            "sync step or fist optional on downbeat. Prefer shout-sing over quiet croon."
        ),
    },
    "classical_legato": {
        "name": "Classical / long tone",
        "triggers": (
            "opera", "aria", "classical sing", "long note", "legato",
            "sings classical", "choir",
        ),
        "doctrine": (
            "CLASSICAL/LEGATO: one long open vowel or short lyric; posture tall; "
            "ribs expand on breath. One sustained idea per section — never rush six lines."
        ),
    },
    "hum_melody": {
        "name": "Hum / wordless melody",
        "triggers": (
            "hum", "hums", "humming", "hum a tune", "wordless", "la la",
            "oohs", "sings without words",
        ),
        "doctrine": (
            "HUM/WORDLESS: *hums a short melody* / *soft ooh* — no fake sheet-music. "
            "Visible closed or soft-open lips; can bridge sections between spoken or sung lines."
        ),
    },
    "freestyle_vocal": {
        "name": "General sing (freestyle)",
        "triggers": (),
        "doctrine": (
            "GENERAL SING: at least 2–4 short sung phrases across the clip when duration allows. "
            "Format: She/He sings (soft|warm|firm): \"short lyric.\" "
            "Alternate with action sections so it is not wall-of-lyrics. "
            "If music preset is on, land phrases near kicks/hooks when MIX; keep soft if BACKGROUND."
        ),
    },
}


def detect_sing_paths(
    intent: str = "",
    scenario: str = "",
    *,
    video_style: str = "",
    max_paths: int = 3,
) -> list[str]:
    if not wants_sing(intent, scenario, video_style=video_style):
        return []
    b = _blob(intent, scenario, video_style)
    hits: list[tuple[int, str]] = []
    for key, meta in SING_PATHS.items():
        if key == "freestyle_vocal":
            continue
        score = 0
        for t in meta.get("triggers") or ():
            if t in b:
                score = max(score, len(t))
        if score:
            hits.append((score, key))
    hits.sort(key=lambda x: -x[0])
    keys = [k for _, k in hits[:max_paths]]
    if not keys:
        keys = ["freestyle_vocal"]
    return keys


# ─────────────────────────────────────────────────────────────────────────────
#  ACCENT × SING — full bank (every accents_ld key). English lyrics first;
#  native slips as seasoning between phrases — never comedy phonetics.
# ─────────────────────────────────────────────────────────────────────────────

# Each entry:
#   vocal   — how the voice should feel when singing (LTX-describable)
#   lyric   — English grammar/rhythm inside short sung lines
#   slips   — optional native/regional tags BETWEEN phrases (not every bar)
#   anti    — failure modes
ACCENT_SING: dict[str, dict[str, str]] = {
    "korean": {
        "vocal": "syllable-even English hooks; soft rising ends; light nasal warmth; short breath groups",
        "lyric": "drop a/the often in lyrics; short clauses; topic-first OK (\"this night, I stay\")",
        "slips": "between phrases only: 자기야 / 좋아 / 더 / 진짜 — never spam one particle every line",
        "anti": "no hangul walls; no K-pop romanization soup; no ending every hook with 진짜",
    },
    "japanese": {
        "vocal": "mora-like short units; crisp consonants; soft rising ends; polite or breathy heat",
        "lyric": "drop articles; short hooks; optional soft ne/yo feel in English tags (\"right?\", \"okay?\") sparingly",
        "slips": "between phrases: ねえ / もっと / 好き / だめ — one varied slip, not wallpaper",
        "anti": "no full Japanese verses; no desu/masu comedy English",
    },
    "mandarin": {
        "vocal": "even staccato English; slight tonal push under vowels; clear finals; short punchy hooks",
        "lyric": "short clauses; less linking; no American drawl in the sung line",
        "slips": "between phrases: 好 / 对 / 快点 / 亲爱的 — sparingly",
        "anti": "no tone-mark spellings; no 好 on every line",
    },
    "thai": {
        "vocal": "soft sing-song under English; gentle rises; warm mid pitch; melodic short lines",
        "lyric": "polite soft heat; short melodic hooks; soft … between phrases",
        "slips": "between phrases: ที่รัก / ใช่ / มา — light only",
        "anti": "no ครับ/ค่ะ spam on every sung line",
    },
    "vietnamese": {
        "vocal": "quick light English; tonal shadow under vowels; sharp short vowels; rising questions",
        "lyric": "staccato hooks; short breath groups",
        "slips": "between phrases: ơi / ừ / đi — rare seasoning",
        "anti": "no tone orthography games; no comedy respelling",
    },
    "french": {
        "vocal": "even rhythm; soft consonants; open vowels on long notes; slight uvular-R only in voice line prose not spelling",
        "lyric": "complete short English lines; soft finals; chanson-length phrasing (one idea per section)",
        "slips": "between phrases: oui / alors / mon amour / allez — not every bar",
        "anti": "no ze/zis comedy French; no full French aria unless intent is French lyrics (still keep short)",
    },
    "spanish_castilian": {
        "vocal": "crisp forward vowels; lively stress; clear ends; Mediterranean energy on belts",
        "lyric": "open vowels in English lyrics; rhythmic stress on content words",
        "slips": "between phrases: venga / mira / amor / joder (if explicit heat) — sparingly",
        "anti": "no fake inverted punctuation spam; no wall of Spanish",
    },
    "spanish_latin": {
        "vocal": "warm open vowels; musical stress; softer than Castilian; reggaeton/pop pocket friendly",
        "lyric": "warm English hooks; optional slight Spanish word order flavour without breaking sense",
        "slips": "between phrases: amor / ay / mami / dale — one at a time, varied",
        "anti": "no cartoon 'aye papi' loop every section",
    },
    "italian": {
        "vocal": "open vowels; musical stress; lively cadence; bel canto posture on longer notes",
        "lyric": "vowel-forward English; one clear emotion per short line",
        "slips": "between phrases: amore / dai / bella / per favore — sparingly",
        "anti": "no pizza-pasta stereotype lyrics; no fake -a endings on English words",
    },
    "portuguese": {
        "vocal": "soft musical English; nasal hint in voice description; warm mid tone; bossa/MPB pocket OK",
        "lyric": "gentle hooks; soft ends; unhurried",
        "slips": "between phrases: amor / então / vem / sim — light",
        "anti": "no comedy nasal spelling; no full Portuguese walls",
    },
    "german": {
        "vocal": "harder consonants; clear ends; firm stress; less soft US melody; rock/anthem friendly",
        "lyric": "blunt short clauses; complete words; firm cadence in the hook",
        "slips": "between phrases: ja / komm / bitte / scheiße (if heat) — rare",
        "anti": "no fake harsh 'achtung' parody; no every-line ja?",
    },
    "dutch": {
        "vocal": "flat clear English; direct; slight hard-g only in voice prose not spelling",
        "lyric": "plain short hooks; no soft American mush",
        "slips": "between phrases: ja / kom / lekker — sparingly",
        "anti": "no fake guttural comedy English",
    },
    "swedish": {
        "vocal": "sing-song pitch melody under English; soft consonants; Nordic lift on ends",
        "lyric": "melodic short lines; gentle rises; light",
        "slips": "between phrases: hej / vänta / snälla — rare",
        "anti": "no chef-skit Swedish; no melodic misspelling",
    },
    "norwegian": {
        "vocal": "sing-song Nordic melody; soft but clear; warm mid",
        "lyric": "melodic short English; soft rises",
        "slips": "between phrases: hei / bare / kom — rare",
        "anti": "no fake Nordic cartoon vowels in spelling",
    },
    "russian": {
        "vocal": "hard consonants; clipped ends; heavy stress; lower pitch; dark warmth on belts",
        "lyric": "firm short lines; no soft US drawl; stress on content words",
        "slips": "between phrases: да / нет / давай / родной — sparingly",
        "anti": "no 'strong like bull' parody; no wall of Cyrillic",
    },
    "polish": {
        "vocal": "consonant-forward; firm clear stress; central European firmness",
        "lyric": "short firm hooks; clear ends",
        "slips": "between phrases: tak / proszę / kochanie — rare",
        "anti": "no consonant-cluster comedy spelling",
    },
    "czech": {
        "vocal": "flat-clear; firm consonants; central European cadence",
        "lyric": "plain short English; direct",
        "slips": "between phrases: ano / pojď / prosím — rare",
        "anti": "no fake ř respelling",
    },
    "greek": {
        "vocal": "warm open Mediterranean rhythm; lively stress; sunlit belts",
        "lyric": "open vowels; short warm hooks",
        "slips": "between phrases: ναι / έλα / αγάπη μου — sparingly",
        "anti": "no plate-smashing cliché lyrics",
    },
    "arabic": {
        "vocal": "warm weight; clear stress; longer held vowels OK; soft ornament as *ooh* / *ya* runs not fake maqam notation",
        "lyric": "short complete English lines; optional longer open vowel on last word of the hook",
        "slips": "between phrases: habibi / yalla / ya / wallah — varied, not every line",
        "anti": "no fake Arabic script dump; no terrorist/parody tropes; no constant habibi spam",
    },
    "hebrew": {
        "vocal": "direct dry modern edge; clear stress; urban warm when soft",
        "lyric": "short direct hooks; no mushy filler",
        "slips": "between phrases: כן / יאללה / מותק — rare",
        "anti": "no political slogans; no fake pointed-text spam",
    },
    "swahili": {
        "vocal": "open vowels; rhythmic warm East African English bounce; soft pocket",
        "lyric": "rhythmic short English; bounce on the beat if music on",
        "slips": "between phrases: tafadhali / ndiyo / habari — light",
        "anti": "no safari cliché lyrics",
    },
    "filipino_english": {
        "vocal": "clear syllable English; light Tagalog colour; warm friendly stress; karaoke-culture natural",
        "lyric": "clear short hooks; friendly warmth; karaoke sing-along friendly",
        "slips": "between phrases: gago (heat) / mahal / sige / oy — sparingly",
        "anti": "no mock-Filipino spelling; no every-line po/opo unless character is formal",
    },
    "new_zealand": {
        "vocal": "laid-back; soft ends; raised-vowel feel only in voice prose; easy croon",
        "lyric": "relaxed short English; understated hooks",
        "slips": "between phrases: yeah / sweet as / eh — light Kiwi tags, not spam",
        "anti": "no fake vowel respelling (fush/chups)",
    },
    "nigerian_english": {
        "vocal": "rhythmic West African English; clear stress; lively bounce; Afrobeats pocket friendly",
        "lyric": "rhythmic short lines; confident hooks; bounce on the beat",
        "slips": "between phrases: abeg / oya / jare / my guy — varied seasoning",
        "anti": "no pidgin wall every section; no mock accent spelling",
    },
    "ghanaian_english": {
        "vocal": "warm West African English; slightly softer than Naija; clear ends; friendly bounce",
        "lyric": "warm short hooks; clear ends; hiplife/afrobeats pocket OK",
        "slips": "between phrases: chale / paa / mei — sparingly",
        "anti": "no mock spelling; no every-line chale",
    },
    "south_african_english": {
        "vocal": "clipped dry warmth; flattened-vowel feel only in voice prose; firm pocket",
        "lyric": "dry short English; direct hooks",
        "slips": "between phrases: ja / lekker / eish — light",
        "anti": "no apartheid/political slogans; no fake vowel respelling",
    },
    "trinidadian": {
        "vocal": "Caribbean melody under clear English; playful bounce; warm ends; soca/carnival energy OK",
        "lyric": "playful short hooks; bounce; clear English base",
        "slips": "between phrases: gyal / wine / oui (Trini) — sparingly",
        "anti": "no nonstop dialect wall; no comedy respelling",
    },
    "indian_english": {
        "vocal": "syllable-clear English; even tempo; retroflex hint only in voice prose; filmi warmth on long notes OK",
        "lyric": "clear short English hooks; even rhythm; optional slightly formal sweetness",
        "slips": "between phrases: yaar / na / bas / ji — sparingly",
        "anti": "no Apu parody; no fake retroflex spelling; no every-line na?",
    },
    "cockney": {
        "vocal": "lively London energy; glottal/dropped-H only in voice line description — never respelt lyrics",
        "lyric": "plain English hooks with London rhythm; cheeky short lines; no letter-dropping spelling",
        "slips": "between phrases: mate / innit / love / oi — varied, not every hook",
        "anti": "NEVER write wiv/free/fink in lyrics; describe accent, spell standard",
    },
    "scottish": {
        "vocal": "firm cadence; rolled-R feel in voice prose only; tighter vowels; ballad or pub-belt both OK",
        "lyric": "standard spelling English; firm short lines; soft ballad or grit — match intent",
        "slips": "between phrases: aye / lass / hen / pure — sparingly",
        "anti": "no pho-nettic Scottish (cannae spelled only if rare flavour — prefer aye + standard English lyrics)",
    },
    "irish": {
        "vocal": "lilting melody; soft ends; musical stress; ballad croon natural",
        "lyric": "melodic short English; soft rises; storytelling hooks",
        "slips": "between phrases: love / sure / grand / pet — light",
        "anti": "no leprechaun parody; no fake 'top o the mornin' spam",
    },
    "scouse": {
        "vocal": "Liverpool melody; sharp lively; musical ends",
        "lyric": "lively short English; sharp hooks; standard spelling",
        "slips": "between phrases: la / sound / boss — sparingly",
        "anti": "no comedy Scouse respelling",
    },
    "geordie": {
        "vocal": "North-East bounce; firm warm; direct energy",
        "lyric": "warm short English; bounce; standard spelling",
        "slips": "between phrases: pet / man / howay — rare",
        "anti": "no fake Geordie orthography",
    },
    "northern_english": {
        "vocal": "flatter vowels feel in prose only; dry direct; less soft South polish",
        "lyric": "dry short English; direct hooks; no RP polish unless intent says",
        "slips": "between phrases: love / mate / now then — light",
        "anti": "no mock Northern spelling",
    },
    "welsh": {
        "vocal": "sing-song Welsh English melody; soft rises; musical lilt (speech-song already close to sing)",
        "lyric": "melodic short English; soft rises on ends; ballad-friendly",
        "slips": "between phrases: cariad / right / love — sparingly",
        "anti": "no fake Welsh orthography in English lyrics; no every-line boyo",
    },
    "rp_british": {
        "vocal": "clear non-rhotic Southern British; clipped polish; controlled croon or clean belt",
        "lyric": "complete polished English; no dropped letters; controlled short lines",
        "slips": "between phrases: darling / love / right — restrained",
        "anti": "no stuffy parody; no fake posh misspellings",
    },
    "australian": {
        "vocal": "laid-back; broader-vowel feel in prose only; rising terminals sometimes; easy croon",
        "lyric": "relaxed short English; understated hooks; standard spelling",
        "slips": "between phrases: mate / yeah nah / love — light",
        "anti": "no fake Strine respelling (no 'g'day mate' spam every section)",
    },
    "jamaican_rasta": {
        "vocal": "Caribbean lilt under clear English; warm bounce; relaxed stress; toast/singjay natural",
        "lyric": "clear English base; rhythmic hooks; toast fragments OK; soft ends",
        "slips": "between phrases: yeah mon / irie / gyal / bredren / one love — VARIETY, not yeah-mon every line",
        "anti": "no nonstop patois wall; no mock Rasta parody; no fake phonetic jungle spelling",
    },
    "southern_us": {
        "vocal": "slow drawl feel in prose only; warm longer vowels; country/soul croon natural; melisma OK as *ooh*",
        "lyric": "warm short English; longer vowels on key words; storytelling hooks",
        "slips": "between phrases: sugar / baby / y'all / darlin — sparingly",
        "anti": "no fake 'yeehaw' spam; no mock Southern orthography (no 'y'all' every bar)",
    },
}

# Sanity: every accents_ld key should have a row (assert at import when ACCENTS available)
def _verify_accent_sing_coverage() -> None:
    try:
        from .accents_ld import ACCENTS
    except ImportError:
        try:
            from accents_ld import ACCENTS
        except ImportError:
            return
    missing = [k for k in ACCENTS if k not in ACCENT_SING]
    extra = [k for k in ACCENT_SING if k not in ACCENTS]
    if missing or extra:
        raise RuntimeError(
            f"ACCENT_SING coverage broken — missing={missing} extra={extra}"
        )


try:
    _verify_accent_sing_coverage()
except Exception as _e:
    # Don't crash Comfy on partial load; print once
    print(f"[PromptForgeLD] sing_ld accent coverage: {_e}")


def resolve_sing_accent_key(force_key: str = "", intent: str = "") -> str:
    """Map UI force / intent detect → ACCENT_SING key."""
    try:
        from .accents_ld import resolve_accent_key, ACCENTS
    except ImportError:
        try:
            from accents_ld import resolve_accent_key, ACCENTS
        except ImportError:
            k = (force_key or "").strip().lower()
            return k if k in ACCENT_SING else ""
    raw = (force_key or "").strip().lower()
    if raw in ("", "auto", "none", "off", "same", "same as lead"):
        # auto from intent only when force is auto; off stays off
        if raw in ("off", "none", "same", "same as lead"):
            return ""
        key = resolve_accent_key(intent, "auto" if raw in ("", "auto") else force_key)
    else:
        key = resolve_accent_key(intent, force_key)
    if key in ACCENT_SING:
        return key
    if key in ACCENTS and key not in ACCENT_SING:
        return ""  # should not happen if coverage assert holds
    return ""


def format_accent_sing_colour(key: str, *, role: str = "LEAD") -> str:
    """Multi-line doctrine strip for one speaker."""
    meta = ACCENT_SING.get(key) or {}
    if not meta:
        return ""
    try:
        from .accents_ld import ACCENTS
        name = (ACCENTS.get(key) or {}).get("name") or key
    except Exception:
        name = key
    return "\n".join([
        f"【{role} SING COLOUR — {name}】",
        f"  VOCAL: {meta.get('vocal', '')}",
        f"  LYRIC ENGLISH: {meta.get('lyric', '')}",
        f"  SLIPS BETWEEN PHRASES: {meta.get('slips', '')}",
        f"  ANTI: {meta.get('anti', '')}",
        "  HARD: English lyrics standard spelling; accent in rhythm/grammar/voice line — never comedy phonetics.",
    ])


def accent_sing_block(
    intent: str = "",
    *,
    accent_mode: str = "auto",
    accent_partner: str = "off",
) -> str:
    """Lead (+ partner if set) accent-specific sing colour. Empty if no usable accent."""
    lead = resolve_sing_accent_key(accent_mode, intent)
    partner_raw = (accent_partner or "").strip().lower()
    partner = ""
    if partner_raw not in ("", "off", "none", "same", "same as lead", "auto"):
        partner = resolve_sing_accent_key(accent_partner, "")
    elif partner_raw == "auto":
        # partner auto without separate intent signal — skip unless lead set and pair context
        partner = ""

    if not lead and not partner:
        # Intent may still name an accent while UI is Auto
        lead = resolve_sing_accent_key("auto", intent)
    if not lead and not partner:
        return ""

    lines = [
        "",
        "━━ ACCENT × SING (FULL COLOUR — DO NOT DROP WHEN THEY SING) ━━",
        "Spoken accent rules still apply. Sung lines keep the SAME accent family.",
        "Most lyrics = accented ENGLISH. Native slips = seasoning between phrases, not the whole song.",
    ]
    if lead:
        lines.append(format_accent_sing_colour(lead, role="LEAD"))
    if partner and partner != lead:
        lines.append(format_accent_sing_colour(partner, role="PARTNER"))
        lines.append(
            "PARTNER vs LEAD: keep two distinct vocal colours — never blend mid-phrase. "
            "Label who sings when both perform."
        )
    elif partner and partner == lead:
        lines.append(
            "PARTNER shares the same accent family as lead — still keep who-is-who clear on each sung line."
        )
    return "\n".join(lines)


def _music_vocal_colour(
    music_key: str = "",
    music_text: str = "",
    *,
    background: bool = False,
) -> str:
    blob = f"{music_key or ''} {music_text or ''}".lower()
    if not blob.strip() or blob.startswith("none"):
        return (
            "MUSIC: no preset — diegetic voice / a cappella is fine; "
            "still write sings (…) with short lyrics or hums."
        )
    if background or "background" in blob or "quiet under" in blob:
        return (
            "MUSIC (BACKGROUND): score stays quiet under. Sing soft/close — croon, not belt. "
            "Never 'shouts the chorus over the bass'. Prefer soft plant + soft sung phrases."
        )
    # Genre tips
    if any(x in blob for x in ("r&b", "soul", "rnb")):
        return "MUSIC COLOUR: R&B pocket — breathy hooks, optional *ooh* runs, confident half-sung lines."
    if any(x in blob for x in ("hip-hop", "hip hop", "rap", "808")):
        return "MUSIC COLOUR: hip-hop — melodic hooks or short rap bars on the beat; chest on kicks."
    if any(x in blob for x in ("electronic", "edm", "techno")):
        return "MUSIC COLOUR: EDM — short chant hooks on drops; call over the kick if MIX."
    if any(x in blob for x in ("reggae", "dancehall")):
        return "MUSIC COLOUR: reggae/dancehall — toast or singjay fragments over the riddim."
    if any(x in blob for x in ("rock", "metal", "classic rock")):
        return "MUSIC COLOUR: rock — gritty short chorus lines; jaw/chest work visible."
    if any(x in blob for x in ("classical", "orchestral")):
        return "MUSIC COLOUR: classical — long tones, controlled breath, theatrical posture."
    if any(x in blob for x in ("country",)):
        return "MUSIC COLOUR: country — storytelling croon, easy vowels, grounded stance."
    if any(x in blob for x in ("pop",)):
        return "MUSIC COLOUR: pop — chorus-facing short hooks; smile/eye optional on the line."
    return "MUSIC COLOUR: land sung phrases with the pulse; keep lyrics short and complete."


def sing_block(
    intent: str = "",
    scenario: str = "",
    *,
    music_key: str = "",
    music_text: str = "",
    music_background: bool = False,
    dialogue_tier: str = "standard",
    video_style: str = "",
    accent_mode: str = "auto",
    accent_partner: str = "off",
    accent_on: bool = False,  # legacy; ignored if accent_mode passed
    seed: int = 0,
    max_paths: int = 3,
) -> str:
    """System inject for singing. Empty if intent does not ask."""
    if not wants_sing(intent, scenario, video_style=video_style):
        return ""

    silent = (dialogue_tier or "").lower() in ("none", "silent", "off")
    paths = detect_sing_paths(intent, scenario, video_style=video_style, max_paths=max_paths)
    rng = random.Random(int(seed or 0) ^ 0x51C6)
    if paths == ["freestyle_vocal"]:
        extra = rng.choice(["soft_croon", "sing_along", "hum_melody"])
        if extra not in paths:
            paths = ["freestyle_vocal", extra]

    lines = [
        "\n━━ SINGING (active — craft tools) ━━",
        "Intent asked for song/sing/karaoke. Invent short lyrics for THIS scene — do not dodge into only says.",
        "Music alone does not force singing. Quiet BG = soft track volume only; still sings/croons + accent colour.",
        "",
        "Format (one verb — never 'sings says'):",
        '  She sings (soft): "short lyric."   ·   He sings along (warm): "hook."   ·   hums OK wordless',
        "3–12 words per sung line · 2–4 sung moments when length allows · action ↔ sing alternating.",
        "Mouth busy → hum only. No fake phonetics. Show lips/breath/jaw — not 'sings beautifully'.",
        "",
        "Avoid interchangeable karaoke mush: \"this song so good\" / \"just one more song\" / "
        "\"music feels so right\" / \"dancing through the night\".",
        "Invent lyrics that name a prop or stake (mic, booth, glass, rain…) and carry accent colour when locked.",
    ]

    if silent:
        lines += [
            "",
            "SILENT DIALOGUE TIER IS ON: NO quoted speech and NO quoted lyrics.",
            "Use wordless vocal only: hums, soft ooh, breath melody, mouth shapes without words.",
            "Accent colour still affects *how* the hum/voice is described (rhythm/weight) — no spoken slips.",
            "Do not invent karaoke lines until dialogue is Standard/Talkative.",
        ]
    else:
        lines += [
            "",
            "SPOKEN vs SUNG: you MAY still use says (…) for talk beats, but if intent wants a song,",
            "at least half of the vocal moments should be sings/croons/sings along — not all says.",
            "When ACCENT is locked: ≥2 sung lines must be unmistakably that accent "
            "(not plain US pop with one token foreign word).",
        ]

    # Full per-accent sing colour (all 39 keys when resolved)
    _acc = accent_sing_block(
        intent,
        accent_mode=accent_mode or ("auto" if accent_on else "off"),
        accent_partner=accent_partner or "off",
    )
    if _acc:
        lines.append(_acc)
    elif accent_on:
        lines += [
            "",
            "ACCENT + SING: keep accent grammar/rhythm on sung English; "
            "native ad-libs between phrases only.",
        ]

    lines.append("\nACTIVE SING PATHS:")
    for k in paths:
        meta = SING_PATHS.get(k) or {}
        lines.append(f"【{meta.get('name', k)}】")
        lines.append(f"  {meta.get('doctrine', '')}")

    lines.append("\n" + _music_vocal_colour(music_key, music_text, background=music_background))

    vs = (video_style or "").lower()
    if "music-video" in vs or "music video" in vs:
        lines.append(
            "VIDEO STYLE is Music-video: vocal moments are part of the performance spine — "
            "plant track early, face camera on hooks when it fits."
        )

    lines.append(
        "\nSING LAYOUT: section = body setup → one sung phrase OR hum → optional short action. "
        "Do not stack a full verse in one paragraph.\n"
    )
    return "\n".join(lines)


def sing_remember_line(
    intent: str = "",
    scenario: str = "",
    *,
    video_style: str = "",
    dialogue_tier: str = "standard",
    accent_mode: str = "auto",
    accent_partner: str = "off",
) -> str:
    if not wants_sing(intent, scenario, video_style=video_style):
        return ""
    silent = (dialogue_tier or "").lower() in ("none", "silent", "off")
    lead = resolve_sing_accent_key(accent_mode, intent)
    bits = []
    if silent:
        bits.append("wordless hum/melody only (Silent; no quoted lyrics)")
    else:
        bits.append("sings/croons with short lyrics (not only says)")
    if lead:
        bits.append(f"LEAD sing colour={lead}")
    p = resolve_sing_accent_key(accent_partner, "") if (accent_partner or "").lower() not in (
        "", "off", "none", "same", "same as lead", "auto"
    ) else ""
    if p:
        bits.append(f"PARTNER sing colour={p}")
    bits.append("mouth free; LTX-safe short phrases")
    return "• SING: " + "; ".join(bits)
