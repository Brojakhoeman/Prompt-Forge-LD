"""
music_ld.py — Music / Soundtrack presets for PromptForge LD

Rhythm, BPM, instrumentation, how motion lands on the beat.
No vibe paint words (sensual/seductive/desire) — those fight THE CANON.
"""

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
        "The beat is relentless; motion is rhythmic and precise, hitting every kick with "
        "hip movement and body waves, freezing on the drop's silence. If the scene calls for vocals, "
        "they are breathy, processed pop toplines cutting through the mix. The bass is strong enough "
        "to vibrate glass."
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


def music_block(key: str) -> str:
    """Return the descriptive block for the selected music preset."""
    if not key or key not in MUSIC_PRESETS or MUSIC_PRESETS[key] is None:
        return ""
    return MUSIC_PRESETS[key]
