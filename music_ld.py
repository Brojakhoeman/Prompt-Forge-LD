"""
music_ld.py — Music / Soundtrack presets for PromptForge LD

Rhythm, BPM, instrumentation, how motion lands on the beat.
No vibe paint words (sensual/seductive/desire) — those fight THE CANON.

When a preset is selected, doctrine is injected EARLY in the system prompt so the
script plants the groove in the first body section (proven better for LTX).
"""

# Shared laws — "in the mix" (default loud) vs background (quiet under dialogue)
MUSIC_LAW_MIX = (
    "━━ MUSIC / SOUNDTRACK (IN THE MIX — PLANT EARLY + THROUGHOUT) ━━\n"
    "HARD RULES:\n"
    "1) OPEN PLANT (NON-NEGOTIABLE): After any I2V anchor line, the FIRST body section is identity + pose "
    "(vision honesty) AND the music already playing in that SAME section — genre/BPM/feel from the preset "
    "(kick, bass, groove). Music is part of the open, not a later afterthought.\n"
    "   BAD: open is only who/pose, music first appears in section 3+.\n"
    "   GOOD: 'A young woman with long brown hair kneels… A heavy EDM kick and bass already fill the room.'\n"
    "2) THROUGH-LINE: Keep the track alive after the open — re-mention the pulse/bass/groove at least once "
    "in the middle half and once more later (or on a strong action beat). Do not plant once and forget.\n"
    "3) MUSIC NEVER PAUSES FOR SPEECH: The track keeps playing under dialogue. "
    "People TALK OVER or SHOUT OVER the music (club/party/loud rooms = raised voice, shout, call out). "
    "BAD: music stops so someone can talk, then music restarts. "
    "GOOD: bass still thumping while he leans in and says / shouts the line; crowd yells over the drop.\n"
    "4) MOTION ON THE BEAT: hips, thrusts, steps, swallows, fabric peels land on kicks/downbeats "
    "when action is rhythmic.\n"
    "5) Singing only if the intent asks — when it does, prefer sings/croons with short lyrics "
    "(not only says). Otherwise music scores / drives motion and room energy.\n"
    "6) If VIDEO STYLE is Music-video performance, this soundtrack is the spine of the clip.\n"
    "\n"
    "PRESET FEEL (use this texture — LOUD / IN THE ROOM):\n"
)

MUSIC_LAW_BG = (
    "━━ MUSIC / SOUNDTRACK (BACKGROUND — QUIET UNDER) — SCORE VOLUME ONLY ━━\n"
    "This mode controls the SOUNDTRACK VOLUME only. It does NOT erase place, dance, "
    "performance energy, or accent colour from USER INTENT.\n"
    "HARD RULES (score prose only):\n"
    "1) OPEN PLANT (NON-NEGOTIABLE, SOFT): After any I2V anchor, the FIRST body section is identity + pose "
    "AND quiet music already under the room in that SAME section — genre from the quiet preset below. "
    "Use: faint / low / distant / under the room / soft speakers / quiet bass. "
    "Music is wallpaper in the open, not missing until halfway.\n"
    "   BAD: first half has zero music words; a loud techno line appears mid-clip.\n"
    "   GOOD: '…kneels… A faint techno kick ticks under the room.'\n"
    "2) THROUGH-LINE (SOFT): Re-mention the quiet score at least once mid-clip and once late "
    "(one short clause each) — still continuous, still quiet. Never the hero of every section, "
    "but never absent after the open either.\n"
    "3) VOLUME: Music stays QUIET and CONTINUOUS. Never pause for speech. Never duck to total silence. "
    "Never describe the TRACK as loud, deafening, room-shaking, vibrating glass/walls, thumping through the floor, "
    "or a 'loud techno beat pulsing through the room'.\n"
    "4) SPEECH vs MUSIC — BANNED PHRASES (never write these):\n"
    "   • shouted over the music / yelling over the bass / called over the drop / talks over the thumping kicks\n"
    "   • voice raised over the track / shouting over the heavy bass / screaming over the speakers\n"
    "   GOOD: says (intense): \"…\" / sings (warm): \"…\" / calls out — while a faint beat stays under the room.\n"
    "   Crowd, neon, booths, busy club BODIES are allowed when INTENT says club — that is place/people energy, "
    "NOT an excuse to make the soundtrack prose loud.\n"
    "5) Mouth heat / Intense may still make dialogue filthy or urgent — use brackets (intense) (urgent) (low) — "
    "but do NOT frame delivery as competing with a loud soundtrack.\n"
    "6) MOTION: do NOT force hip hits on every kick from the wallpaper score alone. "
    "IF intent asks for dance / dancefloor / club performance, still film real dance mechanisms "
    "(weight, hips, hands) — quiet score under the move. Dance is not banned by Background.\n"
    "7) Singing when intent asks: soft croon preferred under quiet score (never belt/shout-over the track). "
    "Still use sings/croons with short lyrics and ACCENT colour — do not collapse to plain US pop mush.\n"
    "\n"
    "QUIET PRESET (this is the only music texture — ignore any loud club-mix memory for the SCORE):\n"
)

# Back-compat name
MUSIC_LAW = MUSIC_LAW_MIX

MUSIC_PRESETS = {
    "None — LLM decides": None,

    "Classic Rock — driving guitars & pounding drums": (
        "Classic rock fills the scene — big electric guitars, pounding drums, "
        "120-135 BPM with a steady, anthemic groove. The rhythm is muscular and propulsive; "
        "every downbeat lands with weight, and the subject's motion syncs to it — steps, hip rolls "
        "and reaches hit the beat. If the scene calls for singing, the delivery is gritty and "
        "full-throated, almost shouting the chorus. If clothing comes off, each peel lands "
        "deliberately on a downbeat. The sound is loud and live, distortion and reverb filling the air."
    ),

    "Hip-Hop / Rap — heavy 808s & crisp hi-hats": (
        "Modern hip-hop / trap — deep 808 bass hits, rapid crisp hi-hats, "
        "130-145 BPM with a bouncy swing. The low end is physical; "
        "the body reacts to the sub frequencies with slow, heavy movement and chest pops on the kicks. "
        "If the scene calls for vocals, the style is melodic and confident — half-sung hooks. "
        "The mix is clean but bass-heavy enough to feel in the chest."
    ),

    "Classical / Orchestral — sweeping strings & dramatic builds": (
        "Classical music swells through the scene — lush strings, powerful brass, dramatic dynamic "
        "shifts, 60-90 BPM with long phrasing. The music has tension and release; "
        "motion is large and theatrical, big moves timed to the swells, stillness in the quiet bars. "
        "If the scene calls for singing, the voice is pure — long notes, controlled vibrato. "
        "The sound is rich and room-filling, like a concert hall."
    ),

    "Electronic / EDM — pulsing synths & four-on-the-floor": (
        "EDM / techno pulses through the scene — four-on-the-floor kick at 128 BPM, "
        "big supersaw synths, sidechained pads, builds and drops. "
        "The beat is relentless and continuous under everything; motion is rhythmic and precise, "
        "hitting every kick with hip movement, thrusts, or body waves. Spoken lines are shouted or "
        "called OVER the mix — the track does not duck out for dialogue. The bass is strong enough "
        "to vibrate glass and the floor."
    ),

    "Mainstream Pop — catchy hooks & bright production": (
        "Upbeat pop — bright synths, punchy drums, catchy melodic hooks, "
        "110-125 BPM, polished and radio-friendly. The groove is playful; motion is "
        "performative with timing to the chorus, eyes toward the view on the hook. "
        "If the scene calls for singing, the vocals are bright and confident. "
        "The music feels like a night drive with the windows down."
    ),

    "R&B / Soul — smooth grooves & warm bass": (
        "Smooth R&B / soul — warm electric piano, deep round bass, "
        "laid-back drums at 80-95 BPM, close and low. The pocket is slow and heavy; "
        "motion melts into the groove with body rolls and unhurried weight shifts. "
        "If the scene calls for singing, the voice is breathy and melismatic — runs and ad-libs. "
        "The sound is close and personal, low light, chest-level warmth."
    ),

    "Heavy Metal — aggressive riffs & double-kick drums": (
        "Heavy metal roars through the scene — chugging palm-muted guitars, fast double-kick drums, "
        "140-170 BPM, aggressive and intense. The energy is raw and physical; motion is powerful and "
        "precise — sharp moves, hair swings, actions timed to the riffs. If the scene calls for vocals, "
        "they are screamed or growled. The sound is distorted and loud enough to feel in the chest."
    ),

    "Country — twangy guitars & storytelling swing": (
        "Country music — acoustic and electric guitars with twang, "
        "steady train-beat drums, 100-120 BPM, warm and narrative. The feel is "
        "earthy; motion has an easy swagger that rides the swing. "
        "If the scene calls for singing, the voice is warm with a drawl, storytelling phrasing. "
        "The sound is honest and roadhouse-loud."
    ),

    "Funk / Disco — groovy basslines & funky drums": (
        "Funk / disco — slap bass locked with tight funky drums, wah guitar stabs, "
        "105-120 BPM, irresistible pocket. The groove demands movement — hips, shoulders and steps "
        "land inside the pocket, playful and loose. If the scene calls for vocals, they are soulful "
        "with falsetto flourishes. The sound is warm, punchy and alive."
    ),

    "Reggae / Dancehall — offbeat skank & deep bass": (
        "Reggae / dancehall — offbeat guitar skank, deep rolling bass, "
        "70-100 BPM (or double-time dancehall bounce), relaxed but insistent. Motion is loose-hipped "
        "and unhurried, winding with the riddim. If the scene calls for vocals, the delivery is "
        "melodic toasting or smooth singjay. The bass is deep enough to move through the floor."
    ),

    "Ambient / Atmospheric — pads & slow pulse": (
        "Ambient score — wide pads, soft low pulse at 60-80 BPM, sparse percussion. "
        "Motion is slow and continuous; holds last longer; small gestures read large. "
        "If the scene calls for vocals, they are quiet and close-miked. "
        "The sound is spacious with long reverb tails."
    ),

    "Cinematic Trailer — brass hits & rising tension": (
        "Trailer-style score — low brass hits, ticking percussion, rising strings, "
        "70-100 BPM building into heavier drops. Motion lands on impacts; stillness between hits. "
        "If the scene calls for vocals, they are sparse and spoken-word tight. "
        "The sound is large, compressed, and room-filling."
    ),
}

MUSIC_KEYS = list(MUSIC_PRESETS.keys())

# Background mode: short quiet genre skins (loud preset bodies fight QUIET doctrine).
MUSIC_PRESETS_BG = {
    "Classic Rock — driving guitars & pounding drums": (
        "Quiet classic-rock texture under the room — distant electric guitar and a soft mid-tempo drum pulse "
        "(about 120 BPM), low in the mix like a bar PA two rooms away. Continuous; never pauses for speech. "
        "No wall-of-amp volume, no shout-over-the-track framing."
    ),
    "Hip-Hop / Rap — heavy 808s & crisp hi-hats": (
        "Quiet hip-hop under the room — soft distant 808 thump and light hi-hat tick at a relaxed pocket, "
        "felt more than heard. Continuous wallpaper score. No chest-rattling subs, no yell-over-the-beat lines."
    ),
    "Classical / Orchestral — sweeping strings & dramatic builds": (
        "Quiet classical under the room — soft strings and a low sustained pad, gentle dynamics, "
        "like a film score played quietly. Continuous; never a concert-hall blast."
    ),
    "Electronic / EDM — pulsing synths & four-on-the-floor": (
        "Quiet EDM / techno under the room — faint four-on-the-floor kick (~128 BPM) and soft sidechained pads, "
        "distant club speakers or a low phone speaker on a table. Continuous faint pulse only. "
        "Never loud techno filling the room, never vibrating glass, never dialogue shouted over the mix."
    ),
    "Mainstream Pop — catchy hooks & bright production": (
        "Quiet pop under the room — bright soft synths and a light drum pocket, low volume like a car radio "
        "two rooms away. Continuous; never radio-blast loud."
    ),
    "R&B / Soul — smooth grooves & warm bass": (
        "Quiet R&B / soul under the room — warm electric piano, soft round bass, laid-back pocket (~80–95 BPM), "
        "close and low. Continuous intimate score; never club-loud."
    ),
    "Heavy Metal — aggressive riffs & double-kick drums": (
        "Quiet metal texture under the room — distant muted guitars and a soft double-kick murmur, "
        "like headphones leaking. Continuous; never arena volume or screamed-over-the-amps delivery."
    ),
    "Country — twangy guitars & storytelling swing": (
        "Quiet country under the room — soft acoustic twang and a gentle train-beat, low like a porch radio. "
        "Continuous; never roadhouse-blast."
    ),
    "Funk / Disco — groovy basslines & funky drums": (
        "Quiet funk / disco under the room — soft slap-bass pocket and light funky drums, low in the mix. "
        "Continuous groove wallpaper; never dance-floor blast."
    ),
    "Reggae / Dancehall — offbeat skank & deep bass": (
        "Quiet reggae / dancehall under the room — soft offbeat skank and a deep but quiet bass roll. "
        "Continuous; never sound-system pressure."
    ),
    "Ambient / Atmospheric — pads & slow pulse": (
        "Quiet ambient score — wide soft pads, slow low pulse, sparse percussion. Already wallpaper; keep it that way."
    ),
    "Cinematic Trailer — brass hits & rising tension": (
        "Quiet cinematic under the room — soft low brass murmurs and a distant ticking pulse, "
        "tension as atmosphere not trailer blast. Continuous and restrained."
    ),
}


def _truthy(v, default=False) -> bool:
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() not in ("0", "false", "off", "no", "")


def music_is_on(key: str) -> bool:
    if not key or key not in MUSIC_PRESETS:
        return False
    return MUSIC_PRESETS[key] is not None


def music_genre_label(key: str) -> str:
    """Short genre tag for open plants / scrub inject (e.g. 'EDM', 'R&B')."""
    if not key or not music_is_on(key):
        return "music"
    head = key.split("—")[0].strip()
    # "Electronic / EDM" → prefer punchy second tag when short
    if " / " in head:
        a, b = [p.strip() for p in head.split(" / ", 1)]
        if b and (len(b) <= 12 or len(b) <= len(a)):
            return b
        return a or b
    if " & " in head:
        head = head.split(" & ", 1)[0].strip()
    # Drop trailing dash fragments like "Hip-Hop" kept whole
    return head or "music"


def music_open_plant_phrase(key: str, background: bool = False) -> str:
    """One concrete clause for the identity OPEN when model/scrub need a plant."""
    genre = music_genre_label(key)
    if _truthy(background):
        return (
            f"A faint {genre} pulse sits under the room — quiet continuous score already playing."
        )
    return (
        f"{genre} already fills the room — kick and bass in the mix, continuous under everything."
    )


def music_block(key: str, background: bool = False) -> str:
    """Return law + preset prose for the selected music (empty if None / off).

    background=True → quiet under dialogue (normal speaking voice).
    background=False → in the mix (talk/shout over, motion on beat).
    """
    if not music_is_on(key):
        return ""
    bg = _truthy(background)
    if bg:
        body = (MUSIC_PRESETS_BG.get(key) or MUSIC_PRESETS.get(key) or "").strip()
        law = MUSIC_LAW_BG
    else:
        body = (MUSIC_PRESETS.get(key) or "").strip()
        law = MUSIC_LAW_MIX
    if not body:
        return ""
    return law + body + "\n"
