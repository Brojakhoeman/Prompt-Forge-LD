# -*- coding: utf-8 -*-
"""
styles_ld.py — VIDEO STYLE direction for PromptForge LD (mostly T2V)

Not a camera preset. A style is the whole path of the clip: genre, wardrobe
defaults, lighting, body energy, sound habit, and how user intent gets bent.

Default: None — returns "" so zero tokens are added unless the user picks one.
User intent is still law for identity/place/props when named.
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
#  STYLE BANK
#  key → dict(name, modes, tagline, doctrine, forces_explicit?, music_default?)
#  doctrine is injected ONLY when key is not None.
# ─────────────────────────────────────────────────────────────────────────────

_NONE = "None — off (no style path)"

STYLES = {
    _NONE: None,

    "✨ Gravure — slow body tease (close & personal)": {
        "name": "Gravure",
        "modes": ("t2v",),
        "tagline": "Sexy lingerie / sheer / soft Asian idol gravure path",
        "music_hint": "R&B / Soul or Ambient if music is on — soft, not club bangers",
        # Forces accented Asian mixed-English voice (see pick_gravure_asian_accent)
        "force_asian_accent": True,
        "doctrine": (
            "━━ VIDEO STYLE: GRAVURE (NON-NEGOTIABLE PATH) ━━\n"
            "This entire clip is GRAVURE — premium East-Asian idol / soft body-tease video. "
            "Not porn-sprint, not runway, not horror, not a phone vlog, not a locked-off tripod beauty still.\n"
            "\n"
            "LOOK (always):\n"
            "  East-Asian / K-beauty / J-beauty / C-beauty gravure model — soft features, clear skin, "
            "tasteful makeup, long dark or soft-coloured hair. Solo female lead by default.\n"
            "  If the user names a specific Asian look (Korean / Japanese / Chinese / Thai / Vietnamese), honour that. "
            "Do NOT default to Western / non-Asian casting for this style.\n"
            "\n"
            "VOICE / ACCENT (ALWAYS — non-negotiable):\n"
            "  She ALWAYS speaks accented mixed English — never flat native unaccented English. "
            "Grammar slightly off + soft L2 rhythm + occasional native slips (Korean / Japanese / Mandarin / "
            "Thai / Vietnamese — whichever the ACCENT LOCK / seed / intent picked). "
            "Short breathy lines about fabric, skin, light, camera, shy tease. "
            "Filth only if mouth-heat is aggressive / explicit is on.\n"
            "  Example shape: 'ah… this light is so soft on me' / 'wait… don't look there yet' — "
            "NOT polished native monologue.\n"
            "\n"
            "WARDROBE THEME (this is the style):\n"
            "  Sexy but tasteful by default — lingerie, sheer blouse, lace bra, silk slip, "
            "satin robe half-open, thigh-highs, soft knit that rides up, wet-look or translucent fabric. "
            "If the user names clothes, keep them but lean into how they cling, slip, or reveal. "
            "If the user names nothing, INVENT a lingerie/sheer/sexy-casual outfit and name fabric.\n"
            "  NEVER jump to full hardcore naked sex as the default path; undress is a slow tease chain "
            "if it happens at all (straps → shoulders → hem → not one-shot nude).\n"
            "\n"
            "BODY / TEMPO: unhurried. Weight shifts, hip sway, shoulder roll, hands trailing fabric, "
            "a strap sliding one centimetre, breath, eyes to the view then away. One body-motion per section.\n"
            "LIGHT: soft diffused, beauty-soft, bedroom/studio window glow — not horror contrast.\n"
            "\n"
            "CAMERA (ALWAYS HUNTING — never a still lock):\n"
            "  The camera is ALIVE. It does not sit on one frame for the whole clip. "
            "Each blank-line section should reframe: new angle, new distance, or a slow push/pull. "
            "Hunt for beauty — face CU → collarbone → waist/hip → fabric detail → ¾ body → "
            "over-shoulder glance → low hip-up → high looking-down. "
            "Drift, arc, orbit a few degrees, tilt to catch lace edge, push in on eyes/lips, "
            "pull back to show silhouette, slide to a side profile. "
            "Motion is soft and deliberate (beauty cam / idol BTS), NOT horror shake or phone vlog chaos.\n"
            "  BANNED camera: static locked tripod, one medium shot for every section, "
            "\"holds still on her face\" as the whole language of the clip.\n"
            "\n"
            "USER INTENT: keep named place/props; bend everything into this sexy slow hunting-cam path.\n"
            "BANNED: jump-cut sex, slam aggression, found-footage shake, comedy, crowd extras, "
            "unaccented native-English chatter, frozen single angle.\n"
        ),
    },

    "📱 Handheld phone vlog — arm's-length selfie": {
        "name": "Handheld phone vlog",
        "modes": ("t2v", "i2v"),
        "tagline": "Selfie phone; talk to lens while doing the day",
        "music_hint": "optional light pop/ambient; diegetic room sound first",
        "doctrine": (
            "━━ VIDEO STYLE: HANDHELD PHONE VLOG (NON-NEGOTIABLE PATH) ━━\n"
            "THEME: everyday personal vlog. The view IS a phone at arm's length (or selfie stick).\n"
            "WARDROBE: normal day clothes unless user says otherwise — hoodie, tee, jeans, loungewear. "
            "Not lingerie default, not formal editorial.\n"
            "BODY: micro shake, reframe, walk-and-talk, point phone at a prop then back at face. "
            "Imperfect handheld — NOT steadicam cinema.\n"
            "DIALOGUE: to the viewer (\"you\" OK in quotes); task + reaction + prop names.\n"
            "SOUND: room noise, footsteps, object foley; music secondary.\n"
            "USER INTENT: honour task/place; path always selfie-vlog.\n"
            "BANNED: gravure lingerie path, horror scares, multi-cam coverage, perfect tripod lock.\n"
        ),
    },

    "👻 Horror — dread & unease": {
        "name": "Horror",
        "modes": ("t2v", "i2v"),
        "tagline": "Eerie wardrobe/light; invent dread around user place",
        "music_hint": "Ambient / Atmospheric or Trailer tension if music on; else diegetic hush",
        "doctrine": (
            "━━ VIDEO STYLE: HORROR (NON-NEGOTIABLE PATH) ━━\n"
            "THEME: short dread beat. Mechanism fear — not the word 'scary'.\n"
            "WARDROBE: ordinary clothes that fit the place (coat in graveyard, nightshirt at home) — "
            "slightly wrong detail OK (mud, torn hem) if it serves dread. Not glam lingerie unless user asks.\n"
            "LIGHT: underexposed pockets, single practical, failing bulb, long shadow. Cool or sickly colour.\n"
            "BODY: slow approach, freeze, held breath, wrong stillness, a turn that shows empty space.\n"
            "INVENT: place-fitting horror beats (footsteps among stones, door that should stay shut) "
            "while keeping user people/place. Prefer practical fear over gore unless user asks gore.\n"
            "SOUND: hush, creak, single sharp hit; if music on, lean drone/tension (see MUSIC block).\n"
            "DIALOGUE: sparse whisper — leave/stay/did-you-hear-that.\n"
            "BANNED: bright beauty light, gravure tease, cheerful vlog, slapstick.\n"
        ),
    },

    "🎵 Music-video performance": {
        "name": "Music-video performance",
        "modes": ("t2v",),
        "tagline": "Performance path; HARD-HOOKS the Music dropdown when set",
        "music_hint": "REQUIRED energy from Music section when set — motion lands on that groove",
        "hooks_music": True,
        "doctrine": (
            "━━ VIDEO STYLE: MUSIC-VIDEO PERFORMANCE (NON-NEGOTIABLE PATH) ━━\n"
            "THEME: short music-video performance. Choreography and attitude over plot.\n"
            "WARDROBE: stage / clip-ready — statement outfit, boots, jacket, mic optional, "
            "performance makeup. If user names clothes, keep them and make them read on-beat.\n"
            "BODY: readable poses, hip/shoulder hits on the beat, hair/fabric accents on accents. "
            "Lip-sync only if the user asks to sing.\n"
            "MUSIC HOOK (critical):\n"
            "  • If a MUSIC / SOUNDTRACK preset is present below, that groove is LAW — "
            "describe motion landing on kicks, chorus lifts, drops. Name BPM feel from that block.\n"
            "  • If music is None/off, invent a clear beat in SOUND (count-in, kick, hook) and keep it consistent.\n"
            "LIGHT: performance lighting — backlight, colour wash, strobe optional on drops — not horror underexpose.\n"
            "DIALOGUE: sparse; ad-libs or short hook lines only if talkative; body does the work.\n"
            "USER INTENT: honour place/people; path is always performance-for-view.\n"
            "BANNED: slow gravure undress as the whole path, documentary phone shake, pure horror dread.\n"
        ),
    },

    "🎞 Found-footage / security cam energy": {
        "name": "Found footage",
        "modes": ("t2v", "i2v"),
        "tagline": "Diegetic cam; ordinary clothes; observational",
        "music_hint": "usually none — diegetic hum, fan, distant traffic",
        "doctrine": (
            "━━ VIDEO STYLE: FOUND FOOTAGE (NON-NEGOTIABLE PATH) ━━\n"
            "THEME: recovered / security / body-cam / camcorder. Observational, slightly wrong framing OK.\n"
            "WARDROBE: ordinary practical clothes for the place — not glamour default.\n"
            "BODY: people may not look at the view; natural tasks; occasional bad composition that stays readable.\n"
            "INVENT: why the camera is running (hallway cam, dashcam left on) if intent is thin.\n"
            "SOUND: room tone, compressor feel, no glossy score unless music is forced on.\n"
            "DIALOGUE: overheard / natural — not stage monologue.\n"
            "BANNED: beauty softbox default, music-video dance breaks, gravure lingerie path.\n"
        ),
    },

    "☕ Slice-of-life cinema": {
        "name": "Slice of life",
        "modes": ("t2v",),
        "tagline": "Everyday clothes; props; small human stakes",
        "music_hint": "soft ambient or none — diegetic cafe/street first",
        "doctrine": (
            "━━ VIDEO STYLE: SLICE-OF-LIFE CINEMA (NON-NEGOTIABLE PATH) ━━\n"
            "THEME: quiet realism. Small stakes — cold coffee, stuck key, last train, wet coat.\n"
            "WARDROBE: everyday — jeans, coat, sweater, work clothes. Not lingerie, not stage costume.\n"
            "BODY: natural continuous motion; rich prop handling; emotion visible, not melodramatic.\n"
            "LIGHT: natural practicals (window, cafe neon, kitchen strip).\n"
            "DIALOGUE: everyday, specific, prop-tied.\n"
            "USER INTENT: keep place/people; invent small grounded complications if thin.\n"
            "BANNED: horror monsters, gravure sexy default, music-video pose spam, hard explicit default.\n"
        ),
    },

    "👗 Fashion editorial / lookbook": {
        "name": "Fashion editorial",
        "modes": ("t2v",),
        "tagline": "Garment is the star; pose & fabric",
        "music_hint": "minimal techno / ambient / soft pop — attitude, not mosh",
        "doctrine": (
            "━━ VIDEO STYLE: FASHION EDITORIAL (NON-NEGOTIABLE PATH) ━━\n"
            "THEME: lookbook / editorial. Silhouette, fabric, attitude.\n"
            "WARDROBE: the star — tailored coat, designer dress, boots, statement jewelry. "
            "If user names nothing, invent a strong editorial outfit and name materials (wool, silk, leather).\n"
            "BODY: clear poses, slow turns that show the garment, hands on collar/hem/belt. Cool confidence.\n"
            "LIGHT: clean studio or fashion location — rim light, soft key, or hard editorial contrast.\n"
            "DIALOGUE: short, cool, optional.\n"
            "BANNED: porn path, horror, phone-vlog chaos, gym-sweat path.\n"
        ),
    },

    "🎤 Late-night confessional": {
        "name": "Late-night confessional",
        "modes": ("t2v",),
        "tagline": "Soft lamp; close face; private talk",
        "music_hint": "Ambient / Atmospheric if music on — low, not bangers",
        "doctrine": (
            "━━ VIDEO STYLE: LATE-NIGHT CONFESSIONAL (NON-NEGOTIABLE PATH) ━━\n"
            "THEME: private 2am honesty to the view.\n"
            "WARDROBE: soft private clothes — oversized tee, robe, sleep shirt, hoodie — not stage glam, "
            "not full lingerie set unless user asks.\n"
            "BODY: mostly still; micro motion (breath, mug, eye line, hair tuck). Face is the instrument.\n"
            "LIGHT: one warm practical lamp / phone glow / window night.\n"
            "DIALOGUE: lead — longer soft lines (low) (tired) (honest); invent stake if thin "
            "(apology, decision, memory).\n"
            "BANNED: party chaos, horror jumps, music-video dance, hard explicit as default.\n"
        ),
    },

    "🏃 Athletic / training diary": {
        "name": "Athletic training",
        "modes": ("t2v",),
        "tagline": "Gym kit; sweat; form & reps",
        "music_hint": "EDM / Hip-Hop / Rock if music on — motion hits the beat",
        "sync_music": True,
        "doctrine": (
            "━━ VIDEO STYLE: ATHLETIC TRAINING DIARY (NON-NEGOTIABLE PATH) ━━\n"
            "THEME: training diary — effort, form, sweat.\n"
            "WARDROBE: athletic kit — sports bra, shorts, leggings, tank, sneakers, sweat sheen. "
            "Name fabric stretch and damp patches when relevant.\n"
            "BODY: clear exercise mechanism (rep, grip, stance); breath and effort visible; no deform verbs.\n"
            "LIGHT: gym fluorescents / hard daylight / mirror wall — practical, not beauty softbox only.\n"
            "DIALOGUE: short status (\"two more\") or coach-self.\n"
            "If music is on, land reps on the beat (see MUSIC block).\n"
            "BANNED: pure gravure lingerie path, horror, headshot monologue with no physical work.\n"
        ),
    },

    "🌃 Night-drive / neon city": {
        "name": "Night drive",
        "modes": ("t2v",),
        "tagline": "Car + neon; night clothes; reflections",
        "music_hint": "R&B / Ambient / Electronic if music on — night drive score",
        "sync_music": True,
        "doctrine": (
            "━━ VIDEO STYLE: NIGHT-DRIVE / NEON CITY (NON-NEGOTIABLE PATH) ━━\n"
            "THEME: late city + car / wet street / neon.\n"
            "WARDROBE: night-out or night-casual — leather jacket, dark dress, hoodie, sunglasses optional. "
            "Not sunny picnic clothes.\n"
            "BODY: small motion (wheel, glance, city sliding past, window light on face) unless user asks more.\n"
            "LIGHT: neon streaks, dashboard glow, wet reflection, red tail-lights — colour on skin.\n"
            "DIALOGUE: late quiet or charged short lines (road, hour, next stop).\n"
            "USER INTENT: keep city/car; invent neon/wet texture if thin.\n"
            "BANNED: sunny slice-of-life default, cabin-in-woods horror unless user places it.\n"
        ),
    },

    "🔥 Explicit heat — slow filth": {
        "name": "Explicit heat",
        "modes": ("t2v",),
        "tagline": "Adult path; lingerie-to-skin OK; mechanism-first sex/tease",
        "music_hint": "R&B / Ambient if music on — slow groove not circus",
        "forces_explicit": True,
        "doctrine": (
            "━━ VIDEO STYLE: EXPLICIT HEAT — SLOW FILTH (NON-NEGOTIABLE PATH) ━━\n"
            "THEME: adult slow heat. Hungry but not jump-cut porn chaos.\n"
            "WARDROBE: starts sexy (lingerie, open shirt, nothing under a coat) → access chain if undressing; "
            "name anatomy when the act needs it. Honour mouth-state and garment mechanics.\n"
            "BODY: slow continuous sexual motion or heavy tease; one clear act progression.\n"
            "LIGHT: low warm practical / hotel lamp / night window — intimate, not horror green.\n"
            "DIALOGUE: filthy when free-mouth; wet sounds when occupied.\n"
            "Do not fade-to-black; this style welcomes explicit.\n"
            "BANNED: pure SFW slice-of-life, phone-vlog comedy, monster horror.\n"
        ),
    },

    "😌 Soft romance": {
        "name": "Soft romance",
        "modes": ("t2v",),
        "tagline": "Tender pair; soft clothes; closeness",
        "music_hint": "R&B / Soft Pop / Ambient if music on",
        "doctrine": (
            "━━ VIDEO STYLE: SOFT ROMANCE (NON-NEGOTIABLE PATH) ━━\n"
            "THEME: tender pair chemistry — almost-kiss, shared coat, umbrella, last train.\n"
            "WARDROBE: soft romantic casual — coat, dress, sweater, scarf. Not full lingerie unless user asks; "
            "not athletic kit.\n"
            "BODY: gentle touch, eye contact, shared props, slow lean-in. Pair cast preferred.\n"
            "LIGHT: warm golden / rain window / cafe practical.\n"
            "DIALOGUE: soft, specific, not empty flirt spam.\n"
            "Heat stays warm unless mouth-heat is aggressive.\n"
            "BANNED: horror, hard explicit default, documentary chaos, pure solo gravure unless user forces solo.\n"
        ),
    },

    "⛓ BDSM power exchange": {
        "name": "BDSM power exchange",
        "modes": ("t2v", "i2v"),
        "tagline": "Dom/sub path; collar/leather cues; command voice",
        "music_hint": "Ambient / dark electronic / industrial if music on — tension, not party",
        "forces_explicit": True,
        "doctrine": (
            "━━ VIDEO STYLE: BDSM POWER EXCHANGE (NON-NEGOTIABLE PATH) ━━\n"
            "THEME: short power-exchange beat. Who holds control is visible every section — "
            "voice, posture, props (collar, cuffs, leash, rope, crop, blindfold, chair, wall) — "
            "not a generic porn sprint.\n"
            "\n"
            "WHO IS WHO (honour user / scenario / POV):\n"
            "  • DOM / MISTRESS / MASTER: upright, measured motion, eye contact or look-down, "
            "short commands, honorifics expected (Ma'am / Mistress / Sir / Goddess as fits). "
            "Hands place, correct, or hold a prop with authority.\n"
            "  • SUB: lower posture (kneel, sit back on heels, bound stance, chin tilt up), "
            "slower reactive motion, short answers / yes-Ma'am / please — unless mouth is busy.\n"
            "  If POV is on: the VIEW is one body only. POV Mistress = view is the domme "
            "(sub fills frame at bottom edge / below). POV Sub = view is the sub "
            "(domme fills frame above / looking down). Never invent the viewpoint face/torso.\n"
            "\n"
            "WARDROBE DEFAULTS (when user does not name clothes):\n"
            "  Leather / latex / harness / corset / thigh boots / collar + ring / gloves — "
            "or smart dominant streetwear (blazer, heels) vs sub soft undergarments. "
            "If I2V: start-image wardrobe is law; only ADD small props the still can support "
            "(collar already there, handcuffs enter from edge, rope already on wrists).\n"
            "  Restraint: ENTER BEFORE USE — cuff/rope/collar must appear or be already on "
            "before it limits motion. Never teleport bondage mid-line.\n"
            "\n"
            "BODY / TEMPO: controlled. One power beat per section (order → compliance → reaction). "
            "Explicit acts OK when free mouths and access allow; mechanism-first. "
            "Do NOT default to full dungeon dungeon-spam — one clear restraint system is enough.\n"
            "LIGHT: low practicals, rim, cool or warm moody — not bright beauty vlog.\n"
            "DIALOGUE: power language (command / check / praise / denial). Free mouths only. "
            "Avoid empty 'obey' spam every line — concrete props and consequences.\n"
            "USER INTENT: keep named people/place; bend into power exchange.\n"
            "BANNED: soft romance path, phone-vlog comedy, music-video dance as the whole clip, "
            "horror monsters, vanishing restraints, viewpoint body invention in POV.\n"
        ),
    },
}

STYLE_KEYS = list(STYLES.keys())


def is_style_on(key) -> bool:
    if not key:
        return False
    k = str(key).strip()
    if not k or k.startswith("None"):
        return False
    return k in STYLES and STYLES[k] is not None


def resolve_style(key):
    if not is_style_on(key):
        return None
    return STYLES.get(str(key).strip())


def style_forces_explicit(key) -> bool:
    d = resolve_style(key)
    return bool(d and d.get("forces_explicit"))


def style_hooks_music(key) -> bool:
    d = resolve_style(key)
    return bool(d and d.get("hooks_music"))


def is_gravure_style(key) -> bool:
    """True when VIDEO STYLE is Gravure (forces Asian accented English + hunting cam)."""
    d = resolve_style(key)
    if d and d.get("name") == "Gravure":
        return True
    k = (key or "").lower()
    return "gravure" in k


# Seed / intent pick among these for gravure voice (always accented mixed English)
GRAVURE_ASIAN_ACCENTS = (
    "korean",
    "japanese",
    "mandarin",
    "thai",
    "vietnamese",
)


def pick_gravure_asian_accent(
    intent: str = "",
    seed: int = 0,
    force_key: str | None = None,
) -> str:
    """Which Asian accent gravure uses this generate.

    Priority:
      1) User forced accent if it is already in the Asian pool
      2) Intent names Korean / Japanese / Chinese / Thai / Vietnamese / etc.
      3) Seed-stable pick from GRAVURE_ASIAN_ACCENTS
    Always returns one of GRAVURE_ASIAN_ACCENTS (never empty, never Western).
    """
    import random as _random

    # Intent cues → specific Asian accent
    blob = f"{intent or ''} {force_key or ''}".lower()
    intent_map = (
        (("korean", "korea", "seoul", "busan", "k-pop", "kpop", "k-beauty"), "korean"),
        (("japanese", "japan", "tokyo", "osaka", "j-beauty", "idol jp", "gravure idol"), "japanese"),
        (("mandarin", "chinese", "china", "beijing", "shanghai", "taiwan", "c-beauty", "cantonese"), "mandarin"),
        (("thai", "thailand", "bangkok"), "thai"),
        (("vietnamese", "vietnam", "hanoi", "saigon", "ho chi minh"), "vietnamese"),
    )
    for cues, key in intent_map:
        if any(c in blob for c in cues):
            return key

    fk = (force_key or "").strip().lower()
    if fk in ("", "auto", "none", "off"):
        fk = ""
    if fk in GRAVURE_ASIAN_ACCENTS:
        return fk
    # Alias-ish
    if fk in ("chinese", "taiwanese", "cantonese"):
        return "mandarin"

    rng = _random.Random(int(seed or 0) & 0x7FFFFFFF)
    return rng.choice(list(GRAVURE_ASIAN_ACCENTS))


def style_block(key, mode: str = "t2v", intent: str = "",
                music_key: str = "", music_text: str = "",
                seed: int = 0, accent_hint: str = "") -> str:
    """Return doctrine text or '' (None = zero tokens).

    music_key / music_text: when style hooks music (music-video), hard-link the Music dropdown.
    """
    d = resolve_style(key)
    if not d:
        return ""
    modes = d.get("modes") or ("t2v",)
    m = (mode or "t2v").lower()
    if m not in modes:
        return ""
    body = d.get("doctrine") or ""
    if not body:
        return ""

    parts = [body]

    # Intent hook — style only fills gaps
    if (intent or "").strip():
        parts.append(
            "INTENT FIRST (FILL GAPS ONLY): User intent is supreme — who, body, age, wardrobe, action, place. "
            "This VIDEO STYLE only supplies genre path / tempo / camera habits / wardrobe defaults where intent "
            "is silent. Never overwrite a fact the user already named.\n"
        )

    # Gravure: stamp which Asian accent this seed/intent locked (matches ACCENT LOCK)
    if d.get("force_asian_accent") or is_gravure_style(key):
        ak = pick_gravure_asian_accent(intent, seed=seed, force_key=accent_hint or None)
        label = {
            "korean": "Korean",
            "japanese": "Japanese",
            "mandarin": "Mandarin Chinese",
            "thai": "Thai",
            "vietnamese": "Vietnamese",
        }.get(ak, ak)
        parts.append(
            f"━━ GRAVURE VOICE LOCK THIS CLIP: {label}-accented mixed English ━━\n"
            f"Every spoken line uses a heavy {label} L2 English accent (mixed English + occasional "
            f"native slips). Never switch to unaccented native English mid-clip. "
            f"Camera keeps hunting angles/CUs as above — never one static frame.\n"
        )

    # Music hard-hook for styles that care (especially music-video)
    mk = (music_key or "").strip()
    music_on = bool(mk) and not mk.startswith("None") and bool((music_text or "").strip())
    if d.get("hooks_music"):
        if music_on:
            parts.append(
                "━━ MUSIC ↔ STYLE LOCK (ACTIVE) ━━\n"
                f"Selected soundtrack: {mk}\n"
                "This Music preset is the rhythmic spine of the music-video. "
                "Every major motion, pose hit, hair/fabric accent, and section energy "
                "must sync to that groove (kicks, chorus lifts, drops described in the MUSIC block). "
                "Do not invent a conflicting genre of music.\n"
            )
        else:
            parts.append(
                "━━ MUSIC ↔ STYLE (NO PRESET PICKED) ━━\n"
                "Music dropdown is off/None. Invent a consistent diegetic beat in SOUND "
                "(kick pulse, clap, count-in) and keep motion locked to it for the whole clip. "
                "Hint: pick a Music preset (EDM, Hip-Hop, R&B, Rock…) for stronger results.\n"
            )
    elif music_on and d.get("sync_music"):
        parts.append(
            "━━ MUSIC SYNC (STYLE) ━━\n"
            f"Selected soundtrack: {mk}\n"
            f"Style note: {d.get('music_hint') or 'let motion land on the groove'}. "
            "When a MUSIC block is present, land at least one motion per section on a beat "
            "(step, rep, glance, fabric hit) — do not ignore the score.\n"
        )
    elif music_on and d.get("music_hint"):
        parts.append(
            f"MUSIC NOTE for this style: {d['music_hint']}. "
            "Honour the MUSIC / SOUNDTRACK block when present; lean diegetic if it fights the theme.\n"
        )

    return "".join(parts)


def list_style_keys(mode: str | None = None) -> list:
    out = [_NONE]
    m = (mode or "").lower().strip()
    for k, v in STYLES.items():
        if k == _NONE or v is None:
            continue
        if m and m in ("i2v", "t2v"):
            if m not in (v.get("modes") or ("t2v",)):
                continue
        out.append(k)
    return out
