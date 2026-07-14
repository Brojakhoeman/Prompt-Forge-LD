"""
music_ld.py — Music / Soundtrack presets for PromptForge LD

Each entry provides rich, LTX-optimized description of how the music should feel,
how it drives the performance, rhythm for stripping/dancing, singing style,
and car-speaker vibe. These are injected as a dedicated block so the model
can sync actions and vocals to the music properly.

Format is similar to scenarios/environments for consistency.
"""

MUSIC_PRESETS = {
    "None — LLM decides": None,

    "Classic Rock — driving guitars & pounding drums": (
        "Classic rock blasting from the car stereo — big electric guitars, pounding drums, "
        "around 120-135 BPM with a steady, anthemic groove. The rhythm is muscular and propulsive; "
        "every downbeat should land with weight. Stripping should feel deliberate and powerful, "
        "hitting the beat with hip rolls and slow peels. Vocals are gritty and full-throated — "
        "she sings with rock attitude, almost shouting the chorus. The car speakers are turned up loud, "
        "distortion and reverb filling the night air."
    ),

    "Hip-Hop / Rap — heavy 808s & crisp hi-hats": (
        "Modern hip-hop / trap from the car — deep 808 bass hits, rapid crisp hi-hats, "
        "around 130-145 BPM with a bouncy but menacing swing. The low end is physical; "
        "her body should react to the sub frequencies with slow, heavy ass movements and "
        "chest pops on the kicks. Singing/ rapping style is melodic and confident, half-sung "
        "hooks with attitude. The music feels like it's coming from expensive car audio — "
        "clean but bass-heavy, rattling the chassis slightly."
    ),

    "Classical / Orchestral — sweeping strings & dramatic builds": (
        "Classical music pouring from the car — lush strings, powerful brass, dramatic dynamic shifts, "
        "60-90 BPM with long, emotional phrasing. The music has grandeur and tension/release. "
        "Stripping should feel elegant and theatrical, slow reveals timed to the swells. "
        "Her singing is operatic or classically trained — pure tone, long notes, emotional vibrato. "
        "The car audio sounds surprisingly rich, like a concert hall on wheels."
    ),

    "Electronic / EDM — pulsing synths & four-on-the-floor": (
        "EDM / techno thumping from the car — four-on-the-floor kick at 128 BPM, "
        "big supersaw synths, sidechained pads, euphoric builds and drops. "
        "The beat is relentless and hypnotic; her stripping should be rhythmic and almost "
        "robotic-sexy, hitting every kick with hip thrusts and body waves. "
        "She sings the topline with breathy, processed pop vocals that cut through the mix. "
        "The bass is so strong the car windows vibrate."
    ),

    "Mainstream Pop — catchy hooks & bright production": (
        "Upbeat pop from the car radio — bright synths, punchy drums, catchy melodic hooks, "
        "110-125 BPM, very polished and radio-friendly. The groove is fun and sexy. "
        "Stripping should feel playful and performative, with lots of eye contact and "
        "teasing timing to the chorus. She sings with bright, confident pop vocals, "
        "almost like she's putting on a show for the driver. The music feels like a "
        "summer night drive with the windows down."
    ),

    "R&B / Soul — smooth grooves & sensual bass": (
        "Smooth R&B / soul from the car — warm electric piano, deep round bass, "
        "laid-back drums at 80-95 BPM, very intimate and seductive. The pocket is "
        "sexy and slow. Stripping should be slow, sensual, and full of body rolls "
        "that melt into the groove. Her singing is breathy, melismatic, and emotional — "
        "lots of runs and ad-libs. The music feels close and personal, like the car "
        "is filled with warm, low light and desire."
    ),

    "Heavy Metal — aggressive riffs & double-kick drums": (
        "Heavy metal roaring from the car — chugging palm-muted guitars, fast double-kick drums, "
        "around 140-170 BPM, aggressive and intense. The energy is raw and physical. "
        "Stripping should feel powerful and almost violent in its precision — sharp movements, "
        "headbanging hair whips, aggressive clothing removal timed to the riffs. "
        "She screams or growls the vocals with real metal attitude. The car audio is "
        "distorted and loud enough to feel in your chest."
    ),

    "Country — twangy guitars & storytelling swing": (
        "Country music from the car — acoustic and electric guitars with twang, "
        "steady train-beat drums, 100-120 BPM, warm and narrative. The feel is "
        "earthy and a little outlaw. Stripping has a playful, teasing country-girl "
        "vibe — slow sways, boot taps, deliberate unbuttoning. She sings with a "
        "slight drawl and attitude, almost talking-singing the verses. The music "
        "feels like a dusty road at night with the windows cracked."
    ),

    "Funk / Disco — groovy basslines & funky drums": (
        "Funk and disco blasting from the car — fat slap bass, tight funky drums, "
        "bright horns, around 110-125 BPM with an irresistible pocket. Everything "
        "is about the groove. Her stripping should be extremely rhythmic and "
        "confident — lots of shoulder rolls, hip pops, and clothing removal that "
        "lands exactly on the one. She sings with sassy, soulful funk vocals. "
        "The car sounds like a party on wheels."
    ),

    "Reggae / Dancehall — offbeat skank & deep bass": (
        "Reggae or dancehall thumping from the car — offbeat guitar skank, "
        "heavy sub bass, drums at 70-85 BPM (half-time feel), very relaxed but "
        "hypnotic. The rhythm is all about the space between the beats. "
        "Stripping should be slow, wavy, and sensual — wind your body like a "
        "snake to the riddim. She sings with a melodic, slightly lazy patois style "
        "or soulful crooning. The bass is so deep it feels like it's massaging the car."
    ),
}

MUSIC_KEYS = list(MUSIC_PRESETS.keys())


def music_block(key: str) -> str:
    """Return the rich descriptive block for the selected music preset."""
    if not key or key not in MUSIC_PRESETS or MUSIC_PRESETS[key] is None:
        return ""
    return MUSIC_PRESETS[key]
