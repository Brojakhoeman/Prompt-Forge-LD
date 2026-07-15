"""
scenarios_ld.py — I2V scenarios vs T2V shot recipes for PromptForge LD
===========================================================================
Two lanes (filtered by video mode in the UI):
  • I2V — honour the start frame; JUMP cuts; micro-motion; no restage fights
  • T2V — deep SHOT RECIPES (stakes, section plan, dialogue shape, cast hints)

Storage: each entry is a dict with at least tag/setup/choreography/modes.
Legacy 3-tuples are accepted by the normalizer for hot-edit compatibility.
"""

from __future__ import annotations

import os
import re
import sys
import importlib


def _modes_tuple(modes):
    if not modes:
        return ("i2v", "t2v")
    if isinstance(modes, str):
        modes = (modes,)
    out = []
    for m in modes:
        m = (m or "").lower().strip()
        if m in ("i2v", "t2v") and m not in out:
            out.append(m)
    return tuple(out) or ("i2v", "t2v")


def normalize_scenario(val):
    """tuple/dict/sentinel → dict | None | \"RANDOM\"."""
    if val is None or val == "RANDOM":
        return val
    if isinstance(val, dict):
        d = dict(val)
        tag = d.get("tag") or "SFW"
        d["tag"] = "RECIPE" if str(tag).upper() == "RECIPE" else str(tag).upper()
        d["setup"] = d.get("setup") or ""
        d["choreography"] = d.get("choreography") or d.get("choreo") or ""
        d["modes"] = _modes_tuple(d.get("modes") or ("i2v", "t2v"))
        return d
    if isinstance(val, (tuple, list)) and len(val) >= 3:
        tag, setup, choreo = val[0], val[1], val[2]
        modes = val[3] if len(val) > 3 else None
        extra = val[4] if len(val) > 4 and isinstance(val[4], dict) else {}
        d = {"tag": tag, "setup": setup, "choreography": choreo, **extra}
        if modes is not None:
            d["modes"] = _modes_tuple(modes)
        elif str(tag).upper() == "JUMP":
            d["modes"] = ("i2v",)
        else:
            d["modes"] = ("i2v", "t2v")
        d["tag"] = "RECIPE" if str(tag).upper() == "RECIPE" else str(tag).upper()
        return d
    return None


SCENARIO_PRESETS = {
    "None — user's prompt decides": None,
    "🎲 Random — seed picks": "RANDOM",
    '🚶 Walk in and stop': {
        "tag": 'SFW',
        "modes": ('i2v', 't2v'),
        "setup": 'A person walks into the space and stops.',
        "choreography": 'She walks forward at a steady pace, stops centre-frame, weight settles on both feet, and faces the camera.',
    },
    '🚪 Enter through a door': {
        "tag": 'SFW',
        "modes": ('i2v', 't2v'),
        "setup": 'A person opens a door and steps through.',
        "choreography": 'She pushes the door open, steps through in one motion, then turns her torso and head together to face into the room.',
    },
    '🪑 Sit down on a chair': {
        "tag": 'SFW',
        "modes": ('i2v', 't2v'),
        "setup": 'A person sits on a chair.',
        "choreography": 'She steps to the chair, turns to face out, and lowers into the seat in one smooth motion.',
    },
    '🧍 Stand up from a chair': {
        "tag": 'SFW',
        "modes": ('i2v', 't2v'),
        "setup": 'A person rises from a chair.',
        "choreography": 'She pushes on the armrests or thighs and rises to her feet, straightening as she stands.',
    },
    '🔄 Turn to look back': {
        "tag": 'SFW',
        "modes": ('i2v', 't2v'),
        "setup": 'A person looks back over the shoulder.',
        "choreography": 'She rotates torso and head together at the waist to look back over her shoulder; hips stay mostly forward unless the beat needs a full turn.',
    },
    '💃 Dance on the spot': {
        "tag": 'SFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Solo dance / sway.',
        "choreography": 'She sways hips side to side, arms drift with the beat, weight shifts foot to foot, facing the camera.',
    },
    '🤗 Walk up and hug': {
        "tag": 'SFW',
        "modes": ('i2v', 't2v'),
        "setup": 'One person hugs another.',
        "choreography": 'She walks up to him, wraps both arms around him, and presses into a close hug; both faces stay readable or one cheek to shoulder.',
    },
    '💋 Blow a kiss to camera': {
        "tag": 'SFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Blow a kiss.',
        "choreography": 'She lifts fingertips to her lips, then sweeps her hand out toward the camera in a slow blown kiss.',
    },
    '🍑 Walk away, glance back': {
        "tag": 'SFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Walk away, look back.',
        "choreography": 'She walks away back-to-camera, stops, rotates torso and head together to look back over her shoulder at the camera while feet stay pointed away.',
    },
    '☕ Sip a drink': {
        "tag": 'SFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Sip a drink.',
        "choreography": 'She raises a cup or glass to her lips, takes a slow sip, lowers it, eyes toward camera or out a window.',
    },
    '🎤 Talk to camera / monologue': {
        "tag": 'SFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Address the camera with spoken lines.',
        "choreography": 'She faces the camera, hands gesture lightly, and delivers several short spoken lines with emotion brackets; small weight shifts only — this is a talking shot.',
    },
    '📞 Phone call pace': {
        "tag": 'SFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Phone call while pacing.',
        "choreography": 'She holds a phone to her ear, paces a few steps, turns torso+head together as she talks, then stops and lowers the phone.',
    },
    '🏋️ Workout rep': {
        "tag": 'SFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Simple exercise beat.',
        "choreography": 'She performs a clear rep (squat, push-up, or stretch) with controlled form, breath visible, then stands or resets facing camera.',
    },
    '🍳 Kitchen cook beat': {
        "tag": 'SFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Cooking action.',
        "choreography": 'She chops or stirs at a counter, lifts a pan or utensil, glances toward camera once, keeps hands busy with the task.',
    },
    '🚗 Lean on a car': {
        "tag": 'SFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Lean against a car.',
        "choreography": 'She leans back against the car body, one hand on the metal, weight settled, looking at camera.',
    },
    '💺 Sit between his legs': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": "She sits between a seated man's legs, back to his chest, facing camera.",
        "choreography": 'She steps between his spread legs, turns to face the camera, lowers to sit between his legs with her back against his chest; small hip circles as she settles.',
    },
    '🪑 Lap sit, facing him': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'She sits on his lap facing him, chest to chest.',
        "choreography": 'She steps over his thighs, faces him, lowers onto his lap straddling his hips, arms over his shoulders.',
    },
    '🔃 Grind on his lap': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Seated grind facing him.',
        "choreography": 'Seated on his lap facing him, she rolls her hips forward and back in a slow steady rhythm, torso upright.',
    },
    '🧍 Pressed to a wall': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Pinned to a wall, clothed or as intent says.',
        "choreography": 'He moves her back to the wall and leans in; she may lift one leg around his hip; faces stay close.',
    },
    '🔥 Missionary': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Missionary sex — she on her back, he between her legs.',
        "choreography": 'She lies on her back, knees open. He kneels between her legs and drives his cock into her pussy in a steady rhythm; name penetration every section.',
    },
    '🔥 Doggy': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Doggy — she on all fours, he behind.',
        "choreography": 'She on all fours, face toward camera if possible, back to him. He grips her hips and fucks her pussy from behind; continuous penetration language.',
    },
    '🔥 Cowgirl': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Cowgirl — she rides facing him.',
        "choreography": 'She straddles him facing him, lowers onto his cock, rides with rolling hips, hands on his chest.',
    },
    '🔥 Reverse cowgirl': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Reverse cowgirl — she rides facing camera, back to him.',
        "choreography": 'She straddles facing away, back to his chest, lowers onto his cock, rides while facing camera.',
    },
    '🔥 Bent over surface': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Bent over table/bed/counter, taken from behind.',
        "choreography": 'She bends at the waist over the surface, ass up. He grips her hips and fucks her from behind.',
    },
    '🔥 Standing wall sex': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Standing sex against a wall.',
        "choreography": 'Her back to the wall facing him; legs around his waist or one leg up; he fucks up into her.',
    },
    '🔥 Blowjob (kneeling)': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Kneeling blowjob.',
        "choreography": 'She kneels facing him, takes his cock in her mouth, bobs in a steady rhythm; hand on shaft if needed; eyes up when free.',
    },
    '🔥 POV blowjob': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'POV blowjob — camera is his eyes; she services the view.',
        "choreography": 'Eye-level male POV. She kneels into frame, takes the cock at the bottom edge into her mouth, bobs, hands visible; viewpoint = view/hands/sound only, never I/me/my body.',
    },
    '🔥 Oral on her': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'He eats her out.',
        "choreography": 'She on her back or edge of bed, thighs open. He between her legs licking her pussy; her hips press up.',
    },
    '🔥 Face sitting': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'She sits on his face.',
        "choreography": 'She straddles his head, lowers her pussy to his mouth, grinds slow circles; facing his feet or camera as fits.',
    },
    '🔥 69': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Mutual oral 69.',
        "choreography": 'Head-to-toe: she sucks his cock while he licks her pussy; both rock together.',
    },
    '🔥 Spooning sex': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Side-lying sex from behind.',
        "choreography": 'She on her side; he behind chest-to-back; cock into pussy from behind, spooned rhythm.',
    },
    '🍑 Doggy anal': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Anal doggy.',
        "choreography": 'She on all fours; he behind drives cock into her ass; grip hips; plain anatomy every section.',
    },
    '🌸 F/F scissor / grind': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'Two women grind pussies together.',
        "choreography": 'They interlock or stack and grind pussy-to-pussy in a building rhythm; hands on hips/thighs.',
    },
    '🌸 F/F oral': {
        "tag": 'NSFW',
        "modes": ('i2v', 't2v'),
        "setup": 'One woman goes down on another.',
        "choreography": 'One lies back thighs open; the other licks her pussy in a steady rhythm.',
    },
    '⚡ Jump: hello → POV blowjob': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens dressed, says hello; hard-cuts to POV blowjob (still clothed unless intent says naked).',
        "choreography": "SECTIONS 1–2 (setup, ~first third): She faces the view or camera fully clothed as in the frame/intent, smiles or lifts a hand, and says a short hello/greeting with an emotion bracket (use the user's words if they gave a line). Small natural motion only — no undress yet. HARD JUMP CUT (next section — mandatory): Instant cut. She is on her knees at eye-level male POV if POV is on (else third-person close). WARDROBE: KEEP her clothes from setup/start image unless the user's intent clearly asks for naked/topless/stripped — blowjob does NOT require full nude (top, dress, jeans still on is fine and preferred). She takes his cock into her mouth and sucks in a steady bobbing rhythm; hands on shaft/hips; restate pose + oral plainly after the cut — do not invent a full strip. Remaining sections: continue the blowjob with wet sounds; free mouths talk if dialogue is on.",
    },
    '⚡ Jump: chat → doggy': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens talking/flirting dressed; hard-cuts to doggy sex.',
        "choreography": 'SECTIONS 1–2: She (and he if present) talk face-to-face or she talks to camera, clothed, light gesture only. HARD JUMP CUT: Instant cut to her on all fours naked, him behind fucking her pussy doggy-style; name cock/pussy/penetration; no undress bridge. Continue doggy rhythm and dirty talk after the cut.',
    },
    '⚡ Jump: kiss → cowgirl': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens kissing; hard-cuts to her riding cowgirl.',
        "choreography": 'SECTIONS 1–2: They kiss standing or seated, mostly clothed. HARD JUMP CUT: Instant cut to her naked straddling him, pussy on his cock, riding cowgirl facing him. Restate the new pose; continue ride + talk.',
    },
    '⚡ Jump: doorway hello → wall pin fuck': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens at a door saying hi; hard-cuts to standing wall sex.',
        "choreography": 'SECTIONS 1–2: She in a doorway, greets him/camera, one step forward. HARD JUMP CUT: Her back naked against a wall, legs around him, he fucks her standing; plain penetration language.',
    },
    '⚡ Jump: dance → strip mid-song': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens dancing clothed; hard-cuts to topless or fully naked still dancing.',
        "choreography": 'SECTIONS 1–2: She dances clothed to the beat. HARD JUMP CUT: Same dance energy but top gone or fully naked (as intensity allows); no slow peel — the cut removes the clothes. Continue dance + optional talk.',
    },
    '⚡ Jump: sofa talk → reverse cowgirl': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens sitting talking on a sofa; hard-cuts to reverse cowgirl.',
        "choreography": 'SECTIONS 1–2: Both on a sofa talking, clothed. HARD JUMP CUT: She naked riding him reverse cowgirl facing camera, back to his chest, cock in pussy; continue ride + dirty talk.',
    },
    '⚡ Jump: mirror makeup → bent over sink': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens at mirror fixing hair/makeup; hard-cuts to bent over sink from behind.',
        "choreography": 'SECTIONS 1–2: She at a mirror, touches hair or face, may speak to the reflection/camera. HARD JUMP CUT: She bent over the sink naked, him fucking her from behind; face may catch in mirror; penetration continuous after cut.',
    },
    '⚡ Jump: car lean hello → backseat sex': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens leaning on a car saying hi; hard-cuts to backseat sex.',
        "choreography": 'SECTIONS 1–2: She leans on a car, greets, light pose. HARD JUMP CUT: Inside the car, seats reclined or backseat, explicit sex (missionary or her on top); restate cabin and naked contact.',
    },
    '⚡ Jump: interview smile → face sit': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens smiling/talking like an interview; hard-cuts to face sitting.',
        "choreography": 'SECTIONS 1–2: She faces camera, smiles, delivers 1–2 clean spoken lines. HARD JUMP CUT: She straddling his face, grinding on his mouth; he under her; skirt/panties aside or lower half bare as needed — full nude only if intent asks; explicit oral language.',
    },
    '⚡ Jump: hug → mating press': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens in a hug; hard-cuts to mating press.',
        "choreography": 'SECTIONS 1–2: Close clothed hug, small sway. HARD JUMP CUT: She on her back knees to chest, he folded over fucking deep missionary/mating press; name penetration.',
    },
    '⚡ Jump: wave to camera → solo fingers': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens waving hello; hard-cuts to solo masturbation.',
        "choreography": 'SECTIONS 1–2: She waves and says hello to camera, clothed. HARD JUMP CUT: She naked, fingers in her pussy or rubbing clit, legs open to camera; no strip sequence — cut does the change.',
    },
    '⚡ Jump: SFW argument → angry makeout fuck': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens arguing; hard-cuts to rough sex.',
        "choreography": 'SECTIONS 1–2: Heated argument, clothed, sharp spoken lines. HARD JUMP CUT: Clothes gone or shoved aside, him fucking her hard (wall or bed); keep angry/hungry dirty talk after the cut.',
    },
    '⚡ Jump: cook together → counter sex': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens cooking side by side; hard-cuts to sex on the counter.',
        "choreography": 'SECTIONS 1–2: Kitchen task, light talk, clothed. HARD JUMP CUT: She on the counter, him between her legs fucking her; pans/kitchen still in background; explicit after cut.',
    },
    '⚡ Jump: gym spot → locker oral': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens gym/spotter beat; hard-cuts to oral in locker room.',
        "choreography": 'SECTIONS 1–2: Gym motion or stretch, brief talk. HARD JUMP CUT: Locker bench, she kneeling blowing him or him eating her — keep gym clothes unless intent says stripped; restate location after cut.',
    },
    '⚡ Jump: texting on bed → him behind her': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens alone on bed on phone; hard-cuts to doggy/prone bone.',
        "choreography": 'SECTIONS 1–2: She on bed with phone, maybe one line. HARD JUMP CUT: Phone gone, him behind fucking her into the mattress; face in pillow optional; explicit rhythm after cut.',
    },
    '⚡ Jump: hello → kneel for Mistress': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens dressed greeting the view; hard-cuts to kneeling power-exchange (collar/order).',
        "choreography": (
            "SECTIONS 1–2 (setup): She faces the view/camera fully clothed as in the start image, "
            "short hello or soft command tease with emotion brackets — small motion only, no bondage yet. "
            "HARD JUMP CUT (mandatory): Instant cut. POWER FRAME: she is upright as Domme/Mistress "
            "(or he as Master if lead is male); the sub is on knees at the bottom of frame if POV male-sub "
            "or she is kneeling to the view if POV is the Domme looking down. "
            "WARDROBE: keep start-image clothes; ADD only one clear prop if the still allows "
            "(collar already on, cuff click, crop in hand) — do not invent a full dungeon. "
            "One hard order + one compliance beat after the cut. Explicit contact only if intent asks; "
            "otherwise posture + command is enough. Free mouths: honorifics (Ma'am/Mistress/Sir)."
        ),
    },
    '⚡ Jump: chat → collared restraint': {
        "tag": 'JUMP',
        "modes": ('i2v',),
        "setup": 'Opens talking clothed; hard-cuts to collar/cuffs + controlled pose.',
        "choreography": (
            "SECTIONS 1–2: Face-to-face or to-camera talk, clothed, light gesture — establish who is in charge in tone. "
            "HARD JUMP CUT: Instant cut. Sub is restrained (collar + leash taut, wrists cuffed, or rope already on) "
            "in a held pose (kneel, hands behind, back to wall). Dom stands or sits with control of the prop. "
            "ENTER-BEFORE-USE is already satisfied by the cut showing restraint on. "
            "Remaining sections: one correction, one breath, optional explicit service if intent asks "
            "(oral/hand) without stripping the whole outfit unless intent says naked."
        ),
    },

    # ── I2V-first helpers ──────────────────────────────────────────────
    '🖼 I2V: Honour pose — small motion only': {
        'tag': 'SFW',
        'modes': ('i2v',),
        'setup': 'Start image is law. Subject stays in the same basic pose.',
        'choreography': 'I2V ONLY: Do not walk them into a new set. First section restates exact pose/wardrobe from the frame.\nThen only small motions the still can support (breath, blink, weight shift, hand tighten, slight lean).\nIf dialogue is on, they talk without restaging. Never invent a second person not in the frame.',
    },
    '🖼 I2V: Look at view / camera from still': {
        'tag': 'SFW',
        'modes': ('i2v',),
        'setup': 'From the start pose, turn attention toward the view/camera if the body can.',
        'choreography': 'Honour the start image. If facing allows, rotate torso+head together toward the view.\nIf the still is face-down or back-to-camera, do NOT invent a face turn unless motion clearly starts it.\nOptional short greeting lines if dialogue is on.',
    },
    '🖼 I2V: Hands already on — tighten & continue': {
        'tag': 'NSFW',
        'modes': ('i2v',),
        'setup': 'Contact already visible in the still continues; no re-placement from nowhere.',
        'choreography': 'If hands/bodies are already touching in the image, they tighten, drag, or press — never re-enter as if new.\nBuild rhythm from existing contact. Explicit language only if the act is implied or intent asks.',
    },
    '🖼 I2V: Dialogue only — freeze body': {
        'tag': 'SFW',
        'modes': ('i2v',),
        'setup': 'Talking head / still body; motion is micro only.',
        'choreography': 'Body stays almost locked to the start image. Mouth, eyes, micro head+torso turns only.\nTalkative-friendly: many lines, almost no travel motion.',
    },
    '🖼 I2V: Animation still — keep the medium': {
        'tag': 'SFW',
        'modes': ('i2v',),
        'setup': 'Start frame is animation / anime / illustrated — style is mandatory.',
        'choreography': 'STYLE LOCK: This is animation (or the medium visible in the still). Every section must read as the same medium continuing from that exact frame — line weight, cel shading, paint style, or 3D toon look as shown.\nDo NOT collapse into live-action photoreal skin. Motion is animated motion: clear poses, readable arcs, no real-camera documentary feel.\nFirst section: restate the animated design (colours, outlines, costume shapes) from the still.',
    },

    # ── T2V deep shot recipes ─────────────────────────────────────────
    '🎬 Recipe: Talkative rain kiss (12s pair)': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Night rain under a bus-stop awning. Two people soaked, last bus almost gone.',
        'choreography': "SECTION PLAN (talkative pair, ~11s write target for a 12s clip):\n1) Establish: rain streaks, wet hair, coats, bus timetable glow; they face each other under the awning.\n2) Stake talk: one says the last bus is in minutes; the other says they don't care.\n3) Prop beat: grip wet lapel or umbrella handle; rain noise under the lines.\n4) Almost-kiss lean: torsos turn together, mouths close, one short line about missing the bus on purpose.\n5) Kiss: mouths meet, hands in wet hair/coat, rain still visible on shoulders.\n6) Break for air + one more stake line, then kiss again or forehead press.\nEvery spoken line names rain, bus, wet clothes, or the choice to stay. No empty flirt stock.",
        'stakes': 'Last bus leaving; choosing the kiss over the ride home.',
        'dialogue_shape': 'Short urgent lines, 6–10 total; brackets warm/breathless; prop+stake every line.',
        'cast_hint': 'pair',
        'motion': 'soft',
        'mouth_heat': 'normal',
        'duration_hint': 12,
        'dialogue_tier_hint': 'talkative',
    },
    '🎬 Recipe: Kitchen fight → kiss': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Small kitchen, argument mid-prep; marble or wood counter between them.',
        'choreography': '1) Argue over something concrete (burnt pan / late text / open door) — sharp lines, hands busy with utensil or glass.\n2) Volume rises; one plants a palm on the counter (no teleport slam).\n3) Space closes; backs hit the counter edge.\n4) Anger flips into a kiss; utensil forgotten.\n5) Hands grip waist/jaw; one angry-hungry line between kisses.\nKeep counter grain visible. Head+torso turn together on face-offs.',
        'stakes': 'The fight topic stays named until the kiss flips it.',
        'dialogue_shape': 'Confrontation first half; heated short lines after. No begging.',
        'cast_hint': 'pair',
        'motion': 'intense',
        'mouth_heat': 'intense',
        'duration_hint': 12,
        'dialogue_tier_hint': 'talkative',
    },
    '🎬 Recipe: Cafe leave now': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Daytime cafe booth; two cups; one person wants to leave for somewhere private.',
        'choreography': '1) Cups, window light. Low voices about a plan (hotel / car / upstairs).\n2) Phone or watch check; stake: shift ends / roommate / rain starting.\n3) Legs touch or fingers brush; line about not finishing the coffee.\n4) Stand, coats, door — last line: we should leave now.\nPublic-safe motion; heat lives in talk and the exit.',
        'stakes': 'Leave together before the window closes.',
        'dialogue_shape': 'Conspiratorial, specific, 5–8 lines; end on leave-now.',
        'cast_hint': 'pair',
        'motion': 'soft',
        'mouth_heat': 'normal',
        'duration_hint': 12,
        'dialogue_tier_hint': 'talkative',
    },
    '🎬 Recipe: Gym spotter flirt': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Gym floor, bench or squat rack; spotter + lifter.',
        'choreography': '1) Chalk, bar, breath. Spotter hands hover near the bar.\n2) Rep with effort sounds; spotter cues form.\n3) Rest sit; towel; flirt tied to the set.\n4) Optional closer: hand on shoulder, charged line about after.\nName equipment every other section.',
        'stakes': 'Finish the set; secondary stake = the after.',
        'dialogue_shape': 'Focused + playful; effort grunts between lines.',
        'cast_hint': 'pair',
        'motion': 'normal',
        'mouth_heat': 'soft',
        'duration_hint': 12,
        'dialogue_tier_hint': 'standard',
    },
    '🎬 Recipe: Phone breakup walk': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Night sidewalk; one person on a phone call ending a relationship.',
        'choreography': '1) Phone to ear, pacing; one-sided call we hear.\n2) Concrete terms: keys / dog / lease — not vague goodbye only.\n3) Stops under a light; jaw/eyes change.\n4) Ends call, lowers phone, one muttered line to empty air.\nSolo cast unless a second body is intentional.',
        'stakes': 'Breakup terms (keys, dog, lease).',
        'dialogue_shape': 'Phone-call register; 6+ lines; topic lock on terms.',
        'cast_hint': 'solo',
        'motion': 'soft',
        'mouth_heat': 'normal',
        'duration_hint': 15,
        'dialogue_tier_hint': 'talkative',
    },
    '🎬 Recipe: POV ♀ undress slow': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Bedroom/hotel; female-POV watching a partner undress for the view.',
        'choreography': 'POV CONTRACT: Eye-level female POV. Only VIEW / HANDS / SOUND / CONSEQUENCE.\n1) Open Eye-level female POV; partner wardrobe concrete.\n2) Partner undresses one garment at a time; view hands may help a button.\n3) Partner talks to the view — heat, hurry, or slow down.\n4) Clothes land; partner steps closer to bottom edge.\nNever invent the viewpoint body or face.',
        'stakes': 'Clothes off without rushing mechanism; charged talk.',
        'dialogue_shape': 'Partner speaks; no hands-speak.',
        'cast_hint': 'pair',
        'motion': 'soft',
        'mouth_heat': 'normal',
        'duration_hint': 12,
        'dialogue_tier_hint': 'standard',
        'pov_hint': 'female',
    },
    '🎬 Recipe: POV ♂ strip tease talk': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Male POV; partner strips while talking to the view.',
        'choreography': 'Eye-level male POV. Partner fills frame; viewpoint hands may grip at bottom edge.\nGarment removal is mechanism-only. Lines scene-tied (room, shirt, bed).\nBuild toward contact at bottom edge without viewpoint hips/face.',
        'stakes': 'Partner controls pace; talk leads the strip.',
        'dialogue_shape': 'Seductive + dirty-light; partner-only speech.',
        'cast_hint': 'pair',
        'motion': 'normal',
        'mouth_heat': 'intense',
        'duration_hint': 12,
        'dialogue_tier_hint': 'talkative',
        'pov_hint': 'male',
    },
    '🎬 Recipe: POV Mistress (domme view)': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Female-POV Domme / Mistress; submissive partner fills the lower frame.',
        'choreography': (
            'POV CONTRACT: Eye-level female POV — view is HER eyes/body as Domme. '
            'Only VIEW / HER HANDS / SOUND / CONSEQUENCE. Never invent her face or torso as an object.\n'
            '1) Open: sub already low (kneeling / sitting back on heels / hands bound lightly) at bottom edge; '
            'collar, cuffs, or leash optional but ENTERED if used.\n'
            '2) Domme hands enter from bottom/sides — chin lift, collar tug, crop tap, or place hands on shoulders.\n'
            '3) One clear order; sub complies (posture, eye line up into the view, short yes-Ma\'am).\n'
            '4) Escalate: praise/denial OR controlled contact (hand service / oral on the view at bottom edge) '
            'if heat is high — mouth-state law: busy mouth = sounds only.\n'
            'Power is continuous: she controls pace. Pair cast. Explicit OK when free mouths allow.'
        ),
        'stakes': 'Will the sub earn relief or stay denied — say it in-world.',
        'dialogue_shape': 'Domme: short commands + cool praise. Sub: brief honorific answers when free-mouth.',
        'cast_hint': 'pair',
        'motion': 'normal',
        'mouth_heat': 'intense',
        'duration_hint': 12,
        'dialogue_tier_hint': 'talkative',
        'pov_hint': 'female',
        'explicit': True,
    },
    '🎬 Recipe: POV Sub (looking up)': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Submissive POV looking up at a Domme/Mistress (or Master) who fills the frame.',
        'choreography': (
            'POV CONTRACT: Eye-level sub POV — view is the SUB\'s eyes from below. '
            'Domme/Master fills the upper/mid frame looking down. '
            'Only VIEW / SUB HANDS (if free) / SOUND / CONSEQUENCE. Never invent the viewpoint face.\n'
            '1) Open low angle: boots, hem, collar ring, gloved hand, or standing legs; chin tilts up.\n'
            '2) Domme speaks down into the view; issues one order; may rest a boot or hand near the bottom edge.\n'
            '3) Sub hands (if free) rise into frame to touch boot/thigh/leash — or stay cuffed behind (state once).\n'
            '4) Compliance beat + reaction (breath, shiver, short please/yes-Ma\'am). '
            'Optional service toward the Domme body if intent is explicit — still no viewpoint body invention.\n'
            'Who holds power is never ambiguous.'
        ),
        'stakes': 'Approval vs punishment — Domme names the price.',
        'dialogue_shape': 'Domme owns most lines; sub short free-mouth answers only.',
        'cast_hint': 'pair',
        'motion': 'soft',
        'mouth_heat': 'intense',
        'duration_hint': 12,
        'dialogue_tier_hint': 'talkative',
        'pov_hint': 'male',
        'explicit': True,
    },
    '🎬 Recipe: Collar check & kneel (third person)': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Third-person power exchange: Domme checks collar; sub kneels; short command chain.',
        'choreography': (
            '1) Establish room (dim practicals) + both bodies; Domme upright, sub standing or already low.\n'
            '2) Collar/cuffs ENTER then USE — finger under collar ring, clip leash, test fit.\n'
            '3) Order to kneel; sub drops; Domme circles once or adjusts posture with a hand.\n'
            '4) One reward or denial line; hold the kneel. Explicit only if intent pushes further.\n'
            'Not a full dungeon inventory — one restraint system, clear power.'
        ),
        'stakes': 'Stay kneeling until told otherwise.',
        'dialogue_shape': 'Commands + short compliance; honorifics.',
        'cast_hint': 'pair',
        'motion': 'normal',
        'mouth_heat': 'normal',
        'duration_hint': 12,
        'dialogue_tier_hint': 'standard',
        'explicit': True,
    },
    '🎬 Recipe: POV Master (male dom view)': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Male-POV Master/Dom; submissive partner fills the lower frame.',
        'choreography': (
            'POV CONTRACT: Eye-level male POV — view is HIS eyes as Dom/Master. '
            'Only VIEW / HIS HANDS / SOUND / CONSEQUENCE. Never invent his face or torso as an object.\n'
            '1) Sub already low (kneeling / sitting back on heels) at bottom edge; collar optional but ENTERED if used.\n'
            '2) Dom hands enter — chin lift, hair grip, collar tug, or place on shoulders.\n'
            '3) One clear order; sub complies (posture, eyes up into the view, short yes-Sir).\n'
            '4) Escalate: praise/denial OR controlled contact at bottom edge if heat is high — mouth-state law.\n'
            'He controls pace. Pair cast. Explicit OK when free mouths allow.'
        ),
        'stakes': 'Earn relief or stay denied — Dom names it.',
        'dialogue_shape': 'Dom short commands; sub brief honorific answers when free-mouth.',
        'cast_hint': 'pair',
        'motion': 'normal',
        'mouth_heat': 'intense',
        'duration_hint': 12,
        'dialogue_tier_hint': 'talkative',
        'pov_hint': 'male',
        'explicit': True,
    },
    '🎬 Recipe: POV ♀ Sub (looking up at Master)': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Female-POV sub looking up at a Master/Dom who fills the frame.',
        'choreography': (
            'POV CONTRACT: Eye-level female sub POV — view is HER eyes from below. '
            'Dom/Master fills upper frame looking down. Only VIEW / SUB HANDS (if free) / SOUND / CONSEQUENCE.\n'
            '1) Open low angle: boots, belt, hand, jaw — chin tilts up.\n'
            '2) Dom speaks down; one order; may rest a hand near bottom edge.\n'
            '3) Sub hands (if free) rise to touch boot/thigh — or stay bound (state once).\n'
            '4) Compliance + breath + short please/yes-Sir. Optional service if intent explicit.\n'
            'Power is never ambiguous.'
        ),
        'stakes': 'Approval vs correction — Dom sets the price.',
        'dialogue_shape': 'Dom owns most lines; sub short free-mouth answers.',
        'cast_hint': 'pair',
        'motion': 'soft',
        'mouth_heat': 'intense',
        'duration_hint': 12,
        'dialogue_tier_hint': 'talkative',
        'pov_hint': 'female',
        'explicit': True,
    },
    '🎬 Recipe: Solo window rain silent': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'One person at a rainy window; pure motion and breath.',
        'choreography': 'Silent: breath fog on glass, finger trace, weight shift, look out then down.\nNo spoken words. Sound = rain + breath. One prop (mug / phone dark).\n3–5 sections max.',
        'stakes': 'Waiting or deciding to leave — shown, not told.',
        'dialogue_shape': 'None — silent.',
        'cast_hint': 'solo',
        'motion': 'asmr',
        'mouth_heat': 'asmr',
        'duration_hint': 10,
        'dialogue_tier_hint': 'none',
    },
    '🎬 Recipe: Club pull-in dance': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Dark club, bass-heavy; two people find each other.',
        'choreography': '1) Crowd smear + lights; they spot each other.\n2) Pull-in: hand on waist, bodies sync to the beat.\n3) Mouths near ears — short lines over music (drink, exit, song energy).\n4) Grind/sway; optional kiss; leave toward hallway.\nHead+torso turn together in crowd turns.',
        'stakes': 'Leave together vs stay on the floor.',
        'dialogue_shape': 'Short loud lines; brackets over the music.',
        'cast_hint': 'pair',
        'motion': 'intense',
        'mouth_heat': 'normal',
        'duration_hint': 12,
        'dialogue_tier_hint': 'standard',
    },
    '🎬 Recipe: Hotel door pin (explicit)': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Hotel hallway → room; key card, door, wall pin.',
        'choreography': '1) Door opens; key card / Do Not Disturb as props.\n2) Back to door; kissing; jacket/shirt off one piece at a time.\n3) Explicit sex against door or bed edge — name anatomy once it starts.\n4) Dirty talk tied to the room (neighbors, checkout).\nNo teleport nudity — access clothing first.',
        'stakes': "Don't wake the hallway; checkout time.",
        'dialogue_shape': 'Intense dirty talk, room props, no loops.',
        'cast_hint': 'pair',
        'motion': 'aggressive',
        'mouth_heat': 'aggressive',
        'duration_hint': 15,
        'dialogue_tier_hint': 'talkative',
        'explicit': True,
    },
    '🎬 Recipe: Backseat night (explicit)': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Parked car at night; streetlight; cramped backseat.',
        'choreography': '1) Seat recline / climb — cramped mechanism matters.\n2) Clothes shoved aside (jeans to knees) — access before penetration.\n3) Explicit sex; windows fog as consequence.\n4) Lines about being seen, gear stick, cold leather.\nKeep cabin geometry honest.',
        'stakes': 'Someone could walk by; fogged glass; limited space.',
        'dialogue_shape': 'Whispered urgency + explicit; car props.',
        'cast_hint': 'pair',
        'motion': 'intense',
        'mouth_heat': 'intense',
        'duration_hint': 12,
        'dialogue_tier_hint': 'talkative',
        'explicit': True,
    },
    '🎬 Recipe: ASMR hair brush monologue': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Close vanity; brush hair / lotion; close-mic talk.',
        'choreography': 'ASMR: soft voice, long sibilants, brush strokes as prose sound.\nTalk about calm concrete things (brush, light, breathing).\nMotion stays small.',
        'stakes': 'Keep the listener calm / present.',
        'dialogue_shape': 'ASMR register; many soft lines; no degradation.',
        'cast_hint': 'solo',
        'motion': 'asmr',
        'mouth_heat': 'asmr',
        'duration_hint': 12,
        'dialogue_tier_hint': 'talkative',
    },
    '🎬 Recipe: Airport last call': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Airport gate; departure board; one person leaving.',
        'choreography': '1) Rolling bag, boarding pass, gate numbers spoken.\n2) Goodbye or solo rush — name flight time and city.\n3) Hug or almost-kiss under the board; last call PA as sound.\n4) Walk toward jet bridge; look-back torso+head together.\nSpecificity mandatory: gate, city, time.',
        'stakes': 'Miss the flight vs miss the person.',
        'dialogue_shape': 'Talkative stakes; flight facts in the lines.',
        'cast_hint': 'pair',
        'motion': 'normal',
        'mouth_heat': 'soft',
        'duration_hint': 12,
        'dialogue_tier_hint': 'talkative',
    },
    '🎬 Recipe: Garage bolt + wrench talk': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Residential garage; wrench; work light.',
        'choreography': 'Hands on real tools; dialogue about the stuck bolt, the part on order, the beer after.\nOptional light flirt prop-tied. Grease on fingers as continuity.',
        'stakes': 'Get the bolt free before dark.',
        'dialogue_shape': 'Casual + focused; tool names.',
        'cast_hint': 'pair',
        'motion': 'normal',
        'mouth_heat': 'soft',
        'duration_hint': 12,
        'dialogue_tier_hint': 'talkative',
    },
    '🎬 Recipe: Argument street then walk-off': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'City sidewalk; public argument.',
        'choreography': 'Sharp lines with a concrete grievance (message, friend, money).\nHands gesture; step in / step back; never head-only turns.\nEnds with walk-away + one last line down the sidewalk.',
        'stakes': 'Named grievance; separation unless intent flips it.',
        'dialogue_shape': 'Confrontation; no begging default.',
        'cast_hint': 'pair',
        'motion': 'intense',
        'mouth_heat': 'intense',
        'duration_hint': 12,
        'dialogue_tier_hint': 'talkative',
    },
    '🎬 Recipe: Undress button-by-button': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Close bedroom light; shirt or dress with many buttons.',
        'choreography': 'Each section opens one or two buttons — mechanism only.\nDialogue about heat, AC, the next button — never stock you-wish loops.\nIf explicit intent: after access, plain anatomy; else stop at open shirt.',
        'stakes': "Don't rush the buttons; the wait is the point.",
        'dialogue_shape': 'Soft-to-normal heat; unique lines; zero phrase loops.',
        'cast_hint': 'pair',
        'motion': 'soft',
        'mouth_heat': 'normal',
        'duration_hint': 15,
        'dialogue_tier_hint': 'talkative',
    },
    '🎬 Recipe: Group party kitchen spill': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'House party kitchen island; three+ people; drinks.',
        'choreography': 'GROUP: tag people by wardrobe (red dress / leather jacket / gold chain).\nSpill or toast; overlapping short lines; focus two bodies per section.\nStable identities — no face swaps.',
        'stakes': 'Who goes home with whom / who spilled on whom.',
        'dialogue_shape': 'Overlapping casual + playful; name people by tags.',
        'cast_hint': 'group',
        'motion': 'normal',
        'mouth_heat': 'normal',
        'duration_hint': 15,
        'dialogue_tier_hint': 'talkative',
    },
    '🎬 Recipe: Shower steam pair': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Steam shower; tile; two bodies; continuous water.',
        'choreography': 'Water runs; soap; faces in steam. Soft-to-intense contact against tile.\nIf explicit: name wet contact honestly; water continuity.\nShort lines that could echo off tile.',
        'stakes': 'Hot water running out; bathroom privacy.',
        'dialogue_shape': 'Close soft or intense; few words, lots of breath.',
        'cast_hint': 'pair',
        'motion': 'soft',
        'mouth_heat': 'normal',
        'duration_hint': 12,
        'dialogue_tier_hint': 'standard',
    },
    '🎬 Recipe: Office after-hours': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Empty office at night; monitor glow; desk lamp.',
        'choreography': "Two coworkers who shouldn't; talk about email / deadline / elevator cameras.\nDesk edge pin or chair; clothes access only if intent explicit.\nProps: badge lanyard, cold coffee, spreadsheet light.",
        'stakes': 'Getting caught; morning meeting.',
        'dialogue_shape': 'Conspiratorial whisper + workplace props.',
        'cast_hint': 'pair',
        'motion': 'normal',
        'mouth_heat': 'normal',
        'duration_hint': 12,
        'dialogue_tier_hint': 'talkative',
    },
    '🎬 Recipe: Elevator stuck talk': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Elevator car; panel buttons; stuck between floors.',
        'choreography': '1) Jolt stop; panel; alarm or intercom.\n2) Talk fills the wait: floors, jobs, carpet smell.\n3) Close bodies, polite then less polite.\n4) Optional almost-kiss when lights flicker; doors may crack open.\nName buttons, floor numbers, alarm.',
        'stakes': 'Time trapped; how intimate before rescue.',
        'dialogue_shape': 'Talkative prop-rich goldmine.',
        'cast_hint': 'pair',
        'motion': 'soft',
        'mouth_heat': 'soft',
        'duration_hint': 15,
        'dialogue_tier_hint': 'talkative',
    },
    '🎬 Recipe: Aggressive wall pin fuck': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Hall or bedroom wall; clothes yanked for access; hard pace.',
        'choreography': 'Aggressive body intensity: pin, lift leg, access zipper/skirt, plain penetration every section.\nMouth heat aggressive: short filthy lines, varied insults, no phrase loops.\nWall texture and doorframe as props.',
        'stakes': 'Hard and fast before someone comes home.',
        'dialogue_shape': 'Filthy, short, varied; wall/door props.',
        'cast_hint': 'pair',
        'motion': 'aggressive',
        'mouth_heat': 'aggressive',
        'duration_hint': 12,
        'dialogue_tier_hint': 'talkative',
        'explicit': True,
    },
    '🎬 Recipe: Soft morning bed talk': {
        'tag': 'RECIPE',
        'modes': ('t2v',),
        'setup': 'Morning bed; sheets; window light; no rush.',
        'choreography': 'Soft bodies under sheets; small motions; coffee smell or phone face-down as prop.\nTalk about the day ahead, last night, staying ten more minutes.\nNo aggressive sex unless intent flips — this is soft intimacy.',
        'stakes': 'Get up for work vs stay.',
        'dialogue_shape': 'Soft intimate + casual; many gentle lines.',
        'cast_hint': 'pair',
        'motion': 'soft',
        'mouth_heat': 'soft',
        'duration_hint': 12,
        'dialogue_tier_hint': 'talkative',
    },
}


SCENARIO_KEYS = list(SCENARIO_PRESETS.keys())

_SENTINELS = {"None — user's prompt decides", "🎲 Random — seed picks"}


def _is_playable(val):
    n = normalize_scenario(val)
    return isinstance(n, dict)


_SCENARIO_RANDOM_POOL = [
    k for k, v in SCENARIO_PRESETS.items() if _is_playable(v)
]


def keys_for_mode(mode: str = "i2v") -> list:
    """UI list: sentinels + scenarios allowed for this video mode.

    I2V: JUMP cuts ONLY. Honour-pose / freeze / dual-mode helpers fight the
    start frame unless the still is perfect — they stay in the bank for T2V
    dual-mode if tagged, but are hidden from the I2V dropdown.
    T2V: shot recipes first, then rest, then JUMP (if any dual-mode).
    """
    m = (mode or "i2v").lower().strip()
    if m not in ("i2v", "t2v"):
        m = "i2v"
    out = ["None — user's prompt decides", "🎲 Random — seed picks"]
    recipes, jumps, rest = [], [], []
    for k, v in SCENARIO_PRESETS.items():
        if k in _SENTINELS:
            continue
        n = normalize_scenario(v)
        if not isinstance(n, dict):
            continue
        if m not in n.get("modes", ("i2v", "t2v")):
            continue
        tag = n.get("tag", "")
        if tag == "RECIPE":
            recipes.append(k)
        elif tag == "JUMP":
            jumps.append(k)
        else:
            rest.append(k)
    if m == "t2v":
        out.extend(recipes)
        out.extend(rest)
        out.extend(jumps)
    else:
        # I2V dropdown: JUMP only
        out.extend(jumps)
    return out


def scenario_tag(key):
    v = normalize_scenario(SCENARIO_PRESETS.get(key))
    return v.get("tag", "") if isinstance(v, dict) else ""


def scenario_modes(key):
    v = normalize_scenario(SCENARIO_PRESETS.get(key))
    return list(v.get("modes", ())) if isinstance(v, dict) else []


def scenario_is_explicit(key, seed=0, mode=None):
    v = resolve_scenario(key, seed=seed, mode=mode)
    if not v:
        return False
    if v.get("explicit") is True:
        return True
    return v.get("tag") in ("NSFW", "JUMP")


def _seed_rng(seed=0):
    import random
    try:
        s = int(seed) & 0x7FFFFFFF
    except (TypeError, ValueError):
        s = 0
    return random.Random(s)


def resolve_scenario_key(key, seed=0, mode=None) -> str:
    """Return concrete scenario key (RANDOM → picked for mode)."""
    k = (key or "").strip()
    if not k:
        return k
    v = SCENARIO_PRESETS.get(k)
    if v == "RANDOM" or k in ("🎲 Random — seed picks", "RANDOM"):
        pool = list(_SCENARIO_RANDOM_POOL)
        if mode:
            m = (mode or "").lower()
            filtered = []
            for pk in pool:
                n = normalize_scenario(SCENARIO_PRESETS.get(pk))
                if not isinstance(n, dict) or m not in n.get("modes", ()):
                    continue
                if m == "i2v" and n.get("tag") != "JUMP":
                    continue
                filtered.append(pk)
            pool = filtered or pool
        if not pool:
            return k
        return _seed_rng(seed).choice(pool)
    return k


def resolve_scenario(key, seed=0, mode=None):
    """Return normalized dict or None. RANDOM respects mode filter when given."""
    concrete = resolve_scenario_key(key, seed=seed, mode=mode)
    v = SCENARIO_PRESETS.get(concrete) if concrete else None
    if v == "RANDOM":
        return None
    n = normalize_scenario(v)
    return n if isinstance(n, dict) else None


def resolve_scenario_tuple(key, seed=0, mode=None):
    """Back-compat: (tag, setup, choreography) or None."""
    d = resolve_scenario(key, seed=seed, mode=mode)
    if not d:
        return None
    return (d.get("tag") or "SFW", d.get("setup") or "", d.get("choreography") or "")


def build_scenario_block(key, seed=0, mode=None):
    d = resolve_scenario(key, seed=seed, mode=mode)
    if not d:
        return ""
    tag = d.get("tag") or "SFW"
    block = (
        "━━ SCENARIO — THIS IS THE ACTION (mandatory) ━━\n"
        f"Setup: {d.get('setup', '')}\n"
        f"Choreography: {d.get('choreography', '')}\n"
    )
    if tag == "RECIPE":
        if d.get("stakes"):
            block += f"Stakes: {d['stakes']}\n"
        if d.get("dialogue_shape"):
            block += f"Dialogue shape: {d['dialogue_shape']}\n"
        if d.get("cast_hint"):
            block += f"Cast hint: {d['cast_hint']} (honour node cast if set).\n"
        block += (
            "This is a SHOT RECIPE — follow the section plan and stakes. "
            "User intent still outranks wardrobe/identity fluff.\n"
        )
    if tag == "JUMP":
        block += (
            "JUMP CUT RULES: First sections = setup only. Then a HARD CUT section that "
            "restates the NEW pose/act in plain mechanism language. Do not slowly "
            "undress into the second half unless choreography says so — the cut is the transition. "
            "WARDROBE: oral/blowjob keeps clothes unless intent asks nude; penetrative sex may leap "
            "to naked/access; strip/solo cuts may change wardrobe. After the cut, stay in the new reality.\n"
        )
    if tag in ("NSFW", "JUMP") or d.get("explicit"):
        block += (
            "EXPLICIT: after any cut (or from the start for pure NSFW), name anatomy and "
            "contact plainly where the act requires it.\n"
        )
    return block


def get_scenario_data(key):
    d = normalize_scenario(SCENARIO_PRESETS.get(key))
    if not isinstance(d, dict):
        return None
    return {
        "tag": d.get("tag"),
        "setup": d.get("setup", ""),
        "choreography": d.get("choreography", ""),
        "modes": list(d.get("modes") or []),
        "stakes": d.get("stakes", ""),
        "dialogue_shape": d.get("dialogue_shape", ""),
        "cast_hint": d.get("cast_hint", ""),
        "motion": d.get("motion", ""),
        "mouth_heat": d.get("mouth_heat", ""),
        "duration_hint": d.get("duration_hint"),
        "dialogue_tier_hint": d.get("dialogue_tier_hint", ""),
        "pov_hint": d.get("pov_hint", ""),
        "explicit": bool(d.get("explicit")),
    }


def recipe_ui_hints(key, seed=0, mode=None) -> dict:
    d = resolve_scenario(key, seed=seed, mode=mode)
    if not d or d.get("tag") != "RECIPE":
        return {}
    hints = {}
    for field in (
        "cast_hint", "motion", "mouth_heat", "duration_hint",
        "dialogue_tier_hint", "pov_hint",
    ):
        if d.get(field) not in (None, ""):
            hints[field] = d[field]
    if d.get("explicit"):
        hints["explicit"] = True
    return hints


SCENARIO_SFW = [
    k for k, v in SCENARIO_PRESETS.items()
    if isinstance(normalize_scenario(v), dict) and normalize_scenario(v).get("tag") == "SFW"
]
SCENARIO_NSFW = [
    k for k, v in SCENARIO_PRESETS.items()
    if isinstance(normalize_scenario(v), dict) and normalize_scenario(v).get("tag") in ("NSFW", "JUMP")
]
SCENARIO_JUMP = [
    k for k, v in SCENARIO_PRESETS.items()
    if isinstance(normalize_scenario(v), dict) and normalize_scenario(v).get("tag") == "JUMP"
]
SCENARIO_RECIPES = [
    k for k, v in SCENARIO_PRESETS.items()
    if isinstance(normalize_scenario(v), dict) and normalize_scenario(v).get("tag") == "RECIPE"
]
SCENARIO_I2V_KEYS = keys_for_mode("i2v")
SCENARIO_T2V_KEYS = keys_for_mode("t2v")


def _python_string_literal(text: str) -> str:
    escaped = (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )
    return f'"{escaped}"'


def update_scenario_in_source(key: str, new_setup: str, new_choreography: str) -> bool:
    """Best-effort edit of setup/choreography strings for the UI save button."""
    filepath = os.path.abspath(__file__)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    setup_lit = _python_string_literal(new_setup)
    choreo_lit = _python_string_literal(new_choreography)

    # Find dict block for this key
    m = re.search(rf'("{re.escape(key)}")\s*:\s*\{{', content)
    if not m:
        return False
    start = m.end()
    depth = 1
    i = start
    while i < len(content) and depth:
        ch = content[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        i += 1
    block = content[start : i - 1]

    def repl_field(block_text, field, lit):
        pat = rf'("{field}"\s*:\s*)("(?:[^"\\]|\\.)*")'
        new_b, n = re.subn(pat, rf"\1{lit}", block_text, count=1)
        return new_b, n

    block2, c1 = repl_field(block, "setup", setup_lit)
    block3, c2 = repl_field(block2, "choreography", choreo_lit)
    if c1 == 0 and c2 == 0:
        return False
    new_content = content[:start] + block3 + content[i - 1 :]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    mod = sys.modules[__name__]
    importlib.reload(mod)
    global SCENARIO_PRESETS
    SCENARIO_PRESETS = mod.SCENARIO_PRESETS
    return True


if __name__ == "__main__":
    print("total playable:", len(_SCENARIO_RANDOM_POOL))
    print(
        "SFW:", len(SCENARIO_SFW),
        "| NSFW+JUMP:", len(SCENARIO_NSFW),
        "| JUMP:", len(SCENARIO_JUMP),
        "| RECIPES:", len(SCENARIO_RECIPES),
    )
    print("I2V keys:", len(SCENARIO_I2V_KEYS), "T2V keys:", len(SCENARIO_T2V_KEYS))
