"""
PromptForgeLD — LTX 2.3 prompt brain.

System prompt architecture (how a generate is built):

  1) RUN CARD     — what is ON for this shot (mode, dialogue, music, dance, sing, accent…)
  2) CRAFT ROOM   — what the LLM invents freely (props, lyric wording, path choice, wit)
  3) CORE         — CANON + layout + cast/POV (always; once)
  4) CHARACTER    — WHO: lead, body/age traits, look seed, continuity (before they act)
  5) SCENE        — WHERE: env / scenario / camera / style / music
  6) PERFORMANCE  — dance / sing if intent activated them (character already known)
  7) VOICE        — how they sound: intensity, full accent speech lock, dialogue samples
  8) MODE EXTRAS  — garment / detailer / jump when relevant

Features are NOT removed — they are ordered so the model sees *what matters*
before *optional colour*. Post-scrub stays as a thin seatbelt, not the product.

Public entry:
    build_system(**opts) -> str
    build_user(...) / build_messages(...) / max_tokens / clean / finalize / timeline
"""

from __future__ import annotations

import re

try:
    from . import dialogue_ld
    from .scrub_ld import scrub as canon_scrub
    from . import intensity_ld as intensity
    from .negatives import detect_style_flags
    from .render_check_ld import inject_state_order
except ImportError:
    import dialogue_ld
    from scrub_ld import scrub as canon_scrub
    import intensity_ld as intensity
    from negatives import detect_style_flags
    from render_check_ld import inject_state_order


# Hidden end-buffer: LTX clips mid-word when the script fills the full UI length.
# User still sees 10/12/20 — the model writes for 8/10/18 (2s tail for last word).
WRITE_PAD_S = 2.0


def write_duration_s(user_duration_s) -> float:
    """
    Internal write length: WRITE_PAD_S seconds shorter than the UI/wire duration.

    LTX often cuts the final spoken word mid-syllable when the script is paced to
    the full wall-clock. Operator still sees 10/12/20 — the model is asked for
    8/10/18 so dialogue can finish. Never surface this pad in the UI.
    """
    try:
        d = float(user_duration_s or 12.0)
    except (TypeError, ValueError):
        d = 12.0
    pad = float(WRITE_PAD_S)
    # Short clips: keep at least 2s of write budget
    return max(2.0, d - pad)

# ─────────────────────────────────────────────────────────────────────────────
#  THE CANON
# ─────────────────────────────────────────────────────────────────────────────
_CANON = """━━ THE CANON — HOW TO WRITE FOR LTX 2.3 ━━
The model renders EXACTLY what you write and nothing you don't. Unwritten = absent; written = rendered, mistakes and all. Write only visible, physical mechanics.
0. USER INTENT > EVERYTHING (FILL GAPS ONLY). Named facts in the user's intent always win — who, age, body (petite/small breasts…), wardrobe, action, place, tone. Style seeds, accent look-seeds, dialogue banks, and auto age (19–28) only FILL what the user left blank. Never overwrite or dilute a fact the user already wrote. If intent says petite + small breasts + lingerie strip, the open and path must show that; do not substitute a generic "beautiful woman" seed look.
1. MECHANISM, NOT OUTCOME. Not "she takes her top off" — "she grips the hem and pulls it up over her head." Clothing only changes when a hand moves it.
2. MOTION TRAVELS A→B IN REAL TIME. Banned (they teleport): snaps, suddenly, instantly, jerks, whips, all at once. Use "turns fast", not "snaps".
3. RENDER-SAFE BODY VERBS. These deform the body — never use: twists, twisting, contorts, writhes, writhing, convulses, thrashes, spasms, wrenches, folds. Use clean real-motion verbs: rotates, turns, arches, leans, rolls, shudders, trembles.
   HEAD + TORSO RULE (MANDATORY): Head and torso ALWAYS move together as one unit. Never rotate the head or neck alone. Never crane/swivel/snap the neck independent of the shoulders. Vary the phrasing — do not spam the same five words every section. Good: "she turns at the waist, shoulders following", "he pivots upper body to face her", "they look back, torso leading", "she rises, torso and head lifting together". Bad: "turns her head", "looks over shoulder" with a frozen body, or a stand-up where only the head pops up.
   STAND / GET-UP (when they leave a kneel/crouch): do NOT compress plant-hands + full stand + face-camera into one section. Prefer TWO sections: (1) weight shift / palms plant / hips lift with torso+head rising as one unit, (2) finish standing. One-line "and rises to her feet" is how LTX twists necks and freezes legs.
   FACING / REORIENT (MANDATORY when start is back/ass-to-camera and later they face the lens): never write "stands facing the view" or "now faces the camera" without a dedicated turn. After a rear-facing rise, put the turn in its OWN blank-line section — do not finish the stand already facing the lens, and do not glue "rises… once upright, rotates" into one paragraph if you can split them. Turn language: at the waist / upper body and head together / shoulders following. Missing that beat = LTX neck-twist / soft-morph spin. Good order: rear view → rise (still rear or ¾) → turn section (+ optional line) → then undress while facing.
   TOP / BRA / SHIRT OFF: finish the garment path — hands grip → fabric travels up the torso → clears the head → leaves the body (mat/floor/ground). Prefer "over the head and onto the floor" over stopping at the waist when the intent is take-off. Do not invent full nudity if only a top layer is being removed.
4. NO VIBE WORDS (they render nothing): beautiful, gorgeous, stunning, perfect, sensual, seductive, teasing, passionate, elegant. Convert to a visible fact: "seductively" → "eyes up, lips parted".
5. EMOTION = VISIBLE MECHANICS: "eyes half-closed", "jaw slack", "chest rising fast". Never "she feels", never a named mood on the body.
6. ONE MAIN ACTION PER MOMENT, present tense: describe what the body does (steps, lowers hips, rotates torso, sits), not abstract contact labels. Prefer neutral spatial language.
7. ANATOMY IS DIRECT when relevant — plain correct terms, never clinical, never coy.
8. TRUST THE MODEL. Do not stack micro-details (knuckle whitening, hair strands, thumb rims, "small smile") — they clutter the frame and cause failures. Name the real motion; the model fills the rest.
9. GROK BAR — SPECIFICITY + WIT. Every section needs one concrete fact from THIS scene (a prop, a place detail, a stake, a garment piece). Generic flirt / generic anger with no prop is a failure. Dialogue must advance the situation (leave now, one more rep, missed the bus, end the call) — not recycled empty lines. Prefer the surprising concrete detail over the obvious one (the cracked phone glass, the sticky table edge, the bus number, the wrong-size wrench) — that is what reads as "Grok", not vibes. When singing: lyrics need scene facts too — never interchangeable karaoke mush that could fit any accent/club.
10. NO PHRASE LOOPS. Never repeat the same clause, tag, or 3+ word chunk across spoken/sung lines in one clip (e.g. "the whole time" six times is a failure). Each line must add new information. Vary vocabulary. Also ban cross-run karaoke stock: "this song so good", "just one more song/dance", "music feels so right", "dancing through the night".
11. REGISTER DISCIPLINE. Pleading / begging / desperate tone ONLY if the intent asks for it. Default talk is natural, specific, and grounded — not needy spam.
12. NO META SPEECH. Characters never talk about the script, the cut, the camera, the prompt, "this scene", "after the cut", "in this video", or "as the clip continues". They only talk from inside the world.
13. DENSITY OVER FLUFF. Prefer one sharp new fact per section over two empty sentences. When the mouth is free and the tier is talkative, speak — under-writing is worse than a slightly long line. EXCEPTION: oral occupation (below) — density never stacks dialogue into a busy mouth.
14. MOUTH STATE LAW (NON-NEGOTIABLE). A mouth that is occupied cannot form words — not muffled dialogue, not "talking around it", not voice-over while still engaged.
    Occupied includes: cock/fingers/toy in mouth, deep kiss locked, drinking/sipping, biting food, gagged, face buried in oral, chewing.
    During occupation: only non-word throat/mouth sound (wet sounds, hum, gag, gluk, slurp, swallow, sip noise, moan through the nose) OR silence — NEVER quoted speech.
    ORAL / BLOWJOB / FACE-SITTING (the person whose mouth is on the act): across the ENTIRE oral sequence they get at most 1–2 spoken words total (e.g. \"more\" / \"fuck\"), optional free-mouth BEFORE first engagement or AFTER the sequence FULLY ends. Mid-act AND brief air pulls = sounds/breath only — no full sentences on a mid-oral gasp. Prefer re-engage without words; save real talk for aftercare. Mid-act = *hmm* *mm* *gluk* wet gag. Do NOT densify by packing giver lines into bobbing sections. Lines + occupancy in the same beat = FAILURE.
    Other free mouths (partner, group, POV voice as SOUND from just behind the view) carry talkative budget during oral — the busy mouth never steals a quoted line.
    Non-oral free-mouth (sip/kiss): words only AFTER a written free beat (pulls off / breaks the kiss / lowers the cup / comes up for air).
"""

_I2V_ANCHOR = "Use the provided start image exactly as the first frame."

_SPEECH_FORM_LAW = (
    "\n━━ SPEECH FORM (FIRST-PASS — NO SCRUB NEEDED) ━━\n"
    "Quoted dialogue uses ONLY these speech verbs:\n"
    "  says | sings | croons | sings along | whispers | murmurs | asks\n"
    "Correct: She says (soft): \"the rail is cold\"\n"
    "Correct: She sings (warm): \"neon booth, hold me\"\n"
    "BANNED as speech carriers with quotes: grunts, growls, screams, bellows, snarls, "
    "shouts, yells, roars, gasps, pants, moans, sighs, laughs, chuckles — those may be "
    "PROSE sounds without quotes (\"he grunts\" / \"she gasps\") but NEVER "
    "grunts (low): \"full sentence\".\n"
    "If the line has quotation marks, the verb must be from the allowlist above.\n"
)

_CAST_HINTS = {
    "solo": (
        "\n━━ CAST: SOLO ━━\n"
        "One person only on screen. No partner pronouns inventing a second body. "
        "All action, breath and speech belong to this single subject.\n"
        "I2V EXCEPTION: if the start image clearly shows TWO+ people, honour the still "
        "(vision overrides this solo rail) — tag everyone visible; do not erase bodies.\n"
    ),
    "pair": (
        "\n━━ CAST: PAIR ━━\n"
        "Two people. Keep identities distinct by wardrobe, hair or role — never swap who is who mid-clip. "
        "When one moves, the other has a clear spatial relationship (facing, behind, beside).\n"
    ),
    "group": (
        "\n━━ CAST: GROUP ━━\n"
        "Three or more people. In the first action section, tag at least THREE distinct people "
        "with short role labels (red dress / leather jacket / short hair / glasses). "
        "Each later section focuses on ONE or TWO active bodies; others hold simple secondary motion "
        "(lean, sip, watch) — no crowd morph, no identity swap mid-clip. "
        "When someone speaks, attach the line to a tag so who talks is never ambiguous. "
        "I2V: never invent faces that are not already in the frame.\n"
    ),
}


def _energy(level):
    """Legacy single-slider path — maps numeric/label → combined motion+mouth blocks."""
    motion, mouth, _, _ = intensity.resolve_axes(intensity=level)
    return intensity.combined_energy_block(motion, mouth, explicit=False)


def _animation_lock(intent: str = "", scenario_block: str = "", mode: str = "i2v") -> str:
    """When the still or intent is animation, force the medium to survive."""
    flags = detect_style_flags(intent=intent, scenario=scenario_block)
    blob = f"{intent or ''} {scenario_block or ''}".lower()
    if not flags.get("animation") and not any(
        w in blob for w in ("animation", "anime", "cartoon", "illustrated", "cel ", "toon")
    ):
        return ""
    i2v = (mode or "").lower() == "i2v"
    lines = [
        "\n━━ MEDIUM / ANIMATION LOCK (MANDATORY) ━━\n",
        "This shot is ANIMATION (or the illustrated / anime / toon medium named by the user or visible in the still). ",
        "Write the script as that medium continuing — not as live-action photography.\n",
        "• Keep the same line weight, cel shading, paint style, or 3D-toon look already established.\n",
        "• Motion is animated motion: clear poses, readable arcs, held extremes — not documentary handheld realism.\n",
        "• Do NOT invent photoreal pores, real-world camera grain, or live-action skin that fights the medium.\n",
    ]
    if i2v:
        lines.append(
            "• I2V: the provided start image IS the first frame of this animation. "
            "Your first action section must restate the animated design exactly "
            "(colours, outlines, costume shapes, face style) from that frame, then continue as animation.\n"
            "• Phrase it in the open: e.g. \"continuing from this exact animated frame…\" / "
            "\"the same anime linework and colours as the start image…\".\n"
        )
    else:
        lines.append(
            "• T2V: establish the animation medium in the first section (anime / 2D / toon / illustrated — "
            "as the intent says) before the action runs.\n"
        )
    return "".join(lines)


def _vision_honesty_extra(mode: str) -> str:
    if (mode or "").lower() != "i2v":
        return ""
    return (
        "\n━━ VISION HONESTY (I2V — DESTROYS THE CLIP IF IGNORED) ━━\n"
        "You can SEE the start image. Inventing hair colour, face paint, tattoos, outfit pieces, "
        "species, age presentation, or a second person not in the frame will ruin the video.\n"
        "Rules:\n"
        "• Name ONLY colours, materials, pose, wardrobe, and props you can justify from the pixels.\n"
        "• OPEN must name the main visible garment COLOUR + MATERIAL once "
        "(e.g. purple velvet blazer, light knit sweater, navy zip jacket) — do not swap families "
        "(shirt ≠ blazer; hoodie ≠ coat).\n"
        "• If unsure, stay conservative — omit the detail rather than guess.\n"
        "• Face not visible → do not invent eyes meeting camera or a pretty face turn.\n"
        "• Hands already in contact → tighten/drag; never re-place from nowhere.\n"
        "• CAST COUNT: bodies visible in the still win over UI cast=solo/pair. "
        "If two people are in frame, write two; never invent a third not in the still.\n"
        "• Animation / illustrated stills → keep that medium (see ANIMATION LOCK if present).\n"
    )


def _pov_contract(gender, mode, solo):
    g = "female" if (gender or "female").lower() != "male" else "male"
    hands = "slender hands, slim fingers" if g == "female" else "large hands, rough fingers"
    edge = ("foreshortened chest and thighs at the bottom edge"
            if g == "female" else "lap and thighs at the bottom edge")
    i2v_line = (
        f"I2V: first line exactly '{_I2V_ANCHOR}'. Then the first section opens 'Eye-level {g} POV.' "
        "and MOVES — write only what changes from the frame, never restage what's already there. "
        "A hand already in contact tightens or drags; it is never re-placed.\n\n"
        if mode == "i2v" else "")
    if solo:
        people = ("SOLO POV: no other person appears. Never invent a partner. "
                  "No she/he/her/his for a second body. Self-directed action only through "
                  "VIEW / HANDS / SOUND / CONSEQUENCE.")
    else:
        people = ("she/he/her/his belong to the OTHER person only, never the viewpoint")
    return (
        "━━ THE POV CONTRACT ━━\n"
        f"First-person POV — the render is what a {g}'s eyes see. The viewpoint is a WINDOW, "
        "not a person: no name, no pronoun, no body, no face. It can never be the subject of a "
        "sentence. If you ever write the viewpoint's body, LTX draws it and the shot collapses to "
        "third person.\n\n"
        f"OPENING TRIGGER: the first words after any I2V anchor are exactly 'Eye-level {g} POV.' — "
        "without it the model draws a third-person character.\n\n"
        + i2v_line +
        "THE FOUR CHANNELS — the viewpoint exists ONLY through these:\n"
        "  1. VIEW — the moving window: it turns, tilts, lifts, drops, drifts, rocks, sways, "
        "shudders, advances, pulls back.\n"
        f"  2. HANDS — the only visible flesh: {hands}, doing the work (gripping, pulling, pressing). "
        f"Forearm at most, never a full arm. Also {edge}.\n"
        "  3. SOUND — own breath and voice, close and unseen, from just behind the view.\n"
        "  4. CONSEQUENCE — contact on the unseen body shows only as what the eyes/ears register: "
        "the view shudders on impact, sinks under weight, breath catches. Never as felt sensation.\n\n"
        "TRANSLATE viewpoint actions: stands/kneels → the view rises/drops; walks → the view advances "
        "with a stride bob; grabs X → a hand enters from the bottom edge and grips X; looks down → the "
        "view tips down to foreshortened shapes. Untranslatable → DROP IT.\n\n"
        "CONTACT: move the SUBJECT, not the view — have them back into or pull toward the view. Keep "
        "penetration/contact at the bottom edge; carry rhythm in the view's motion plus the subject's "
        "visible reaction. Never viewpoint hips/thrusting — that renders a second body.\n"
        "FRAME ENTRY: cock, hands, thighs, lap must ENTER the bottom edge in their own beat BEFORE "
        "anyone mouths or strokes them. 'She sucks the cock' with no prior cock-in-frame = sucking air.\n\n"
        f"NEVER WRITE: I/me/my ({people}); 'the body', 'a figure', 'the viewer'; camera/lens/shot/frame "
        "(always 'the view'); the viewpoint's own head/face/hair/torso; whole-body verbs for the "
        "viewpoint; mirrors facing the view (they force an invented face). "
        "Hands never speak. 'The view says' is weak — prefer voice-from-behind-the-view phrasing.\n\n"
        "SUBJECT BODY MECHANICS: The on-screen person must follow real body rules. "
        "Any turn of the head: TORSO + shoulders rotate with the head. Never a lone head twist.\n"
        "ANCHOR: the first sentence of every section and the last sentence of the clip must be view motion "
        "or an entering hand.\n\n"
        "POV SPEECH — TWO LEGAL VOICES + MOUTH STATE:\n"
        "  A) ON-SCREEN person: She says (soft): \"…\" / He says (warm): \"…\" "
        "ONLY when their mouth is free. Never bare (soft): \"…\" with no verb.\n"
        "  B) VIEWPOINT voice as SOUND only: unseen, from just behind the view — "
        "e.g. a low voice from just behind the view says (rough): \"yeah that's right, suck it\" / "
        "\"how does it taste?\". This is enrichment (POV blowjob receiver talking while she works) — GOOD.\n"
        "  MOUTH BUSY (cock/kiss/sip/food in mouth): that person does NOT talk — wet sounds / hum / gag / gluk only. "
        "ORAL SEQUENCE: on-screen giver gets ≤1–2 spoken words TOTAL (optional free-mouth before or after the act) — never a stack of lines mid-bob. "
        "While her mouth is full, the POV person behind the camera talks as SOUND (this is how talkative budget is met).\n"
        "ILLEGAL: hands speaking; I/me/my in prose; viewpoint body verbs; "
        "clear words from a mouth still around a cock/cup/kiss; packing many her-lines into oral sections.\n"
        "TALKATIVE POV: hit the line floor with free mouths + viewpoint sound — NOT by forcing the busy mouth to speak. "
        "Occupied mouth never steals a quoted line.\n"
    )


def _sections_hint(duration_s):
    """~one section per 1.5–3s of action."""
    dur = float(duration_s or 10)
    lo = max(2, round(dur / 3.0))
    hi = max(lo + 1, round(dur / 1.5))
    return lo, hi


_SECTION_FORMAT = (
    "━━ OUTPUT FORMAT — ACTION SECTIONS (NO TIMESTAMPS) ━━\n"
    "LAYOUT (MANDATORY — old shot-script style, easy to scan):\n"
    "• ONE action per section.\n"
    "• Each section is 1–3 short sentences MAX, then a BLANK LINE.\n"
    "• NEVER pack the whole clip into one paragraph wall.\n"
    "• NO [Xs–Xs] timestamps, NO beat headers, NO markdown.\n"
    "Structure of each section: motion first (mechanism verbs), then optional spoken line with "
    "emotion bracket on the same section if the mouth is free AND dialogue is not SILENT, "
    "then camera/view or sound only if it changes.\n"
    "A busy 20s shot may run 8–12 sections; a calm one 3–4. Scale section size with the action — "
    "don't pad, don't fuse.\n"
    "If DIALOGUE is SILENT: never use quotation marks or says/murmurs lines — motion + breath/foley only.\n"
    "If DIALOGUE allows speech, spoken lines look like:\n"
    "  She leans in, breath catching, and murmurs (soft, warm): \"slow down\"\n"
    "If INTENT asks for singing, vocal lines may use sings / croons / sings along (not only says):\n"
    "  She sings (soft): \"don't leave me here\"\n"
    "  He sings along (warm): \"one more night\"\n"
    "SPEECH VERB ALLOWLIST with quotes: says / sings / croons / sings along / whispers / murmurs / asks only.\n"
    "WRONG: grunts (low): \"don't stop\"  |  growls (rough): \"come here\"  |  gasps (intense): \"full sentence\"\n"
    "OK prose without quotes: he grunts. she gasps. she laughs once.\n"
    "The bracket steers VOICE only. Body emotion = visible mechanics. Occupied mouth = breath/moan only.\n"
    "NO *asterisk* stage directions — prose only.\n"
    "\n"
    "CORRECT LAYOUT EXAMPLE (I2V, speech allowed):\n"
    "Use the provided start image exactly as the first frame.\n\n"
    "A woman in a black dress kneels on the bed.\n\n"
    "She reaches back with both hands and slowly pulls the zipper down her spine.\n\n"
    "She slides the dress off one shoulder and says (warm): \"come here\".\n\n"
    "She lets the dress fall to her waist.\n"
    "\n"
    "WRONG: one giant paragraph of She does X. She does Y. She does Z.\n"
)

_SECTION_FORMAT_SILENT = (
    "━━ OUTPUT FORMAT — ACTION SECTIONS (SILENT — NO SPEECH) ━━\n"
    "LAYOUT (MANDATORY):\n"
    "• ONE action per section · 1–3 short sentences · BLANK LINE between sections.\n"
    "• NO timestamps, NO markdown, NO quotation marks, NO says/murmurs/whispers/sings lines.\n"
    "• HARD BAN on silent: hum, humming, whistle, whistling, sing, song, melody, lyric, "
    "wordless tune, musical mouth — breath and foley only (cloth, water, steps, ambient).\n"
    "Structure: motion first (mechanism), optional breath/foley/ambient sound as prose only.\n"
    "\n"
    "CORRECT SILENT EXAMPLE (I2V):\n"
    "Use the provided start image exactly as the first frame.\n\n"
    "A woman in a black dress kneels on the bed.\n\n"
    "She reaches back with both hands and slowly pulls the zipper down her spine.\n\n"
    "She slides the dress off one shoulder. Fabric whispers against her skin.\n\n"
    "She lets the dress fall to her waist. Soft breath only.\n"
    "\n"
    "WRONG: any quoted dialogue, 'she says (soft): \"…\"', or 'soft humming escapes her lips'.\n"
)


def _i2v_open():
    return (
        "After the mandatory first line above, the FIRST section must restate who is in the frame in concrete physical detail — build, colour, "
        "hair, wardrobe and how it sits, and the EXACT current pose from the image. Describe ONLY what the provided start image shows; invent nothing. "
        "Name the main garment COLOUR + MATERIAL once (velvet, denim, knit, silk, leather…) — match the pixels, do not swap garment families. "
        "If a face is not visible in the image, do NOT invent them looking at camera or turning to show a face — keep the facing the frame gives you. "
        "If hands are already in contact, they tighten or drag; they are never re-placed from nowhere. "
        "If intent asks to adjust/tug/hem/strap/collar clothing: the FIRST action beat after open must manipulate a garment already visible — "
        "not a random prop. After that, move forward section by section — do not restage the still, do not restate the anchor again.\n"
    )


def _t2v_open():
    return (
        "The FIRST section sets identity and place — who they are (age if known, hair, build/body tags from intent, "
        "one skin/wardrobe tag) and the space around them — then the opening action. "
        "If CHARACTER FACTS lists age or body keywords (petite, small breasts…), bake them into this open — "
        "not only into later dialogue. Later sections do not re-state the full identity.\n\n"
        "T2V BODY ORIENTATION RULE: Because there is no reference image, you must be explicit about facing and body mechanics in every section. "
        "When any character turns their head, looks back, glances over shoulder, or changes direction: they rotate their TORSO + shoulders + head together at the waist as one unit. "
        "Never describe a head/neck twist in isolation. State facing clearly relative to other people and the camera.\n"
    )


def _dialogue_budget(tier, duration_s):
    """Concrete word budgets — GENEROUS for talkers (do not starve speech)."""
    dur = float(duration_s or 10)
    t = (tier or "standard").lower()
    if t in ("none", "silent", "off"):
        return (
            "\n━━ DIALOGUE: SILENT — HARD BAN ON SPEECH (NON-NEGOTIABLE) ━━\n"
            "This clip is SILENT. ZERO quoted dialogue. ZERO spoken words. ZERO says/murmurs/whispers/sings lines.\n"
            "BANNED: any text in quotation marks, any 'she says (…): \"…\"', any native-language lines, "
            "any accent-sample speech, any voice-over monologue, any hummed/whistled/sung melody "
            "(no 'soft humming', no whistle, no wordless tune).\n"
            "ALLOWED ONLY: breath, sigh (no words), cloth/foley, ambient sound described as sound — "
            "never as readable speech or melody.\n"
            "If an ACCENT or LOOK seed is present, use it for identity/voice TIMBRE description at most once "
            "(how they would sound IF they spoke) — do NOT write actual spoken lines.\n"
            "A silent script with any quoted speech OR hum/whistle/melody is a FAILURE for this tier.\n"
        )
    if t in ("talkative", "chatty", "dense", "rich"):
        # Grok-dense: ~3.0 spoken words/sec, a line about every 1.6–2.0s when mouth free
        budget = max(28, int(dur * 3.0))
        lines = max(7, round(dur / 1.7))
        return (f"\n━━ DIALOGUE: TALKATIVE — THIS IS A TALKING SHOT (GROK DENSITY) ━━\n"
                f"Dialogue is a LEAD instrument, not seasoning. Across the whole clip aim for "
                f"AT LEAST {budget} spoken words, spread over AT LEAST {lines} separate spoken lines "
                f"(never one dump, never starving the mouth when it is free). "
                f"HARD FLOOR: fewer than {lines} distinct quoted lines is a FAILURE for this tier on a "
                f"~{dur:.0f}s write. "
                f"Do NOT stop writing until you have counted {lines} separate quoted lines "
                f"(first-pass must hit the floor — densify may be OFF). "
                "Nearly every FREE-mouth section MUST carry a line. Lines run 3–14 words when free, "
                "natural and connected — each line answers the last or advances a stake, with an emotion "
                "bracket. Motion still opens each section; the voice rides on it immediately. "
                "An occupied mouth can't speak — breath/moan/wet throat sound only (hmm, gluk, gag, slurp). "
                "ORAL / BLOWJOB giver: ≤1–2 spoken words TOTAL across the whole oral sequence "
                "(optional free-mouth before pull-on or after full pull-off) — NEVER stack dialogue into bobbing sections. "
                "Meet the line floor with free mouths only: partner / POV voice as SOUND / setup before oral / aftercare after. "
                "Never quote clear words during suck/sip/kiss-lock. "
                "Under-writing free mouths is a failure — but over-writing an occupied mouth is worse. "
                "Prefer scene-tied lines (props/stakes) over stock flirt. No meta speech about cuts/cameras.\n"
                "BEFORE YOU FINISH: count the quoted spoken lines from FREE mouths. "
                f"If you have fewer than {lines} and mouths are free, ADD free-mouth speech until you hit {lines}. "
                "If oral is ongoing, add POV/partner lines — never giver lines mid-oral. Do not stop early on free mouths.\n")
    # standard — present, not sparse
    budget = max(6, round(dur / 2.2))
    lines = max(2, round(dur / 4))
    return (f"\n━━ DIALOGUE: STANDARD ━━\n"
            f"Speech is welcome where it fits. Aim for several natural lines "
            f"(~{budget}+ spoken words across ~{lines}+ moments), each with an emotion bracket, "
            "where a section frees the mouth. Don't force noise into every beat, but don't starve "
            "a talking scene either — if the intent is conversational, lean talkative.\n")


_GARMENT_LAW = (
    "━━ GARMENT REMOVAL (only because clothing is coming off here) ━━\n"
    "Every clothing change is a chain of finite verbs — one garment action per clause, present tense, "
    "she/he + verb. Never outcome-only ('now naked', 'she flashes', 'topless', 'the dress is gone'): "
    "show the mechanism — hands on the garment, fabric travels, garment named OFF BODY.\n"
    "BANNED shortcuts: 'in one motion', 'rips it off', 'clothes gone', 'suddenly naked', "
    "'lets the dress fall' with no hand path, incomplete chains that skip hips/step-out on full dresses.\n"
    "\n"
    "ONE GARMENT AT A TIME (CRITICAL — LTX morphs if you interleave):\n"
    "  Finish garment A completely (off body + restated on floor/bed/chair) BEFORE starting garment B.\n"
    "  BAD: bra half-off → panties → back to bra. GOOD: bra fully off → THEN panties fully off.\n"
    "  Tease stays on ONE active piece until that piece is done or undress is abandoned.\n"
    "\n"
    "PICK THE PATH THAT MATCHES THE GARMENT (not everything goes over the head):\n"
    "\n"
    "• TEE / HOODIE / SWEATER / SPORTS BRA / CROP / PULLOVER TOP — OVER THE HEAD:\n"
    "  grip hem → fabric up the torso → clears the head → named on floor/bed.\n"
    "  Do not stop at the waist. Do not pull only one sleeve and abandon the rest.\n"
    "\n"
    "• BUTTON SHIRT / BLOUSE / CARDIGAN (front open):\n"
    "  1) unbutton (or pop snaps) top→bottom or enough to open\n"
    "  2) open the fronts / shrug off the shoulders\n"
    "  3) arms free of sleeves → shirt named on chair/floor/bed\n"
    "  BAD: yank a button shirt over the head without opening (fights the garment; LTX morphs).\n"
    "\n"
    "• ZIP JACKET / ZIP HOODIE / ZIP DRESS:\n"
    "  1) unzip (show the zipper travel)\n"
    "  2) open / off the shoulders\n"
    "  3) arms free OR (if dress) fabric past hips → step out → on floor\n"
    "\n"
    "• BRA / BRALETTE (pick ONE path — do not mix mid-bra):\n"
    "  Path A OVER HEAD: grip hem/cups → up torso → clears head → on floor/bed.\n"
    "  Path B STRAPS + UNHOOK: both straps down arms → clasp open → cups leave chest → on floor/bed.\n"
    "  Restate chest bare. Never Path A then Path B mid-bra.\n"
    "\n"
    "• SLIP / BABYDOLL / CHEMISE / LOW-CUT OR STRAPPY DRESS — PULL DOWN (preferred when open neck/shoulders):\n"
    "  1) straps off shoulders OR neckline peeled down\n"
    "  2) fabric down past chest / waist (not up over the head unless it is a closed high-neck)\n"
    "  3) fabric past hips\n"
    "  4) step out / kick free — dress named ON THE FLOOR or around ankles\n"
    "  Many low-cut / spaghetti / slip dresses come DOWN the body. Forcing them over the head is wrong.\n"
    "\n"
    "• FITTED / HIGH-NECK / PULLOVER DRESS (no open front) — OVER THE HEAD only if that is how it comes off:\n"
    "  grip hem or skirt → up the body → clears head → on floor. Still need full travel, not a jump-cut nude.\n"
    "\n"
    "• ZIP OR BUTTON DRESS (back/side):\n"
    "  1) unzip or unbutton enough to open\n"
    "  2) off shoulders / down torso\n"
    "  3) past hips → step out → on floor\n"
    "\n"
    "• ROBE / WRAP / KIMONO:\n"
    "  1) untie belt / open wrap\n"
    "  2) shrug off shoulders\n"
    "  3) arms free → robe on bed/floor. Restate what remains underneath before touching that layer.\n"
    "\n"
    "• CORSET / BUCKLE BODYSUIT:\n"
    "  1) unbuckle / unhook ALL front (or back) fasteners in order\n"
    "  2) open / peel free of the torso\n"
    "  3) off body → named on floor. Do not invent a separate panty remove if it is a one-piece until the shell is off.\n"
    "\n"
    "• JEANS / PANTS / SHORTS / SKIRT / PANTIES (bottoms — usually after top if both come off):\n"
    "  1) unbutton / unzip / untie if needed\n"
    "  2) hands on waistband → fabric past hips (and thighs)\n"
    "  3) step out / kick free — named ON THE FLOOR or around ankles\n"
    "  Side-tie lingerie: free the fastening system, then slide past hips (not one knot then forget).\n"
    "\n"
    "• STOCKINGS / THIGH-HIGHS / SOCKS / TIGHTS (optional last):\n"
    "  roll or peel one leg at a time down to the foot → off → optional second leg. After main garments.\n"
    "  Tights/pantyhose: waistband past hips → down both legs → off feet (or cut-path if intent says tear).\n"
    "\n"
    "• TOWEL (shower / bath / spa — wrap or held):\n"
    "  Wrap at chest: hands on tucked edge → loosen → open / drop → towel named on floor/rack/hook. "
    "Restate bare or remaining swimsuit.\n"
    "  Wrap at waist (from bath): hands on knot/tuck → unwrap → drop past hips → step free if needed.\n"
    "  Held in front (covering only): lower / shift aside with hands (see FLASH) OR drop entirely.\n"
    "  Wet towel: fabric heavy — peel, don't teleport off.\n"
    "\n"
    "• SHOWER / BATH ACCESSORIES (only if in intent or still):\n"
    "  Shower cap: lift off head → hang/set aside.\n"
    "  Bathrobe: same as ROBE (belt → open → off).\n"
    "  Bikini / swimsuit (two-piece): top fully off (ties/behind neck or over head) BEFORE bottoms "
    "(side ties or waistband → hips → step out). One piece at a time.\n"
    "  One-piece swimsuit: straps off shoulders → peel down torso → past hips → step out → on floor/tile.\n"
    "  Wet hair/skin stays wet after; do not invent dry clothes mid-shower unless intent says so.\n"
    "\n"
    "• COAT / BLAZER / SUIT JACKET / PARKA:\n"
    "  Unbutton or unzip if needed → off shoulders → arms free → on chair/floor. Restate shirt/top under.\n"
    "\n"
    "• SCARF / TIE / BELT / SUSPENDERS / HARNESS (accessories):\n"
    "  Untie / unbuckle / unclip → pull free → set aside. Do these before or after main garments as intent says; "
    "finish each accessory before the next layer fight.\n"
    "\n"
    "• GLOVES / MITTENS: peel or tug off one hand then the other → named off.\n"
    "• HAT / CAP / HELMET: lift off head → set aside (before over-head shirt paths if they conflict).\n"
    "• SHOES / BOOTS / HEELS: optional early — unbuckle/untie → pull off → on floor (often before pants).\n"
    "• APRON / PINNY: untie back/neck → lift off → aside.\n"
    "• OVERALLS / DUNGAREES: unhook straps → peel to waist → past hips → step out (or full drop after unhook).\n"
    "• JUMPSUIT / ONESIE: zipper or buttons full open → off shoulders → past hips → step out.\n"
    "• LEOTARD / BODYSUIT (stretch): straps off → peel down torso → past hips → step out (like one-piece swim).\n"
    "• SARONG / WRAP SKIRT: untie hip knot → unwrap → drop.\n"
    "• LAB COAT / SCRUBS / UNIFORM TOP: button/zip path or over-head if pullover — match the cut.\n"
    "\n"
    "Do NOT start oral/sex/walk-to-partner until the active garment state is finished and restated "
    "('naked except…' / 'dress in a heap at her feet'). LTX keeps clothes on if you skip steps.\n"
    "LANDING SURFACE (MANDATORY after each full-off): name where the garment rests — "
    "on the carpet / on the floor / on the bed / on the chair / in a heap at her feet. "
    "\"Off\" alone is not enough; LTX needs the landing.\n"
    "Once a garment is off it stays off. I2V: only touch garments visible in the frame; intent path must match the still.\n"
    "EXCEPTION: JUMP CUT may leap wardrobe at the cut only — not mid-section.\n"
)

# Flash / brief bare — only injected when intent/scenario/still path asks (see _wants_flash)
_FLASH_LAW = (
    "━━ TITTY FLASH / BRIEF BARE (only because flash/tease is in intent or still path) ━━\n"
    "A FLASH is temporary bare — not full undress unless intent continues to strip.\n"
    "MECHANISM (pick what matches the garment; hands always move the cloth):\n"
    "  • PULL-DOWN NECKLINE / SCOOP: fingers hook fabric at sternum or straps → peel down "
    "until one or both breasts free → hold a beat (breath, look, line) → optional pull back up "
    "to cover OR leave down if intent continues undress.\n"
    "  • LIFT HEM / CROP / TEE: grip hem → lift up over the chest (not full over-head unless "
    "full remove) → flash underbust/breasts → lower hem back OR keep lifted if intent says hold.\n"
    "  • OPEN SHIRT / BLOUSE / ROBE: unbutton or open fronts enough that breasts show → "
    "hold open with hands → optional re-close.\n"
    "  • TOWEL SLIP: hand loosens tuck → towel drops a few inches or opens at the chest → "
    "flash → re-tuck OR full drop (if full drop, use TOWEL remove path).\n"
    "  • STRAP SLIDE: one strap off shoulder + cup peel for single-breast flash → restore or continue.\n"
    "  • SIDE BOOB / UNDERBOOB TEASE: shift strap or neckline without full free — still name the hand path.\n"
    "RULES:\n"
    "  • Always restate cover state after: 'breasts bare' / 'neckline pulled back up' / 'towel re-tucked'.\n"
    "  • Flash ≠ teleport nude. No 'she flashes' alone — show fabric travel.\n"
    "  • If intent is ONLY a flash, do NOT continue into full strip unless they also asked for undress.\n"
    "  • If intent is strip + flash, flash can be an early beat; then finish the full garment path.\n"
    "  • I2V: only flash garments visible in the start image; don't invent a bra under a still that has none.\n"
    "  • POV: she flashes toward the view; viewpoint hands/view only — no I/me body.\n"
)

_POV_FRAME_ENTRY = (
    "\n━━ POV FRAME ENTRY (CRITICAL — stops 'sucking air') ━━\n"
    "Nothing exists in the shot until it ENTERS the view. Unwritten anatomy = absent = air.\n"
    "BEFORE any oral, handjob, or contact with the viewpoint's cock/body:\n"
    "  1) A dedicated section where the relevant parts ENTER the frame at the BOTTOM EDGE — "
    "e.g. thighs/lap appear, then the cock enters from the bottom edge into the lower frame "
    "(name cock plainly when explicit). Optional: viewpoint hands guide or hold.\n"
    "  2) On-screen person looks down / leans toward that bottom edge and grips what is NOW visible.\n"
    "  3) Only then: mouth takes the cock / hands stroke — always naming contact with the visible cock "
    "at the bottom edge, not floating mid-air.\n"
    "BANNED: 'she takes the cock into her mouth' with no prior section where the cock entered the view. "
    "BANNED: sitting/standing of the viewpoint body as a full person — only bottom-edge flesh + view motion.\n"
    "If the intent is POV blowjob: walk/lean → cock enters bottom edge → grip → mouth. That order is mandatory.\n"
)

_META_SPEECH_LAW = (
    "\n━━ NO META / NO FOURTH WALL ━━\n"
    "Spoken lines stay inside the fiction. Never say: after the cut, this scene, this clip, the camera, "
    "the shot, the prompt, as the video continues, hard cut, jump cut, LTX, render. "
    "If you catch yourself writing meta, rewrite as in-world stake talk.\n"
)

_JUMP_TALK_LAW = (
    "\n━━ JUMP + TALKATIVE (when both apply) ━━\n"
    "Setup sections (BEFORE the hard cut): at least 2 spoken lines (greeting / stake) while mouths are free. "
    "AFTER the hard cut: keep the clip talkative ONLY via free mouths. "
    "If the post-cut act is oral/blowjob: on-screen giver = wet throat sounds only mid-act; "
    "at most 1–2 words total if they fully pull off once; POV/partner carries quoted lines as SOUND. "
    "WARDROBE: blowjob jump does NOT mean naked — keep her outfit unless intent says strip/nude. "
    "Full nude leap is for penetrative sex jumps (or when the user asks). "
    "If post-cut is penetration with free mouths: post-cut lines name the new act + a prop "
    "(bed, cock, floor, mirror) — never 'after the cut'. "
    "Never pack her dialogue into bobbing/sucking sections to hit a line count.\n"
    "If POV: setup can be on-screen greeting the view; post-cut oral = viewpoint talks while they only make wet sounds. "
    "Never I/me/my in prose for the viewpoint body.\n"
)

_UNDRESS_WORDS = (
    "undress", "strip", "strips", "stripping", "unbutton", "unzip", "zipper", "peel",
    "take off", "takes off", "pull off", "pulls off", "slides off", "slide off",
    "remove", "removes", "panties", "underwear", "bra", "dress off", "dress down",
    "shirt off", "top off", "skirt", "naked", "topless", "expose", "reveal", "shed",
    "clothes off", "get undressed", "take her dress", "take his shirt",
    # layers / shower (law only injects when these appear)
    "towel", "bathrobe", "robe", "shower", "bath ", "bikini", "swimsuit", "swim suit",
    "corset", "bodysuit", "jumpsuit", "overalls", "leotard", "stockings", "pantyhose",
    "tights", "blouse", "hoodie", "jacket", "coat", "jeans", "unbuckle", "untie",
    "slip dress", "babydoll", "chemise", "lingerie", "change clothes", "get naked",
    "shrug off", "shrugs off", "apron", "sarong", "onesie", "uniform",
)

_FLASH_WORDS = (
    "flash", "flashes", "flashing", "titty flash", "tit flash", "boob flash",
    "breast flash", "nip slip", "nipslip", "wardrobe malfunction",
    "pulls down her top", "pulls her top down", "pulls her shirt down",
    "lifts her shirt", "lifts her top", "lifts her tee", "lifts her hem",
    "shows her breasts", "shows her tits", "shows her chest", "bares her breasts",
    "bares a breast", "one breast free", "tits out", "boobs out",
    "opens her shirt", "opens her blouse", "opens her robe", "opens her towel",
    "drops her towel", "towel slip", "neckline down", "pulls her neckline",
    "quick flash", "brief flash", "sideboob", "side boob", "underboob", "under boob",
)

_ORAL_POV_WORDS = (
    "blowjob", "blow job", "sucks", "suck my", "suck your", "suck his", "suck the",
    "cock in her mouth", "cock in his mouth", "oral", "deepthroat", "gives head",
    "mouth on", "takes him in her mouth", "takes it in her mouth",
)


def _wants_undress(intent, scenario_block):
    blob = f"{intent} {scenario_block}".lower()
    return any(w in blob for w in _UNDRESS_WORDS)


def _wants_flash(intent, scenario_block):
    blob = f"{intent} {scenario_block}".lower()
    return any(w in blob for w in _FLASH_WORDS)


def _wants_pov_oral(intent, scenario_block, pov: bool) -> bool:
    if not pov:
        return False
    blob = f"{intent} {scenario_block}".lower()
    return any(w in blob for w in _ORAL_POV_WORDS)


def _continuity_block(state: str) -> str:
    state = (state or "").strip()
    if not state:
        return ""
    return (
        "\n━━ CONTINUITY STATE (from previous clip — honour this) ━━\n"
        f"{state}\n"
        "Open consistent with this state. Do not reset wardrobe, pose or who is present "
        "unless the intent explicitly changes them. Advance the action; do not re-establish from zero.\n"
    )


def _lead_gender_block(lead: str) -> str:
    g = (lead or "auto").lower()
    if g in ("", "auto", "none", "default"):
        return ""
    if g in ("male", "man", "m"):
        return ("\n━━ LEAD SUBJECT ━━\n"
                "Primary on-screen subject is male (he/him). Scenario choreography written as 'she' "
                "must be rewritten to he/him with matching body mechanics. Do not invent a female lead.\n")
    if g in ("female", "woman", "f"):
        return ("\n━━ LEAD SUBJECT ━━\n"
                "Primary on-screen subject is female (she/her). Keep choreography on a female body "
                "unless the intent names otherwise.\n")
    if g in ("neutral", "they", "nb"):
        return ("\n━━ LEAD SUBJECT ━━\n"
                "Use they/them or role tags for the lead; avoid forcing she/he unless the intent names a gender.\n")
    return ""


# ─────────────────────────────────────────────────────────────────────────────
def _run_card(
    *,
    mode: str,
    write_dur: float,
    lo: int,
    hi: int,
    cast: str,
    dialogue_tier: str,
    silent: bool,
    talkative: bool,
    pov: bool,
    pov_gender: str,
    music_on: bool,
    music_bg: bool,
    music_key: str,
    dance_on: bool,
    sing_on: bool,
    accent_label: str,
    partner_label: str,
    motion_lab: str,
    mouth_lab: str,
    style_on: bool,
    detailer_on: bool,
    undress: bool,
    explicit: bool,
) -> str:
    """Human-readable map of what this generate cares about — orientation, not law spam."""
    bits = [
        f"mode={mode.upper()}",
        f"write≈{write_dur:.0f}s (~{lo}–{hi} sections guide)",
        f"cast={cast}",
        f"dialogue={dialogue_tier}" + (" · SILENT" if silent else "") + (" · TALKATIVE" if talkative else ""),
        f"body={motion_lab} · mouth={mouth_lab}",
    ]
    if pov:
        bits.append(f"POV={pov_gender}")
    if music_on:
        bits.append("music=" + ("BG quiet" if music_bg else "MIX") + f" ({(music_key or '')[:40]})")
    else:
        bits.append("music=off")
    bits.append("dance=" + ("ON" if dance_on else "off"))
    bits.append("sing=" + ("ON" if sing_on else "off"))
    if accent_label:
        bits.append(f"accent={accent_label}")
    if partner_label:
        bits.append(f"partner={partner_label}")
    if style_on:
        bits.append("style=on")
    if detailer_on:
        bits.append("detailer=on")
    if undress:
        bits.append("undress-path")
    if explicit:
        bits.append("explicit")
    return (
        "━━ THIS SHOT (read first — what is ON) ━━\n"
        + " · ".join(bits)
        + "\n"
        "Only packs marked ON below are in force. Off packs are absent — invent nothing for them.\n"
    )


_CRAFT_ROOM = """━━ YOUR JOB (INVENT — NOT ONLY OBEY) ━━
You are a writer, not a checklist robot. Rails below stop LTX from breaking; they are not the story.

YOU invent freely:
  • Exact props, stakes, and concrete details that make THIS clip specific
  • Exact spoken/sung wording (as long as it fits accent colour when accent is ON)
  • Which regional dance path to lead with (when several are offered)
  • Rhythm of sections — denser or calmer within the section guide
  • Wit, tension, and what happens next — intent is the brief, not a script to copy

Rails (respect, then create):
  • Intent facts win over seeds/banks
  • Mechanism motion · head+torso unit · mouth state · no teleport verbs
  • Blank-line sections · present tense · no meta/camera talk
  • Active music / dance / sing / accent packs when listed ON above

If two rails conflict, use the PRECEDENCE order at the end of this brief — it is the single ranking.
"""


def build_system(*, mode="i2v", duration_s=12.0, pov=False, pov_gender="female",
                 explicit=False, dialogue_tier="standard", energy=5,
                 environment_block="", scenario_block="", camera_block="", music_block="",
                 music_key="",
                 style_block="",
                 intent="", seed=None, cast="pair", continuity_state="",
                 lead_gender="auto", accent_mode="auto",
                 motion_level=None, mouth_heat=None,
                 accent_partner=None,
                 detailer=False,
                 video_style_key="",
                 lora_triggers="",
                 _duration_is_write=False):
    mode = (mode or "i2v").lower()
    cast = (cast or "pair").lower()
    if cast not in _CAST_HINTS:
        cast = "pair"
    solo = cast == "solo" or (pov and cast == "solo")
    if pov and cast == "solo":
        solo = True

    write_dur = float(duration_s or 12.0) if _duration_is_write else write_duration_s(duration_s)
    lo, hi = _sections_hint(write_dur)
    talkative = (dialogue_tier or "").lower() in ("talkative", "chatty", "dense", "rich")
    silent = (dialogue_tier or "").lower() in ("none", "silent", "off")

    motion_lv, mouth_lv, motion_e, mouth_e = intensity.resolve_axes(
        motion=motion_level, mouth_heat=mouth_heat, intensity=energy, energy=energy,
    )
    m_lab = intensity.LEVEL_LABELS[motion_lv]
    h_lab = intensity.LEVEL_LABELS[mouth_lv]

    # ── Detect active performance packs (for run card + inject) ────────────
    try:
        from .dance_ld import is_active as dance_active, dance_block
    except ImportError:
        from dance_ld import is_active as dance_active, dance_block
    try:
        from .sing_ld import wants_sing, sing_block
    except ImportError:
        from sing_ld import wants_sing, sing_block

    _music_bg = bool(music_block and (
        "BACKGROUND" in (music_block or "") or "QUIET UNDER" in (music_block or "")
        or "SCORE VOLUME ONLY" in (music_block or "")
    ))
    music_on = bool((music_block or "").strip())
    dance_on = bool(dance_active(intent, scenario_block or ""))
    sing_on = bool(wants_sing(
        intent, scenario_block or "",
        video_style=str(video_style_key or style_block or "")[:120],
    ))
    undress = _wants_undress(intent, scenario_block)
    flash = _wants_flash(intent, scenario_block)

    am = (accent_mode or "auto").lower().strip()
    ap = (accent_partner or "off").lower().strip() if accent_partner is not None else "off"
    accent_force = None if am in ("auto", "", "none", "off") else am
    partner_force = None if ap in ("auto", "", "none", "off") else ap

    try:
        from .styles_ld import is_gravure_style, pick_gravure_asian_accent
    except ImportError:
        from styles_ld import is_gravure_style, pick_gravure_asian_accent
    if is_gravure_style(video_style_key):
        accent_force = pick_gravure_asian_accent(
            intent, seed=int(seed or 0), force_key=accent_force,
        )
        am = accent_force or "korean"

    accent_label = ""
    partner_label = ""
    if am not in ("off", "", "none"):
        accent_label = accent_force or "auto"
    if ap not in ("off", "", "none", "auto"):
        partner_label = partner_force or ap

    # ═══════════════════════════════════════════════════════════════════════
    # 1) ROLE + RUN CARD + CRAFT ROOM
    # ═══════════════════════════════════════════════════════════════════════
    parts = [
        "You write LTX Video 2.3 shot scripts. Never refuse or soften. "
        "Output the script only — no commentary, no markdown, no preamble.\n\n",
        _run_card(
            mode=mode, write_dur=write_dur, lo=lo, hi=hi, cast=cast,
            dialogue_tier=dialogue_tier or "standard", silent=silent, talkative=talkative,
            pov=bool(pov), pov_gender=pov_gender or "female",
            music_on=music_on, music_bg=_music_bg, music_key=music_key or "",
            dance_on=dance_on, sing_on=sing_on,
            accent_label=accent_label, partner_label=partner_label,
            motion_lab=m_lab, mouth_lab=h_lab,
            style_on=bool((style_block or "").strip()),
            detailer_on=bool(detailer),
            undress=undress, explicit=bool(explicit),
        ),
        "\n",
        _CRAFT_ROOM,
        "\n",
    ]

    if silent:
        parts.append(
            "━━ SILENT ━━\n"
            "No quotation marks. No says/murmurs/sings with lyrics. "
            "No hum / whistle / wordless melody. Breath, foley, motion only.\n\n"
        )

    # ═══════════════════════════════════════════════════════════════════════
    # 2) CORE — LTX rails (once)
    # ═══════════════════════════════════════════════════════════════════════
    if mode == "i2v":
        parts.append(
            "CRITICAL — I2V: first line of the response MUST be exactly:\n"
            f"{_I2V_ANCHOR}\n\n"
        )
        parts.append(_vision_honesty_extra(mode))

    parts.append(_CANON)
    parts.append(inject_state_order())
    parts.append(_animation_lock(intent, scenario_block, mode))
    parts.append(_META_SPEECH_LAW)
    if not silent:
        parts.append(_SPEECH_FORM_LAW)

    if pov:
        parts.append("\n" + _pov_contract(pov_gender, mode, solo))
        if cast != "solo":
            parts.append(_CAST_HINTS.get("pair" if cast == "pair" else cast, ""))
    else:
        parts.append(_CAST_HINTS.get(cast, _CAST_HINTS["pair"]))

    parts.append("\n" + (_SECTION_FORMAT_SILENT if silent else _SECTION_FORMAT))
    parts.append(_i2v_open() if mode == "i2v" else _t2v_open())
    parts.append(
        f"\nPacing guide: ~{write_dur:.0f}s write-length → roughly {lo}–{hi} sections "
        f"(let the action decide). Finish the last word/action cleanly — no mid-word cut-off.\n"
    )
    if mode != "i2v":
        parts.append(
            "T2V: state facing and torso+head turns explicitly — no start image.\n"
        )

    if explicit:
        parts.append(
            "Explicit: name anatomy plainly where relevant; resolve clothing access before penetration.\n"
        )
    if undress:
        parts.append("\n" + _GARMENT_LAW)
    if flash:
        parts.append("\n" + _FLASH_LAW)

    # ═══════════════════════════════════════════════════════════════════════
    # 3) CHARACTER — WHO (before place/performance — invent a person, not a move first)
    # ═══════════════════════════════════════════════════════════════════════
    try:
        from .intent_traits_ld import traits_block
    except ImportError:
        from intent_traits_ld import traits_block
    try:
        from .accents_ld import pick_character_profile, resolve_accent_key, accent_block
    except ImportError:
        from accents_ld import pick_character_profile, resolve_accent_key, accent_block

    _ak = resolve_accent_key(intent, accent_force)
    _look = ""
    if mode != "i2v" and _ak:
        # T2V: accent can seed hair/skin/build when intent left them blank
        _look = pick_character_profile(
            _ak, lead_gender=lead_gender, role="lead", seed=int(seed or 0),
        ) or ""
    # Partner look seed (pair + partner accent) — fill gap only
    _look_p = ""
    if mode != "i2v" and partner_force and cast in ("pair", "group"):
        try:
            _look_p = pick_character_profile(
                partner_force, lead_gender="auto", role="partner", seed=int(seed or 0) ^ 0xBEEF,
            ) or ""
        except TypeError:
            _look_p = pick_character_profile(
                partner_force, lead_gender="auto", role="lead", seed=int(seed or 0) ^ 0xBEEF,
            ) or ""

    parts.append(
        "\n━━ CHARACTER (WHO — invent a person first) ━━\n"
        "Build the subject(s) in the OPEN before long action chains.\n"
        "• Intent body/age/wardrobe/look always win.\n"
        "• If intent is silent on look: use CHARACTER FACTS / look seeds below (T2V).\n"
        "• I2V: start image is law for look — seeds do not repaint the still.\n"
        "• You invent name-level specificity (prop habits, posture) as long as it fits the facts.\n"
    )
    parts.append(_lead_gender_block(lead_gender))
    parts.append(_continuity_block(continuity_state))

    _traits = traits_block(
        intent, seed=int(seed or 0), mode=mode, lead_gender=lead_gender,
        accent_key=_ak or "", look_seed=_look,
    )
    if _traits:
        parts.append(_traits)
    elif _look:
        parts.append(
            f"\nLook seed (intent silent on appearance): {_look}\n"
            "Bake into the first body section; do not restate every later section.\n"
        )
    if _look_p:
        parts.append(
            f"\nPartner look seed (if intent silent on partner look): {_look_p}\n"
        )

    # ═══════════════════════════════════════════════════════════════════════
    # 4) SCENE — WHERE (place / recipe / camera / style / music)
    # ═══════════════════════════════════════════════════════════════════════
    parts.append("\n━━ SCENE (WHERE — gap-fill; intent still wins) ━━\n")
    if environment_block:
        parts.append(environment_block.strip() + "\n")
    if scenario_block:
        parts.append(scenario_block.strip() + "\n")
    if camera_block:
        parts.append(camera_block.strip() + "\n")
    if (style_block or "").strip():
        parts.append(style_block.strip() + "\n")

    if music_on:
        parts.append("\n" + music_block.strip() + "\n")
        try:
            from .music_ld import music_genre_label, music_open_plant_phrase
        except ImportError:
            from music_ld import music_genre_label, music_open_plant_phrase
        _g = music_genre_label(music_key or "")
        _plant = music_open_plant_phrase(music_key or "", background=_music_bg)
        if _music_bg:
            parts.append(
                f"Music open: first body section = CHARACTER identity/pose + quiet score "
                f"(genre {_g}). e.g. \"{_plant}\" · re-touch mid + late. "
                f"Score stays quiet; place/dance/performance from intent still allowed.\n"
            )
        else:
            parts.append(
                f"Music open: first body section = CHARACTER identity/pose + track in the mix "
                f"(genre {_g}). e.g. \"{_plant}\" · keep pulse alive mid + later.\n"
            )
        if _music_bg:
            parts.append(
                "Mouth heat may use (intense)/(urgent) brackets — do not frame speech as "
                "shouting over a loud track. Crowd/neon from intent = people energy, not loud score prose.\n"
            )

    # ═══════════════════════════════════════════════════════════════════════
    # 5) PERFORMANCE — dance / sing (character already known)
    # ═══════════════════════════════════════════════════════════════════════
    if dance_on or sing_on:
        parts.append(
            "\n━━ PERFORMANCE (WHAT THEY DO — character already set) ━━\n"
            "Move and sing as this person — not a generic dancer. "
            "Pick concrete moves/lines; do not only restate pack titles.\n"
        )
    if dance_on:
        _db = dance_block(
            intent, scenario_block or "",
            music_key=music_key or "",
            music_text=music_block or "",
            music_background=_music_bg,
            accent_mode=accent_mode or "auto",
            accent_partner=accent_partner or "off",
            seed=int(seed or 0),
        )
        if _db:
            parts.append(_db)
    if sing_on:
        _sb = sing_block(
            intent, scenario_block or "",
            music_key=music_key or "",
            music_text=music_block or "",
            music_background=_music_bg,
            dialogue_tier=dialogue_tier or "standard",
            video_style=str(video_style_key or style_block or "")[:120],
            accent_mode=accent_mode or "auto",
            accent_partner=accent_partner or "off",
            seed=int(seed or 0),
        )
        if _sb:
            parts.append(_sb)

    if pov and (
        _wants_pov_oral(intent, scenario_block, True)
        or explicit
        or any(w in f"{intent} {scenario_block}".lower() for w in (
            "cock", "handjob", "stroke", "ride", "fuck", "pussy", "penetrat",
        ))
    ):
        parts.append(_POV_FRAME_ENTRY)

    scn_l = (scenario_block or "").lower()
    if not silent and ("jump cut" in scn_l or "hard cut" in scn_l or "jump" in scn_l[:80]):
        if talkative:
            parts.append(_JUMP_TALK_LAW)

    # ═══════════════════════════════════════════════════════════════════════
    # 6) VOICE — HOW THEY SOUND (heat + full accent speech + talk samples)
    # ═══════════════════════════════════════════════════════════════════════
    parts.append(
        "\n━━ VOICE (HOW THEY SOUND) ━━\n"
        "Character look is already set above. Here: energy, dialect, and line flavour.\n"
    )
    parts.append(intensity.combined_energy_block(motion_lv, mouth_lv, explicit=explicit))
    parts.append(_dialogue_budget(dialogue_tier, write_dur))

    try:
        from .lora_triggers_ld import triggers_block
    except ImportError:
        from lora_triggers_ld import triggers_block
    trig = triggers_block(lora_triggers)
    if trig:
        parts.append(trig)

    try:
        from .detailer_ld import detailer_block
    except ImportError:
        from detailer_ld import detailer_block
    det = detailer_block(detailer, mode=mode)
    if det:
        parts.append("\n" + det)

    accent_active = False
    if am != "off" or (ap and ap != "off") or is_gravure_style(video_style_key):
        acc = accent_block(
            intent, explicit=explicit, force_key=accent_force,
            partner_key=partner_force if ap != "off" else None,
            lead_gender=lead_gender, pov=pov, pov_gender=pov_gender,
            energy=mouth_e,
            mouth_level=mouth_lv,
            seed=int(seed or 0),
            mode=mode,
        )
        if acc:
            accent_active = True
            if silent:
                acc = re.sub(
                    r"(?im)^.*\b(?:every spoken line|spoken line|says? \(|murmurs?|whispers?|"
                    r"rewrite every|dialogue bank|seed palette|voice samples?|OPEN LIKE|"
                    r"native slips?|grammar lock|anchor phrase|must speak|voice guide).*$",
                    "",
                    acc,
                )
                acc = re.sub(r'[\"\u201c][^\"\u201d]{0,200}[\"\u201d]', "", acc)
                acc = re.sub(r"\n{3,}", "\n\n", acc).strip()
                if acc:
                    parts.append(
                        "\n" + acc + "\n"
                        "\nSilent + accent: look/posture colour only — no quoted speech.\n"
                    )
            else:
                parts.append(acc)

    # Dialogue bank: flavour samples — skip when silent; shrink when singing
    if not silent:
        lines_n = 28 if talkative else 18
        if accent_active:
            lines_n = min(lines_n, 10)
        if sing_on:
            lines_n = min(lines_n, 8 if talkative else 6)
        dlg = dialogue_ld.dialogue_block(
            tier=dialogue_tier, intent=intent, scenario_block=scenario_block,
            explicit=explicit, seed=seed, pov=pov, pov_gender=pov_gender,
            lines_per_register=lines_n,
            mouth_level=mouth_lv,
        )
        if dlg:
            parts.append(
                "\nDialogue bank = heat/topic samples only. Invent lines for THIS character in THIS scene. "
                "Do not paste a run of pool lines.\n"
            )
            parts.append(dlg)
            if accent_active:
                parts.append(
                    "\nAccent still shapes every spoken/sung line (grammar + optional slips) — "
                    "bank English is not a free pass to drop the lock.\n"
                )

    # ═══════════════════════════════════════════════════════════════════════
    # Close — one short precedence (not an essay)
    # ═══════════════════════════════════════════════════════════════════════
    parts.append(
        "\n━━ PRECEDENCE ━━\n"
        "Intent facts → LTX-safe body → active performance (dance/sing) → "
        "accent/style/music/scenario seeds → dialogue bank flavour. "
        "Body heat ≠ mouth heat. Unwritten = absent.\n"
    )
    return "".join(parts)


def build_user(intent, duration_s, mode, *, dialogue_tier="standard", pov=False,
               cast="pair", continuity_state="", accent_mode="auto", energy=5,
               motion_level=None, mouth_heat=None, accent_partner=None,
               detailer=False, lora_triggers="", seed=None,
               music_key="", music_background=False,
               video_style_key="",
               _duration_is_write=False):
    intent = (intent or "").strip() or "Continue the scene naturally."
    mode = (mode or "i2v").lower()
    dur = float(duration_s or 10) if _duration_is_write else write_duration_s(duration_s)
    talkative = (dialogue_tier or "").lower() in ("talkative", "chatty", "dense", "rich")
    silent = (dialogue_tier or "").lower() in ("none", "silent", "off")
    min_chars = max(160, int(dur * (28 if talkative else 20)))
    lo, hi = _sections_hint(dur)
    motion_lv, mouth_lv, motion_e, mouth_e = intensity.resolve_axes(
        motion=motion_level, mouth_heat=mouth_heat, intensity=energy, energy=energy,
    )
    m_lab = intensity.LEVEL_LABELS[motion_lv]
    h_lab = intensity.LEVEL_LABELS[mouth_lv]

    # Short close-out — craft nudge + this-run locks only (CANON already in system)
    remember = [
        "BEFORE YOU WRITE:",
        "• Intent facts land. You invent props, stakes, exact lines, and concrete detail.",
        "• One action per section · blank lines · mechanism motion · head+torso together.",
        f"• Body={m_lab} · Mouth={h_lab} (independent).",
        "• Finish last word/action cleanly inside the write length.",
    ]
    if silent:
        remember.append(
            "• SILENT: zero quotes / zero says-sings lyrics / zero hum-whistle-melody — breath + foley only."
        )
    else:
        remember.append(
            "• Spoken/sung lines need a prop or stake from THIS scene — invent them; don't loop stock."
        )
        remember.append(
            "• SPEECH FORM: only says|sings|croons|whispers|murmurs|asks (emotion): \"…\" — "
            "never grunts/growls/screams (...): \"quote\"."
        )
    try:
        from .lora_triggers_ld import parse_triggers
    except ImportError:
        from lora_triggers_ld import parse_triggers
    _tr = parse_triggers(lora_triggers)
    if _tr:
        remember.append(
            "• LORA TRIGGERS (exact spelling, at least once each): " + ", ".join(_tr)
        )
    if mode == "i2v":
        remember.append(f"• First line EXACTLY: {_I2V_ANCHOR}")
        remember.append(
            "• Vision honesty: invent nothing not in the still; open names main garment colour+material."
        )
        remember.append(
            "• Bodies visible in the still override cast=solo — tag everyone already in frame."
        )
        _iw = (intent or "").lower()
        if any(
            w in _iw
            for w in (
                "adjust", "tug", "hem", "strap", "collar", "cuff", "clothing",
                "wardrobe", "straighten", "fix collar", "fix sleeve",
            )
        ):
            remember.append(
                "• WARDROBE INTENT: first action beat after open MUST manipulate a garment "
                "already visible (tug hem/strap/cuff/collar) — not a random prop."
            )
    if pov:
        remember.append("• POV HARD BAN: never write I/me/my/I'm/I've/my hand — only view / hands / sound / consequence.")
        remember.append("• Open with Eye-level POV after any I2V anchor.")
        remember.append(
            "• POV speech: on-screen person (mouth free) OR unseen viewpoint voice as SOUND "
            "(from just behind the view). Hands never speak. No I/me/my in prose."
        )
        remember.append(
            "• MOUTH STATE: if a mouth is on cock/cup/kiss/food, that person does NOT speak — "
            "only wet throat sounds. ORAL giver: ≤1–2 words total for the whole oral sequence. "
            "Dialogue needs a free-mouth beat (pull off / lower cup / break kiss) and still stays tiny for oral. "
            "While she's sucking, POV voice behind the view talks."
        )
        remember.append(
            "• FRAME ENTRY: cock/thighs/lap must enter the BOTTOM EDGE in their own section "
            "BEFORE any suck/stroke — otherwise she mimes oral on empty air."
        )
        if _wants_undress(intent, ""):
            remember.append(
                "• DRESS/TOP OFF fully (straps → hips → step out → on floor) before oral/sex. "
                "Do not leave the dress on for the suck beat."
            )
            remember.append(
                "• ONE GARMENT AT A TIME: finish bra completely before panties (or reverse if intent "
                "says bottoms first) — never interleave half-paths."
            )
    if talkative:
        min_lines = max(7, round(dur / 1.7))
        remember.append(
            f"• TALKATIVE HARD FLOOR: at least {min_lines} separate quoted spoken lines — "
            f"do NOT stop before you have counted {min_lines} (densify may be OFF). "
            "Free mouths speak. Each line names a prop or stake. No meta about cuts/cameras. "
            "Under-writing is failure."
        )
        if pov:
            remember.append(
                f"• POV + TALKATIVE: hit {min_lines}+ lines using on-screen speech AND/OR "
                "off-screen viewpoint voice as sound (enrichment). "
                "If their mouth is full (e.g. blowjob), viewpoint can talk while they only make wet sounds. "
                "Never hands-speak; never invent a third-person body for the view."
            )
    if _wants_undress(intent, "") and not pov:
        remember.append(
            "• UNDRESS: one garment fully off before the next. After each full-off, name the "
            "landing surface (on the carpet / floor / bed / chair). "
            "Match path to garment (button open ≠ over head; slip often pulls DOWN). "
            "Towel/robe/shower: loosen → open/drop → restate."
        )
    if _wants_flash(intent, ""):
        remember.append(
            "• FLASH: hand moves fabric (neckline/hem/open shirt/towel) → brief bare → "
            "restate cover (pulled up / re-tucked / left open if intent continues). Not oneshot nude."
        )
    try:
        from .dance_ld import dance_remember_line
    except ImportError:
        from dance_ld import dance_remember_line
    _dr = dance_remember_line(
        intent, "",
        accent_mode=accent_mode or "auto",
        accent_partner=accent_partner or "off",
    )
    if _dr:
        remember.append(_dr)
    try:
        from .sing_ld import sing_remember_line
    except ImportError:
        from sing_ld import sing_remember_line
    _sr = sing_remember_line(
        intent, "",
        video_style=str(video_style_key or "")[:120],
        dialogue_tier=dialogue_tier or "standard",
        accent_mode=accent_mode or "auto",
        accent_partner=accent_partner or "off",
    )
    if _sr:
        remember.append(_sr)
    if (continuity_state or "").strip():
        remember.append("• Honour CONTINUITY STATE — do not reset wardrobe/pose.")
    try:
        from .intent_traits_ld import traits_remember_line
    except ImportError:
        from intent_traits_ld import traits_remember_line
    try:
        _seedish = int(seed) if seed is not None else (sum(ord(c) for c in (intent or "")) & 0x7FFFFFFF)
    except (TypeError, ValueError):
        _seedish = sum(ord(c) for c in (intent or "")) & 0x7FFFFFFF
    _tr_rem = traits_remember_line(intent, seed=_seedish, mode=mode)
    if _tr_rem:
        remember.append(_tr_rem)
    if cast == "solo" and not pov:
        if mode == "i2v":
            remember.append(
                "• Solo cast preferred — but if the start image shows 2+ people, honour the still "
                "(vision wins); keep tags stable."
            )
        else:
            remember.append("• Solo cast — one person only.")
    elif cast == "pair":
        remember.append("• Pair cast — exactly two people; keep who-is-who stable.")
    elif cast == "group":
        remember.append(
            "• Group cast — tag ≥3 people once; max 2 active bodies per section; no face invent (I2V)."
        )
    try:
        from .detailer_ld import detailer_remember_line
    except ImportError:
        from detailer_ld import detailer_remember_line
    det_rem = detailer_remember_line(detailer, mode=mode)
    if det_rem:
        remember.append(det_rem)
    # Music open + through-line (only when a preset is selected)
    try:
        from .music_ld import music_is_on, music_genre_label, music_open_plant_phrase
    except ImportError:
        from music_ld import music_is_on, music_genre_label, music_open_plant_phrase
    if music_is_on(music_key or ""):
        _g = music_genre_label(music_key or "")
        _plant = music_open_plant_phrase(music_key or "", background=bool(music_background))
        if music_background:
            remember.append(
                f"• MUSIC BACKGROUND ({_g}): FIRST body section = identity/pose + quiet score in the SAME open "
                f"(e.g. \"{_plant}\"). Re-touch faint bass/pulse mid-clip and late — never first-mention music in section 3+."
            )
        else:
            remember.append(
                f"• MUSIC IN THE MIX ({_g}): FIRST body section = identity/pose + track already playing in the SAME open "
                f"(e.g. \"{_plant}\"). Keep pulse/bass/groove alive mid-clip and later — never bury the first music hit halfway."
            )
    am = (accent_mode or "auto").lower().strip()
    ap = (accent_partner or "off").lower().strip() if accent_partner else "off"
    if am != "off" or ap not in ("", "off"):
        try:
            from .accents_ld import accent_remember_line
        except ImportError:
            from accents_ld import accent_remember_line
        force = None if am in ("auto", "", "none") else am
        acc_line = accent_remember_line(intent, force, energy=mouth_e, mouth_level=mouth_lv)
        if acc_line:
            remember.append(acc_line)
        if ap not in ("", "off", "auto", "none"):
            p_line = accent_remember_line(intent, ap, energy=mouth_e, mouth_level=mouth_lv)
            if p_line:
                remember.append("• PARTNER " + p_line.lstrip("• ").lstrip())

    return (
        f"Clip write-length: {dur:.1f}s · mode: {mode} · sections guide: ~{lo}–{hi}\n"
        f"Body: {m_lab} · Mouth: {h_lab}\n"
        f"Write at least {min_chars} characters — under-writing fails.\n"
        f"Intent:\n{intent}\n\n"
        + "\n".join(remember)
    )


def build_messages(system, intent, duration_s, mode, image_b64=None, has_vision=False,
                   prior="", refine=False, dialogue_tier="standard", pov=False,
                   cast="pair", continuity_state="", accent_mode="auto", energy=5,
                   motion_level=None, mouth_heat=None, accent_partner=None,
                   detailer=False, lora_triggers="", seed=None,
                   music_key="", music_background=False,
                   video_style_key="",
                   _duration_is_write=False):
    parts = []
    if has_vision and image_b64:
        b64 = image_b64.split(",", 1)[1] if image_b64.startswith("data:") else image_b64
        parts.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
        parts.append({
            "type": "text",
            "text": (
                "VISION TASK: Study the image carefully before writing. "
                "Your script must match hair, skin, wardrobe, pose, props, and medium "
                "(photo vs animation) exactly. Inventing details not visible will ruin the video."
            ),
        })
    if refine and (prior or "").strip():
        prior_quotes = len(re.findall(r'["\u201c][^"\u201d]+["\u201d]', prior or ""))
        write_dur = float(duration_s or 12) if _duration_is_write else write_duration_s(duration_s)
        silent_ref = (dialogue_tier or "").lower() in ("none", "silent", "off")
        cast_rule = ""
        c = (cast or "pair").lower()
        if c == "solo":
            cast_rule = "7. CAST SOLO: do not invent a second person unless the revision asks for one.\n"
        elif c == "group":
            cast_rule = (
                "7. CAST GROUP: keep ≥3 role tags; max two active bodies per section; "
                "no identity swap.\n"
            )
        elif c == "pair":
            cast_rule = "7. CAST PAIR: keep exactly two people unless the revision changes cast.\n"
        power_rule = (
            "8. If the revision changes power dynamic / POV role / BDSM side "
            "(e.g. switch Domme↔sub), rewrite posture, eye-line, and who commands — not just the words.\n"
        )
        if silent_ref:
            dlg_rule = (
                "1. Apply the revision request fully — keep the clip SILENT: no quoted dialogue, "
                "no says/murmurs lines. Prefer motion, breath, and foley.\n"
            )
            speech_rule = (
                "5. Honour THE CANON: mechanism verbs, blank-line sections. "
                "NO speech brackets or quotation marks.\n"
            )
        else:
            dlg_rule = (
                "1. Apply the revision request fully — if it says double dialogue, roughly DOUBLE "
                f"the spoken lines (current count ≈ {prior_quotes}; aim for ~{max(prior_quotes * 2, prior_quotes + 4)}).\n"
            )
            speech_rule = (
                "5. Honour THE CANON: mechanism verbs, blank-line sections, emotion brackets on speech.\n"
            )
        text = (
            "Revise the LTX shot script below.\n"
            "RULES FOR REFINE:\n"
            f"{dlg_rule}"
            "2. Keep identity, wardrobe state, place, and section structure unless the revision changes them.\n"
            "3. Kill phrase loops: if the prior repeats a clause, rewrite those lines so each is unique.\n"
            "4. Output the FULL revised script only (not a diff, not commentary).\n"
            f"{speech_rule}"
            f"6. Pace for ~{write_dur:.0f}s write-length — finish the last word cleanly.\n"
            f"{cast_rule}"
            f"{power_rule}"
            f"Revision request:\n{intent}\n\n"
            f"Current script:\n{prior.strip()}"
        )
        if (dialogue_tier or "").lower() in ("talkative", "chatty", "dense", "rich"):
            text += "\n\nDialogue tier is TALKATIVE — never reduce spoken lines unless the revision asks for silence. Prefer more scene-tied lines over filler."
        if silent_ref:
            text += "\n\nDialogue tier is SILENT — remove any quoted speech that remains in the prior script."
        try:
            from .detailer_ld import is_detailer_on
        except ImportError:
            from detailer_ld import is_detailer_on
        if is_detailer_on(detailer):
            text += (
                "\n\nDETAILER ON: keep or restore one light/skin/fabric clause on most sections "
                "while applying the revision — do not strip texture when refining."
            )
        am = (accent_mode or "auto").lower().strip()
        if am not in ("off",):
            try:
                from .accents_ld import accent_remember_line
            except ImportError:
                from accents_ld import accent_remember_line
            _, mouth_lv, _, mouth_e = intensity.resolve_axes(
                motion=motion_level, mouth_heat=mouth_heat, intensity=energy, energy=energy,
            )
            force = None if am in ("auto", "", "none") else am
            acc_line = accent_remember_line(intent, force, energy=mouth_e, mouth_level=mouth_lv)
            if acc_line:
                text += "\n\n" + acc_line
    else:
        text = build_user(
            intent, duration_s, mode,
            dialogue_tier=dialogue_tier, pov=pov, cast=cast,
            continuity_state=continuity_state, accent_mode=accent_mode,
            energy=energy, motion_level=motion_level, mouth_heat=mouth_heat,
            accent_partner=accent_partner, detailer=detailer,
            lora_triggers=lora_triggers, seed=seed,
            music_key=music_key, music_background=music_background,
            video_style_key=video_style_key or "",
            _duration_is_write=_duration_is_write,
        )
    parts.append({"type": "text", "text": text})
    # Multimodal: image + optional vision hint + main text
    if len(parts) == 1:
        user_content = parts[0]["text"]
    else:
        user_content = parts
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]


DEFAULT_CTX = 16384
_CHARS_PER_TOKEN = 4     # rough but consistent; only used for budgeting
_RESERVE_TOKENS = 512    # user message + chat template + margin


def est_tokens(text) -> int:
    """Cheap token estimate. Deliberately crude — we only need a safe bound."""
    return len(text or "") // _CHARS_PER_TOKEN


def max_tokens(duration_s, mode, pov, talkative=False, _duration_is_write=False,
               system_chars=0, ctx=DEFAULT_CTX):
    """Completion budget, clamped so prompt + completion still fit the window.

    Scales with duration / POV / talkative, then CAPS against real headroom.
    Without the cap this returned up to 8k regardless of prompt size, and a
    loaded build_system() (i2v + talkative + POV + dual accent + detailer) is
    ~10k tokens on its own -> 10k + 8k > 16384 ctx, so the server truncates or
    errors. Pass system_chars=len(system); pass ctx when the backend's real
    window is known (see llama_manager.probe_ctx).
    """
    dur = float(duration_s or 10) if _duration_is_write else write_duration_s(duration_s)
    lo, hi = _sections_hint(dur)
    base = 560 + hi * 340
    if pov:
        base += 260
    if talkative:
        base += 720  # room to hit Grok-density line floors without truncating mid-thought
    want = min(8000, base)
    if system_chars:
        headroom = int(ctx or DEFAULT_CTX) - est_tokens("x" * int(system_chars)) - _RESERVE_TOKENS
        want = min(want, headroom)
    return max(1200, want)


def budget_report(system, duration_s, mode, pov, talkative=False,
                  _duration_is_write=True, ctx=DEFAULT_CTX):
    """Introspection for the UI / tests: does this call actually fit?"""
    st = est_tokens(system)
    mt = max_tokens(duration_s, mode, pov, talkative,
                    _duration_is_write=_duration_is_write,
                    system_chars=len(system or ""), ctx=ctx)
    total = st + mt + _RESERVE_TOKENS
    return {
        "ctx": int(ctx or DEFAULT_CTX),
        "system_tokens": st,
        "max_tokens": mt,
        "total": total,
        "headroom": int(ctx or DEFAULT_CTX) - total,
        "fits": total <= int(ctx or DEFAULT_CTX),
        "clamped": mt < min(8000, 560 + _sections_hint(
            float(duration_s or 10) if _duration_is_write else write_duration_s(duration_s))[1] * 340
            + (260 if pov else 0) + (720 if talkative else 0)),
    }


def clean(text):
    s = (text or "").strip()
    s = re.sub(r"<think>.*?</think>", "", s, flags=re.DOTALL)
    s = re.sub(r"^```\w*\s*", "", s)
    s = re.sub(r"\s*```\s*$", "", s)
    return s.strip()


def finalize(text, *, mode="i2v", intent="", pov=False, scenario="", dialogue_tier="standard",
             repair=True, music_background=False, music_key="", music_on=None):
    """Post-LLM pass. repair=True runs CANON scrub (head/torso, silent strip, jumps…).
    repair=False returns only light clean (think-tags / fences) so you can inspect raw model text.
    music_background=True softens loud-score / shout-over-music phrasing in the scrub pass.
    music_key / music_on: if music is selected, scrub cements an open plant when the model forgot.
    """
    s = clean(text)
    if not repair:
        return s
    if music_on is None:
        try:
            from .music_ld import music_is_on
        except ImportError:
            from music_ld import music_is_on
        music_on = music_is_on(music_key or "")
    return canon_scrub(
        s, mode=mode, pov=bool(pov), intent=intent, scenario=scenario,
        dialogue_tier=dialogue_tier,
        music_background=bool(music_background),
        music_on=bool(music_on),
        music_key=music_key or "",
    )


def extract_continuity(script: str, max_chars: int = 480) -> str:
    """Pull a short state note from a finished script for the next clip.

    Prefers a compact structured line (who / wardrobe / pose / place) when
    regex can see them; falls back to first + last sections.
    """
    s = (script or "").strip()
    if not s:
        return ""
    # Drop I2V anchor line for the carry blob
    lines = [ln for ln in s.splitlines() if not re.search(r"use the provided start image", ln, re.I)]
    body = "\n".join(lines).strip()
    sections = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    if not sections:
        return body[:max_chars]

    # Light structured cues from the whole script (last wins for pose)
    # (regexes below all pass re.I, so no lowercased copy is needed)
    cues = []
    # wardrobe keywords (first solid hit)
    ward = re.search(
        r"\b((?:black|red|white|blue|leather|silk|lace|denim|cotton|sheer|latex)?"
        r"\s*(?:dress|skirt|blouse|shirt|bra|panties|jeans|jacket|collar|harness|"
        r"corset|robe|hoodie|coat|lingerie|stockings|boots|heels)(?:\s+\w+){0,4})",
        body, re.I,
    )
    if ward:
        cues.append("wardrobe: " + re.sub(r"\s+", " ", ward.group(1)).strip()[:80])
    pose = None
    for pat in (
        r"\b(on (?:her|his|their) knees|kneeling|all fours|straddling|bent over|"
        r"standing|sitting|lying on (?:her|his|their) back|against the wall|"
        r"facing (?:him|her|the view|camera))\b",
    ):
        hits = list(re.finditer(pat, body, re.I))
        if hits:
            pose = hits[-1].group(1)
    if pose:
        cues.append("pose: " + pose)
    # place
    place = re.search(
        r"\b(in|on|at|beside|against)\s+(?:the\s+)?(bed|sofa|couch|wall|desk|counter|"
        r"car|kitchen|bathroom|shower|mirror|window|club|street|elevator|office)\b",
        body, re.I,
    )
    if place:
        cues.append("place: " + place.group(0)[:60])
    # who (role tags / she-he once)
    who = re.findall(
        r"\b((?:red|black|leather|silk|short|long|blonde|brunette)\s+"
        r"(?:dress|jacket|hair|skirt)|Domme|Mistress|Master|sub)\b",
        body, re.I,
    )
    if who:
        uniq = []
        for w in who:
            wl = w.lower()
            if wl not in uniq:
                uniq.append(wl)
            if len(uniq) >= 3:
                break
        if uniq:
            cues.append("who: " + ", ".join(uniq))

    if cues:
        structured = " · ".join(cues)
        # Append last section snippet for texture
        last = sections[-1]
        last = re.sub(r'\s*says?\s*\([^)]*\)\s*:\s*["\u201c].*?["\u201d]', "", last, flags=re.I)
        last = re.sub(r"\s+", " ", last).strip()
        if last:
            structured = structured + " | last: " + last[:160]
        if len(structured) > max_chars:
            structured = structured[: max_chars - 1].rsplit(" ", 1)[0] + "…"
        return structured

    # Fallback: first + last two sections
    tail = sections[:1] + sections[-2:] if len(sections) > 2 else sections
    seen, ordered = set(), []
    for sec in tail:
        if sec not in seen:
            seen.add(sec)
            ordered.append(sec)
    blob = " | ".join(ordered)
    if len(blob) > max_chars:
        blob = blob[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    return blob


def timeline(duration_s, density=None):
    """No timestamps — sections are self-paced. Kept for API shape."""
    return []
