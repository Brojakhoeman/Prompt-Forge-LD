"""
negatives.py — NAG-aware LTX negatives.

Negatives actually steer when a NAG node is in the graph. Design law:
  1. ALWAYS block UI junk that never belongs (subtitles, watermarks, logos…).
  2. ALWAYS protect body mechanics LTX fails on (morph, extra limbs, head-only turn…).
  3. CONDITIONALLY block things that would fight the user's intent
     (music, cartoon, game, horror, interview, yelling, etc.).
  4. Never put a term in the negative that the positive is trying to achieve.

Build with context from the compose path so the negative ENHANCES the shot.
"""

from __future__ import annotations

import re

# ── Always on: never want these burned into the frame / track ───────────────
ALWAYS = [
    # text / UI overlays
    "subtitles", "captions", "on-screen text", "subtitle", "closed captions",
    "text overlay", "text", "watermark", "logo", "wordmark", "timestamp overlay",
    "lower third", "chyron", "channel bug",
    # quality / freeze junk
    "still image", "static frame", "frozen frame", "slideshow",
    "bad quality", "low quality", "blur", "blurry", "out of focus",
    "compression artifacts", "pixelation",
    # audio garbage that LTX sometimes invents as visual or tone
    "bleep", "bleeping", "beep", "beeping", "censor bar", "censoring", "censor",
    "pixelated censor",
    # body failure modes (render-safe)
    "morphing", "distortion", "warping", "flicker", "jitter",
    "extra limbs", "deformed hands", "wrong hand count", "fused fingers",
    "twisted neck", "head facing backward", "head only turn",
    "neck twist", "head swivel without body", "broken anatomy",
    "melting face", "identity swap mid clip",
    # Stand-up / turn failure modes LTX loves
    "detached head turn", "head rotating without shoulders",
    "neck cracking turn", "floating head above frozen torso",
    "legs frozen while torso rises", "body popping upright without weight shift",
    "exorcist head spin", "independent head tracking",
]

# Soft always — stability without killing intentional style
ALWAYS_SOFT = [
    "overlay effects", "HUD", "UI elements", "meme caption",
]

# ── Conditional banks ───────────────────────────────────────────────────────
MUSIC_OFF = [
    "background music", "soundtrack", "score music", "musical score",
    "bgm", "incidental music",
]

# Audio bed noise when we are NOT doing ASMR / intentional noise beds
NOISE_OFF = [
    "white noise", "static noise", "radio static", "tape hiss",
    "loud ambient noise bed",
]

# Game / CGI look — off unless intent asks for game/animation
GAME_OFF = [
    "pc game", "console game", "video game", "video game cutscene",
    "game UI", "health bar", "quest marker", "3d game render",
]

# Cartoon / childish — OFF unless animation style is requested
CARTOON_OFF = [
    "cartoon", "childish", "childlike proportions", "saturday morning cartoon",
    "comic book panel", "sticker art",
]

# Ugly generic — careful: only when not going for gritty/horror
UGLY_OFF = [
    "ugly", "grotesque deformity",
]

# Broadcast / talking-head formats that steal the shot
BROADCAST_OFF = [
    "newscast", "news anchor desk", "interview show", "podcast studio mic arm",
    "talk show set", "documentary interview",
]

# Horror / mutant — off unless asked
HORROR_OFF = [
    "horror", "mutant", "body horror", "jump scare face", "nightmare creature",
]

# Slow-mo — off unless asked (fights real-time LTX motion)
SLOWMO_OFF = [
    "slow-motion", "slow motion", "bullet time", "overcranked slowmo",
]

# Yelling — off when voice is ASMR/soft
YELLING_OFF = [
    "yelling", "screaming dialogue", "shouting match loudness",
]

POV_EXTRA = [
    "third person full body of viewer", "visible camera body",
    "filmed from behind the viewer", "viewer face in frame",
    "mirror selfie of viewpoint face", "reflection of viewpoint face",
    "viewer torso filling the whole frame from outside",
    "floating disembodied camera body",
]

GROUP_EXTRA = [
    "face swap between people", "identity morph between cast",
    "merging faces", "extra heads", "wrong number of people",
    "crowd morph", "duplicate face copies", "person count changing mid clip",
]

# When NOT on a BDSM/power path — avoid random dungeon spam
BDSM_OFF = [
    "random dungeon inventory", "teleporting handcuffs", "vanishing rope",
    "bondage appearing from nowhere",
]

# When BDSM/power path IS on — fight the failure modes
BDSM_ON = [
    "restraints vanishing mid clip", "cuffs disappearing", "rope teleport",
    "collar appearing without enter", "broken restraint physics",
]

TALKATIVE_EXTRA = [
    "silent mouth when speaking", "muted dialogue", "lips sealed while talking",
    "no speech when dialogue is required",
]

SILENT_EXTRA = [
    "clear spoken words", "readable dialogue lines", "conversation",
]

# Animation style LOCK — when we WANT animation, do NOT put cartoon in negatives;
# instead push against live-action photoreal collapse.
ANIMATION_KEEP_STYLE = [
    "photoreal human skin pores", "live action plate", "real world camera footage",
    "documentary realism", "uncanny real face on cartoon body",
]


def _blob(*parts) -> str:
    return " ".join(str(p or "") for p in parts).lower()


def _wants(blob: str, words) -> bool:
    return any(w in blob for w in words)


def detect_style_flags(
    *,
    intent: str = "",
    scenario: str = "",
    environment: str = "",
    music: str = "",
    motion_level: str = "normal",
    mouth_level: str = "normal",
    dialogue_tier: str = "standard",
    pov: bool = False,
    explicit: bool = False,
    cast: str = "pair",
    video_style: str = "",
) -> dict:
    """Booleans used by build() and by the brain (animation lock)."""
    b = _blob(intent, scenario, environment, music, video_style)
    animation = _wants(b, (
        "animation", "animated", "anime", "cartoon", "illustrated", "2d",
        "3d render", "cgi character", "pixar", "toon", "drawn", "comic style",
        "cel shaded", "stop motion", "claymation",
    ))
    game = _wants(b, ("video game", "pc game", "console game", "gameplay", "esport", "hud"))
    horror = _wants(b, ("horror", "mutant", "body horror", "nightmare", "monster", "gore"))
    broadcast = _wants(b, (
        "interview", "podcast", "newscast", "news anchor", "talk show", "documentary interview",
    ))
    slowmo = _wants(b, ("slow motion", "slow-mo", "slowmo", "bullet time", "overcrank"))
    wants_music = bool(music) and not str(music).lower().startswith("none")
    if _wants(b, ("background music", "soundtrack", "score music", "bgm", "musical score")):
        wants_music = True
    asmr_soft = (str(motion_level).lower() in ("asmr", "soft")
                 or str(mouth_level).lower() in ("asmr", "soft")
                 or _wants(b, ("asmr", "whisper", "soft voice")))
    silent = (dialogue_tier or "").lower() in ("none", "silent", "off")
    talkative = (dialogue_tier or "").lower() in ("talkative", "chatty", "dense", "rich")
    cast_l = (cast or "pair").lower()
    group = cast_l == "group" or _wants(b, ("group scene", "three people", "threesome", "crowd"))
    bdsm = _wants(b, (
        "bdsm", "bondage", "domme", "dominatrix", "mistress", "master", "submissive",
        "collar", "handcuff", "restraint", "power exchange", "femdom", "maledom",
    )) or "bdsm" in (video_style or "").lower() or "power exchange" in (video_style or "").lower()
    return {
        "animation": animation,
        "game": game,
        "horror": horror,
        "broadcast": broadcast,
        "slowmo": slowmo,
        "wants_music": wants_music,
        "asmr_soft": asmr_soft,
        "silent": silent,
        "talkative": talkative,
        "pov": bool(pov),
        "explicit": bool(explicit),
        "group": group,
        "bdsm": bdsm,
    }


def build(
    pov: bool = False,
    music: bool = False,
    talkative: bool = False,
    explicit: bool = False,
    *,
    intent: str = "",
    scenario: str = "",
    environment: str = "",
    music_key: str = "",
    motion_level: str = "normal",
    mouth_level: str = "normal",
    dialogue_tier: str = "standard",
    silent: bool = False,
    cast: str = "pair",
    video_style: str = "",
) -> str:
    """
    Compose the negative string for the pack / NAG node.

    Prefer passing intent/scenario/music so conditionals are smart.
    Legacy positional args still work.
    """
    flags = detect_style_flags(
        intent=intent,
        scenario=scenario,
        environment=environment,
        music=music_key or ("on" if music else ""),
        motion_level=motion_level,
        mouth_level=mouth_level,
        dialogue_tier="none" if silent else (dialogue_tier or ("talkative" if talkative else "standard")),
        pov=pov,
        explicit=explicit,
        cast=cast,
        video_style=video_style,
    )
    # honour explicit music=True from caller even without key
    if music:
        flags["wants_music"] = True
    if talkative:
        flags["talkative"] = True
    if silent:
        flags["silent"] = True

    terms: list[str] = []
    terms.extend(ALWAYS)
    terms.extend(ALWAYS_SOFT)

    if not flags["wants_music"]:
        terms.extend(MUSIC_OFF)
        terms.extend(NOISE_OFF)

    if not flags["game"] and not flags["animation"]:
        terms.extend(GAME_OFF)

    if not flags["animation"]:
        terms.extend(CARTOON_OFF)
    else:
        # Protect the animation look from collapsing into live-action
        terms.extend(ANIMATION_KEEP_STYLE)

    if not flags["horror"]:
        terms.extend(HORROR_OFF)
        terms.extend(UGLY_OFF)

    if not flags["broadcast"]:
        terms.extend(BROADCAST_OFF)

    if not flags["slowmo"]:
        terms.extend(SLOWMO_OFF)

    if flags["asmr_soft"]:
        terms.extend(YELLING_OFF)

    if flags["pov"]:
        terms.extend(POV_EXTRA)

    if flags.get("group"):
        terms.extend(GROUP_EXTRA)

    if flags.get("bdsm"):
        terms.extend(BDSM_ON)
    else:
        terms.extend(BDSM_OFF)

    if flags["talkative"]:
        terms.extend(TALKATIVE_EXTRA)
    if flags["silent"]:
        terms.extend(SILENT_EXTRA)

    # de-dupe, preserve order
    seen, out = set(), []
    for t in terms:
        k = t.lower().strip()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(t)
    return ", ".join(out)


def explain(**kwargs) -> dict:
    """Debug helper for tests / preview."""
    flags = detect_style_flags(**{
        k: kwargs[k] for k in (
            "intent", "scenario", "environment", "music",
            "motion_level", "mouth_level", "dialogue_tier", "pov", "explicit",
        ) if k in kwargs
    })
    neg = build(**kwargs)
    return {"flags": flags, "negative": neg, "term_count": len(neg.split(", "))}
