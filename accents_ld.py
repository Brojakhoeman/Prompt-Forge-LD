# -*- coding: utf-8 -*-
"""
accents_ld.py — L1-transfer accent system for LTX shot scripts
================================================================
English with a foreign/regional accent + OCCASIONAL native slips.

Rules of the road (Grok bar):
  • Accent lives in GRAMMAR + RHYTHM + VOICE LINE — not phonetic garble.
  • LTX prints text literally: never "ze"/"zis"/"wery" comedy spelling.
  • Each language has ~15 AD-LIBS (mini phrases/tags) seeded into the clip —
    model sprinkles them naturally; user does not need to type "ja?" / "seen?" into Intent.
  • Native words are CONTEXT SLIPS + AD-LIBS (agreement, urge, surprise, intimate) —
    not the same particle on every line ("ja?" spam is a failure).
  • SHIBBOLETHS (accent_shibboleths.json): English target words that show L1 colour
    when spoken correctly — plant 1–3 as props/stakes. NEVER phonetic garble (no "ze"/"wery").
  • Never reuse the same ad-lib/slip or the same example line twice in one clip.
  • First section: voice line. First spoken line: optional varied opener.
  • Most lines are accented ENGLISH; ad-libs are seasoning, not wallpaper.
  • T2V: CHARACTER_PROFILES seeds phenotype (hair/skin/build) per accent+gender so
    voice and face match (Scottish freckles ≠ Korean East-Asian features). Seed rotates.
  • I2V: start image wins on look — profiles do not override the still.

UI keys (force) map to ACCENTS keys via resolve_accent_key / aliases.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
#  ENGLISH SHIBBOLETHS (L1-hard words — correct spelling, plant as props)
#  Loaded from accent_shibboleths.json next to this module.
#  Keys match ACCENTS keys; unused keys are ignored.
# ─────────────────────────────────────────────────────────────────────────────

_SHIB_PATH = Path(__file__).resolve().parent / "accent_shibboleths.json"
_SHIBBOLETHS: dict[str, list[str]] = {}


def _load_shibboleths() -> dict[str, list[str]]:
    global _SHIBBOLETHS
    if _SHIBBOLETHS:
        return _SHIBBOLETHS
    out: dict[str, list[str]] = {}
    if _SHIB_PATH.is_file():
        try:
            raw = json.loads(_SHIB_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                for k, words in raw.items():
                    key = str(k).strip().lower()
                    if not key or not isinstance(words, list):
                        continue
                    cleaned = []
                    seen = set()
                    for w in words:
                        s = re.sub(r"\s+", " ", str(w or "").strip())
                        if not s or len(s) > 40:
                            continue
                        kl = s.lower()
                        if kl in seen:
                            continue
                        seen.add(kl)
                        cleaned.append(s)
                    if cleaned:
                        out[key] = cleaned
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            out = {}
    _SHIBBOLETHS = out
    return _SHIBBOLETHS


def get_shibboleths(key: str, seed: int = 0, n: int = 6) -> list[str]:
    """Seeded subset of English shibboleth words for this accent (max n)."""
    bank = _load_shibboleths().get((key or "").strip().lower()) or []
    if not bank:
        return []
    import random
    n = max(3, min(int(n or 6), 8, len(bank)))
    stable = sum(ord(c) for c in (key or "x")) & 0xFFFF
    rng = random.Random(int(seed or 0) ^ stable ^ 0x51B5)
    pool = list(bank)
    rng.shuffle(pool)
    return pool[:n]


# ─────────────────────────────────────────────────────────────────────────────
#  ACCENT BANK
#  Each entry:
#    name, triggers, acoustic, prosody, grammar[]
#    openers[]           — rotate; first spoken line MAY open with one
#    slips: {context: [words]}  — pick by moment, not random spam
#    examples: {register: [lines]}  — shape guides, not paste-all
#    anti[]              — explicit failure modes for this accent
# ─────────────────────────────────────────────────────────────────────────────

ACCENTS = {
    # ═══ EAST ASIA ═══════════════════════════════════════════════════════════
    "korean": {
        "name": "Korean",
        "triggers": [r"korean?", r"seoul", r"busan", r"k-?pop"],
        "acoustic": "syllable-timed, soft, slightly nasal, even weight per syllable, rising ends",
        "prosody": "short beats; soft rises; never long fluent American runs",
        "grammar": [
            "drop a/the often",
            "drop do/does — \"you like this?\"",
            "topic-first — \"me, I don't know\"",
            "soft tags: okay? / right?",
        ],
        "openers": ["안녕", "야", "있잖아"],
        "slips": {
            "agree": ["응", "네", "좋아"],
            "urge": ["더", "이리 와", "빨리"],
            "surprise": ["어머", "아이고", "진짜?"],
            "intimate": ["자기야", "오빠", "언니"],
            "soft": ["잠깐", "조금만"],
        },
        "examples": {
            "casual": [
                "야… you hear that?",
                "here so quiet… I like",
                "wait… 잠깐… look at me",
            ],
            "heated": [
                "더… more… like that",
                "don't stop… 진짜… so good",
                "이리 와… closer… now",
            ],
            "intimate": [
                "자기야… slow… for me",
                "좋아… just there",
                "you make me crazy… 미치겠어",
            ],
        },
        "anti": [
            "do NOT end every line with 진짜 or 자기야",
            "do NOT paste the same opener twice",
        ],
    },
    "japanese": {
        "name": "Japanese",
        "triggers": [r"japan(?:ese)?", r"tokyo", r"osaka", r"kyoto"],
        "acoustic": "mora-timed, crisp, light, rising soft ends, precise consonants",
        "prosody": "even short units; soft …; polite or breathy heat without American slang flood",
        "grammar": [
            "drop articles",
            "optional soft tag ne? / yo at ends — not every line",
            "topic first — \"this, I like\"",
            "short clauses",
        ],
        "openers": ["ねえ", "あの", "ちょっと"],
        "slips": {
            "agree": ["はい", "うん", "そう"],
            "urge": ["もっと", "来て", "だめ"],
            "surprise": ["えっ", "すごい", "本当に"],
            "intimate": ["あなた", "好き", "気持ちいい"],
            "soft": ["ちょっと", "待って"],
        },
        "examples": {
            "casual": [
                "ねえ… you watching?",
                "ちょっと… wait… this light",
                "so quiet… I like, ne?",
            ],
            "heated": [
                "もっと… more… yes",
                "だめ… don't stop",
                "来て… closer… please",
            ],
            "intimate": [
                "あなた… slow",
                "気持ちいい… right there",
                "好き… so much",
            ],
        },
        "anti": [
            "do NOT put ne? on every line",
            "do NOT spam もっと every beat",
        ],
    },
    "mandarin": {
        "name": "Mandarin Chinese",
        "triggers": [r"chinese", r"mandarin", r"beijing", r"shanghai", r"taiwan(?:ese)?"],
        "acoustic": "staccato, even beats, slight tonal push under English, clear finals",
        "prosody": "short punchy clauses; less linking; no drawl",
        "grammar": [
            "often no plural -s",
            "loose tense — \"yesterday I go\"",
            "drop articles",
            "optional ma? only when asking — rare",
        ],
        "openers": ["哎呀", "喂", "那个"],
        "slips": {
            "agree": ["好", "对", "嗯"],
            "urge": ["快点", "过来", "再来"],
            "surprise": ["真的", "哇", "什么"],
            "intimate": ["亲爱的", "想要", "舒服"],
            "soft": ["等等", "一下"],
        },
        "examples": {
            "casual": [
                "哎呀… this place so loud",
                "you see that? 真的",
                "等等… wait for me",
            ],
            "heated": [
                "快点… more",
                "再来… like that",
                "好… don't stop",
            ],
            "intimate": [
                "想要… closer",
                "舒服… right there",
                "过来… now",
            ],
        },
        "anti": ["do NOT tack 好 onto every line", "no comedy tone spelling"],
    },
    "thai": {
        "name": "Thai",
        "triggers": [r"thai", r"thailand", r"bangkok"],
        "acoustic": "soft, sing-song under English, gentle rises, warm mid pitch",
        "prosody": "melodic short lines; soft …; polite heat",
        "grammar": [
            "drop articles often",
            "simple present for everything",
            "soft particles sparingly",
        ],
        "openers": ["นี่", "เฮ้", "รอ"],
        "slips": {
            "agree": ["ใช่", "ดี", "ครับ", "ค่ะ"],
            "urge": ["มา", "อีก", "เร็ว"],
            "surprise": ["จริงเหรอ", "ว้าว"],
            "intimate": ["ที่รัก", "อยาก", "ดีจัง"],
            "soft": ["นิดหน่อย", "ช้าๆ"],
        },
        "examples": {
            "casual": ["นี่… you cold?", "here nice… I like", "รอ… wait little"],
            "heated": ["อีก… more", "มา… closer", "ดี… yes like that"],
            "intimate": ["ที่รัก… slow", "อยาก… you", "ดีจัง… don't stop"],
        },
        "anti": ["do not end every line with ครับ/ค่ะ"],
    },
    "vietnamese": {
        "name": "Vietnamese",
        "triggers": [r"vietnam(?:ese)?", r"hanoi", r"saigon", r"ho chi minh"],
        "acoustic": "quick, light, tonal shadow under English, sharp short vowels",
        "prosody": "staccato; short breath groups; rising questions",
        "grammar": [
            "drop articles",
            "simple verbs, little tense",
            "blunt short orders okay",
        ],
        "openers": ["này", "ơi", "thôi"],
        "slips": {
            "agree": ["đúng", "vâng", "ừ"],
            "urge": ["thêm", "lại", "nhanh"],
            "surprise": ["thật à", "ôi"],
            "intimate": ["em", "anh", "muốn"],
            "soft": ["chờ", "chậm"],
        },
        "examples": {
            "casual": ["này… you hear?", "ơi… look here", "quiet… I like"],
            "heated": ["thêm… more", "nhanh… yes", "đúng… there"],
            "intimate": ["muốn… you", "chậm… slow", "đừng dừng"],
        },
        "anti": ["no same particle every line"],
    },

    # ═══ ROMANCE ═════════════════════════════════════════════════════════════
    "french": {
        "name": "French",
        "triggers": [r"french", r"france", r"paris", r"lyon", r"marseille", r"québec", r"quebec"],
        "acoustic": "even rhythm, soft consonants, slight uvular R hint in description only, musical stress",
        "prosody": "linked short phrases; … as breath; elegant or heated but not American slang flood",
        "grammar": [
            "occasional article slip is fine but do NOT destroy all grammar",
            "English stays understandable — accent is music + a few slips",
            "rhetorical non? / yes? rare, not every line",
            "prefer full English with French seasoning — not Franglais soup",
        ],
        "openers": ["bon", "alors", "écoute"],
        "slips": {
            "agree": ["oui", "d'accord", "bien sûr"],
            "urge": ["encore", "viens", "plus fort"],
            "surprise": ["putain", "mon dieu", "sérieux?"],
            "intimate": ["chéri", "chérie", "mon amour", "j'ai envie"],
            "soft": ["doucement", "attends"],
        },
        "examples": {
            "casual": [
                "alors… this place is loud, non?",
                "écoute… look at me a second",
                "bon… we leave after this drink",
            ],
            "heated": [
                "encore… like that",
                "viens… closer… now",
                "plus fort… yes",
            ],
            "intimate": [
                "chéri… slow… for me",
                "j'ai envie… of you",
                "doucement… there… oui",
            ],
        },
        "anti": [
            "do NOT put oui/non on every line",
            "do NOT turn every sentence into broken English",
            "English with French accent + occasional French slip — not a French monologue",
        ],
    },
    "spanish_castilian": {
        "name": "Spanish (Spain)",
        "triggers": [r"castilian", r"spain", r"madrid", r"barcelona", r"spaniard"],
        "acoustic": "crisp, forward, clear vowels, lively stress",
        "prosody": "punchy short lines; heat in rhythm; less drawl",
        "grammar": [
            "drop subject pronoun sometimes — \"want more\"",
            "present-tense bias",
            "optional ¿no? rare",
        ],
        "openers": ["mira", "oye", "venga"],
        "slips": {
            "agree": ["sí", "claro", "vale"],
            "urge": ["más", "ven", "ahora"],
            "surprise": ["joder", "hostia", "¿en serio?"],
            "intimate": ["cariño", "quiero", "así"],
            "soft": ["espera", "despacito"],
        },
        "examples": {
            "casual": ["mira… you see her?", "oye… wait", "vale… we go"],
            "heated": ["más… así", "ven… closer", "ahora… don't stop"],
            "intimate": ["cariño… slow", "quiero… you", "así… yes"],
        },
        "anti": ["do not spam vale/sí every beat"],
    },
    "spanish_latin": {
        "name": "Spanish (Latin America)",
        "triggers": [r"latin(?:o|a)?", r"mexican", r"mexico", r"argentina", r"colombia", r"spanish(?!.*spain)"],
        "acoustic": "warm, open vowels, musical stress, softer than Castilian",
        "prosody": "rolling short clauses; heat without harshness",
        "grammar": [
            "drop subjects sometimes",
            "present bias",
            "affectionate tags rare",
        ],
        "openers": ["mira", "oye", "ay"],
        "slips": {
            "agree": ["sí", "claro", "órale"],
            "urge": ["más", "ven", "sigue"],
            "surprise": ["ay dios", "no manches", "¿en serio?"],
            "intimate": ["mi amor", "papi", "mami", "rico"],
            "soft": ["espera", "suave"],
        },
        "examples": {
            "casual": ["mira… that light", "oye… come here", "sí… I hear you"],
            "heated": ["más… sigue", "ven… closer", "así… yes"],
            "intimate": ["mi amor… slow", "rico… right there", "sigue… don't stop"],
        },
        "anti": ["no mami/papi every line unless the scene is that voice"],
    },
    "italian": {
        "name": "Italian",
        "triggers": [r"italian", r"italy", r"rome", r"milan", r"naples"],
        "acoustic": "open vowels, musical stress, lively cadence",
        "prosody": "sing-song English; short bursts; expressive …",
        "grammar": [
            "drop articles sometimes",
            "hands-in-voice energy without comedy",
            "blunt present tense",
        ],
        "openers": ["allora", "dai", "senti"],
        "slips": {
            "agree": ["sì", "va bene", "certo"],
            "urge": ["ancora", "vieni", "più"],
            "surprise": ["mamma mia", "dio", "davvero?"],
            "intimate": ["amore", "tesoro", "così"],
            "soft": ["piano", "aspetta"],
        },
        "examples": {
            "casual": ["allora… we stay?", "senti… look at me", "dai… one more drink"],
            "heated": ["ancora… così", "vieni… closer", "più… yes"],
            "intimate": ["amore… slow", "così… perfect", "piano… there"],
        },
        "anti": ["do NOT say mamma mia every line", "no cartoon Italian"],
    },
    "portuguese": {
        "name": "Portuguese",
        "triggers": [r"portuguese", r"portugal", r"brazil(?:ian)?", r"rio", r"lisbon", r"lisboa"],
        "acoustic": "soft, musical, nasal hint, warm mid tone",
        "prosody": "rolling; soft …; sensual without vibe-word spam on the BODY",
        "grammar": [
            "drop articles sometimes",
            "simple present",
            "affectionate slips sparingly",
        ],
        "openers": ["então", "olha", "vai"],
        "slips": {
            "agree": ["sim", "tá", "claro"],
            "urge": ["mais", "vem", "continua"],
            "surprise": ["nossa", "meu deus", "sério?"],
            "intimate": ["amor", "querido", "assim"],
            "soft": ["espera", "devagar"],
        },
        "examples": {
            "casual": ["olha… this song", "então… we go?", "sim… I hear"],
            "heated": ["mais… assim", "vem… closer", "continua… yes"],
            "intimate": ["amor… slow", "assim… right there", "devagar… for me"],
        },
        "anti": ["no nossa on every beat"],
    },

    # ═══ GERMANIC ════════════════════════════════════════════════════════════
    "german": {
        "name": "German",
        "triggers": [r"german", r"germany", r"berlin", r"munich", r"hamburg", r"deutsch"],
        "acoustic": "harder consonants, clear ends, flat-to-firm stress, less soft American melody",
        "prosody": "blunt short clauses; firm …; no sing-song",
        "grammar": [
            "can drop articles sometimes — not every noun",
            "verb can sit later in feel — keep English clear",
            "compound bluntness — \"come here now\"",
            "ja/nein are rare SLIPS — never line-ending punctuation",
        ],
        "openers": ["also", "na", "hör mal", "wart"],
        "slips": {
            "agree": ["genau", "klar", "stimmt", "ja"],  # ja last — prefer genau/klar
            "urge": ["mehr", "komm", "jetzt", "weiter", "nochmal"],
            "surprise": ["scheiße", "was", "echt?", "unglaublich"],
            "intimate": ["schatz", "liebling", "bitte"],
            "soft": ["warte", "langsam", "ruhig"],
        },
        "scene_bits": [
            "also… this place is too loud",
            "hör mal… look at me",
            "genau… like that",
            "warte… not so fast",
            "komm her… now",
            "mehr… keep that",
            "langsam… for me",
            "nochmal… there",
            "klar… we stay",
            "scheiße… already?",
            "weiter… don't stop",
            "ruhig… breathe",
            "stimmt… perfect",
            "jetzt… closer",
            "schatz… slow",
        ],
        "examples": {
            "casual": [
                "also… this bar is too loud",
                "hör mal… look at me",
                "na… we leave after this?",
                "klar… I see you",
            ],
            "heated": [
                "mehr… just like that",
                "komm… closer… now",
                "weiter… don't stop",
                "jetzt… hold still",
            ],
            "intimate": [
                "schatz… slow",
                "nochmal… there",
                "langsam… right there",
                "bitte… stay",
            ],
        },
        "anti": [
            "NEVER end most lines with ja / ja?",
            "NEVER \"how are you ja\" / \"you like this ja\" / \"yes ja\" spam",
            "ja is a rare agreement slip (prefer genau / klar / stimmt), not punctuation",
            "no cartoon hard-R spelling of English words",
        ],
    },
    "dutch": {
        "name": "Dutch",
        "triggers": [r"dutch", r"netherlands", r"amsterdam", r"holland"],
        "acoustic": "flat, clear, slightly hard g-feel in description only, direct",
        "prosody": "straight short lines; dry heat",
        "grammar": [
            "direct word order",
            "drop fluff words",
            "blunt questions",
        ],
        "openers": ["nou", "hé", "kijk"],
        "slips": {
            "agree": ["ja", "oke", "tuurlijk"],
            "urge": ["meer", "kom", "door"],
            "surprise": ["shit", "echt?", "godver"],
            "intimate": ["schat", "lief", "zo"],
            "soft": ["wacht", "rustig"],
        },
        "examples": {
            "casual": ["nou… busy here", "kijk… that way", "oke… we go"],
            "heated": ["meer… zo", "kom… closer", "door… yes"],
            "intimate": ["schat… slow", "zo… perfect", "niet stoppen"],
        },
        "anti": ["no ja on every line"],
    },
    "swedish": {
        "name": "Swedish",
        "triggers": [r"swedish", r"sweden", r"stockholm"],
        "acoustic": "sing-song pitch melody under English, soft consonants",
        "prosody": "melodic rises; gentle …; light",
        "grammar": ["drop some articles", "simple present", "soft tags rare"],
        "openers": ["hej", "alltså", "vänta"],
        "slips": {
            "agree": ["ja", "okej", "absolut"],
            "urge": ["mer", "kom", "igen"],
            "surprise": ["fan", "herregud", "allvarligt?"],
            "intimate": ["älskling", "så", "nära"],
            "soft": ["sakta", "vänta"],
        },
        "examples": {
            "casual": ["hej… you cold?", "alltså… this song", "vänta… one second"],
            "heated": ["mer… så", "kom… closer", "igen… yes"],
            "intimate": ["älskling… slow", "så… there", "nära… stay"],
        },
        "anti": ["no melodic comedy misspelling"],
    },
    "norwegian": {
        "name": "Norwegian",
        "triggers": [r"norwegian", r"norway", r"oslo", r"bergen"],
        "acoustic": "sing-song Nordic melody, soft but clear",
        "prosody": "light rises; short phrases",
        "grammar": ["simple English", "drop fluff", "soft bluntness"],
        "openers": ["hei", "altså", "vent"],
        "slips": {
            "agree": ["ja", "greit", "selvfølgelig"],
            "urge": ["mer", "kom", "igjen"],
            "surprise": ["faen", "herregud"],
            "intimate": ["elskling", "sånn", "nærmere"],
            "soft": ["sakte", "vent"],
        },
        "examples": {
            "casual": ["hei… look", "vent… wait", "greit… we go"],
            "heated": ["mer… sånn", "kom… closer", "igjen… yes"],
            "intimate": ["elskling… slow", "sånn… there", "nærmere… stay"],
        },
        "anti": ["no same particle spam"],
    },

    # ═══ SLAVIC ══════════════════════════════════════════════════════════════
    "russian": {
        "name": "Russian",
        "triggers": [r"russian?", r"moscow", r"slav(?:ic)?", r"ukrainian?", r"kiev", r"kyiv"],
        "acoustic": "hard consonants, clipped ends, heavy stress, lower pitch, no soft US drawl",
        "prosody": "short blunt clauses; … punches; never long fluent American sentences",
        "grammar": [
            "drop a/the often",
            "drop is/are often — \"you so tight\" / \"is good\"",
            "short 3–8 word lines",
            "blunt orders okay",
        ],
        "openers": ["ну", "слушай", "давай"],
        "slips": {
            "agree": ["да", "хорошо", "конечно"],
            "urge": ["давай", "ещё", "сильнее", "быстрее"],
            "surprise": ["блять", "боже", "что?"],
            "intimate": ["милый", "милая", "хочу", "ещё"],
            "soft": ["подожди", "тише"],
        },
        "examples": {
            "casual": [
                "ну… this place too loud",
                "слушай… look at me",
                "хорошо… we go after",
            ],
            "heated": [
                "давай… deeper… like this",
                "ещё… more… yes",
                "сильнее… don't stop",
            ],
            "intimate": [
                "милый… slow… for me",
                "хочу… you… now",
                "боже… right there",
            ],
        },
        "anti": [
            "one native word in the whole clip is a FAILURE",
            "do NOT only bolt милый onto fluent American lines",
            "do NOT use the same opener every spoken line",
        ],
    },
    "polish": {
        "name": "Polish",
        "triggers": [r"polish", r"poland", r"warsaw", r"krakow", r"kraków"],
        "acoustic": "consonant-heavy, firm, clear stress",
        "prosody": "clipped; firm …; direct",
        "grammar": ["drop articles often", "blunt present", "short clauses"],
        "openers": ["no", "słuchaj", "czekaj"],
        "slips": {
            "agree": ["tak", "dobrze", "jasne"],
            "urge": ["więcej", "chodź", "dalej"],
            "surprise": ["kurwa", "boże", "serio?"],
            "intimate": ["kochanie", "chcę", "tak"],
            "soft": ["wolniej", "czekaj"],
        },
        "examples": {
            "casual": ["słuchaj… look", "no… we stay?", "dobrze… okay"],
            "heated": ["więcej… tak", "chodź… closer", "dalej… yes"],
            "intimate": ["kochanie… slow", "chcę… you", "tak… there"],
        },
        "anti": ["no kurwa every line"],
    },
    "czech": {
        "name": "Czech",
        "triggers": [r"czech", r"prague", r"czechia"],
        "acoustic": "flat-clear, firm consonants, central European cadence",
        "prosody": "even; short; dry heat",
        "grammar": ["drop articles", "simple present", "blunt"],
        "openers": ["no", "hele", "počkej"],
        "slips": {
            "agree": ["ano", "jo", "dobře"],
            "urge": ["víc", "pojď", "ještě"],
            "surprise": ["do prdele", "bože"],
            "intimate": ["miláčku", "chci", "tak"],
            "soft": ["pomalu", "počkej"],
        },
        "examples": {
            "casual": ["hele… look", "no… quiet here", "dobře… we go"],
            "heated": ["víc… tak", "pojď… closer", "ještě… more"],
            "intimate": ["miláčku… slow", "chci… you", "pomalu… there"],
        },
        "anti": ["no same slip spam"],
    },

    # ═══ OTHER WORLD ═════════════════════════════════════════════════════════
    "greek": {
        "name": "Greek",
        "triggers": [r"greek", r"greece", r"athens"],
        "acoustic": "warm, open, Mediterranean rhythm",
        "prosody": "musical short bursts",
        "grammar": ["drop articles sometimes", "present bias"],
        "openers": ["ελα", "άκου", "λοιπόν"],
        "slips": {
            "agree": ["ναι", "εντάξει", "σίγουρα"],
            "urge": ["ακόμα", "έλα", "πιο"],
            "surprise": ["θεέ μου", "σοβαρά;"],
            "intimate": ["αγάπη", "θέλω", "έτσι"],
            "soft": ["σιγά", "περίμενε"],
        },
        "examples": {
            "casual": ["άκου… this song", "λοιπόν… we stay?", "ναι… I hear"],
            "heated": ["ακόμα… έτσι", "έλα… closer", "πιο… more"],
            "intimate": ["αγάπη… slow", "θέλω… you", "σιγά… there"],
        },
        "anti": ["no one-word spam"],
    },
    "arabic": {
        "name": "Arabic",
        "triggers": [r"arabic", r"arab", r"egypt(?:ian)?", r"lebanon|lebanese", r"morocco|moroccan", r"dubai", r"gulf"],
        "acoustic": "rich pharyngeal colour in description, warm weight, clear stress",
        "prosody": "weighty short lines; emphatic …",
        "grammar": ["drop articles sometimes", "present bias", "blunt affection"],
        "openers": ["يا", "انظر", "تعال"],
        "slips": {
            "agree": ["نعم", "أيوة", "تمام"],
            "urge": ["יותר", "יותר", "تعالي", "كمان"],
            "surprise": ["يا الله", "والله?"],
            "intimate": ["حبيبي", "حبيبتي", "أريد"],
            "soft": ["بشويش", "استنى"],
        },
        "examples": {
            "casual": ["انظر… look there", "تعال… here", "تمام… okay"],
            "heated": ["كمان… more", "تعالي… closer", "نعم… like that"],
            "intimate": ["حبيبي… slow", "أريد… you", "بشويش… there"],
        },
        "anti": ["do not put حبيبي on every line", "mix English + rare slips"],
    },
    "hebrew": {
        "name": "Hebrew",
        "triggers": [r"hebrew", r"israeli?", r"tel aviv", r"jerusalem"],
        "acoustic": "direct, dry, clear stress, modern urban edge",
        "prosody": "blunt short lines; little fluff",
        "grammar": ["drop fluff", "present bias", "direct questions"],
        "openers": ["טוב", "תשמע", "בואי"],
        "slips": {
            "agree": ["כן", "בסדר", "יאללה"],
            "urge": ["עוד", "בואי", "יותר"],
            "surprise": ["אלוהים", "ברצינות?"],
            "intimate": ["מתוק", "רוצה", "ככה"],
            "soft": ["לאט", "חכי"],
        },
        "examples": {
            "casual": ["תשמע… look", "טוב… we go?", "כן… I got it"],
            "heated": ["עוד… more", "בואי… closer", "יאללה… now"],
            "intimate": ["מתוק… slow", "רוצה… you", "ככה… yes"],
        },
        "anti": ["no יאללה every line"],
    },
    "swahili": {
        "name": "Swahili / East African",
        "triggers": [
            r"swahili", r"kenya|kenyan", r"tanzania|tanzanian", r"nairobi",
            r"east african", r"mombasa", r"dar es salaam", r"kampala", r"uganda",
        ],
        "acoustic": "open vowels, rhythmic warm East African English, soft bounce",
        "prosody": "even musical English; short friendly phrases; unhurried heat",
        "grammar": [
            "clear English with East African rhythm",
            "simple present; drop fluff words sometimes",
            "sawa / poa / polepole as rare slips — not every line",
        ],
        "openers": ["sasa", "angalia", "njoo", "eh"],
        "slips": {
            "agree": ["ndiyo", "sawa", "poa", "yes"],
            "urge": ["zaidi", "njoo", "tena", "more"],
            "surprise": ["lo", "kweli?", "ah?"],
            "intimate": ["mpenzi", "nataka", "sweetie"],
            "soft": ["polepole", "ngoja", "slow"],
        },
        "scene_bits": [
            "sasa… you ready?",
            "angalia… that way",
            "sawa… okay",
            "poa… like that",
            "njoo… closer",
            "polepole… slow",
            "zaidi… more",
            "mpenzi… stay",
            "ngoja… wait",
            "tena… again",
            "kweli… already?",
            "eh… look at me",
            "ndiyo… right there",
            "nataka… you",
            "slow… for me",
        ],
        "examples": {
            "casual": [
                "sasa… you ready?",
                "angalia… that way",
                "sawa… we go after",
                "eh… this place is loud",
            ],
            "heated": [
                "zaidi… more",
                "njoo… closer",
                "tena… yes",
                "more… like that",
            ],
            "intimate": [
                "mpenzi… slow",
                "nataka… you",
                "polepole… there",
                "sawa… stay",
            ],
        },
        "anti": ["no sawa / poa spam every line", "English first; Swahili slips are seasoning"],
    },
    "filipino_english": {
        "name": "Filipino English",
        "triggers": [
            r"filipino", r"philippines", r"tagalog", r"manila", r"pinoy", r"filipina",
        ],
        "acoustic": "clear syllable English, light Tagalog colour, warm friendly stress",
        "prosody": "even short lines; soft rises; polite then heated",
        "grammar": [
            "clear English; occasional Tagalog slips",
            "present simple; light article drop rare",
            "no full Tagalog monologue",
        ],
        "openers": ["uy", "teh", "wait", "hoy"],
        "slips": {
            "agree": ["oo", "sige", "okay", "yes"],
            "urge": ["more", "halika", "sige na", "again"],
            "surprise": ["ay", "grabe", "talo?"],
            "intimate": ["mahal", "baby", "sinta"],
            "soft": ["dahan-dahan", "wait", "sandali"],
        },
        "scene_bits": [
            "uy… look at me",
            "sige… like that",
            "wait… sandali",
            "halika… closer",
            "oo… yes",
            "dahan-dahan… slow",
            "baby… stay",
            "grabe… already?",
            "more… again",
            "sige na… now",
            "mahal… for me",
            "okay… right there",
            "hoy… come here",
            "ay… so good",
            "sinta… easy",
        ],
        "examples": {
            "casual": [
                "uy… bit loud in here",
                "teh… look at me",
                "wait… sandali lang",
                "okay… we go?",
            ],
            "heated": [
                "more… just like that",
                "halika… closer… now",
                "sige na… don't stop",
                "again… yes",
            ],
            "intimate": [
                "mahal… slow",
                "dahan-dahan… there",
                "baby… stay",
                "sinta… for me",
            ],
        },
        "anti": [
            "do NOT end every line with sige / po",
            "no full Tagalog walls",
            "English carrier; Tagalog seasoning",
        ],
    },
    "new_zealand": {
        "name": "New Zealand / Kiwi",
        "triggers": [r"new zealand", r"kiwi", r"auckland", r"wellington", r"nz\b"],
        "acoustic": "raised vowel feel in description, laid-back, soft ends",
        "prosody": "understated short lines; dry humour; chill heat",
        "grammar": [
            "clear English with Kiwi cadence",
            "yeah nah / sweet as rare slips",
            "no full phonetic Kiwi wall",
        ],
        "openers": ["yeah", "hey", "sweet", "choice"],
        "slips": {
            "agree": ["yeah", "sweet as", "too right", "keen"],
            "urge": ["more", "c'mon", "again", "go on"],
            "surprise": ["bro", "shit", "you're joking"],
            "intimate": ["love", "babe", "darl"],
            "soft": ["easy", "slow", "chill"],
        },
        "scene_bits": [
            "yeah… bit loud eh",
            "sweet as… like that",
            "hey… look at me",
            "easy… slow",
            "c'mon… closer",
            "keen… stay",
            "chill… right there",
            "love… for me",
            "again… yeah",
            "go on… more",
            "bro… already?",
            "choice… perfect",
            "too right… keep going",
            "babe… stay",
            "yeah nah… wait",
        ],
        "examples": {
            "casual": [
                "yeah… bit loud in here",
                "hey… look at me",
                "sweet as… we good?",
                "choice… this light",
            ],
            "heated": [
                "more… just like that",
                "c'mon… closer",
                "again… yeah",
                "go on… don't stop",
            ],
            "intimate": [
                "love… slow",
                "easy… right there",
                "babe… stay",
                "chill… for me",
            ],
        },
        "anti": [
            "sweet as / yeah nah not every line",
            "no full phonetic Kiwi respelling",
        ],
    },
    "nigerian_english": {
        "name": "Nigerian English",
        "triggers": [r"nigerian", r"nigeria", r"lagos", r"naija", r"yoruba", r"igbo", r"hausa", r"pidgin"],
        "acoustic": "rhythmic West African English, clear stress, lively bounce",
        "prosody": "punchy; musical; direct address; warm energy",
        "grammar": [
            "Nigerian English patterns — present where native might use progressive",
            "emphatic now / sha / o sparingly as slips — never every line",
            "keep intelligible English; light pidgin colour only (dey/abeg rare)",
            "no cartoon phonetic spelling",
        ],
        "openers": ["abeg", "see", "oya", "wetin"],
        "slips": {
            "agree": ["yes now", "na so", "correct", "e correct"],
            "urge": ["more", "come", "oya", "sharp sharp"],
            "surprise": ["chai", "god o", "you serious?", "ah ah"],
            "intimate": ["baby", "my guy", "my dear", "softly"],
            "soft": ["wait o", "slow", "easy now", "calm down"],
        },
        "scene_bits": [
            "abeg… look at me",
            "see… this place dey loud",
            "oya… we move",
            "yes now… like that",
            "wait o… not so fast",
            "chai… already?",
            "come… closer",
            "softly… stay",
            "na so… perfect",
            "sharp sharp… now",
            "my dear… slow",
            "easy now… hold",
            "god o… that good",
            "correct… right there",
            "calm down… for me",
        ],
        "examples": {
            "casual": [
                "see… this place dey loud",
                "abeg… look at me a second",
                "oya… we move before it close",
                "wetin… you still standing?",
            ],
            "heated": [
                "more… like that",
                "come… closer… now",
                "yes now… don't stop",
                "oya… keep that",
            ],
            "intimate": [
                "baby… slow",
                "softly… there",
                "abeg… stay",
                "my dear… right there",
            ],
        },
        "anti": [
            "not every line needs o / sha / abeg",
            "no mock accent spelling (no full phonetic pidgin walls)",
            "most words = clear English; Naija is seasoning",
        ],
    },
    "ghanaian_english": {
        "name": "Ghanaian English",
        "triggers": [r"ghanaian", r"ghana", r"accra", r"kumasi", r"twi"],
        "acoustic": "warm West African English, slightly softer than Naija, clear ends, friendly bounce",
        "prosody": "melodic short lines; polite heat; unhurried then punchy",
        "grammar": [
            "clear English with Ghanaian rhythm",
            "please / paa / paa? as rare emphasis — not every line",
            "present simple often; keep LTX-readable",
        ],
        "openers": ["chale", "eh", "please", "see"],
        "slips": {
            "agree": ["yes", "ei", "paa", "for sure"],
            "urge": ["more", "come", "now", "hurry"],
            "surprise": ["eh!", "walahi", "you serious?"],
            "intimate": ["baby", "dear", "my love"],
            "soft": ["softly", "wait", "small small"],
        },
        "scene_bits": [
            "chale… look at me",
            "eh… this place is loud",
            "small small… slow",
            "for sure… like that",
            "come… closer",
            "wait… not so fast",
            "paa… that good",
            "baby… stay",
            "hurry… now",
            "ei… already?",
            "softly… right there",
            "please… more",
            "see… the light",
            "my love… easy",
            "yes… keep going",
        ],
        "examples": {
            "casual": [
                "chale… bit loud in here",
                "eh… look at me a second",
                "see… we going?",
                "please… wait small",
            ],
            "heated": [
                "more… just like that",
                "come… closer… now",
                "paa… don't stop",
                "hurry… keep that",
            ],
            "intimate": [
                "baby… slow",
                "small small… there",
                "dear… stay",
                "softly… for me",
            ],
        },
        "anti": [
            "do NOT put chale / paa on every line",
            "no cartoon Ghanaian spelling walls",
            "English first; Ghana colour is seasoning",
        ],
    },
    "south_african_english": {
        "name": "South African English",
        "triggers": [
            r"south african", r"south africa", r"johannesburg", r"cape town",
            r"afrikaans", r"joburg", r"durban", r"braai",
        ],
        "acoustic": "flattened vowels feel in description, clipped, dry warmth",
        "prosody": "dry short lines; understated heat; sharp then soft",
        "grammar": [
            "SA English cadence — blunt and clear",
            "occasional Afrikaans slip (ja / ag / lekker / liefie) — never ja? spam",
            "readable; not full Afrikaans",
        ],
        "openers": ["hey", "ag", "listen", "ja"],
        "slips": {
            "agree": ["ja", "sure", "lekker", "sharp"],
            "urge": ["more", "come", "again", "now-now"],
            "surprise": ["ag no", "shit", "really?", "hells"],
            "intimate": ["liefie", "love", "come here"],
            "soft": ["wait", "softly", "easy"],
        },
        "scene_bits": [
            "hey… look sharp",
            "ag… this noise",
            "lekker… like that",
            "liefie… slow",
            "now-now… closer",
            "ja… stay",
            "easy… right there",
            "sharp… perfect",
            "come… here",
            "wait… not so fast",
            "ag no… already?",
            "softly… for me",
            "more… again",
            "listen… look at me",
            "sure… we good",
        ],
        "examples": {
            "casual": [
                "hey… busy here",
                "ag… this place is loud",
                "listen… look at me",
                "ja… we can go after",
            ],
            "heated": [
                "more… just like that",
                "come… closer",
                "again… ja",
                "now-now… don't stop",
            ],
            "intimate": [
                "liefie… slow",
                "just there… stay",
                "softly… yes",
                "easy… right there",
            ],
        },
        "anti": [
            "ja is not every line's ending",
            "lekker / ag max rare — not wallpaper",
            "no full Afrikaans monologue",
        ],
    },
    "trinidadian": {
        "name": "Trinidadian / Trini",
        "triggers": [
            r"trinidad", r"tobago", r"trini", r"soca", r"carnival",
            r"port of spain", r"caribbean english",
        ],
        "acoustic": "Caribbean melody under clear English, playful bounce, warm ends",
        "prosody": "musical short lines; party-to-intimate swing; not Jamaican rasta same bank",
        "grammar": [
            "clear English with Trini rhythm",
            "present feel sparingly — never full creole walls LTX can't parse",
            "gyul / fuh real / steups as rare slips only",
        ],
        "openers": ["oy", "eh", "listen", "allyuh"],
        "slips": {
            "agree": ["yeah", "fuh real", "true", "alright"],
            "urge": ["more", "come", "again", "doh stop"],
            "surprise": ["eh!", "lord", "you serious?"],
            "intimate": ["gyul", "baby", "darlin'", "sweetness"],
            "soft": ["easy", "slow", "take time"],
        },
        "scene_bits": [
            "oy… look at me",
            "eh… this place too loud",
            "fuh real… like that",
            "easy… slow",
            "come… closer",
            "doh stop… now",
            "baby… stay",
            "true… right there",
            "listen… hold that",
            "sweetness… for me",
            "again… yeah",
            "lord… already?",
            "take time… yes",
            "alright… keep going",
            "gyul… slow",
        ],
        "examples": {
            "casual": [
                "oy… bit loud in here",
                "eh… look at me a second",
                "listen… we going?",
                "fuh real… this light nice",
            ],
            "heated": [
                "more… just like that",
                "come… closer… now",
                "doh stop… yes",
                "again… keep that",
            ],
            "intimate": [
                "baby… slow",
                "gyul… right there",
                "sweetness… stay",
                "easy… for me",
            ],
        },
        "anti": [
            "do NOT spam gyul / fuh real / allyuh every line",
            "not the same as Jamaican rasta — different melody, no irie/mon default",
            "no full creole walls (deh/fi/dem) as the whole script",
        ],
    },
    "indian_english": {
        "name": "Indian English",
        "triggers": [r"indian", r"india", r"hindi", r"mumbai", r"delhi", r"bangalore", r"chennai"],
        "acoustic": "syllable-clear, retroflex hint in description, even tempo",
        "prosody": "precise short clauses; less reduction; formal-to-warm",
        "grammar": [
            "present continuous sometimes where native wouldn't",
            "\"only\" / \"itself\" emphasis sparingly",
            "keep clear Standard-ish English + slips",
        ],
        "openers": ["arey", "dekho", "sun"],
        "slips": {
            "agree": ["haan", "theek hai", "bilkul"],
            "urge": ["aur", "aao", "tez"],
            "surprise": ["arre", "yaar", "sach?"],
            "intimate": ["jaan", "meri jaan", "chahiye"],
            "soft": ["dhire", "ruko"],
        },
        "examples": {
            "casual": ["dekho… that side", "arey… wait na", "theek hai… we go"],
            "heated": ["aur… more", "aao… closer", "haan… like that"],
            "intimate": ["jaan… slow", "dhire… there", "bas… don't stop"],
        },
        "anti": ["no na on every line", "no comedy head-wobble text"],
    },

    # ═══ UK / IRISH / ANZ / US ═══════════════════════════════════════════════
    "cockney": {
        "name": "Cockney (London)",
        "triggers": [r"cockney", r"east end", r"east london", r"working.?class london"],
        "acoustic": "dropped H feel in description, glottal stops described not respelt, lively London",
        "prosody": "quick, cheeky, clipped; rhyming slang RARE (one max if any)",
        "grammar": [
            "ain't / innit sparingly — not every line",
            "me for my sometimes — \"me hands\"",
            "present where careful English would polish",
            "keep readable — no full phonetic respelling",
        ],
        "openers": ["oi", "ere", "right"],
        "slips": {
            "agree": ["yeah", "too right", "innit"],
            "urge": ["c'mon", "more", "go on"],
            "surprise": ["bloody hell", "christ", "you're joking"],
            "intimate": ["love", "darlin'", "sweetheart"],
            "soft": ["easy", "hold up"],
        },
        "examples": {
            "casual": [
                "oi… look at that",
                "right… we moving or what?",
                "ere… come 'ere a sec",
            ],
            "heated": [
                "go on… like that",
                "more… yeah",
                "c'mon… don't you stop",
            ],
            "intimate": [
                "love… slow down",
                "darlin'… right there",
                "that's it… stay",
            ],
        },
        "anti": [
            "do NOT put innit on every line",
            "do NOT write fackin phonetic mess LTX will print",
            "one cheeky tag max every few lines",
        ],
    },
    "scottish": {
        "name": "Scottish",
        "triggers": [r"scottish", r"scotland", r"glasgow", r"edinburgh", r"scot\b"],
        "acoustic": "rolled R feel in description, tighter vowels, firm cadence",
        "prosody": "punchy; dry humour; short firm lines",
        "grammar": [
            "readable English with light Scots seasoning — not a phonetic wall",
            "aye / nae / wee / ken as rare slips — never wallpaper",
            "direct orders and dry understatement over soft pet-names",
            "present tense firm; cut fluff words",
        ],
        "openers": ["right", "here", "listen", "well"],
        "slips": {
            "agree": ["aye", "too right", "sure", "that's pure", "no bother"],
            "urge": ["c'mere", "more", "again", "noo", "keep going"],
            "surprise": ["christ", "you're joking", "fuck me", "pure mental"],
            "intimate": ["love", "darlin'", "pal"],  # hen is RARE — see scene_bits, not every line
            "soft": ["easy", "slow", "steady", "wee bit"],
        },
        # 15 non-repeating scene-seeded bits — pick by moment, never spam one tag
        "scene_bits": [
            "right… look at me",
            "aye… this place is mental",
            "wee bit closer",
            "noo… like that",
            "steady… don't rush",
            "pure good… stay",
            "c'mere a second",
            "that's it… hold",
            "no bother… I've got you",
            "you're joking… already?",
            "easy does it",
            "again… aye",
            "keep that… right there",
            "listen… slow for me",
            "well… you coming?",
        ],
        "examples": {
            "casual": [
                "right… loud in here",
                "here… look at me a second",
                "well… we going or what?",
                "aye… this bar's pure mental",
            ],
            "heated": [
                "more… noo",
                "c'mere… closer",
                "again… like that",
                "keep going… don't you dare stop",
            ],
            "intimate": [
                "easy… right there",
                "steady… for me",
                "that's pure good… stay",
                "love… slow",  # "hen" at most once per clip if ever
            ],
        },
        "anti": [
            "do NOT end every line with aye",
            "do NOT say hen every line — hen is at most ONE rare intimate slip per clip (or skip it)",
            "no full phonetic Scots wall LTX can't parse (no 'ye cannae' spam)",
            "seasoning not a dialect thesis — most words are clear English",
        ],
    },
    "irish": {
        "name": "Irish",
        "triggers": [r"irish", r"ireland", r"dublin", r"cork", r"belfast", r"galway"],
        "acoustic": "lilting melody, soft ends, musical stress",
        "prosody": "rise-fall music; warm; storytelling even in short lines",
        "grammar": [
            "softening tags rare — sure / like sparingly",
            "present lively",
            "keep clear English + Irish music",
        ],
        "openers": ["sure", "here", "listen"],
        "slips": {
            "agree": ["yeah", "sure", "grand"],
            "urge": ["more", "come here", "again"],
            "surprise": ["jesus", "feck", "are you serious?"],
            "intimate": ["love", "pet", "darlin'"],
            "soft": ["easy", "slow"],
        },
        "examples": {
            "casual": [
                "sure… this place is mad",
                "listen… look at me a second",
                "grand… we'll go after",
            ],
            "heated": [
                "more… like that",
                "come here… now",
                "again… yes",
            ],
            "intimate": [
                "love… slow for me",
                "that's it… stay",
                "easy… right there",
            ],
        },
        "anti": [
            "do NOT put sure/like on every line",
            "no stage-Irish caricature",
        ],
    },
    "scouse": {
        "name": "Scouse (Liverpool)",
        "triggers": [r"scouse", r"liverpool", r"scouser"],
        "acoustic": "Liverpool melody, sharp, lively",
        "prosody": "quick musical punch; cheeky",
        "grammar": ["direct", "present", "local tags rare"],
        "openers": ["la", "here", "right"],
        "slips": {
            "agree": ["yeah", "sound", "too right"],
            "urge": ["more", "c'mon", "go on"],
            "surprise": ["calm down", "you're joking"],
            "intimate": ["love", "la", "darlin'"],
            "soft": ["easy", "hold on"],
        },
        "examples": {
            "casual": ["here… look la", "right… we off?", "sound… okay"],
            "heated": ["more… go on", "c'mon… closer", "yeah… like that"],
            "intimate": ["love… slow", "that's it… stay", "easy… there"],
        },
        "anti": ["la is not every line"],
    },
    "geordie": {
        "name": "Geordie (Newcastle)",
        "triggers": [r"geordie", r"newcastle", r"toon"],
        "acoustic": "North-East bounce, firm, warm",
        "prosody": "bouncy short lines",
        "grammar": ["direct", "pet as rare slip", "present"],
        "openers": ["howay", "here", "man"],
        "slips": {
            "agree": ["aye", "yeah", "why aye"],
            "urge": ["more", "howay", "again"],
            "surprise": ["bloody hell", "christ"],
            "intimate": ["pet", "love", "hinny"],
            "soft": ["easy", "slow"],
        },
        "examples": {
            "casual": ["here… look man", "howay… we going?", "aye… alright"],
            "heated": ["more… howay", "again… like that", "aye… don't stop"],
            "intimate": ["pet… slow", "that's it… stay", "easy… there"],
        },
        "anti": ["why aye not every line", "pet not wallpaper"],
    },
    "northern_english": {
        "name": "Northern English",
        "triggers": [r"northern english", r"yorkshire", r"manchester", r"leeds", r"sheffield", r"manc"],
        "acoustic": "flatter vowels feel in description, dry, direct",
        "prosody": "dry short lines; understated",
        "grammar": ["blunt", "present", "little fluff"],
        "openers": ["right", "here", "ey"],
        "slips": {
            "agree": ["yeah", "aye", "go on then"],
            "urge": ["more", "c'mon", "again"],
            "surprise": ["bloody hell", "christ"],
            "intimate": ["love", "duck", "darlin'"],
            "soft": ["easy", "slow"],
        },
        "examples": {
            "casual": ["right… bit loud this", "ey… look here", "yeah… we off?"],
            "heated": ["more… go on", "c'mon… closer", "again… that"],
            "intimate": ["love… slow", "that's it… stay", "easy… there"],
        },
        "anti": ["no forced dialect respelling"],
    },
    "welsh": {
        "name": "Welsh English",
        "triggers": [r"welsh", r"wales", r"cardiff", r"swansea"],
        "acoustic": "sing-song Welsh English melody, soft rises",
        "prosody": "musical; gentle punch",
        "grammar": ["clear English", "melodic tags rare"],
        "openers": ["right", "here", "lovely"],
        "slips": {
            "agree": ["yeah", "right", "lovely"],
            "urge": ["more", "come on", "again"],
            "surprise": ["bloody hell", "god"],
            "intimate": ["love", "darlin'", "bach"],
            "soft": ["easy", "slow"],
        },
        "examples": {
            "casual": ["right… busy tonight", "here… look", "yeah… alright"],
            "heated": ["more… come on", "again… like that", "yeah… stay"],
            "intimate": ["love… slow", "that's it… there", "easy… for me"],
        },
        "anti": ["no cartoon Welsh spelling"],
    },
    "rp_british": {
        "name": "RP / Southern British",
        "triggers": [r"\brp\b", r"received pronunciation", r"posh british", r"bbc english", r"southern british"],
        "acoustic": "clear non-rhotic Southern British, clipped polish, controlled",
        "prosody": "measured; precise; less American uptalk",
        "grammar": [
            "full careful English — accent is VOICE not broken grammar",
            "understatement okay",
            "rarely any \"native slip\" — slips are British lexis: bloody, quite, rather",
        ],
        "openers": ["right", "well", "look"],
        "slips": {
            "agree": ["yes", "quite", "indeed"],
            "urge": ["more", "come here", "again"],
            "surprise": ["good god", "bloody hell", "christ"],
            "intimate": ["darling", "love", "dear"],
            "soft": ["easy", "slowly"],
        },
        "examples": {
            "casual": ["right… bit loud in here", "look… at me", "well… shall we?"],
            "heated": ["more… just like that", "come here… now", "again… yes"],
            "intimate": ["darling… slow", "that's it… stay", "easy… there"],
        },
        "anti": [
            "do NOT break English grammar for RP — it's polished English",
            "bloody is rare spice not every line",
        ],
    },
    "australian": {
        "name": "Australian",
        "triggers": [r"australian", r"australia", r"sydney", r"melbourne", r"aussie"],
        "acoustic": "broader vowels feel in description, laid-back, rising terminals sometimes",
        "prosody": "laid-back short lines; dry humour",
        "grammar": ["mate/love rare slips", "present", "understated"],
        "openers": ["yeah", "oi", "hey"],
        "slips": {
            "agree": ["yeah", "too right", "nah yeah"],
            "urge": ["more", "c'mon", "again"],
            "surprise": ["shit", "you're kidding", "fuck me"],
            "intimate": ["love", "babe", "darl"],
            "soft": ["easy", "slow"],
        },
        "examples": {
            "casual": ["yeah… bit loud eh", "oi… look here", "hey… we going?"],
            "heated": ["more… like that", "c'mon… closer", "again… yeah"],
            "intimate": ["love… slow", "that's it… stay", "easy… there"],
        },
        "anti": ["mate not every line", "no full phonetic Strine wall"],
    },
    # Niche listen-friendly: Jamaican / roots-reggae English (rasta vibe without
    # cartoon every-line "yah mon" spam). Great for club, beach, chill heat.
    "jamaican_rasta": {
        "name": "Jamaican / Rasta",
        "triggers": [
            r"jamaican", r"jamaica", r"rasta", r"rastafari", r"reggae",
            r"patois", r"yardie", r"kingston", r"irie", r"yah mon",
        ],
        "acoustic": "Caribbean lilt under clear English, warm bounce, relaxed stress, soft ends",
        "prosody": "easy swing; short musical clauses; chill heat not rushed American",
        "grammar": [
            "mostly clear English with light Caribbean rhythm — LTX must parse every word",
            "optional present feel (\"she look good\") sparingly — never full broken English",
            "irie / easy / soon come as rare mood slips — not every line",
            "no phonetic mess (never write \"deh\" \"fi\" walls LTX will print literally)",
        ],
        "openers": ["easy", "yo", "seen", "listen"],
        "slips": {
            "agree": ["yeah", "seen", "irie", "true", "alright"],
            "urge": ["come", "more", "again", "easy now", "bring it"],
            "surprise": ["what", "lord", "you serious?", "bloodclaat"],  # last = rare heat only
            "intimate": ["baby", "love", "darlin'", "sweetness"],
            "soft": ["easy", "slow", "steady", "take time"],
        },
        "scene_bits": [
            "easy… look at me",
            "seen… this place feel right",
            "irie… just like that",
            "yo… come closer",
            "true… don't rush",
            "slow… for me",
            "again… yeah",
            "steady… hold that",
            "listen… stay with me",
            "alright… right there",
            "more… easy now",
            "baby… slow",
            "what… already?",
            "bring it… closer",
            "take time… yeah",
        ],
        "examples": {
            "casual": [
                "easy… bit loud in here",
                "yo… look at me a second",
                "seen… we good?",
                "listen… this light feel nice",
            ],
            "heated": [
                "more… just like that",
                "come… closer… now",
                "again… don't stop",
                "bring it… easy now",
            ],
            "intimate": [
                "baby… slow",
                "steady… right there",
                "irie… stay",
                "sweetness… for me",
            ],
        },
        "anti": [
            "do NOT end every line with mon / yah mon / irie",
            "do NOT write full patois walls (deh, fi, dem) that LTX prints as noise",
            "rasta vibe = rhythm + rare slips, not costume speech every beat",
            "bloodclaat / strong yard words = max one per clip if explicit heat — never spam",
        ],
    },
    "southern_us": {
        "name": "Southern US",
        "triggers": [r"southern(?: us| american)?", r"texas|texan", r"alabama", r"georgia", r"louisiana", r"drawl"],
        "acoustic": "slow drawl feel in description, warm, longer vowels",
        "prosody": "unhurried; soft heat; honeyed without vibe-paint on the body",
        "grammar": [
            "y'all rare and only plural",
            "gonna/wanna okay sparingly",
            "readable — not full eye-dialect",
        ],
        "openers": ["hey", "well", "now"],
        "slips": {
            "agree": ["yeah", "mmhm", "alright"],
            "urge": ["more", "c'mere", "again"],
            "surprise": ["lord", "shit", "you serious?"],
            "intimate": ["baby", "darlin'", "sugar"],
            "soft": ["easy", "slow"],
        },
        "examples": {
            "casual": ["well… bit warm in here", "hey… look at me", "now… we staying?"],
            "heated": ["more… just like that", "c'mere… closer", "again… yeah"],
            "intimate": ["darlin'… slow", "baby… right there", "easy… stay"],
        },
        "anti": ["darlin' not every line", "no cartoon redneck spelling"],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
#  AD-LIBS PER LANGUAGE (~12–15 mini tags/phrases)
#  Seasoning the model can drop naturally when the moment fits — so you do NOT
#  need to type "ja?" / "seen?" / "bloodclaat" into Intent. Seed palette prioritises
#  these; VARIETY LOCK still = each item at most once per clip (no particle spam).
#  Merged into ACCENTS[k]["adlibs"] below. Hand-tuned banks beat auto-synth.
# ─────────────────────────────────────────────────────────────────────────────
ADLIBS_BANKS: dict[str, list[str]] = {
    "korean": [
        "응", "네", "좋아", "진짜?", "아이고", "자기야", "오빠", "언니",
        "더", "빨리", "이리 와", "잠깐", "조금만", "미치겠어", "야…",
    ],
    "japanese": [
        "うん", "はい", "そう", "ねえ", "ちょっと", "もっと", "来て", "だめ",
        "えっ", "すごい", "あなた", "好き", "気持ちいい", "待って", "本当に",
    ],
    "mandarin": [
        "嗯", "好", "对", "哎呀", "真的?", "快点", "过来", "别停",
        "宝贝", "舒服", "等等", "慢点", "再来", "天啊", "就是这样",
    ],
    "thai": [
        "ค่ะ", "ครับ", "นะ", "เร็ว", "มา", "อย่าหยุด", "ดีจัง", "ช้าๆ",
        "อีก", "จ้ะ", "ว้าว", "จริงเหรอ", "ใกล้ๆ", "เบาๆ", "ตรงนั้น",
    ],
    "vietnamese": [
        "ừ", "vâng", "được", "thôi", "nhanh lên", "lại đây", "đừng dừng",
        "chậm thôi", "nữa đi", "trời ơi", "thật á?", "gần hơn", "nhẹ thôi", "đúng chỗ",
    ],
    "french": [
        "oui", "ouais", "d'accord", "merde", "putain", "viens", "encore",
        "doucement", "chéri", "chérie", "attends", "regarde", "comme ça", "plus fort", "là",
    ],
    "spanish_castilian": [
        "vale", "sí", "joder", "hostia", "ven", "más", "despacio",
        "cariño", "espera", "mira", "así", "otra vez", "no pares", "aquí", "coño",
    ],
    "spanish_latin": [
        "sí", "claro", "órale", "joder", "ven", "más", "despacito",
        "bebé", "espera", "mira", "así", "otra vez", "no pares", "aquí", "ay dios",
    ],
    "italian": [
        "sì", "va bene", "cazzo", "dai", "ancora", "piano", "amore",
        "aspetta", "guarda", "così", "ancora di più", "non fermarti", "qui", "bello", "brava",
    ],
    "portuguese": [
        "sim", "tá", "porra", "vem", "mais", "devagar", "amor",
        "espera", "olha", "assim", "de novo", "não para", "aqui", "caralho", "gostoso",
    ],
    "german": [
        "genau", "klar", "stimmt", "scheiße", "mehr", "komm", "jetzt",
        "warte", "langsam", "nochmal", "weiter", "schatz", "also…", "hör mal", "bitte",
    ],
    "dutch": [
        "ja", "oke", "tuurlijk", "meer", "kom", "door", "wacht",
        "rustig", "schat", "zo", "echt?", "kijk", "nou…", "niet stoppen", "godver",
    ],
    "swedish": [
        "ja", "okej", "precis", "fan", "mer", "kom", "sakta",
        "vänta", "så", "igen", "älskling", "titta", "här", "fortsätt", "snälla",
    ],
    "norwegian": [
        "ja", "ok", "akkurat", "faen", "mer", "kom", "sakte",
        "vent", "sånn", "igjen", "elskede", "se", "her", "fortsett", "vær så snill",
    ],
    "russian": [
        "да", "ладно", "точно", "блять", "ещё", "иди", "медленно",
        "подожди", "вот так", "ещё раз", "малыш", "смотри", "сюда", "не останавливайся", "пожалуйста",
    ],
    "polish": [
        "tak", "dobra", "jasne", "kurwa", "więcej", "chodź", "wolno",
        "czekaj", "tak właśnie", "jeszcze raz", "kochanie", "patrz", "tu", "nie przestawaj", "proszę",
    ],
    "czech": [
        "jo", "dobře", "jasně", "kurva", "víc", "pojď", "pomalu",
        "počkej", "takhle", "ještě", "miláčku", "koukej", "tady", "nezastavuj", "prosím",
    ],
    "greek": [
        "ναι", "εντάξει", "ακριβώς", "μαλάκα", "ακόμα", "έλα", "αργά",
        "περίμενε", "έτσι", "ξανά", "αγάπη μου", "κοίτα", "εδώ", "μη σταματάς", "παρακαλώ",
    ],
    "arabic": [
        "ايوه", "تمام", "والله", "يا الله", "اكثر", "تعال", "بطيء",
        "استنى", "كده", "كمان مرة", "حبيبي", "حبيبتى", "بص", "هنا", "متوقفش",
    ],
    "hebrew": [
        "כן", "בסדר", "בדיוק", "לעזאזל", "עוד", "בוא", "לאט",
        "חכה", "ככה", "עוד פעם", "מתוק", "תסתכל", "פה", "אל תעצור", "בבקשה",
    ],
    "swahili": [
        "ndiyo", "sawa", "kweli", "polepole", "njoo", "zaidi", "subiri",
        "hivi", "tena", "mpenzi", "angalia", "hapa", "usiache", "tafadhali", "sasa",
    ],
    "filipino_english": [
        "oo", "sige", "talaga?", "grabe", "halika", "more", "dahan-dahan",
        "sandali", "ganyan", "ulit", "mahal", "tingnan mo", "dito", "huwag tumigil", "please",
    ],
    "indian_english": [
        "haan", "acha", "exactly", "arey", "dekho", "aur", "dheere",
        "ruko", "bas aise", "ek aur", "jaan", "sun", "yahan", "mat rukna", "please yaar",
    ],
    "nigerian_english": [
        "abeg", "sha", "na so", "wetin", "come now", "more", "softly",
        "hold on", "like that", "again o", "baby", "look sharp", "here", "no stop", "chai",
    ],
    "ghanaian_english": [
        "paa", "chale", "ei", "bra", "more", "softly", "wait small",
        "like that", "again", "me nua", "look", "here", "no stop", "please", "woahu?",
    ],
    "south_african_english": [
        "ja", "lekker", "ag", "shame", "more", "come", "softly",
        "wait", "like that", "again", "liefie", "look", "here", "don't stop", "now-now",
    ],
    "trinidadian": [
        "fuh real", "eh", "oy", "allyuh", "doh stop", "easy", "come",
        "again", "gyul", "sweetness", "listen", "lord", "alright", "take time", "true",
    ],
    "jamaican_rasta": [
        "seen?",
        "irie",
        "easy nuh",
        "yeah mon",
        "true true",
        "bloodclaat",
        "what a gwaan",
        "soon come",
        "steady",
        "bring it",
        "yah",
        "lord have mercy",
        "don't rush it",
        "feel that",
        "one love",
    ],
    "cockney": [
        "innit", "mate", "bloody", "oi", "come 'ere", "more", "easy",
        "hold up", "like that", "again", "love", "look", "darlin'", "don't stop", "fuckin' hell",
    ],
    "scottish": [
        "aye", "ken", "pure", "wee", "come here", "more", "easy",
        "hold on", "like that", "again", "hen", "look", "pal", "dinnae stop", "fuckin' hell",
    ],
    "irish": [
        "yeah", "sure", "grand", "feck", "come here", "more", "easy",
        "hold on", "like that", "again", "love", "look", "pet", "don't stop", "Jesus",
    ],
    "scouse": [
        "la", "sound", "boss", "calm down", "come 'ed", "more", "easy",
        "hold up", "like that", "again", "love", "look", "mate", "don't stop", "fuckin' hell",
    ],
    "geordie": [
        "aye", "howay", "pet", "canny", "come here", "more", "easy",
        "hadaway", "like that", "again", "hinny", "look", "mate", "dinna stop", "bloody hell",
    ],
    "northern_english": [
        "aye", "love", "soft lad", "come 'ere", "more", "easy",
        "hold on", "like that", "again", "duck", "look", "mate", "don't stop", "bloody hell",
    ],
    "welsh": [
        "yes", "right", "tidy", "come here", "more", "easy",
        "hold on", "like that", "again", "love", "look", "bach", "don't stop", "bloody hell",
    ],
    "rp_british": [
        "quite", "rather", "indeed", "come here", "more", "gently",
        "one moment", "just so", "again", "darling", "look", "my dear", "don't stop", "bloody hell",
    ],
    "australian": [
        "yeah nah", "mate", "fair dinkum", "come 'ere", "more", "easy",
        "hang on", "like that", "again", "love", "look", "darl", "don't stop", "bloody hell",
    ],
    "new_zealand": [
        "yeah", "sweet as", "bro", "come here", "more", "easy",
        "hang on", "like that", "again", "love", "look", "mate", "don't stop", "choice",
    ],
    "southern_us": [
        "mmhm", "alright now", "lord", "c'mere", "more", "easy",
        "hold on", "just like that", "again", "darlin'", "sugar", "baby", "don't you stop", "shit",
    ],
}

# Attach hand banks; fill any missing accent with a synthesized non-doubling list
for _ak, _spec in ACCENTS.items():
    if _ak in ADLIBS_BANKS and ADLIBS_BANKS[_ak]:
        _spec["adlibs"] = list(ADLIBS_BANKS[_ak])


# ─────────────────────────────────────────────────────────────────────────────
#  INTENSITY → DIALECT HEAT (maps UI 1–10 onto how filthy the accent talks)
#  Motion intensity stays in brain_ld._energy; THIS is speech filth only.
# ─────────────────────────────────────────────────────────────────────────────

def heat_tier(energy) -> str:
    """soft 1–3 · warm 4–6 · hot 7–8 · filthy 9–10"""
    e = max(1, min(10, int(energy or 5)))
    if e <= 3:
        return "soft"
    if e <= 6:
        return "warm"
    if e <= 8:
        return "hot"
    return "filthy"


def heat_label(energy) -> str:
    return {
        "soft": "soft talk",
        "warm": "warm / spicy",
        "hot": "hot / filthy",
        "filthy": "max filthy",
    }.get(heat_tier(energy), "warm / spicy")


# Cross-accent English heat shape (always accented when accent is on)
_HEAT_ENGLISH = {
    "soft": {
        "voice": "quiet, close, warm — whispered or murmured brackets",
        "lex": "soft / good / more / please / stay / slow",
        "examples": [
            "slow… for me",
            "stay… right there",
            "more… soft… yes",
        ],
        "rules": [
            "NO degradation (no slut/whore/filthy)",
            "NO barked orders; keep it intimate",
            "cursing rare or absent",
        ],
    },
    "warm": {
        "voice": "steady heat — full voice, hungry but not mean",
        "lex": "fuck / cock / pussy allowed when explicit; more / harder / don't stop",
        "examples": [
            "fuck… just like that",
            "take it… deeper",
            "don't you stop… more",
        ],
        "rules": [
            "light filth OK when explicit; skip degradation words",
            "urgent, not cruel",
        ],
    },
    "hot": {
        "voice": "raw, loud brackets — snarled / gasped / hungry",
        "lex": "filthy / slut / whore / fucking / take it / wreck / use me — when EXPLICIT",
        "examples": [
            "take it… you filthy fuckin slut",
            "fuckin take that cock",
            "good girl… take it deeper you whore",
            "don't stop… fucking use me",
        ],
        "rules": [
            "IF explicit: lean hard into dirty degradation in the accent's mouth-shape",
            "IF not explicit: stay heated but skip graphic anatomy/degradation",
            "still NO same tag every line; still accent grammar + rare slips",
            "vary insults — don't spam the same slur twice in a row",
        ],
    },
    "filthy": {
        "voice": "maximum heat — barked, snarled, broken breath; short hard lines",
        "lex": "full degradation + graphic sex words when explicit; stacked fucks; mean affection",
        "examples": [
            "take every fuckin inch you dirty slut",
            "gonna wreck that tight cunt — take it",
            "look at you… fuckin desperate whore",
            "beg for it… say you want this cock",
        ],
        "rules": [
            "IF explicit: almost every spoken line is filthy; accent never drops",
            "IF not explicit: max urgency without full porn vocabulary",
            "still variety — rotate insults and native heat slips",
            "brackets match: (snarling) (hungry) (broken) (raw)",
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
#  CHARACTER LOOK SEEDS (T2V accent ↔ phenotype)
#  Several male/female profiles per accent. Seed picks ONE for this clip so
#  "Scottish woman" does not render as a generic K-beauty face (and vice versa).
#  Intent still wins if the user names hair/skin/wardrobe. I2V: image wins.
#  Compact trait strings → assembled into identity openers in the lock.
# ─────────────────────────────────────────────────────────────────────────────

CHARACTER_PROFILES = {
    "scottish": {
        "female": [
            "curly auburn-red hair, fair freckled skin, green eyes, strong freckled cheeks, wool jumper",
            "wavy strawberry-blonde hair, pale skin, hazel eyes, soft freckles across the nose, plaid shirt",
            "dark brown waves, fair cool skin, blue-grey eyes, freckled shoulders, black turtleneck",
            "ginger curls in a messy bun, porcelain freckled face, green eyes, denim jacket",
        ],
        "male": [
            "short auburn hair, fair freckled skin, blue eyes, light stubble, flannel shirt",
            "dark cropped hair, pale skin, hazel eyes, scruffy jaw, grey hoodie",
            "ginger beard, freckled cheeks, green eyes, heavy knit jumper",
            "brown wavy hair, fair skin, sharp jaw, light freckles, black peacoat",
        ],
    },
    "irish": {
        "female": [
            "dark curly hair, fair freckled skin, green eyes, soft freckles, green knit cardigan",
            "auburn waves, pale skin, blue eyes, freckled nose, cream blouse",
            "black hair in a low bun, fair cool skin, grey-green eyes, wool coat",
            "reddish-brown braids, freckled cheeks, hazel eyes, denim jacket",
        ],
        "male": [
            "dark curly hair, fair freckled skin, blue eyes, light stubble, wool jumper",
            "auburn short hair, pale skin, green eyes, freckled jaw, leather jacket",
            "brown hair, fair skin, hazel eyes, clean stubble, grey hoodie",
            "black hair, freckled cheeks, blue eyes, peacoat",
        ],
    },
    "cockney": {
        "female": [
            "bleached blonde waves, fair London skin, sharp eyeliner, gold hoops, leather jacket",
            "dark bob with fringe, olive-fair skin, brown eyes, bold lip, black tank",
            "honey-brown curls, freckled nose, hazel eyes, denim jacket",
            "black ponytail, fair skin, winged liner, crop hoodie",
        ],
        "male": [
            "short faded hair, fair skin, stubble, gold chain, track top",
            "dark cropped hair, London fair skin, sharp jaw, bomber jacket",
            "buzz cut, light stubble, brown eyes, black hoodie",
            "messy brown hair, freckled, grey tracksuit top",
        ],
    },
    "scouse": {
        "female": [
            "long dark waves, fair skin, heavy lashes, bold brow, black blazer",
            "blonde balayage, pale skin, blue eyes, winged liner, leather jacket",
            "auburn curls, freckles, hazel eyes, denim shirt",
            "black bob, fair skin, red lip, crop top",
        ],
        "male": [
            "short dark crop, fair skin, stubble, black tee",
            "light brown quiff, pale skin, blue eyes, denim jacket",
            "buzz cut, freckled, grey hoodie",
            "dark wavy hair, scruffy jaw, bomber",
        ],
    },
    "geordie": {
        "female": [
            "long blonde hair, fair skin, blue eyes, soft makeup, puffer jacket",
            "dark brown waves, pale skin, freckles, grey hoodie",
            "auburn ponytail, green eyes, freckled nose, denim jacket",
            "black hair, fair cool skin, bold liner, black coat",
        ],
        "male": [
            "short brown hair, fair skin, stubble, black hoodie",
            "blonde crop, pale skin, blue eyes, tracksuit top",
            "dark fade, freckled jaw, grey tee",
            "auburn hair, scruff, flannel",
        ],
    },
    "northern_english": {
        "female": [
            "mouse-brown waves, fair skin, freckles, soft eyes, wool coat",
            "dark straight hair, pale skin, blue eyes, denim jacket",
            "blonde bob, freckled cheeks, grey knit",
            "black ponytail, cool fair skin, black hoodie",
        ],
        "male": [
            "short brown hair, fair skin, stubble, work jacket",
            "dark crop, pale skin, blue eyes, grey hoodie",
            "ginger stubble, freckles, flannel",
            "black hair, scruffy jaw, black tee",
        ],
    },
    "welsh": {
        "female": [
            "dark wavy hair, fair skin, soft freckles, green eyes, wool scarf",
            "auburn curls, pale skin, hazel eyes, green knit",
            "black hair, cool fair skin, blue eyes, denim jacket",
            "honey-brown waves, freckles, cream blouse",
        ],
        "male": [
            "dark curly hair, fair freckled skin, green eyes, wool jumper",
            "brown short hair, pale skin, stubble, grey hoodie",
            "auburn beard, freckles, flannel",
            "black hair, blue eyes, peacoat",
        ],
    },
    "rp_british": {
        "female": [
            "sleek dark bob, porcelain skin, clear blue eyes, tailored coat",
            "honey-blonde blowout, fair skin, soft makeup, silk blouse",
            "chestnut waves, cool fair skin, grey eyes, cashmere sweater",
            "black hair in a chignon, pale skin, pearl studs, trench coat",
        ],
        "male": [
            "neat side-part brown hair, fair skin, clean-shaven, navy jumper",
            "dark cropped hair, pale skin, light stubble, tailored coat",
            "blonde short hair, blue eyes, oxford shirt",
            "black hair, sharp jaw, charcoal blazer",
        ],
    },
    "australian": {
        "female": [
            "sun-lightened brown hair, tanned freckled skin, hazel eyes, linen shirt",
            "blonde waves, golden tan, green eyes, tank top",
            "dark beachy waves, olive-tan skin, brown eyes, denim jacket",
            "auburn sun streaks, freckled nose, white tee",
        ],
        "male": [
            "sun-bleached brown hair, tanned skin, stubble, flannel",
            "blonde crop, golden freckles, blue eyes, grey tee",
            "dark messy hair, tan, scruffy jaw, hoodie",
            "auburn hair, freckled, board shirt",
        ],
    },
    "new_zealand": {
        "female": [
            "wavy brown hair, fair-to-tan skin, freckles, soft eyes, wool jumper",
            "blonde beach waves, freckled tan, green eyes, denim jacket",
            "dark straight hair, cool fair skin, grey hoodie",
            "auburn curls, freckles, cream knit",
        ],
        "male": [
            "messy brown hair, fair freckled skin, stubble, flannel",
            "blonde crop, tan freckles, blue eyes, hoodie",
            "dark hair, scruff, grey tee",
            "auburn stubble, freckled, jacket",
        ],
    },
    "southern_us": {
        "female": [
            "long honey-blonde waves, warm fair skin, blue eyes, sundress",
            "dark brown curls, warm olive-tan skin, brown eyes, denim jacket",
            "auburn waves, freckled cheeks, green eyes, flannel shirt",
            "black sleek hair, warm beige skin, gold hoops, white tee",
        ],
        "male": [
            "short brown hair, warm fair skin, stubble, plaid shirt",
            "dark crop, tan arms, blue eyes, grey tee",
            "blonde short hair, freckled, denim jacket",
            "black hair, scruffy jaw, flannel",
        ],
    },
    "jamaican_rasta": {
        "female": [
            "long locs with gold wraps, deep brown skin, warm brown eyes, hoop earrings, crop top",
            "tight black curls, rich brown skin, full lips, gold nose stud, yellow tank",
            "shoulder-length locs, deep bronze skin, dark eyes, leather jacket",
            "natural afro, deep brown skin, high cheekbones, white linen shirt",
        ],
        "male": [
            "long thick locs, deep brown skin, full beard, gold chain, linen shirt",
            "short twists, rich brown skin, warm eyes, denim vest",
            "mid-length locs, deep bronze skin, stubble, reggae-print tee",
            "neat dreads, deep brown skin, sharp jaw, black tank",
        ],
    },
    "trinidadian": {
        "female": [
            "long dark curls, warm brown skin, gold hoops, bright crop top",
            "sleek black ponytail, deep bronze skin, bold liner, carnival-colour top",
            "honey-highlighted curls, medium-brown skin, brown eyes, denim jacket",
            "short natural curls, deep brown skin, gold studs, white tank",
        ],
        "male": [
            "short fade, warm brown skin, light stubble, gold chain, black tee",
            "curly top fade, deep bronze skin, sharp jaw, colourful shirt",
            "low cut, deep brown skin, beard line, denim jacket",
            "twists, medium-brown skin, white tee",
        ],
    },
    "nigerian_english": {
        "female": [
            "long box braids, deep brown skin, warm brown eyes, gold hoops, Ankara-print top",
            "sleek black weave, rich dark skin, full lips, gold studs, fitted blouse",
            "short natural afro, deep brown skin, high cheekbones, denim jacket",
            "cornrow updo, deep bronze skin, bold liner, black dress",
        ],
        "male": [
            "short fade, deep brown skin, clean stubble, gold chain, black polo",
            "low cut with pattern, rich dark skin, sharp jaw, Ankara shirt accent",
            "twists, deep brown skin, beard, grey hoodie",
            "bald fade, deep bronze skin, strong build, white tee",
        ],
    },
    "ghanaian_english": {
        "female": [
            "long black braids, deep brown skin, warm eyes, gold earrings, colourful blouse",
            "natural short curls, rich brown skin, soft smile lines, denim jacket",
            "sleek ponytail, deep bronze skin, gold hoops, white tee",
            "twist-out afro, deep brown skin, high cheekbones, wax-print wrap top",
        ],
        "male": [
            "short crop, deep brown skin, light beard, polo shirt",
            "low fade, rich dark skin, warm eyes, linen shirt",
            "twists, deep bronze skin, stubble, black tee",
            "bald, deep brown skin, strong jaw, grey hoodie",
        ],
    },
    "south_african_english": {
        "female": [
            "sun-streaked brown hair, warm tan skin, freckles, green eyes, linen shirt",
            "dark straight hair, light-brown skin, brown eyes, denim jacket",
            "blonde waves, fair freckled skin, blue eyes, white tee",
            "black curls, medium-brown skin, gold studs, sundress",
        ],
        "male": [
            "short sun-bleached hair, tan freckled skin, stubble, flannel",
            "dark crop, light-brown skin, blue eyes, grey hoodie",
            "blonde short hair, fair freckles, denim jacket",
            "black hair, medium-brown skin, scruff, black tee",
        ],
    },
    "swahili": {
        "female": [
            "long black braids, deep brown skin, warm eyes, gold hoops, colourful kanga-print top",
            "short natural hair, rich dark skin, high cheekbones, white linen",
            "shoulder locs, deep bronze skin, soft liner, denim jacket",
            "sleek black hair, deep brown skin, gold studs, cotton dress",
        ],
        "male": [
            "short crop, deep brown skin, light beard, linen shirt",
            "low cut, rich dark skin, warm eyes, polo",
            "twists, deep bronze skin, stubble, grey tee",
            "bald fade, deep brown skin, strong jaw, open shirt",
        ],
    },
    "korean": {
        "female": [
            "long straight black hair, light East Asian skin, soft monolid eyes, subtle makeup, oversized knit",
            "shoulder-length dark brown hair, light East Asian skin, soft bangs, cream blouse",
            "black hair in a sleek ponytail, light East Asian skin, clear features, denim jacket",
            "wavy dark hair, light East Asian skin, soft pink lip, black turtleneck",
        ],
        "male": [
            "dark undercut, light East Asian skin, soft jaw, black hoodie",
            "messy black hair, light East Asian skin, clean-shaven, grey tee",
            "side-part dark brown hair, light East Asian skin, denim jacket",
            "short black crop, light East Asian skin, soft features, white shirt",
        ],
    },
    "japanese": {
        "female": [
            "straight black bob, light East Asian skin, soft eyes, minimal makeup, cardigan",
            "long black hair, light East Asian skin, gentle features, soft knit",
            "dark brown waves, light East Asian skin, soft bangs, cream sweater",
            "short black hair, light East Asian skin, subtle liner, black coat",
        ],
        "male": [
            "black messy hair, light East Asian skin, clean jaw, hoodie",
            "short dark crop, light East Asian skin, soft features, grey tee",
            "side-swept black hair, light East Asian skin, denim jacket",
            "undercut, light East Asian skin, black shirt",
        ],
    },
    "mandarin": {
        "female": [
            "long straight black hair, light East Asian skin, soft oval face, silk blouse",
            "shoulder dark hair, light East Asian skin, subtle makeup, black dress",
            "black ponytail, light East Asian skin, clear features, denim jacket",
            "wavy dark hair, light East Asian skin, soft lip, cream knit",
        ],
        "male": [
            "short black hair, light East Asian skin, clean-shaven, collared shirt",
            "dark crop, light East Asian skin, sharp jaw, black tee",
            "side-part, light East Asian skin, denim jacket",
            "buzzed sides, light East Asian skin, grey hoodie",
        ],
    },
    "thai": {
        "female": [
            "long black hair, warm medium-tan Southeast Asian skin, dark eyes, soft features, silk top",
            "shoulder dark waves, golden-tan skin, full lips, crop blouse",
            "black ponytail, medium-brown warm skin, gold studs, white tee",
            "sleek black hair, warm tan skin, soft liner, sundress",
        ],
        "male": [
            "short black hair, warm tan Southeast Asian skin, clean jaw, linen shirt",
            "dark crop, golden-tan skin, stubble, black tee",
            "messy black hair, medium-tan skin, denim jacket",
            "fade, warm brown skin, white shirt",
        ],
    },
    "vietnamese": {
        "female": [
            "long straight black hair, light warm Southeast Asian skin, dark eyes, soft features, blouse",
            "black shoulder hair, fair-warm skin, gentle face, denim jacket",
            "ponytail, light tan skin, subtle makeup, white tee",
            "dark waves, warm light skin, black dress",
        ],
        "male": [
            "short black hair, light warm Southeast Asian skin, clean jaw, shirt",
            "dark crop, fair-warm skin, black tee",
            "side-part, light tan skin, denim jacket",
            "messy black hair, warm light skin, hoodie",
        ],
    },
    "filipino_english": {
        "female": [
            "long dark wavy hair, warm medium-tan skin, brown eyes, soft features, crop top",
            "black straight hair, golden-tan skin, full smile, denim jacket",
            "shoulder curls, warm brown skin, gold hoops, white tee",
            "sleek black ponytail, medium-tan skin, soft liner, sundress",
        ],
        "male": [
            "short black hair, warm medium-tan skin, light stubble, polo",
            "dark crop, golden-tan skin, sharp jaw, black tee",
            "messy black hair, warm brown skin, denim jacket",
            "fade, medium-tan skin, white shirt",
        ],
    },
    "indian_english": {
        "female": [
            "long black wavy hair, warm medium-brown skin, dark eyes, gold studs, kurta-style top or blouse",
            "dark straight hair, light-brown skin, soft features, denim jacket",
            "black braid, deep warm brown skin, bindi optional, colourful blouse",
            "shoulder dark curls, medium-brown skin, gold hoops, white tee",
        ],
        "male": [
            "short black hair, warm medium-brown skin, light stubble, button shirt",
            "dark crop, light-brown skin, clean jaw, polo",
            "wavy black hair, deep warm brown skin, beard short, kurta or tee",
            "side-part, medium-brown skin, denim jacket",
        ],
    },
    "french": {
        "female": [
            "dark wavy hair, fair olive skin, brown eyes, soft red lip, trench coat",
            "blonde bob, pale skin, freckles, black turtleneck",
            "chestnut waves, warm fair skin, grey eyes, silk blouse",
            "black sleek hair, cool fair skin, bold liner, leather jacket",
        ],
        "male": [
            "dark messy hair, fair olive skin, stubble, navy jumper",
            "short brown hair, pale skin, light beard, grey coat",
            "black crop, cool fair skin, clean jaw, white shirt",
            "blonde short hair, freckles, denim jacket",
        ],
    },
    "german": {
        "female": [
            "straight blonde hair, fair cool skin, blue eyes, wool coat",
            "dark brown bob, pale skin, grey eyes, black turtleneck",
            "honey-blonde waves, freckled fair skin, denim jacket",
            "black long hair, cool fair skin, sharp features, blazer",
        ],
        "male": [
            "short blonde hair, fair cool skin, blue eyes, grey hoodie",
            "dark cropped hair, pale skin, stubble, black tee",
            "brown short hair, freckled, flannel",
            "black hair, sharp jaw, wool coat",
        ],
    },
    "spanish_latin": {
        "female": [
            "long dark wavy hair, warm olive-tan skin, brown eyes, gold hoops, crop top",
            "black straight hair, medium-tan skin, full lips, denim jacket",
            "caramel highlights, warm brown skin, soft liner, sundress",
            "sleek black ponytail, olive skin, bold lip, white tee",
        ],
        "male": [
            "dark short hair, warm olive-tan skin, stubble, black tee",
            "curly black hair, medium-tan skin, scruff, linen shirt",
            "fade, warm brown skin, sharp jaw, denim jacket",
            "wavy dark hair, olive skin, white shirt",
        ],
    },
    "spanish_castilian": {
        "female": [
            "dark wavy hair, light olive skin, brown eyes, soft makeup, trench",
            "black bob, fair-olive skin, bold liner, black dress",
            "chestnut waves, warm fair skin, denim jacket",
            "long dark hair, light olive, cream blouse",
        ],
        "male": [
            "dark short hair, light olive skin, stubble, navy jumper",
            "brown crop, fair-olive skin, clean jaw, shirt",
            "black messy hair, light olive, denim jacket",
            "side-part, warm fair skin, blazer",
        ],
    },
    "italian": {
        "female": [
            "long dark wavy hair, warm olive skin, brown eyes, gold earrings, silk blouse",
            "black sleek hair, light olive skin, bold lip, leather jacket",
            "chestnut curls, freckled olive, denim shirt",
            "dark bob, warm fair-olive, black dress",
        ],
        "male": [
            "dark curly hair, warm olive skin, stubble, linen shirt",
            "short black hair, light olive, scruff, black tee",
            "brown messy hair, olive skin, denim jacket",
            "fade, warm olive, white shirt",
        ],
    },
    "portuguese": {
        "female": [
            "dark wavy hair, warm olive-tan skin, brown eyes, soft features, blouse",
            "black long hair, light olive, gold studs, denim jacket",
            "chestnut waves, freckled olive, white tee",
            "sleek dark hair, warm tan, sundress",
        ],
        "male": [
            "dark short hair, warm olive skin, stubble, polo",
            "black crop, light olive, scruff, grey tee",
            "wavy brown hair, olive-tan, linen shirt",
            "fade, warm olive, denim jacket",
        ],
    },
    "russian": {
        "female": [
            "long straight blonde hair, pale cool skin, blue eyes, sharp cheekbones, black coat",
            "dark straight hair, porcelain skin, grey eyes, turtleneck",
            "platinum waves, pale freckled skin, leather jacket",
            "chestnut hair, cool fair skin, soft makeup, wool jumper",
        ],
        "male": [
            "short blonde hair, pale cool skin, blue eyes, black hoodie",
            "dark cropped hair, pale skin, stubble, grey coat",
            "brown short hair, cool fair skin, sharp jaw, black tee",
            "buzz cut, pale skin, light stubble, denim jacket",
        ],
    },
    "polish": {
        "female": [
            "long light-brown hair, fair cool skin, blue-grey eyes, wool coat",
            "dark straight hair, pale skin, soft freckles, black turtleneck",
            "blonde waves, fair freckled skin, denim jacket",
            "black bob, cool fair skin, cream blouse",
        ],
        "male": [
            "short light-brown hair, fair cool skin, stubble, grey hoodie",
            "dark crop, pale skin, blue eyes, black tee",
            "blonde short hair, freckles, flannel",
            "black hair, cool fair skin, denim jacket",
        ],
    },
    "czech": {
        "female": [
            "dark wavy hair, fair cool skin, green-grey eyes, wool jumper",
            "blonde straight hair, pale skin, blue eyes, black coat",
            "chestnut bob, freckled fair skin, denim jacket",
            "black long hair, cool fair, cream knit",
        ],
        "male": [
            "short brown hair, fair cool skin, stubble, hoodie",
            "dark crop, pale skin, blue eyes, black tee",
            "blonde short hair, freckles, jacket",
            "black hair, cool fair, grey shirt",
        ],
    },
    "dutch": {
        "female": [
            "long blonde hair, fair freckled skin, blue eyes, denim jacket",
            "light-brown waves, pale skin, soft freckles, wool coat",
            "dark blonde bob, freckled, white tee",
            "strawberry-blonde, fair skin, green eyes, knit",
        ],
        "male": [
            "blonde short hair, fair freckled skin, blue eyes, grey hoodie",
            "light-brown crop, pale skin, stubble, denim jacket",
            "dirty-blonde, freckles, black tee",
            "brown hair, fair skin, flannel",
        ],
    },
    "swedish": {
        "female": [
            "long platinum-blonde hair, fair cool skin, blue eyes, wool coat",
            "ash-blonde waves, pale freckled skin, soft makeup, knit",
            "light-brown hair, cool fair skin, denim jacket",
            "blonde bob, porcelain skin, black turtleneck",
        ],
        "male": [
            "short blonde hair, fair cool skin, blue eyes, grey hoodie",
            "ash-brown crop, pale skin, stubble, black tee",
            "dirty-blonde, freckles, denim jacket",
            "light-brown hair, cool fair, wool jumper",
        ],
    },
    "norwegian": {
        "female": [
            "long light-blonde hair, fair cool skin, blue eyes, wool jumper",
            "ash waves, pale freckled skin, outdoor jacket",
            "light-brown hair, cool fair, knit scarf",
            "blonde braid, porcelain skin, black coat",
        ],
        "male": [
            "blonde short hair, fair cool skin, blue eyes, outdoor jacket",
            "light-brown crop, pale freckles, hoodie",
            "dirty-blonde, stubble, flannel",
            "ash-brown, cool fair, black tee",
        ],
    },
    "greek": {
        "female": [
            "long dark wavy hair, warm olive skin, brown eyes, gold earrings, white blouse",
            "black sleek hair, light olive, bold liner, black dress",
            "chestnut curls, freckled olive, denim jacket",
            "dark ponytail, warm olive, sundress",
        ],
        "male": [
            "dark curly hair, warm olive skin, stubble, linen shirt",
            "short black hair, light olive, scruff, white tee",
            "brown messy hair, olive skin, denim jacket",
            "fade, warm olive, open shirt",
        ],
    },
    "arabic": {
        "female": [
            "long dark wavy hair, warm olive-tan skin, dark eyes, soft features, elegant blouse",
            "black sleek hair, light olive skin, bold liner, abaya-style coat or black dress",
            "dark curls, medium-tan warm skin, gold hoops, cream top",
            "straight black hair, warm beige skin, soft makeup, trench",
        ],
        "male": [
            "short dark hair, warm olive-tan skin, trimmed beard, collared shirt",
            "black crop, light olive, clean stubble, black tee",
            "wavy dark hair, medium-tan, light beard, linen shirt",
            "fade, warm olive, denim jacket",
        ],
    },
    "hebrew": {
        "female": [
            "dark curly hair, warm light-olive skin, brown eyes, soft features, linen top",
            "black straight hair, fair-olive skin, bold liner, black jacket",
            "chestnut waves, freckled olive, denim shirt",
            "dark bob, warm fair skin, white tee",
        ],
        "male": [
            "dark curly hair, warm light-olive skin, stubble, tee",
            "short black hair, fair-olive, scruff, hoodie",
            "brown crop, warm olive, denim jacket",
            "messy dark hair, light olive, linen shirt",
        ],
    },
}


def _profile_gender(lead_gender: str, role: str = "lead") -> str:
    g = (lead_gender or "auto").lower()
    if role == "partner":
        if g in ("male", "man", "m"):
            return "female"
        if g in ("female", "woman", "f"):
            return "male"
        return "male"
    if g in ("male", "man", "m"):
        return "male"
    return "female"  # auto / female default for lead examples


def pick_character_profile(
    accent_key: str,
    *,
    lead_gender: str = "auto",
    role: str = "lead",
    seed: int = 0,
) -> str:
    """Return one look-seed string for this accent + gender (seeded, non-repeating bank)."""
    bank = CHARACTER_PROFILES.get(accent_key) or {}
    gender = _profile_gender(lead_gender, role)
    opts = list(bank.get(gender) or bank.get("female") or bank.get("male") or [])
    if not opts:
        # generic fallback by region-ish name only
        return ""
    stable = sum(ord(c) for c in (accent_key + gender + role)) & 0xFFFF
    import random
    rng = random.Random(int(seed or 0) ^ stable)
    return rng.choice(opts)


def format_identity_opener(
    accent_key: str,
    look: str,
    *,
    lead_gender: str = "auto",
    role: str = "lead",
    intent: str = "",
    seed: int = 0,
    mode: str = "t2v",
) -> str:
    """Assemble 'A Japanese woman, 23, petite with small breasts, with …' from accent + look + intent."""
    adj = identity_label(accent_key)
    person = _person_noun(lead_gender, role=role)
    # Prefer intent-aware open (age 19–28 seed + body keywords)
    try:
        from .intent_traits_ld import (
            pick_age, extract_body_traits, build_open_phrase,
        )
    except ImportError:
        try:
            from intent_traits_ld import (
                pick_age, extract_body_traits, build_open_phrase,
            )
        except ImportError:
            pick_age = extract_body_traits = build_open_phrase = None
    if build_open_phrase is not None:
        is_i2v = (mode or "t2v").lower() == "i2v"
        age, src = pick_age(intent, seed, auto=not is_i2v)
        if is_i2v and src != "intent":
            age = None
        body = extract_body_traits(intent)
        if age is not None or body:
            return build_open_phrase(
                accent_adj=adj, person=person, age=age,
                body_traits=body, look_seed=look or "",
            )
    art = "An" if adj[:1].lower() in "aeiou" else "A"
    if look:
        return f"{art} {adj} {person} with {look}"
    return f"{art} {adj} {person}"


# Accent-flavoured filthy slips (hot/filthy only). Occasional, context-fit.
_HEAT_SLIPS = {
    "cockney": {
        "hot": ["fuckin'", "slag", "dirty cow", "take it love"],
        "filthy": ["fuckin' slag", "dirty whore", "take it you slag", "filthy cunt"],
    },
    "scottish": {
        "hot": ["fuckin'", "dirty cow", "take it love"],
        "filthy": ["fuckin' whore", "dirty slut", "take it ya filthy cow"],
    },
    "irish": {
        "hot": ["fuckin'", "dirty thing", "take it love"],
        "filthy": ["fuckin' slut", "dirty whore", "take every bit"],
    },
    "scouse": {
        "hot": ["fuckin'", "dirty la", "take it"],
        "filthy": ["fuckin' slag", "dirty whore", "take it la"],
    },
    "geordie": {
        "hot": ["fuckin'", "dirty pet", "howay take it"],
        "filthy": ["fuckin' slag", "dirty whore", "take it pet"],
    },
    "northern_english": {
        "hot": ["fuckin'", "dirty cow", "take it love"],
        "filthy": ["fuckin' slag", "filthy slut", "take it you whore"],
    },
    "welsh": {
        "hot": ["fuckin'", "dirty love", "take it"],
        "filthy": ["fuckin' slut", "dirty whore", "take it love"],
    },
    "rp_british": {
        "hot": ["bloody hell", "filthy thing", "take it"],
        "filthy": ["you filthy little slut", "take it properly", "disgusting… perfect"],
    },
    "australian": {
        "hot": ["fuckin'", "dirty thing", "take it"],
        "filthy": ["fuckin' slut", "filthy whore", "take it you dog"],
    },
    "jamaican_rasta": {
        "hot": ["fuckin'", "dirty ting", "take it easy"],
        "filthy": ["fuckin' slut", "dirty whore", "take all of it", "bloodclaat… yes"],
    },
    "trinidadian": {
        "hot": ["fuckin'", "dirty gyul", "take it"],
        "filthy": ["fuckin' slut", "dirty whore", "take all of it"],
    },
    # nigerian / swahili / south_african merged below (were duplicated later — both palettes kept)
    "ghanaian_english": {
        "hot": ["fuckin'", "dirty thing", "take it"],
        "filthy": ["fuckin' slut", "dirty whore", "take all of it"],
    },
    "filipino_english": {
        "hot": ["fuckin'", "grabe", "take it"],
        "filthy": ["fuckin' slut", "dirty whore", "sige na… take it"],
    },
    "new_zealand": {
        "hot": ["fuckin'", "dirty thing", "take it"],
        "filthy": ["fuckin' slut", "filthy whore", "take it love"],
    },
    "southern_us": {
        "hot": ["fuckin'", "dirty girl", "take it baby"],
        "filthy": ["fuckin' slut", "filthy whore", "take that cock sugar"],
    },
    "french": {
        "hot": ["putain", "salope", "encore", "prends-le"],
        "filthy": ["salope", "pute", "prends tout", "putain oui"],
    },
    "german": {
        "hot": ["fick", "Schlampe", "mehr", "nimm es"],
        "filthy": ["du Schlampe", "Hure", "nimm den Schwanz", "fick mich"],
    },
    "russian": {
        "hot": ["блять", "сука", "давай", "сильнее"],
        "filthy": ["шлюха", "сука", "блядина", "возьми"],
    },
    "spanish_latin": {
        "hot": ["puta", "más", "tómalo", "así"],
        "filthy": ["puta", "zorra", "tómalo todo", "pendeja"],
    },
    "spanish_castilian": {
        "hot": ["joder", "puta", "más", "tómalo"],
        "filthy": ["puta", "zorra", "tómalo todo", "cerda"],
    },
    "italian": {
        "hot": ["cazzo", "troia", "ancora", "prendilo"],
        "filthy": ["troia", "puttana", "prendi tutto", "cazzo sì"],
    },
    "portuguese": {
        "hot": ["porra", "vadia", "mais", "toma"],
        "filthy": ["vadia", "puta", "toma tudo", "safada"],
    },
    "korean": {
        "hot": ["씨발", "더", "빨리", "좋아"],
        "filthy": ["씨발", "더 세게", "제발", "미쳐", "개같이"],
    },
    "japanese": {
        "hot": ["だめ", "もっと", "気持ちいい", "いや"],
        "filthy": ["もっと", "だめ…いい", "犯して", "奥"],
    },
    "mandarin": {
        "hot": ["操", "再深", "快点", "爽"],
        "filthy": ["骚货", "操我", "用力", "贱货"],
    },
    "dutch": {
        "hot": ["neuk", "slet", "meer", "pak"],
        "filthy": ["vieze slet", "hoer", "neuk me", "pak hem"],
    },
    "polish": {
        "hot": ["kurwa", "więcej", "bierz", "suko"],
        "filthy": ["kurwa", "dziwka", "bierz to", "suko"],
    },
    "indian_english": {
        "hot": ["saali", "aur", "le le", "chhod"],
        "filthy": ["randi", "saali", "le pura", "chod"],
    },
    # Merged heat palettes (earlier + later definitions — nothing discarded)
    "nigerian_english": {
        "hot": ["fuckin'", "dirty thing", "take am", "ashawo", "more"],
        "filthy": [
            "fuckin' slut", "dirty whore", "take all of it", "abeg… more",
            "ashawo", "dirty girl", "take am all", "no stop",
        ],
    },
    "arabic": {
        "hot": ["يا شرموطة", "أكثر", "خديه"],
        "filthy": ["شرموطة", "قحبة", "خذي كله"],
    },
    "thai": {
        "hot": ["เย็ด", "แรงกว่า", "อีก", "หี"],
        "filthy": ["มึง", "เงี่ยน", "เย็ดแรงๆ", "ควย"],
    },
    "vietnamese": {
        "hot": ["đụ", "mạnh hơn", "thêm", "lồn"],
        "filthy": ["đĩ", "đụ đi", "cặc", "chịch mạnh"],
    },
    "swedish": {
        "hot": ["fan", "mer", "ta den", "fitta"],
        "filthy": ["hora", "slyna", "ta kuken", "knulla"],
    },
    "norwegian": {
        "hot": ["faen", "mer", "ta den", "fitte"],
        "filthy": ["hore", "tøs", "ta kuken", "knull"],
    },
    "czech": {
        "hot": ["kurva", "víc", "ber to", "píča"],
        "filthy": ["děvka", "kurva", "ber to všechno", "čůzo"],
    },
    "greek": {
        "hot": ["μαλάκα", "ακόμα", "πάρε το", "μουνί"],
        "filthy": ["πουτάνα", "σκύλα", "πάρε τον", "γαμήσου"],
    },
    "hebrew": {
        "hot": ["זין", "עוד", "קחי", "כוס"],
        "filthy": ["שרמוטה", "זונה", "קחי הכל", "תזייני"],
    },
    "swahili": {
        "hot": ["fuckin'", "more", "njoo", "zaidi", "chukua", "sana", "malaya"],
        "filthy": [
            "fuckin' slut", "take it", "zaidi… now",
            "malaya", "chukua yote", "piga", "uchafu",
        ],
    },
    "south_african_english": {
        "hot": ["fuckin'", "dirty thing", "take it", "naai", "poes"],
        "filthy": [
            "fuckin' slut", "filthy whore", "take it liefie",
            "fuckin' whore", "vuil slet", "take it all", "naai harder",
        ],
    },
}


def _heat_block(key: str, energy: int, explicit: bool) -> str:
    tier = heat_tier(energy)
    e = max(1, min(10, int(energy or 5)))
    h = _HEAT_ENGLISH[tier]
    lines = [
        f"\n━━ DIALECT HEAT — intensity {e}/10 → {tier.upper()} ━━",
        f"Speech filth scales with intensity. Current tier: {tier} ({heat_label(e)}).",
        f"VOICE ENERGY: {h['voice']}",
        f"ENGLISH LEX (keep accent mouth-shape): {h['lex']}",
    ]
    for r in h["rules"]:
        lines.append(f"   • {r}")
    if not explicit and tier in ("hot", "filthy"):
        lines.append(
            "   • Explicit gate is OFF — use urgency/volume of this tier but NO graphic "
            "anatomy or degradation nouns until the scene is explicit."
        )
    lines.append("SHAPE EXAMPLES (rewrite into THIS accent + THIS scene — don't paste raw):")
    for ex in h["examples"]:
        lines.append(f"   • \"{ex}\"")
    # Accent-specific heat slips
    hs = (_HEAT_SLIPS.get(key) or {}).get(tier) or (_HEAT_SLIPS.get(key) or {}).get(
        "hot" if tier == "filthy" else ""
    )
    if hs and (explicit or tier in ("soft", "warm")):
        if tier in ("hot", "filthy") and not explicit:
            pass  # already warned
        else:
            lines.append(
                f"ACCENT HEAT SLIPS for {tier} (use 1–3 total across the clip, varied): "
                + " · ".join(hs[:8])
            )
    if tier in ("hot", "filthy") and explicit:
        lines.append(
            "MAP intensity into the accent: e.g. Cockney \"take it you fuckin' slag\", "
            "Russian \"давай… take it… сука\", German \"nimm es… Schlampe\", "
            "French \"prends-le… salope\" — ALWAYS still accented English + rare slip, "
            "never a monologue of only curses."
        )
    lines.append("")
    return "\n".join(lines)


_ALIASES = {
    "chinese": "mandarin",
    "spain": "spanish_castilian",
    "spanish": "spanish_latin",
    "mexico": "spanish_latin",
    "mexican": "spanish_latin",
    "brazil": "portuguese",
    "brazilian": "portuguese",
    "portugal": "portuguese",
    "british": "rp_british",
    "uk": "rp_british",
    "england": "rp_british",
    "posh": "rp_british",
    "bbc": "rp_british",
    "london": "cockney",
    "scot": "scottish",
    "scotland": "scottish",
    "ireland": "irish",
    "liverpool": "scouse",
    "newcastle": "geordie",
    "yorkshire": "northern_english",
    "manchester": "northern_english",
    "wales": "welsh",
    "aussie": "australian",
    "australia": "australian",
    "jamaican": "jamaican_rasta",
    "jamaica": "jamaican_rasta",
    "rasta": "jamaican_rasta",
    "rastafari": "jamaican_rasta",
    "reggae": "jamaican_rasta",
    "patois": "jamaican_rasta",
    "yardie": "jamaican_rasta",
    # caribbean alone → jamaican default; trini/soca map separate
    "caribbean": "jamaican_rasta",
    "trinidad": "trinidadian",
    "tobago": "trinidadian",
    "trini": "trinidadian",
    "soca": "trinidadian",
    "russia": "russian",
    "ru": "russian",
    "deutsch": "german",
    "germany": "german",
    "france": "french",
    "paris": "french",
    "korea": "korean",
    "japan": "japanese",
    "india": "indian_english",
    "hindi": "indian_english",
    "nigeria": "nigerian_english",
    "naija": "nigerian_english",
    "pidgin": "nigerian_english",
    "ghana": "ghanaian_english",
    "ghanaian": "ghanaian_english",
    "accra": "ghanaian_english",
    "sa": "south_african_english",
    "afrikaans": "south_african_english",
    "kenya": "swahili",
    "kenyan": "swahili",
    "east_africa": "swahili",
    "filipino": "filipino_english",
    "philippines": "filipino_english",
    "pinoy": "filipino_english",
    "tagalog": "filipino_english",
    "kiwi": "new_zealand",
    "newzealand": "new_zealand",
    "nz": "new_zealand",
    "us_south": "southern_us",
    "southern": "southern_us",
}


def detect_accent(intent: str) -> str:
    t = (intent or "").lower()
    if not t:
        return ""
    for key, spec in ACCENTS.items():
        for trig in spec["triggers"]:
            if re.search(r"\b" + trig + r"\b", t):
                return key
    return ""


def resolve_accent_key(intent: str = "", force_key: str | None = None) -> str:
    key = (force_key or "").strip().lower() if force_key else ""
    if key in ("", "auto", "none", "off"):
        key = ""
    if key and key not in ACCENTS:
        key = _ALIASES.get(key, key)
    if not key or key not in ACCENTS:
        key = detect_accent(intent)
    return key if key in ACCENTS else ""


def list_accent_keys() -> list:
    """Stable UI order: English-sphere first, then alpha rest."""
    priority = [
        # UK / Ireland
        "cockney", "scottish", "irish", "scouse", "geordie", "northern_english",
        "welsh", "rp_british",
        # ANZ / US
        "australian", "new_zealand", "southern_us",
        # Caribbean (listen niches)
        "jamaican_rasta", "trinidadian",
        # Africa
        "nigerian_english", "ghanaian_english", "south_african_english", "swahili",
        # Asia English
        "indian_english", "filipino_english",
        # Europe / rest
        "french", "german", "spanish_latin", "spanish_castilian", "italian",
        "portuguese", "russian", "polish", "czech",
        "korean", "japanese", "mandarin", "thai", "vietnamese",
        "dutch", "swedish", "norwegian", "greek", "arabic", "hebrew",
    ]
    keys = list(ACCENTS.keys())
    out = [k for k in priority if k in ACCENTS]
    out += sorted(k for k in keys if k not in out)
    return out


# ─────────────────────────────────────────────────────────────────────────────
#  PROMPT BLOCKS
# ─────────────────────────────────────────────────────────────────────────────

def identity_label(key_or_name: str) -> str:
    """Short nationality/region tag for identity lines: 'Scottish', 'Korean', 'Southern US'."""
    if key_or_name in ACCENTS:
        nm = ACCENTS[key_or_name]["name"]
    else:
        nm = key_or_name or ""
    # strip parenthetical notes: "Cockney (London)" → "Cockney"
    nm = re.sub(r"\s*\([^)]*\)\s*", "", nm).strip()
    # "Spanish (Latin America)" after strip might leave Spanish — ok
    if not nm:
        return "foreign-accented"
    return nm


def _person_noun(lead_gender="auto", role="lead") -> str:
    """woman / man for identity phrasing from lead control; auto → woman as default example."""
    g = (lead_gender or "auto").lower()
    if role == "partner":
        if g in ("male", "man", "m"):
            return "woman"
        if g in ("female", "woman", "f"):
            return "man"
        return "man"  # default partner example opposite of default woman lead
    if g in ("male", "man", "m"):
        return "man"
    if g in ("female", "woman", "f"):
        return "woman"
    return "woman"  # auto: example uses woman; instruction also allows man from intent


def _voice_line_templates(nm, acoustic, lead_gender="auto", pov=False, pov_gender="female"):
    g = (lead_gender or "auto").lower()
    if g in ("male", "man", "m"):
        primary = f"His voice: English with a heavy {nm} accent — {acoustic}."
    elif g in ("female", "woman", "f"):
        primary = f"Her voice: English with a heavy {nm} accent — {acoustic}."
    elif pov:
        # On-screen partner
        if (pov_gender or "female").lower() == "male":
            primary = f"Her voice: English with a heavy {nm} accent — {acoustic}."
        else:
            primary = f"His voice: English with a heavy {nm} accent — {acoustic}."
    else:
        # Singular default — "Their voices" reads wrong on solo. Pair scenes still get dual.
        primary = f"Voice: English with a heavy {nm} accent — {acoustic}."
    dual = (
        f"Both speakers' voices: English with a heavy {nm} accent — {acoustic}. "
        "Every spoken line is accented English, not fluent unaccented native speech."
    )
    return primary, dual


def _flat_slips(spec: dict) -> list:
    slips = spec.get("slips") or {}
    out = []
    for _, words in slips.items():
        out.extend(words)
    # de-dupe preserve order
    seen, uniq = set(), []
    for w in out:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    return uniq


def _dedupe_phrases(items: list, *, max_n: int = 20) -> list[str]:
    """Case-insensitive de-dupe; keep short seasoning phrases."""
    seen, out = set(), []
    for raw in items or []:
        w = re.sub(r"\s+", " ", str(raw or "").strip())
        if not w or len(w) > 42:
            continue
        k = w.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(w)
        if len(out) >= max_n:
            break
    return out


def ensure_adlibs(spec: dict) -> list[str]:
    """Return ~12–15 ad-libs for this accent — hand bank first, then fill without doubles.

    Prefer explicit adlibs[]; else openers + slips + short scene_bits. Never
    re-lists the same token twice. This is the natural seasoning pool so Intent
    does not need \"ja?\" / \"seen?\" typed by the user.
    """
    if not spec:
        return []
    bank: list[str] = []
    # 1) Hand-tuned adlibs (top priority)
    bank.extend(spec.get("adlibs") or [])
    # 2) Openers (single tags that open a line)
    bank.extend(spec.get("openers") or [])
    # 3) Flat slips (all buckets)
    bank.extend(_flat_slips(spec))
    # 4) Short scene bits (already phrase-shaped)
    for b in spec.get("scene_bits") or []:
        if len(str(b)) <= 36:
            bank.append(str(b))
    # 5) Ultra-short example fragments only if still thin
    if len(_dedupe_phrases(bank, max_n=20)) < 10:
        for ex in _all_examples(spec, explicit=True)[:6]:
            # take first clause of example if short
            bit = str(ex).split("…")[0].strip() if "…" in str(ex) else str(ex)
            if len(bit) <= 28:
                bank.append(bit)
    return _dedupe_phrases(bank, max_n=15)


def _all_examples(spec: dict, explicit: bool) -> list:
    ex = spec.get("examples") or {}
    if isinstance(ex, list):
        return list(ex)
    order = ["casual", "heated"]
    if explicit:
        order.append("intimate")
    lines = []
    for k in order:
        lines.extend(ex.get(k) or [])
    # also intimate always last few if not explicit for shape
    if not explicit:
        lines.extend((ex.get("intimate") or [])[:2])
    return lines


def _seed_palette(spec: dict, seed: int = 0, n: int = 12, scene_blob: str = "") -> list:
    """Pick 10–15 non-repeating AD-LIBS / slips for THIS clip only.

    Priority: hand adlibs → openers → slips → short scene_bits.
    Seeded so re-rolls rotate material; no doubles; scene_blob lightly prefers matches.
    """
    import random
    # Ad-lib bank is the spine (already de-duped, ~15 max)
    adlibs = ensure_adlibs(spec)
    # Optional extras only if adlibs thin — never re-add same tokens
    have = {a.lower() for a in adlibs}
    extras: list[str] = []
    for b in (spec.get("scene_bits") or []):
        s = str(b).strip()
        if s and s.lower() not in have and len(s) <= 40:
            extras.append(s)
            have.add(s.lower())
    for ex in _all_examples(spec, explicit=True)[:5]:
        s = str(ex).strip()
        if s and s.lower() not in have and len(s) <= 40:
            extras.append(s)
            have.add(s.lower())

    uniq = adlibs + extras
    if not uniq:
        return []
    name = spec.get("name") or "x"
    stable = sum(ord(c) for c in name) & 0xFFFF
    rng = random.Random(int(seed or 0) ^ stable)
    blob = (scene_blob or "").lower()
    preferred, rest = [], []
    for w in uniq:
        wl = w.lower()
        words = [t for t in re.findall(r"[a-zA-Z\u00C0-\u024F']{3,}", wl) if t not in (
            "the", "and", "for", "you", "that", "this", "like", "with", "look",
        )]
        if any(t in blob for t in words[:3]):
            preferred.append(w)
        else:
            rest.append(w)
    rng.shuffle(preferred)
    rng.shuffle(rest)
    # Keep first ~half of adlibs order-stable-ish: adlibs head, then shuffled rest
    # so core language tags always show; seed rotates the tail
    n = max(10, min(15, int(n or 12)))
    core = adlibs[: min(8, len(adlibs))]
    tail = [w for w in (preferred + rest) if w not in core]
    rng.shuffle(tail)
    ordered = core + tail
    # de-dupe again after merge
    return _dedupe_phrases(ordered, max_n=n)


def _ensure_scene_bits(spec: dict) -> list:
    """If accent has no scene_bits, synthesize 12 from slips+examples (non-repeating)."""
    existing = list(spec.get("scene_bits") or [])
    if len(existing) >= 10:
        return existing
    built = list(existing)
    for w in _flat_slips(spec):
        if w not in built:
            built.append(w)
    for ex in _all_examples(spec, explicit=True):
        if ex not in built:
            built.append(ex)
    return built[:15]


def _one_speaker_lock(key: str, *, role_label: str, voice_line: str,
                      explicit: bool, energy: int, examples_n: int = 8,
                      lead_gender="auto", pov=False, pov_gender="female",
                      role="lead", seed: int = 0, scene_blob: str = "",
                      mode: str = "t2v", emit_heat: bool = True) -> list:
    """Build lock lines for a single speaker key."""
    s = ACCENTS[key]
    nm = s["name"]
    adj = identity_label(key)
    person = _person_noun(lead_gender, role=role)
    # If auto, still prefer matching she/he in intent — example uses person; note both
    art = "An" if adj[:1].lower() in "aeiou" else "A"
    openers = s.get("openers") or []
    slips = s.get("slips") or {}
    adlibs = ensure_adlibs(s)
    examples = _all_examples(s, explicit)
    anti = s.get("anti") or []
    tier = heat_tier(energy)
    palette = _seed_palette(s, seed=seed, n=12, scene_blob=scene_blob)
    # ensure we always show ≥10 if bank allows
    if len(palette) < 10:
        palette = _seed_palette(
            {**s, "scene_bits": _ensure_scene_bits(s), "adlibs": adlibs},
            seed=seed, n=12, scene_blob=scene_blob,
        )
    look = pick_character_profile(
        key, lead_gender=lead_gender, role=role, seed=seed,
    )
    identity_open = format_identity_opener(
        key, look, lead_gender=lead_gender, role=role,
        intent=scene_blob, seed=seed, mode=mode,
    )
    # Show 2 alt looks for variety awareness (same gender bank)
    gender = _profile_gender(lead_gender, role)
    alt_bank = (CHARACTER_PROFILES.get(key) or {}).get(gender) or []
    alts = [x for x in alt_bank if x != look][:2]

    L = [
        f"\n── SPEAKER: {role_label} — {nm.upper()} ──",
        f"DEFAULT LANGUAGE: ENGLISH with a heavy {nm} accent.",
        "",
        "0) IDENTITY + LOOK (mandatory — FIRST body section after any I2V/POV open):",
        f"   Name WHO they are with the {adj} tag baked in. Match she→{adj} woman, he→{adj} man.",
    ]
    is_i2v = (mode or "").lower() == "i2v"
    if is_i2v:
        L += [
            "   I2V: the START IMAGE is law for face/hair/skin/wardrobe. Do NOT invent a new ethnicity.",
            f"   Still tag them as {adj} in prose if the face can support it; otherwise voice line only.",
            f"   GOOD: \"{art} {adj} {person} [matching the start image hair/skin] …\"",
            "   BAD: restaging a different race/hair than the still just to match an accent seed.",
        ]
    else:
        L += [
            "   T2V: USER INTENT > look-seed. Intent names hair/skin/build/age/wardrobe → use those.",
            "   Look-seed below only FILLS GAPS the intent left blank (never overwrite intent).",
            f"   ★ OPEN LIKE: \"{identity_open} stands…\" / faces the view…",
            "   Still bake the accent identity tag so voice and face match (Scottish ≠ Korean look).",
        ]
        if alts:
            L.append("   Other gap-fill looks for this accent (only if intent silent on hair/skin):")
            for a in alts:
                L.append(
                    f"      · {format_identity_opener(key, a, lead_gender=lead_gender, role=role, intent=scene_blob, seed=seed + 1, mode=mode)}"
                )
        L += [
            f"   GOOD: \"{identity_open} …\" then action.",
            f"   BAD:  plain \"a woman…\" with no {adj} tag, or dropping intent body facts for a seed look",
            "   BAD:  voice line only, open still ignores petite/small breasts/age the user wrote",
            "   Intent body/age/wardrobe keywords MUST land in this open when present.",
            "   Auto age 19–28 only when intent named no age.",
        ]
    L += [
        "   Accent = identity from frame one.",
        "",
        "1) SETUP VOICE LINE (same first section or first speech — almost verbatim):",
        f"   • \"{voice_line}\"",
        "   Without BOTH (0) identity+look AND (1) voice line, LTX treats them as plain English.",
        "",
        "HOW THIS SPEAKER TALKS:",
        "   • Most words = accented ENGLISH (grammar + rhythm below).",
        "   • AD-LIBS / slips = occasional, moment-fit seasoning from THIS language's list — "
        "do NOT require the user to type them in Intent; you add them naturally.",
        "   • VARIETY LOCK: never reuse the same ad-lib twice; never reuse the same full line twice.",
        "   • NEVER phonetic comedy spelling of English.",
        "   • NEVER tack one particle (ja? / aye / mon / ne? / seen?) onto every line — sounds silly.",
        "GRAMMAR / RHYTHM:",
    ]
    for g in s.get("grammar") or []:
        L.append(f"   • {g}")
    L.append(f"   • PACING: {s.get('prosody', 'short clauses; natural … pauses')}")
    L.append(
        f"AD-LIBS FOR {nm.upper()} (this language's mini-phrases — sprinkle when the beat fits: "
        "agree / surprise / urge / intimate. Each at most ONCE. Do not dump the list. "
        "Do not invent a different repeated tag):"
    )
    if adlibs:
        L.append("   " + " · ".join(f'"{p}"' for p in adlibs[:15]))
    else:
        L.append("   (light regional lexis sparingly)")
    L.append(
        "THIS CLIP SEED PALETTE (rotated subset for THIS seed — prefer these over inventing new tags; "
        "each at most ONCE):"
    )
    if palette:
        L.append("   " + " · ".join(f'"{p}"' for p in palette))
    else:
        L.append("   (use ad-libs above sparingly)")
    # Context buckets: only show items NOT already in adlibs (no double list)
    ad_set = {a.lower() for a in adlibs}
    def _ctx_unique(label, arr):
        if not arr:
            return None
        rest = [w for w in arr if str(w).lower() not in ad_set]
        if not rest:
            return None
        return f"   • {label}: " + " · ".join(rest[:6])
    extra_buckets = [
        _ctx_unique("agree / yes", slips.get("agree")),
        _ctx_unique("urge / more", slips.get("urge")),
        _ctx_unique("surprise", slips.get("surprise")),
        _ctx_unique("intimate", slips.get("intimate")),
        _ctx_unique("soft / wait", slips.get("soft")),
    ]
    extra_buckets = [x for x in extra_buckets if x]
    if extra_buckets:
        L.append("EXTRA SLIP BUCKETS (only if palette/ad-libs already used — still no doubles):")
        L.extend(extra_buckets)
    if openers:
        op_show = [o for o in openers[:6] if str(o).lower() not in ad_set]
        if op_show:
            L.append(
                "OPTIONAL FIRST-LINE OPENERS (at most once): "
                + " · ".join(f'\"{o}\"' for o in op_show)
            )
    # English L1-hard words — plant as props/stakes (correct spelling; shows accent colour)
    shibs = get_shibboleths(key, seed=seed, n=6)
    if shibs:
        L.append(
            f"ENGLISH SHIBBOLETHS for {nm.upper()} (L1-hard words — plant 1–3 naturally "
            "as props/stakes inside accented English lines this clip; CORRECT spelling only; "
            "NEVER comedy phonetic like ze/zis/wery; each word at most ONCE):"
        )
        L.append("   " + " · ".join(f'"{w}"' for w in shibs))
    L.append("FAILURE MODES for this speaker:")
    L += [
        "   • Fluent unaccented English + one token foreign word at the end",
        "   • Same particle spam every line (ja? ja? / aye aye / mon mon / seen? seen?)",
        "   • Phonetic misspellings of English",
        "   • Dumping the whole shibboleth list in one line — plant 1–3 as real props only",
        "   • Mouth heat band ignored (too soft or too filthy for the setting)",
        "   • Burning the whole ad-lib list in two lines — season, don't wallpaper",
        "   • Ignoring the language ad-lib bank and inventing American slang instead",
    ]
    for a in anti:
        L.append(f"   • {a}")
    L.append("VOICE SHAPE SAMPLES (rewrite to THIS scene — do not paste all):")
    for ex in examples[:examples_n]:
        L.append(f"   • \"{ex}\"")
    # Heat is global (one mouth-heat band for the whole clip), so the dual path
    # emits it once after both locks instead of repeating it verbatim per speaker.
    if emit_heat:
        L.append(_heat_block(key, energy, explicit))
    L.append(
        f"CHECK ({role_label}): accented English, varied rare slips from palette, "
        f"heat={tier}/{heat_label(energy)}, no repeated particle."
    )
    return L


def _infer_lead_gender(intent: str, lead_gender: str = "auto") -> str:
    """If UI left auto, peek intent for he/she/man/woman so voice line isn't plural-solo."""
    g = (lead_gender or "auto").lower().strip()
    if g not in ("", "auto", "none"):
        return g
    t = (intent or "").lower()
    # explicit role words first
    if re.search(r"\b(a |the )?(man|guy|bloke|lad)\b|\bhe\b|\bhis\b", t) and not re.search(
        r"\b(a |the )?woman\b|\bshe\b", t
    ):
        return "male"
    if re.search(r"\b(a |the )?(woman|girl|lass)\b|\bshe\b|\bher\b", t) and not re.search(
        r"\b(a |the )?man\b|\bhe\b", t
    ):
        return "female"
    return g or "auto"


def accent_block(intent, explicit=False, force_key=None,
                 partner_key=None,
                 lead_gender="auto", pov=False, pov_gender="female",
                 energy=5, mouth_level=None, seed: int = 0, mode: str = "t2v"):
    """
    HARD accent lock. English + accent + OCCASIONAL context slips.

    energy / mouth_level scales dialect heat (filth) of English inside the accent.
    partner_key: optional second accent for the other speaker (pair scenes).
    seed: rotates the non-repeating slip palette + character look seed for this clip.
    mode: t2v gets phenotype look seeds; i2v defers look to the start image.
    """
    # Map qualitative mouth level → energy if provided
    if mouth_level is not None:
        try:
            from .intensity_ld import level_to_energy, coerce_level
        except ImportError:
            from intensity_ld import level_to_energy, coerce_level
        energy = level_to_energy(coerce_level(mouth_level))

    lead_gender = _infer_lead_gender(intent, lead_gender)
    key = resolve_accent_key(intent, force_key)
    pkey = ""
    if partner_key and str(partner_key).lower() not in ("", "off", "none", "auto"):
        pkey = resolve_accent_key("", partner_key)
        if pkey == key:
            pkey = ""  # same accent → single lock is enough

    if not key and not pkey:
        return ""

    scene_blob = intent or ""
    mode = (mode or "t2v").lower()

    # Single-accent path (classic)
    if key and not pkey:
        s = ACCENTS[key]
        nm = s["name"]
        acoustic = s["acoustic"]
        primary, dual = _voice_line_templates(
            nm, acoustic, lead_gender=lead_gender, pov=pov, pov_gender=pov_gender,
        )
        adj = identity_label(key)
        look = pick_character_profile(key, lead_gender=lead_gender, role="lead", seed=seed)
        identity_open = format_identity_opener(
            key, look, lead_gender=lead_gender, role="lead",
            intent=scene_blob, seed=seed, mode=mode,
        )
        L = [
            f"\n━━ ACCENT LOCK — {nm.upper()} (NON-NEGOTIABLE) ━━",
            "Every spoken line in this clip uses this accent unless a per-speaker lock says otherwise.",
            f"Also valid setup line: \"{dual}\"",
            "GROK ACCENT RULE — first body section (after any I2V/POV open):",
            "  (1) IDENTITY + LOOK: nationality/region in WHO they are"
            + (f" — seed: \"{identity_open}…\"" if mode != "i2v" else f" — \"a {adj} woman/man…\""),
            "  (2) VOICE LINE: almost verbatim the setup sentence below.",
            "Without both, the model hears generic English even if one line mentions an accent later.",
            "T2V: phenotype must match the accent (a Scottish woman does not look like a Korean woman).",
            "I2V: start image wins on face — never invent a conflicting ethnicity.",
            "Then every spoken line keeps the grammar/rhythm — not fluent unaccented English + one foreign word.",
            "Write slips as real Unicode words (aye, irie, da, genau, oui) — never mojibake or ???.",
            "Slips are SEASONING from this clip's seed palette — never the same particle on every line.",
        ]
        L += _one_speaker_lock(
            key,
            role_label="LEAD / PRIMARY VOICE",
            voice_line=primary,
            explicit=explicit,
            energy=energy,
            examples_n=12,
            lead_gender=lead_gender,
            pov=pov,
            pov_gender=pov_gender,
            role="lead",
            seed=seed,
            scene_blob=scene_blob,
            mode=mode,
        )
        L += [
            "",
            "FINAL CHECK: first body section names a "
            f"{adj} woman/man (not plain \"a woman\")"
            + ("; look matches the accent seed" if mode != "i2v" else "; look honours start image")
            + "; voice line present; "
            "speech is accented English; slips varied and rare; "
            f"dialect heat matches mouth heat ({heat_tier(energy)}); no repeated particle; "
            "no phonetic comedy spelling of English words.",
            "",
        ]
        return "\n".join(L)

    # Dual-speaker path — resolve who is who BEFORE choosing header text
    partner = pkey or ""
    if not key and partner:
        # only partner forced — collapse to single-accent path (no dual header lie)
        key = partner
        partner = ""
        s = ACCENTS[key]
        nm = s["name"]
        acoustic = s["acoustic"]
        primary, dual = _voice_line_templates(
            nm, acoustic, lead_gender=lead_gender, pov=pov, pov_gender=pov_gender,
        )
        adj = identity_label(key)
        look = pick_character_profile(key, lead_gender=lead_gender, role="lead", seed=seed)
        identity_open = format_identity_opener(
            key, look, lead_gender=lead_gender, role="lead",
            intent=scene_blob, seed=seed, mode=mode,
        )
        L = [
            f"\n━━ ACCENT LOCK — {nm.upper()} (NON-NEGOTIABLE) ━━",
            "Every spoken line in this clip uses this accent unless a per-speaker lock says otherwise.",
            f"Also valid setup line: \"{dual}\"",
            "GROK ACCENT RULE — first body section (after any I2V/POV open):",
            "  (1) IDENTITY + LOOK: nationality/region in WHO they are"
            + (f" — seed: \"{identity_open}…\"" if mode != "i2v" else f" — \"a {adj} woman/man…\""),
            "  (2) VOICE LINE: almost verbatim the setup sentence below.",
            "Without both, the model hears generic English even if one line mentions an accent later.",
            "Then every spoken line keeps the grammar/rhythm — not fluent unaccented English + one foreign word.",
            "Slips are SEASONING from this clip's seed palette — never the same particle on every line.",
        ]
        L += _one_speaker_lock(
            key,
            role_label="LEAD / PRIMARY VOICE",
            voice_line=primary,
            explicit=explicit,
            energy=energy,
            examples_n=12,
            lead_gender=lead_gender,
            pov=pov,
            pov_gender=pov_gender,
            role="lead",
            seed=seed,
            scene_blob=scene_blob,
            mode=mode,
        )
        L += [
            "",
            "FINAL CHECK: first body section names a "
            f"{adj} woman/man (not plain \"a woman\")"
            + ("; look matches the accent seed" if mode != "i2v" else "; look honours start image")
            + "; voice line present; "
            "speech is accented English; slips varied and rare; "
            f"dialect heat matches mouth heat ({heat_tier(energy)}); no repeated particle; "
            "no phonetic comedy spelling of English words.",
            "",
        ]
        return "\n".join(L)

    s1 = ACCENTS[key]
    primary1, _ = _voice_line_templates(
        s1["name"], s1["acoustic"], lead_gender=lead_gender, pov=pov, pov_gender=pov_gender,
    )

    L = [
        "\n━━ PER-SPEAKER ACCENT LOCK (NON-NEGOTIABLE) ━━",
        "Two different accents. Each speaker keeps their own lock for the whole clip.",
        "Never blend accents mid-line. Never swap who has which accent mid-clip.",
        "When BOTH speak in one section, each line is tagged to its speaker by name/role/pronoun.",
    ]

    # Role labels
    g = (lead_gender or "auto").lower()
    if pov:
        lead_role = "ON-SCREEN PARTNER (the body we see)"
        partner_role = "SECOND ON-SCREEN VOICE (if any) / off-screen only as sound"
    elif g in ("male", "man", "m"):
        lead_role = "HE / MALE LEAD"
        partner_role = "SHE / PARTNER" if partner else ""
    elif g in ("female", "woman", "f"):
        lead_role = "SHE / FEMALE LEAD"
        partner_role = "HE / PARTNER" if partner else ""
    else:
        lead_role = "LEAD (primary subject)"
        partner_role = "PARTNER (second person)" if partner else ""

    L += _one_speaker_lock(
        key, role_label=lead_role, voice_line=primary1,
        explicit=explicit, energy=energy, examples_n=10,
        lead_gender=lead_gender, pov=pov, pov_gender=pov_gender, role="lead",
        seed=seed, scene_blob=scene_blob, mode=mode,
    )

    if partner and partner in ACCENTS:
        s2 = ACCENTS[partner]
        # Partner voice template opposite gender heuristic
        if g in ("male", "man", "m"):
            p_line = f"Her voice: English with a heavy {s2['name']} accent — {s2['acoustic']}."
        elif g in ("female", "woman", "f"):
            p_line = f"His voice: English with a heavy {s2['name']} accent — {s2['acoustic']}."
        else:
            p_line = f"Partner's voice: English with a heavy {s2['name']} accent — {s2['acoustic']}."
        L += _one_speaker_lock(
            partner, role_label=partner_role or "PARTNER",
            voice_line=p_line, explicit=explicit, energy=energy, examples_n=10,
            lead_gender=lead_gender, pov=pov, pov_gender=pov_gender, role="partner",
            seed=(int(seed or 0) + 17), scene_blob=scene_blob, mode=mode,
            emit_heat=False,  # heat is global — stated once below, not per speaker
        )
        adj1, adj2 = identity_label(key), identity_label(partner)
        L += [
            "",
            "DUAL-ACCENT RULES:",
            f"   • {lead_role} always sounds {s1['name']} — open as a {adj1} woman/man.",
            f"   • {partner_role or 'Partner'} always sounds {s2['name']} — open as a {adj2} woman/man.",
            "   • First section(s) must establish BOTH identities + voice lines if both will speak.",
            "   • Solo monologue: only the speaking person's accent + identity tag.",
            "   • VARIETY: each speaker has their own slip pool — do not share tags across speakers.",
            "",
        ]

    L.append(
        f"Dialect heat for both mouths tracks mouth-heat band ({heat_tier(energy)} / {heat_label(energy)})."
    )
    return "\n".join(L)


def accent_remember_line(intent: str = "", force_key: str | None = None,
                         energy: int = 5, mouth_level=None) -> str:
    if mouth_level is not None:
        try:
            from .intensity_ld import level_to_energy, coerce_level
        except ImportError:
            from intensity_ld import level_to_energy, coerce_level
        energy = level_to_energy(coerce_level(mouth_level))
    key = resolve_accent_key(intent, force_key)
    if not key:
        return ""
    s = ACCENTS[key]
    tier = heat_tier(energy)
    openers = s.get("openers") or []
    op = f" optional first-line opener from {openers[:3]}" if openers else ""
    adj = identity_label(key)
    return (
        f"• ACCENT LOCK ({s['name']}, heat={tier}/{heat_label(energy)}): "
        f"FIRST body section names a {adj} woman/man (not plain \"a woman\"); "
        f"voice line in that section; ENGLISH with {s['name']} grammar/rhythm; "
        f"occasional CONTEXT slips — never the same tag every line;{op}; "
        f"dialect filth scales with mouth heat (not body intensity)."
    )
