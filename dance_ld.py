# -*- coding: utf-8 -*-
"""
dance_ld.py — Dance + tease motion doctrine for PromptForge LD

Activation (NO BLOAT):
  • Only injects when intent/scenario has clear DANCE or TEASE cues.
  • "dirty" alone does NOT activate dirty dance — needs "dirty dance" / "filthy dance" etc.
  • Music preset alone does NOT force dance — music only *colours* tempo when dance is already on.
  • Seed picks which sub-path tips to emphasize when several match (stable variety).

Outputs a compact system block: active dance paths + tease gestures + music tempo hint.
"""
from __future__ import annotations

import random
import re
from typing import Iterable

# ─────────────────────────────────────────────────────────────────────────────
#  ACTIVATION
# ─────────────────────────────────────────────────────────────────────────────

# Strong dance phrases / stems (substring match on lowercased blob)
_DANCE_CUES = (
    "dance", "dances", "dancing", "danced", "dancer",
    "twerk", "twerking", "twerks",
    "grind", "grinding", "grinds",  # hip grind / lap — dance context
    "vogue", "voguing",
    "shimmy", "shimmies",
    "body roll", "body-roll", "bodyroll",
    "hip roll", "hip-roll", "hiproll", "hip rolls",
    "chest pop", "booty pop", "pop and lock", "pop-lock",
    "slow dance", "slow-dance", "sway with", "swaying together",
    "lap dance", "lapdance", "private dance",
    "chair dance", "pole dance", "poledance", "pole work",
    "sexy dance", "erotic dance", "sensual dance", "striptease dance",
    "dirty dance", "filthy dance", "nasty dance", "freak dance",
    "fast dance", "club dance", "rave dance", "dancefloor", "dance floor",
    "dance for me", "dance for the", "dances for",
    "wiggle", "wiggles", "gyrate", "gyrates", "gyrating",
    "wind her hips", "wind his hips", "winds her hips", "wine her",  # wine = caribbean wind
    "whine her", "whining dance",
    "step-touch", "step touch", "two-step", "two step",
    "choreograph", "choreo",
    "groove her", "groove his", "to the beat", "on the beat",
    "music video dance", "mv dance",
)

# Tease / flirt motion (body display — not dirty-talk register alone)
_TEASE_CUES = (
    "tease", "teases", "teasing", "teased",
    "flirtatious", "flirty gesture", "flirty move", "flirty movement",
    "shows off", "showing off", "show off her", "show off his",
    "plays with her hair", "play with her hair", "twirls her hair",
    "bites her lip", "bite her lip", "licks her lips",
    "blows a kiss", "blow a kiss", "winks", "wink at",
    "looks over her shoulder", "look over shoulder tease",
    "runs hands over", "runs her hands", "caresses her own",
    "squeezes her breasts", "squeeze her tits", "squeezes her tits",
    "teases her tits", "tease her tits", "teases her breasts",
    "teases her ass", "tease her ass", "slaps her ass", "spanks herself",
    "cups her breasts", "cup her breasts", "pushes her breasts",
    "cleavage tease", "ass tease", "hip tease",
    "arches for the camera", "poses for", "model walk", "catwalk",
    "slow strip tease", "strip tease motion",  # motion tease; garment law still owns clothing chain
    # explicit body teases (keyword only — not bloat)
    "pussy tease", "teases her pussy", "tease her pussy", "spreads her pussy",
    "spread her pussy", "spreads her lips", "opens her pussy", "parts her lips",
    "fingers her", "rubs her pussy", "rubs her clit", "circles her clit",
    "licks her fingers", "sucks her fingers", "tastes herself",
    "shows her pussy", "presents her pussy", "pussy flash",
    "spreads her ass", "spreads her cheeks", "opens her ass",
    "touches herself", "plays with herself", "masturbat",
    "squirts", "edge herself", "humps the", "humps her hand",
    "nipple play", "pinches her nipples", "twists her nipples",
    "spit on her", "spits on her chest", "oil on her",
)

# Explicit dirty-dance phrases only (NOT bare "dirty" / "filthy talk")
_DIRTY_DANCE_PHRASES = (
    "dirty dance", "dirty dancing", "dances dirty", "dance dirty",
    "filthy dance", "nasty dance", "freak dance", "freaky dance",
    "slutty dance", "whore dance", "obscene dance",
    "grind dirty", "dirty grind", "floor grind",
)


def _blob(intent: str = "", scenario: str = "") -> str:
    return f"{intent or ''} {scenario or ''}".lower()


def wants_dance(intent: str = "", scenario: str = "") -> bool:
    b = _blob(intent, scenario)
    if not b.strip():
        return False
    return any(c in b for c in _DANCE_CUES)


def wants_tease_motion(intent: str = "", scenario: str = "") -> bool:
    b = _blob(intent, scenario)
    if not b.strip():
        return False
    return any(c in b for c in _TEASE_CUES)


def wants_dirty_dance(intent: str = "", scenario: str = "") -> bool:
    """True only for dirty-dance phrases — never bare 'dirty' or 'dirty talk'."""
    b = _blob(intent, scenario)
    return any(p in b for p in _DIRTY_DANCE_PHRASES)


def is_active(intent: str = "", scenario: str = "") -> bool:
    return wants_dance(intent, scenario) or wants_tease_motion(intent, scenario)


# ─────────────────────────────────────────────────────────────────────────────
#  DANCE PATHS — mechanism doctrine (no vibe paint)
# ─────────────────────────────────────────────────────────────────────────────

DANCE_PATHS: dict[str, dict] = {
    "slow_dance": {
        "name": "Slow dance / sway",
        "triggers": (
            "slow dance", "slow-dance", "sway together", "swaying together",
            "dance slow", "slow swaying", "close sway", "cheek to cheek",
        ),
        "doctrine": (
            "SLOW DANCE / SWAY: weight shifts side to side on a slow count; feet small or planted; "
            "hips rock gently; upper body and head stay as one unit on any turn toward partner/view. "
            "If pair: hands on waist/shoulder/back — contact named, no teleport grip. "
            "One clear sway or step per section; long holds OK. Not grinding unless intent says grind."
        ),
    },
    "sexy_standing": {
        "name": "Sexy standing dance",
        "triggers": (
            "sexy dance", "sensual dance", "erotic dance", "seductive dance",
            "dances sexy", "sexy dancing", "body dance", "sultry dance",
        ),
        "doctrine": (
            "SEXY STANDING DANCE: hip rolls (one direction per section), body rolls chest→hips, "
            "weight on one leg then the other, hands trail flanks/thighs/hair. "
            "Eye-line to view then away. Slow enough to read; no snap spins. "
            "Each section = one readable move (roll OR step OR hand path), not five stacked."
        ),
    },
    "dirty_dance": {
        "name": "Dirty / freak dance",
        "triggers": _DIRTY_DANCE_PHRASES,
        "doctrine": (
            "DIRTY DANCE (only when phrase matches — not bare 'dirty talk'): "
            "deeper hip circles, ass push toward view/partner, floor-level drops if space allows, "
            "hands on own body or partner with clear contact path. "
            "Still mechanism-first: name hip direction, knee bend, hand placement. "
            "Not full sex unless intent also asks undress/penetration."
        ),
    },
    "fast_club": {
        "name": "Fast club / rave",
        "triggers": (
            "fast dance", "club dance", "rave", "dancefloor", "dance floor",
            "jumps to the beat", "jumping on beat", "bounce dance", "hype dance",
            "energetic dance", "wild dance",
        ),
        "doctrine": (
            "FAST CLUB / RAVE: shorter sections; bounce in the knees; hip hits on downbeats; "
            "shoulder pops; hair swings with torso (not neck alone). "
            "Sharp but render-safe — 'turns fast', never snaps/whips. "
            "Freeze half a beat on drops if music implies a drop."
        ),
    },
    "hip_roll": {
        "name": "Hip roll focus",
        "triggers": (
            "hip roll", "hip-roll", "hiproll", "hip rolls", "rolls her hips",
            "rolls his hips", "rolling her hips", "circles her hips", "hip circle",
        ),
        "doctrine": (
            "HIP ROLL: isolate pelvis — circle clockwise or counter once per section; "
            "ribs quieter; knees soft; feet planted or one heel lifts. "
            "State direction and complete the circle before the next move."
        ),
    },
    "body_roll": {
        "name": "Body roll",
        "triggers": (
            "body roll", "body-roll", "bodyroll", "body rolls",
            "rolls her body", "wave through her body", "body wave",
        ),
        "doctrine": (
            "BODY ROLL: sequential wave — chest initiates, travels through ribs to hips "
            "(or reverse if intent says). One full travel per section; head follows torso as a unit."
        ),
    },
    "twerk": {
        "name": "Twerk / booty pop",
        "triggers": (
            "twerk", "twerking", "twerks", "booty pop", "ass bounce",
            "bounces her ass", "pop her ass",
        ),
        "doctrine": (
            "TWERK / BOOTY POP: hinge at hips, knees bent, weight in heels or balls of feet; "
            "glutes bounce or pop in short pulses; hands on floor/knees/thighs for support if low. "
            "Facing away or ¾ back common — reorient with torso+head together if she looks back."
        ),
    },
    "grind": {
        "name": "Grind (standing / against surface)",
        "triggers": (
            "grind", "grinding", "grinds", "grinds on", "grind on",
            "grinds against", "rubs against while dancing",
        ),
        "doctrine": (
            "GRIND: hips press and drag against partner, chair, wall, or view-direction; "
            "name contact surface; slow circular or front-back drag; feet small steps. "
            "Not penetration unless intent says so — this is dance contact."
        ),
    },
    "chair_dance": {
        "name": "Chair dance / seated",
        "triggers": (
            "chair dance", "dances in a chair", "dance in a chair", "seated dance",
            "sitting dance", "on the chair dance", "straddles the chair",
            "dances while sitting", "sexy dance while sitting",
        ),
        "doctrine": (
            "CHAIR DANCE: stay seated or return to seat; grind hips into the seat cushion; "
            "roll pelvis; open/close knees; hands on backrest or thighs; lean torso back then up "
            "as one unit with head. Optional: stand briefly then sit again — restate seat contact. "
            "Chair is a prop — name wood/metal/leather and contact points."
        ),
    },
    "lap_dance": {
        "name": "Lap dance",
        "triggers": (
            "lap dance", "lapdance", "private dance", "dances on his lap",
            "on your lap", "straddles his lap", "straddles your lap",
        ),
        "doctrine": (
            "LAP DANCE: she approaches → stands over / straddles lap → weight on thighs not full sit "
            "unless intent says sit; hip rolls toward partner/view; hair may fall forward with torso; "
            "hands on shoulders/chest/back of chair. Partner contact named. POV: viewpoint is lap/view."
        ),
    },
    "pole": {
        "name": "Pole / vertical prop",
        "triggers": (
            "pole dance", "poledance", "pole work", "on the pole", "spins on the pole",
            "holds the pole", "pole spin",
        ),
        "doctrine": (
            "POLE / VERTICAL PROP: hands grip pole; walk around base; hip to pole; "
            "optional climb or spin only if sections give travel time (not teleport top of pole). "
            "One grip change or orbit per section."
        ),
    },
    "floorwork": {
        "name": "Floorwork",
        "triggers": (
            "floorwork", "floor work", "on the floor dance", "dances on the floor",
            "crawls while dancing", "floor grind", "cat crawl dance",
        ),
        "doctrine": (
            "FLOORWORK: kneel or all-fours or hip-down; crawl with knee-hand sequence; "
            "hip roll on floor; arch back with torso+head unit; stand only via plant-hands rise chain."
        ),
    },
    "partner_lead": {
        "name": "Partner lead / follow",
        "triggers": (
            "leads her in a dance", "leads him in a dance", "partner dance",
            "ballroom", "spins her", "dips her", "dip her", "twirl",
        ),
        "doctrine": (
            "PARTNER LEAD/FOLLOW: leader's hand path first; follower turns at waist with torso+head; "
            "dip = support under back + controlled lean (no snap). Re-establish facing after spin."
        ),
    },
    "shuffle_step": {
        "name": "Steps / shuffle / two-step",
        "triggers": (
            "two-step", "two step", "step-touch", "step touch", "shuffle",
            "footwork", "steps to the music", "dance steps",
        ),
        "doctrine": (
            "STEPS / SHUFFLE: feet do the work — step-touch, weight change, small travel; "
            "hips optional follow; arms counterbalance. One pattern per section."
        ),
    },
    "hair_whip_safe": {
        "name": "Hair swing (safe)",
        "triggers": (
            "hair whip", "hair flip", "flips her hair", "hair swings",
            "throws her hair", "hair dance",
        ),
        "doctrine": (
            "HAIR SWING: hair follows TORSO turn or head+torso unit — never neck-only whip. "
            "Bend knees, rotate upper body, hair arcs after. 'Turns fast' not snaps."
        ),
    },
    "wall_dance": {
        "name": "Wall / door dance",
        "triggers": (
            "against the wall dance", "wall dance", "dances against the wall",
            "back to the wall dance", "grinds the wall",
        ),
        "doctrine": (
            "WALL DANCE: back or side to wall; shoulder blades or ass contact wall; "
            "hip roll with contact; hands on wall optional; slide down wall only with controlled bend."
        ),
    },
    "mirror_dance": {
        "name": "Mirror performance",
        "triggers": (
            "dances in the mirror", "mirror dance", "watches herself dance",
            "performs for the mirror",
        ),
        "doctrine": (
            "MIRROR DANCE: eye-line to reflection then view; same sexy/standing rules; "
            "optional hand on glass after approach — glass contact named."
        ),
    },
    "bed_dance": {
        "name": "Bed / couch dance",
        "triggers": (
            "dances on the bed", "on the bed dance", "couch dance",
            "dances on the couch", "kneels on the bed and dances",
        ),
        "doctrine": (
            "BED/COUCH DANCE: knees or feet on soft surface; bounce sinks into mattress; "
            "hip roll on knees; hands on sheets for balance. Rise from kneel uses torso+head unit."
        ),
    },
    "table_dance": {
        "name": "Table / counter edge",
        "triggers": (
            "dances on the table", "table dance", "on the bar dance",
            "dances on the counter",
        ),
        "doctrine": (
            "TABLE/BAR: feet plant carefully; small steps; hip focus; hands free or on hips; "
            "no wild leaps off edge unless intent says jump down (then land section)."
        ),
    },
    "car_dance": {
        "name": "Car / seat dance",
        "triggers": (
            "dances in the car", "car dance", "in the passenger seat dance",
            "grinds in the seat",
        ),
        "doctrine": (
            "CAR SEAT DANCE: seated grind; limited headroom — small hip rolls; "
            "hands on dash/seat/door; torso lean within cabin. Door open optional only if intent."
        ),
    },
    "shower_dance": {
        "name": "Shower / wet dance",
        "triggers": (
            "dances in the shower", "shower dance", "wet dance",
            "dances under the water",
        ),
        "doctrine": (
            "SHOWER DANCE: wet skin; feet careful on tile; hip sway under spray; "
            "hands on wall/tile; hair heavy when wet — moves with torso. Towel only if intent."
        ),
    },
    "strip_dance": {
        "name": "Dance while stripping",
        "triggers": (
            "striptease dance", "dances while stripping", "strip dance",
            "dances and undresses", "undresses while dancing",
        ),
        "doctrine": (
            "STRIP + DANCE: dance moves BETWEEN garment steps — never interleave two garments. "
            "Example: hip roll → bra path complete → hip roll → panties path. "
            "Garment law still owns clothing chains; dance fills the in-between sections."
        ),
    },
    "mv_performance": {
        "name": "Music-video performance",
        "triggers": (
            "music video dance", "mv dance", "performance dance",
            "dances for the camera", "camera dance", "video girl dance",
        ),
        "doctrine": (
            "MV PERFORMANCE: pose hits held a beat; walk-to-mark; hip/shoulder accents; "
            "eye contact with view on hooks. Camera may hunt angles (gravure-style reframes OK)."
        ),
    },
    "ballet_ish": {
        "name": "Ballet / contemporary light",
        "triggers": (
            "ballet", "contemporary dance", "arabesque", "pirouette",
            "dance lyrical", "modern dance",
        ),
        "doctrine": (
            "BALLET/CONTEMPORARY: long lines; controlled extensions; turns need prep step; "
            "no snap pirouettes — show wind-up and finish facing. Arms second/first positions optional."
        ),
    },
    "hiphop_groove": {
        "name": "Hip-hop groove",
        "triggers": (
            "hip hop dance", "hip-hop dance", "hiphop dance", "rap dance",
            "bounce to the beat", "808 dance",
        ),
        "doctrine": (
            "HIP-HOP GROOVE: bounce in knees; chest pop on kicks; isolations; "
            "loose arms; attitude in eye-line. Pocket > speed."
        ),
    },
    "latin_hip": {
        "name": "Latin hip action",
        "triggers": (
            "salsa", "bachata", "reggaeton dance", "latin dance",
            "merengue", "samba hip",
        ),
        "doctrine": (
            "LATIN HIP: figure-8 hips; rib cage counters; partner frame if pair; "
            "small syncopated steps. One hip figure per section."
        ),
    },
    "kpop_sharp": {
        "name": "K-pop / sharp idol",
        "triggers": (
            "k-pop dance", "kpop dance", "idol dance", "sharp choreography",
            "point choreography",
        ),
        "doctrine": (
            "IDOL/K-POP SHARP: clean hits; points; formations if group; smile/eye sharp; "
            "transitions between poses readable. No mushy continuous roll unless intent says wave."
        ),
    },
    "belly_isolations": {
        "name": "Belly / isolation",
        "triggers": (
            "belly dance", "bellydance", "isolation dance", "ribcage isolation",
            "snake arms",
        ),
        "doctrine": (
            "BELLY/ISOLATION: ribcage slides; hip drops; snake arms optional; "
            "feet quiet. Name which isolation (ribs vs hips) each section."
        ),
    },
    "burlesque": {
        "name": "Burlesque tease-dance",
        "triggers": (
            "burlesque", "burlesque dance", "fan dance", "glove peel dance",
        ),
        "doctrine": (
            "BURLESQUE: performative walk; glove/prop peel with dance pauses; "
            "hip bump; wink optional. Clothing removes still follow garment law."
        ),
    },
    "go_go": {
        "name": "Go-go platform",
        "triggers": (
            "go-go", "gogo dance", "go go dance", "platform dance",
            "cage dance",
        ),
        "doctrine": (
            "GO-GO: continuous energy; high knees optional; hair and hips; "
            "hold platform edge if elevated. Fast but section-readable."
        ),
    },
    "waltz_box": {
        "name": "Waltz / box step",
        "triggers": ("waltz", "box step", "three four dance", "3/4 dance"),
        "doctrine": (
            "WALTZ/BOX: 1-2-3 weight changes; rise and fall mild; partner frame; "
            "turns prepared. Slow and even."
        ),
    },
    "tango": {
        "name": "Tango / close frame",
        "triggers": ("tango", "tango dance", "close embrace dance"),
        "doctrine": (
            "TANGO: close chest contact if pair; sharp weight changes; pause (cortina energy); "
            "leg hooks only with clear plant. Head with torso on ochos."
        ),
    },
    "swing_lindy": {
        "name": "Swing / lindy",
        "triggers": ("swing dance", "lindy", "jitterbug", "east coast swing"),
        "doctrine": (
            "SWING: bounce in the knees; rock-step; underarm turns prepared; "
            "playful hands. Fast but not snap."
        ),
    },
    "line_dance": {
        "name": "Line dance / group sync",
        "triggers": ("line dance", "line dancing", "group choreography", "synced dance"),
        "doctrine": (
            "LINE/GROUP: same foot pattern named; facing wall/view; "
            "if solo doing line pattern still name left/right steps."
        ),
    },
    "krump_hard": {
        "name": "Krump / hard hits",
        "triggers": ("krump", "krumping", "hard hitting dance", "aggressive freestyle dance"),
        "doctrine": (
            "KRUMP/HARD: chest pops; stomps; arm swings with torso; "
            "still no banned contort verbs — sharp ≠ snap neck."
        ),
    },
    "waacking": {
        "name": "Waacking / arms",
        "triggers": ("waacking", "waack", "arm dance", "punking"),
        "doctrine": (
            "WAACKING: big arm arcs; poses on hits; hip secondary; "
            "face performance. One arm phrase per section."
        ),
    },
    "locking": {
        "name": "Locking",
        "triggers": ("locking dance", "lock and", "locks in the dance", "lock dance"),
        "doctrine": (
            "LOCKING: freeze locks after moves; points; knee drops controlled; "
            "grin optional. Freezes held one beat."
        ),
    },
    "robot_iso": {
        "name": "Robot / isolation pop",
        "triggers": ("robot dance", "popping", "isolation pop", "tutting", "animation dance"),
        "doctrine": (
            "ROBOT/POP: joint isolations; hit-hit-hold; minimal blur; "
            "torso separate from hips when named."
        ),
    },
    "contemporary_floor": {
        "name": "Contemporary floor fall",
        "triggers": ("contemporary floor", "fall and recover", "contract release dance"),
        "doctrine": (
            "CONTEMPORARY FALL: controlled lower to floor; roll; recover through plant hands; "
            "torso+head unit on sit-up."
        ),
    },
    "cheer_pom": {
        "name": "Cheer / pom sharp",
        "triggers": ("cheer dance", "pom dance", "cheerleading dance", "high kick dance"),
        "doctrine": (
            "CHEER/POM: sharp kicks only with plant support; arm V/T shapes; "
            "jumps need prep bend. Not neck whip on hair."
        ),
    },
    "bollywood": {
        "name": "Bollywood / filmi",
        "triggers": ("bollywood", "filmi dance", "indian film dance", "bhangra"),
        "doctrine": (
            "BOLLYWOOD/BHANGRA: shoulder shrugs; mudra-like hands optional; "
            "bouncy knees on bhangra; eye-line big."
        ),
    },
    "afrobeats": {
        "name": "Afrobeats / azonto-ish",
        "triggers": ("afrobeats", "afrobeat dance", "azonto", "shaku shaku", "gwara"),
        "doctrine": (
            "AFROBEATS: knee bounce; shoulder rolls; hip push; "
            "loose arms; smile optional. Groove continuous."
        ),
    },
    "dancehall_wine": {
        "name": "Dancehall wine",
        "triggers": ("dancehall", "wine up", "wining", "daggering dance"),
        "doctrine": (
            "DANCEHALL WINE: deep hip circles; knee bend; optional partner wine; "
            "daggering only if intent explicit — still mechanism contact not teleport sex."
        ),
    },
    "stripper_heels": {
        "name": "Heels / platform strut",
        "triggers": (
            "heels dance", "platform heels dance", "strut in heels",
            "walks sexy in heels", "catwalk dance",
        ),
        "doctrine": (
            "HEELS STRUT: weight in balls/heels carefully; hip sway with steps; "
            "hand on wall/pole for balance optional; no ankle snap."
        ),
    },
    "twerk_squat": {
        "name": "Squat twerk hold",
        "triggers": ("squat twerk", "twerk in squat", "low twerk", "ass up dance"),
        "doctrine": (
            "SQUAT TWERK: deep knee bend; hands on floor or knees; pulse glutes; "
            "hold depth; stand via plant-hands if rising."
        ),
    },
    "jerk_dance": {
        "name": "Jerkin' / reject",
        "triggers": ("jerkin", "jerking dance", "reject dance", "pin drop dance"),
        "doctrine": (
            "JERKIN': lean back controlled; kick steps; arm swings; "
            "keep head with torso on leans."
        ),
    },
    "shuffle_melbourne": {
        "name": "Melbourne shuffle",
        "triggers": ("melbourne shuffle", "shuffle dance", "cutting shapes"),
        "doctrine": (
            "SHUFFLE: running man / T-step footwork; upper body quieter; "
            "arms optional. Fast feet, stable torso."
        ),
    },
    "slow_grind_wall": {
        "name": "Slow wall grind",
        "triggers": ("slow grind", "grinds the wall slowly", "wall grind dance"),
        "doctrine": (
            "SLOW WALL GRIND: ass or hips to wall; slow circle; hands on wall; "
            "cheek turn with torso unit."
        ),
    },
    "table_sit_dance": {
        "name": "Sit-on-edge dance",
        "triggers": (
            "sits on the table and dances", "edge of the desk dance",
            "perches and dances",
        ),
        "doctrine": (
            "SIT-EDGE: perch on table/desk edge; swing legs; hip rock seated; "
            "hands on edge for balance."
        ),
    },
    "motorcycle_straddle": {
        "name": "Straddle prop dance",
        "triggers": (
            "straddles the motorcycle", "straddle dance", "humps the pillow dance",
            "grinds the pillow", "humps the chair arm",
        ),
        "doctrine": (
            "STRADDLE PROP: legs either side of prop; hip drag along it; "
            "hands on prop; name friction contact. Not full sex unless intent."
        ),
    },
    "freestyle": {
        "name": "Freestyle / general dance",
        "triggers": (
            "dance", "dances", "dancing", "dancer", "starts to dance",
            "begins to dance", "keeps dancing",
        ),
        "doctrine": (
            "FREESTYLE DANCE (fallback when only generic 'dance'): "
            "alternate weight shifts, one hip move, one arm/hand path, optional step. "
            "Keep it filmable — not abstract 'dances beautifully'. Name the body part that moves."
        ),
    },
}


# ─────────────────────────────────────────────────────────────────────────────
#  TEASE GESTURES — keyword → mechanism
# ─────────────────────────────────────────────────────────────────────────────

TEASE_GESTURES: dict[str, dict] = {
    "tit_squeeze_arms": {
        "name": "Tits squeezed with inner arms / press",
        "triggers": (
            "squeezes her breasts", "squeeze her tits", "squeezes her tits",
            "presses her breasts together", "pushes her breasts together",
            "cleavage squeeze", "squeezes her chest",
            "teases her tits", "tease her tits", "teases her breasts",
        ),
        "doctrine": (
            "TIT SQUEEZE: upper arms press inward against the sides of the breasts "
            "and/or hands cup and push together — name contact (inner arms / palms / fingers). "
            "Hold a beat; optional release. Not a slap unless intent says slap."
        ),
    },
    "tit_cup_lift": {
        "name": "Cup / lift breasts",
        "triggers": (
            "cups her breasts", "cup her breasts", "lifts her breasts",
            "holds her breasts", "presents her breasts",
        ),
        "doctrine": (
            "CUP/LIFT: hands under or around breasts; lift slightly toward view; "
            "thumbs optional on fabric/skin; restate support."
        ),
    },
    "tit_trace": {
        "name": "Trace / circle breasts",
        "triggers": (
            "traces her breasts", "circles her nipples", "fingers on her breasts",
            "runs fingers over her chest", "teases her nipples",
        ),
        "doctrine": (
            "TRACE: fingertip path over fabric or skin — one slow circle or stroke per section; "
            "no teleport to bare if clothes still on (unless flash/undress active)."
        ),
    },
    "ass_tease": {
        "name": "Ass slap / grab / present",
        "triggers": (
            "teases her ass", "tease her ass", "slaps her ass", "spanks herself",
            "grabs her ass", "hands on her ass", "presents her ass",
            "looks back at her ass",
        ),
        "doctrine": (
            "ASS TEASE: turn at waist (torso+head) to show ass OR hands grab/slap own cheeks "
            "with visible impact jiggle; optional look-back over shoulder with torso unit."
        ),
    },
    "hip_present": {
        "name": "Hip pop / present side",
        "triggers": (
            "pops her hip", "hip pop", "cocks her hip", "presents her hip",
            "hand on hip pose",
        ),
        "doctrine": (
            "HIP PRESENT: weight on one leg; free hip kicks out; hand optional on that hip; "
            "hold pose for the view."
        ),
    },
    "hair_play": {
        "name": "Hair play",
        "triggers": (
            "plays with her hair", "play with her hair", "twirls her hair",
            "runs fingers through her hair", "pushes hair behind ear",
            "hair tease",
        ),
        "doctrine": (
            "HAIR PLAY: fingers comb or twirl a lock; tuck behind ear; "
            "lift hair off neck — neck reveal with shoulder roll not neck snap."
        ),
    },
    "lip_bite": {
        "name": "Lip bite / mouth tease",
        "triggers": (
            "bites her lip", "bite her lip", "licks her lips", "lip bite",
            "tongue on lip",
        ),
        "doctrine": (
            "LIP BITE/LICK: upper teeth on lower lip or tongue along lip; "
            "eyes toward view; one beat then release."
        ),
    },
    "blow_kiss": {
        "name": "Blow kiss / wink",
        "triggers": (
            "blows a kiss", "blow a kiss", "winks", "wink at", "blows him a kiss",
        ),
        "doctrine": (
            "BLOW KISS/WINK: hand to lips then open toward view OR single wink; "
            "small head tilt with shoulders if needed."
        ),
    },
    "look_back": {
        "name": "Look-back tease",
        "triggers": (
            "looks over her shoulder", "look over her shoulder",
            "looks back at the camera", "over-shoulder look",
        ),
        "doctrine": (
            "LOOK-BACK TEASE: rotate torso + head together at the waist; eyes to view; "
            "hold; optional return forward same unit. Never head-only."
        ),
    },
    "hands_body": {
        "name": "Hands travel own body",
        "triggers": (
            "runs hands over", "runs her hands", "hands slide down her",
            "caresses her own", "hands over her body", "touches herself while",
        ),
        "doctrine": (
            "HANDS ON OWN BODY: name start and end (neck→chest, waist→thighs); "
            "palms drag fabric or skin; one travel per section."
        ),
    },
    "finger_mouth": {
        "name": "Finger to mouth",
        "triggers": (
            "finger to her lips", "sucks her finger", "bites her finger",
            "finger in her mouth",
        ),
        "doctrine": (
            "FINGER→MOUTH: hand rises; fingertip to lips or between lips; "
            "if mouth occupied later, free the finger before speech."
        ),
    },
    "strap_slip": {
        "name": "Strap slip tease",
        "triggers": (
            "strap slips", "lets a strap fall", "strap falls off",
            "pulls her strap down", "shoulder strap tease",
        ),
        "doctrine": (
            "STRAP SLIP: finger hooks strap; slides off shoulder; cup edge may lower — "
            "if only tease, stop before full bra path; if undress continues, hand off to garment law."
        ),
    },
    "hem_lift": {
        "name": "Hem lift tease",
        "triggers": (
            "lifts her skirt", "lifts her hem", "raises her dress",
            "skirt lift tease", "shows under her skirt",
        ),
        "doctrine": (
            "HEM LIFT: fingers grip hem; lift a measured amount; hold; optional lower. "
            "Not full undress unless intent continues strip."
        ),
    },
    "arch_back": {
        "name": "Arch / present chest",
        "triggers": (
            "arches her back", "arches for", "pushes her chest out",
            "presents her chest", "chest out",
        ),
        "doctrine": (
            "ARCH/PRESENT: ribs lift; shoulders back; head stays with torso unit; "
            "optional inhale that expands chest — visible only."
        ),
    },
    "knee_crawl_tease": {
        "name": "Crawl / approach tease",
        "triggers": (
            "crawls toward", "crawls to the camera", "on her knees toward",
            "approaches on all fours",
        ),
        "doctrine": (
            "CRAWL APPROACH: hand-knee sequence; hips may sway; eye-line up to view; "
            "stop at a marked distance; no teleport to the lens."
        ),
    },
    "foot_tease": {
        "name": "Foot / shoe tease",
        "triggers": (
            "foot tease", "points her toes", "shoe dangle", "dangles her shoe",
            "runs foot up",
        ),
        "doctrine": (
            "FOOT TEASE: extend leg; point toes; optional shoe half-off dangle; "
            "or foot traces partner/chair leg with contact named."
        ),
    },
    "neck_expose": {
        "name": "Neck / collarbone expose",
        "triggers": (
            "exposes her neck", "shows her neck", "tilts her head",
            "collarbone", "offers her neck",
        ),
        "doctrine": (
            "NECK EXPOSE: chin lifts with shoulders/torso; hair swept aside by hand; "
            "collarbones catch light — not a violent head yank."
        ),
    },
    "fabric_bite": {
        "name": "Bite fabric / glove",
        "triggers": (
            "bites her glove", "pulls glove with teeth", "bites the fabric",
            "glove in her teeth",
        ),
        "doctrine": (
            "FABRIC BITE: teeth grip glove/tip or cloth; pull free with head+torso lean; "
            "hand finishes removal if needed."
        ),
    },
    "mirror_self": {
        "name": "Mirror self-admire",
        "triggers": (
            "admires herself", "watches herself in the mirror", "mirror tease",
            "checks herself out",
        ),
        "doctrine": (
            "MIRROR SELF: turn to glass; hands adjust outfit or hair; eye-line reflection↔view."
        ),
    },
    "come_hither": {
        "name": "Come-hither / crook finger",
        "triggers": (
            "crooks her finger", "come hither", "beckons", "motions him over",
            "curls her finger",
        ),
        "doctrine": (
            "BECKON: one hand rises; index finger curls toward self/view; "
            "optional second curl; eyes locked."
        ),
    },
    "spread_knees": {
        "name": "Knee open / close",
        "triggers": (
            "opens her knees", "spreads her knees", "closes her knees",
            "thighs open", "parts her thighs",
        ),
        "doctrine": (
            "KNEE OPEN/CLOSE: seated or standing wide; knees travel outward or inward; "
            "feet plant; one clear open or close per section."
        ),
    },
    "spin_show": {
        "name": "Slow spin show-off",
        "triggers": (
            "spins slowly", "slow spin", "turns full circle", "shows her back then front",
        ),
        "doctrine": (
            "SLOW SPIN: feet step around; torso+head rotate together; full 360 if space; "
            "end facing view. Not a snap twirl."
        ),
    },
    # ── Explicit / genital teases (keyword only) ───────────────────────────
    "pussy_spread": {
        "name": "Spread pussy / open lips",
        "triggers": (
            "spreads her pussy", "spread her pussy", "spreads her lips",
            "opens her pussy", "parts her pussy", "spreads herself open",
            "holds herself open", "pussy spread", "spreads her cunt",
        ),
        "doctrine": (
            "PUSSY SPREAD: seated or reclined or standing with one foot up; "
            "fingers of one or both hands part labia; hold open toward view; "
            "restate grip. If clothing on, pull fabric aside first (named). "
            "Not penetration unless intent adds fingers inside."
        ),
    },
    "pussy_rub": {
        "name": "Rub / circle clit or pussy",
        "triggers": (
            "rubs her pussy", "rubs her clit", "circles her clit",
            "teases her pussy", "tease her pussy", "pussy tease",
            "fingers her folds", "strokes her pussy", "plays with her pussy",
        ),
        "doctrine": (
            "PUSSY RUB: fingertip or pads circle or stroke along slit/clit through fabric or bare; "
            "name over-clothes vs skin; slow tempo; hips may roll into the hand. "
            "One clear stroke pattern per section."
        ),
    },
    "pussy_finger_inside": {
        "name": "Fingers inside self",
        "triggers": (
            "fingers herself", "fingers her pussy", "puts a finger in",
            "two fingers inside", "fucks herself with her fingers",
            "finger fucks herself",
        ),
        "doctrine": (
            "FINGERS INSIDE: show finger(s) enter — not 'she's fingering' alone; "
            "wrist motion; hips answer; free hand optional on breast/ass. "
            "Pull-out before speech if she talks with mouth free."
        ),
    },
    "lick_fingers": {
        "name": "Lick / suck own fingers",
        "triggers": (
            "licks her fingers", "sucks her fingers", "tastes herself",
            "licks her finger", "finger in her mouth after",
            "sucks her fingertips", "cleans her fingers with her tongue",
        ),
        "doctrine": (
            "LICK FINGERS: hand rises from body/pussy/chest to mouth; "
            "tongue along pads or lips close on fingers; eye-line to view optional; "
            "then hand may return. Mouth busy = no speech until fingers leave."
        ),
    },
    "pussy_flash": {
        "name": "Pussy flash / show",
        "triggers": (
            "shows her pussy", "pussy flash", "flashes her pussy",
            "presents her pussy", "shows between her legs",
            "upskirt show", "no panties reveal",
        ),
        "doctrine": (
            "PUSSY SHOW: fabric aside or knees open or hem lifted; "
            "clear view beat; optional close knees/cover after if only flash. "
            "Mechanism of reveal required."
        ),
    },
    "ass_spread": {
        "name": "Spread ass cheeks",
        "triggers": (
            "spreads her ass", "spreads her cheeks", "opens her ass",
            "pulls her cheeks apart", "ass spread", "presents her hole",
        ),
        "doctrine": (
            "ASS SPREAD: bent over or prone or standing lean; hands pull cheeks; "
            "hold; optional look-back with torso+head unit."
        ),
    },
    "ass_rub": {
        "name": "Rub / jiggle ass",
        "triggers": (
            "rubs her ass", "jiggles her ass", "shakes her ass",
            "hands on her ass cheeks", "massages her ass",
        ),
        "doctrine": (
            "ASS RUB/JIGGLE: palms on cheeks; push/spread/jiggle; "
            "visible bounce; facing away or ¾."
        ),
    },
    "nipple_pinch": {
        "name": "Nipple pinch / twist",
        "triggers": (
            "pinches her nipples", "twists her nipples", "nipple play",
            "tugs her nipples", "rolls her nipples", "plays with her nipples",
        ),
        "doctrine": (
            "NIPPLE PLAY: thumb/finger on nipple through fabric or bare; "
            "pinch, roll, or light twist; chest may lift into hand."
        ),
    },
    "spit_tease": {
        "name": "Spit on self / chest",
        "triggers": (
            "spits on her chest", "spits on her tits", "spit on her",
            "lets spit fall", "drools on",
        ),
        "doctrine": (
            "SPIT TEASE: head tilts with torso; spit strand or drop to chest/breast; "
            "hand optional to spread. Visible wet path."
        ),
    },
    "oil_rub": {
        "name": "Oil / lotion rub",
        "triggers": (
            "oils her body", "lotion on her", "rubs oil", "shiny skin rub",
            "oils her breasts", "oils her ass",
        ),
        "doctrine": (
            "OIL RUB: pour or pump named; palms spread oil on named zone; "
            "sheen follows hand path; one body region per section."
        ),
    },
    "hump_prop": {
        "name": "Hump pillow / hand / prop",
        "triggers": (
            "humps the pillow", "humps her hand", "humps the armrest",
            "grinds on her hand", "rides her fingers", "humps the mattress",
        ),
        "doctrine": (
            "HUMP PROP: pelvis drags on pillow/hand/furniture; rhythm; "
            "hands brace; face optional into prop. Contact surface named."
        ),
    },
    "pussy_grind_view": {
        "name": "Grind pussy toward view",
        "triggers": (
            "grinds her pussy toward", "pussy to the camera",
            "rubs against the air toward", "presents and grinds",
        ),
        "doctrine": (
            "PUSSY GRIND TO VIEW: hips push toward lens; small circles; "
            "knees bent; optional fingers spread. POV: toward bottom edge of view."
        ),
    },
    "taste_fingers_pussy": {
        "name": "Fingers from pussy to mouth",
        "triggers": (
            "licks her pussy off her fingers", "tastes her pussy",
            "fingers from her pussy to her mouth", "sucks her juices",
        ),
        "doctrine": (
            "PUSSY→MOUTH: withdraw fingers (show leave body) → rise to lips → "
            "lick/suck pads; eyes to view optional. Two-section chain preferred."
        ),
    },
    "squirt_edge": {
        "name": "Edge / squirt setup",
        "triggers": (
            "edges herself", "edge herself", "squirts", "about to squirt",
            "makes herself squirt",
        ),
        "doctrine": (
            "EDGE/SQUIRT: build with rub/finger tempo; thighs shake visible; "
            "breath only if mouth free; finish only if intent demands — else hold edge."
        ),
    },
    "panty_aside": {
        "name": "Panty crotch aside",
        "triggers": (
            "pulls her panties aside", "panty aside", "moves her underwear aside",
            "hooks panties aside",
        ),
        "doctrine": (
            "PANTY ASIDE: finger hooks crotch fabric; pulls to side; "
            "holds; pussy or skin exposed; optional release. Not full panty remove unless undress."
        ),
    },
    "double_hand_body": {
        "name": "One hand tits one hand pussy",
        "triggers": (
            "one hand on her breast and", "hand on her tit and pussy",
            "touches her breasts and pussy", "both hands on herself",
        ),
        "doctrine": (
            "DUAL HANDS: name each hand's job (e.g. left cups breast, right rubs clit); "
            "simultaneous OK if both contacts clear; hips may roll."
        ),
    },
    "ahegao_tease": {
        "name": "Ahegao / tongue-out face",
        "triggers": (
            "ahegao", "tongue out eyes rolled", "crossed eyes tongue",
            "slut face", "needy face tease",
        ),
        "doctrine": (
            "AHEGAO TEASE: tongue out; eyes half or rolled; jaw loose; "
            "hold one beat; head still with torso — not violent thrash."
        ),
    },
    "collar_tug": {
        "name": "Collar / choker tug",
        "triggers": (
            "tugs her collar", "pulls her choker", "holds her collar",
            "finger in her collar",
        ),
        "doctrine": (
            "COLLAR TUG: finger hooks choker/collar; light pull; chin lifts with torso; "
            "eye contact."
        ),
    },
    "leash_present": {
        "name": "Leash / lead present",
        "triggers": (
            "holds the leash", "offers the leash", "leash in her hand",
            "clips the leash",
        ),
        "doctrine": (
            "LEASH: show clip to collar if attaching; leash slack/taut named; "
            "offer toward view/partner."
        ),
    },
    "money_shower_pose": {
        "name": "Money / tribute pose",
        "triggers": (
            "money on her body", "bills on her", "makes it rain",
            "cash on her tits",
        ),
        "doctrine": (
            "MONEY POSE: bills placed or falling; hands gather or let stay; "
            "chest present; not teleport cash."
        ),
    },
    "foot_worship_self": {
        "name": "Self foot / sole show",
        "triggers": (
            "shows her soles", "soles to the camera", "foot to the lens",
            "arches her foot",
        ),
        "doctrine": (
            "SOLE SHOW: leg extends; sole faces view; toes flex optional; "
            "hold."
        ),
    },
    "armpit_tease": {
        "name": "Armpit / arms-up tease",
        "triggers": (
            "arms up tease", "shows her armpits", "raises both arms",
            "armpit",
        ),
        "doctrine": (
            "ARMS-UP: both arms lift; armpits exposed; torso long; "
            "optional hip shift. Common start for bra-off later."
        ),
    },
    "wet_pussy_show": {
        "name": "Wetness show",
        "triggers": (
            "shows how wet she is", "wet pussy", "slick fingers",
            "glistening pussy", "string of wet",
        ),
        "doctrine": (
            "WET SHOW: fingers part or lift from pussy with visible wet string/sheen; "
            "or fabric dark patch named. Light catches wet skin."
        ),
    },
    "gag_self_fingers": {
        "name": "Deep fingers in mouth",
        "triggers": (
            "gags on her fingers", "pushes fingers deep in her mouth",
            "throat her fingers", "fingers on her tongue",
        ),
        "doctrine": (
            "MOUTH FINGERS DEEP: fingers enter mouth; tongue visible; "
            "optional wet sound; no speech until out."
        ),
    },
    "jerk_off_instruction_pose": {
        "name": "JOI body pose (motion)",
        "triggers": (
            "tells him to stroke", "stroke for me pose", "points at his cock while",
            "watches him stroke",
        ),
        "doctrine": (
            "JOI POSE: body pose holds while she points/eye-lines; "
            "hip rock optional; dialogue can instruct if mouth free — "
            "this gesture block is the body half."
        ),
    },
}


# Merge any dynamic extras count for tests
assert TEASE_GESTURES and DANCE_PATHS



# ─────────────────────────────────────────────────────────────────────────────
#  MUSIC → tempo colour (only when dance already active)
# ─────────────────────────────────────────────────────────────────────────────

# Substring match on music key or music block text
_MUSIC_TEMPO_HINTS: list[tuple[tuple[str, ...], str]] = [
    (("r&b", "soul", "ambient", "atmospheric"),
     "MUSIC TEMPO: slow pocket — lengthen rolls and sways; fewer moves per section."),
    (("hip-hop", "hip hop", "rap", "808"),
     "MUSIC TEMPO: bounce + chest/hip hits on kicks; groove over chaos."),
    (("electronic", "edm", "techno", "four-on-the-floor"),
     "MUSIC TEMPO: pulse on every kick; sharp freezes on builds/drops."),
    (("funk", "disco"),
     "MUSIC TEMPO: hips and shoulders in the pocket; playful loose steps."),
    (("reggae", "dancehall"),
     "MUSIC TEMPO: wine/wind the hips; loose knees; unhurried circles."),
    (("metal", "rock", "trailer"),
     "MUSIC TEMPO: heavy hits on downbeats; bigger hair/torso moves; still render-safe."),
    (("classical", "orchestral"),
     "MUSIC TEMPO: long phrases; theatrical arms; slow travel."),
    (("pop", "mainstream"),
     "MUSIC TEMPO: chorus-facing performance; smile/eye hits on hooks."),
    (("country",),
     "MUSIC TEMPO: easy swagger; two-step optional; grounded feet."),
    (("classic rock",),
     "MUSIC TEMPO: anthemic hip/step hits; confident posture."),
]


def music_tempo_hint(music_key: str = "", music_text: str = "", background: bool = False) -> str:
    blob = f"{music_key or ''} {music_text or ''}".lower()
    if not blob.strip() or blob.startswith("none"):
        return ""
    if background or "background" in blob or "quiet under" in blob:
        return (
            "MUSIC TEMPO (background): soft score under the dance — do not force kick-hits on every move; "
            "keep motion readable; music stays quiet and continuous."
        )
    for cues, hint in _MUSIC_TEMPO_HINTS:
        if any(c in blob for c in cues):
            return hint
    return "MUSIC TEMPO: land at least one hip, step, or accent per section on an audible beat."


# ─────────────────────────────────────────────────────────────────────────────
#  DETECTION + BLOCK
# ─────────────────────────────────────────────────────────────────────────────

def detect_dance_paths(intent: str = "", scenario: str = "", *, max_paths: int = 3) -> list[str]:
    b = _blob(intent, scenario)
    if not wants_dance(intent, scenario) and not wants_dirty_dance(intent, scenario):
        # still allow if only specific path words without generic "dance"? hip roll alone is dance cue
        if not any(c in b for c in _DANCE_CUES):
            return []

    hits: list[tuple[int, str]] = []
    for key, meta in DANCE_PATHS.items():
        if key == "freestyle":
            continue
        score = 0
        for t in meta.get("triggers") or ():
            if t in b:
                score = max(score, len(t))
        if score:
            hits.append((score, key))

    hits.sort(key=lambda x: -x[0])
    keys = [k for _, k in hits[:max_paths]]

    # Dirty dance only with phrase
    if "dirty_dance" in keys and not wants_dirty_dance(intent, scenario):
        keys = [k for k in keys if k != "dirty_dance"]

    if not keys and wants_dance(intent, scenario):
        keys = ["freestyle"]
    elif wants_dance(intent, scenario) and "freestyle" not in keys and len(keys) < max_paths:
        # keep freestyle out if we have specifics
        pass

    return keys


def detect_tease_gestures(intent: str = "", scenario: str = "", *, max_g: int = 5) -> list[str]:
    if not wants_tease_motion(intent, scenario):
        return []
    b = _blob(intent, scenario)
    hits: list[tuple[int, str]] = []
    for key, meta in TEASE_GESTURES.items():
        score = 0
        for t in meta.get("triggers") or ():
            if t in b:
                score = max(score, len(t))
        if score:
            hits.append((score, key))
    hits.sort(key=lambda x: -x[0])
    return [k for _, k in hits[:max_g]]


def dance_block(
    intent: str = "",
    scenario: str = "",
    *,
    music_key: str = "",
    music_text: str = "",
    music_background: bool = False,
    seed: int = 0,
    max_paths: int = 3,
    max_teases: int = 5,
) -> str:
    """
    System inject for dance/tease. Empty if neither family activates.
    Music only adds tempo colour when dance (not tease-only) is active.
    """
    if not is_active(intent, scenario):
        return ""

    paths = detect_dance_paths(intent, scenario, max_paths=max_paths)
    teases = detect_tease_gestures(intent, scenario, max_g=max_teases)

    # Seed can promote one extra tip from freestyle bank when only freestyle
    rng = random.Random(int(seed or 0) ^ 0xDA5CE)
    if paths == ["freestyle"]:
        # sprinkle one spicy standing tip via seed without claiming dirty dance
        extra = rng.choice(["hip_roll", "body_roll", "sexy_standing"])
        if extra not in paths:
            paths = ["freestyle", extra]

    lines = [
        "\n━━ DANCE / TEASE MOTION (INTENT-ACTIVATED — NOT BLOAT) ━━",
        "Only active because intent/scenario named dance and/or tease motion.",
        "'dirty' alone or 'dirty talk' does NOT mean dirty dance — need 'dirty dance' (etc.).",
        "Music preset alone does NOT force dance; if music is set AND dance is on, tempo follows the track.",
        "CANON still wins: mechanism verbs, one main move per section, head+torso together, no snaps/whips.",
        "Film the body: name hip direction, weight shift, hand path, contact surface (chair/wall/partner).",
    ]

    if paths:
        lines.append("\nACTIVE DANCE PATHS:")
        for k in paths:
            meta = DANCE_PATHS.get(k) or {}
            lines.append(f"【{meta.get('name', k)}】")
            lines.append(f"  {meta.get('doctrine', '')}")

    if teases:
        lines.append("\nACTIVE TEASE GESTURES (from intent keywords):")
        for k in teases:
            meta = TEASE_GESTURES.get(k) or {}
            lines.append(f"【{meta.get('name', k)}】")
            lines.append(f"  {meta.get('doctrine', '')}")
    elif wants_tease_motion(intent, scenario) and not teases:
        lines.append(
            "\nTEASE (generic): flirtatious body display — hair, eyes, hands on own body, "
            "slow pose changes — still mechanism-first."
        )

    if wants_dance(intent, scenario) or paths:
        mh = music_tempo_hint(music_key, music_text, background=music_background)
        if mh:
            lines.append("\n" + mh)

    lines.append(
        "\nDANCE LAYOUT: section = setup stance → one dance or tease move → optional short line "
        "if mouth free. Do not stack five moves in one paragraph.\n"
    )
    return "\n".join(lines)


def dance_remember_line(intent: str = "", scenario: str = "") -> str:
    if not is_active(intent, scenario):
        return ""
    bits = []
    if wants_dance(intent, scenario):
        bits.append("dance path filmable (hips/weight/hands named)")
    if wants_dirty_dance(intent, scenario):
        bits.append("dirty-dance phrase OK")
    elif "dirty" in _blob(intent, scenario) and wants_dance(intent, scenario):
        bits.append("NOT dirty-dance unless phrase says so")
    if wants_tease_motion(intent, scenario):
        bits.append("tease gestures mechanism")
    return "• DANCE/TEASE: " + "; ".join(bits) if bits else ""
