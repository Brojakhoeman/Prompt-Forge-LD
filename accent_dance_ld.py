# -*- coding: utf-8 -*-
"""
accent_dance_ld.py — Region / accent-specific dance body-language for PromptForge LD

When Accent is locked (or auto-detected) AND dance cues fire, inject ~3
filmable regional paths with full body language — not vibe words.

Same Grok bar as dance_ld / accents_ld:
  • mechanism verbs, weight, hips, hands, head+torso unit
  • no snaps/whips; one main move per section
  • English description; cultural flavour without costume parody spam
"""
from __future__ import annotations


# Each accent: exactly 3 paths {name, doctrine}
ACCENT_DANCE: dict[str, list[dict[str, str]]] = {
    "korean": [
        {
            "name": "Idol point / sharp hit",
            "doctrine": (
                "Weight on balls of feet; sharp arm points to view or diagonal; "
                "chest pop on the hit; freeze half a beat; head+torso face the hit together. "
                "Smile optional. One clean hit per section — not mushy continuous roll."
            ),
        },
        {
            "name": "Wave body roll (K-stage)",
            "doctrine": (
                "Chest initiates, wave travels ribs→hips in one pass; knees soft; "
                "arms frame face or slide flanks; finish planted. One full travel per section."
            ),
        },
        {
            "name": "Cute sway + heel change",
            "doctrine": (
                "Small side-to-side weight shifts; one heel lifts then the other; "
                "hands near cheeks or clasp in front; shoulders follow head if she looks to view."
            ),
        },
    ],
    "japanese": [
        {
            "name": "Idol pose lock",
            "doctrine": (
                "Step into a held pose: one foot pointed, hip cocked, hands at heart or peace; "
                "hold one full beat; release to next pose. Head stays with torso on any turn."
            ),
        },
        {
            "name": "Precise small step",
            "doctrine": (
                "Tiny clean foot changes (step-touch); wrists precise; elbows soft; "
                "no wild hair whips — controlled. One phrase of steps per section."
            ),
        },
        {
            "name": "Bow-into-dance",
            "doctrine": (
                "Slight torso bow from the waist (head with torso), then rise into a sway or point; "
                "hands slide to sides. Not a head-only nod."
            ),
        },
    ],
    "mandarin": [
        {
            "name": "Sharp stage hit",
            "doctrine": (
                "Plant feet; arm strikes to a clear end-point; torso faces the strike; "
                "hold; optional second hit opposite side. Clean geometry over freestyle mess."
            ),
        },
        {
            "name": "Sleeve / hand ribbon feel",
            "doctrine": (
                "Even without props: long arm arcs, wrists lead, body turns as one unit under the arm; "
                "weight shifts with the arc. Soft continuum, one arc per section."
            ),
        },
        {
            "name": "Square step pocket",
            "doctrine": (
                "Simple box or side-step pattern; arms pump or frame; face view on the strong count; "
                "name left/right feet once."
            ),
        },
    ],
    "thai": [
        {
            "name": "Soft finger-curve pose",
            "doctrine": (
                "Fingers gently curved; elbows lifted soft; weight on one leg; "
                "slow hip shift; head tilts with shoulders as one unit. Graceful, not frozen statue."
            ),
        },
        {
            "name": "Slow kneeling rise dance",
            "doctrine": (
                "From kneel or deep plié: palms optional plant; hips lift; torso+head rise together; "
                "finish standing with soft sway. Split plant vs full stand if needed."
            ),
        },
        {
            "name": "Side-step smile sway",
            "doctrine": (
                "Small lateral steps; hands near ribs or floating; eye-line soft to view; "
                "one continuous sway phrase, not five moves."
            ),
        },
    ],
    "vietnamese": [
        {
            "name": "Light bounce pocket",
            "doctrine": (
                "Quick light knee bounce; shoulders easy; hands clap or brush thighs optional; "
                "short phrase then hold. Energetic but not thrash."
            ),
        },
        {
            "name": "Hand fan without prop",
            "doctrine": (
                "Wrist circles as if fanning; torso turns with the hand path; "
                "weight rocks heel-toe. One clear hand phrase per section."
            ),
        },
        {
            "name": "Forward-back step charm",
            "doctrine": (
                "Two steps toward view, two back; hips soft; arms open then gather; "
                "head with torso on the approach."
            ),
        },
    ],
    "french": [
        {
            "name": "Chanson sway",
            "doctrine": (
                "Slow weight shifts side to side; one hand near chest or mic; "
                "shoulders soft; chin with torso if she turns to view. Intimate, unhurried."
            ),
        },
        {
            "name": "Cabaret hip circle",
            "doctrine": (
                "Plant feet; full slow hip circle once (state direction); ribs quieter; "
                "free hand trails thigh or hat-brim mime. Complete the circle before next move."
            ),
        },
        {
            "name": "Catwalk three-step",
            "doctrine": (
                "Three deliberate steps toward or past view; hip leads slightly; "
                "shoulders level; turn with full upper body at end of path."
            ),
        },
    ],
    "spanish_castilian": [
        {
            "name": "Flamenco-adjacent stamp",
            "doctrine": (
                "Strong foot stamp or heel plant (no injury thrash); upright torso; "
                "arms rise curved; head with torso on any snap-look to view — torso turns, not neck alone."
            ),
        },
        {
            "name": "Castanet-free hand clap rhythm",
            "doctrine": (
                "Clap pattern on the beat if music on; weight bounce in knees; "
                "shoulders proud; one clap phrase then pose hold."
            ),
        },
        {
            "name": "Proud circle walk",
            "doctrine": (
                "Walk a small arc around the spot; arms open; chest lifted; "
                "finish facing view with feet together. Head follows torso through the arc."
            ),
        },
    ],
    "spanish_latin": [
        {
            "name": "Reggaeton dembow hip",
            "doctrine": (
                "Knees soft; hips push back and circle on the dembow pocket; "
                "chest relatively quiet; hands on thighs or in air; one hip figure per section."
            ),
        },
        {
            "name": "Salsa basic (solo mark)",
            "doctrine": (
                "Forward-back or side basic weight changes; arms frame; "
                "spot turn only with torso+head unit. Name the step once."
            ),
        },
        {
            "name": "Bachata side-close",
            "doctrine": (
                "Side step, close, side, tap; hip settles on the close; "
                "optional partner frame if pair — hands named on shoulder/waist."
            ),
        },
    ],
    "italian": [
        {
            "name": "Tarantella-light spin prep",
            "doctrine": (
                "Quick step-hops in place; hands clap above or out; "
                "small prepared turn with whole torso — no whip spin."
            ),
        },
        {
            "name": "Open-arm bel canto sway",
            "doctrine": (
                "Arms open wide; ribs expand on breath; slow sway; "
                "weight shifts grand but controlled; face the view on the open."
            ),
        },
        {
            "name": "Hand-talk gesture dance",
            "doctrine": (
                "Expressive hand shapes (not random flail); step into each gesture; "
                "shoulders and hands linked; one gesture idea per section."
            ),
        },
    ],
    "portuguese": [
        {
            "name": "Samba bounce (soft)",
            "doctrine": (
                "Continuous soft knee bounce; hips answer; feet stay mostly under hips; "
                "arms loose swing. Keep it readable — not blur."
            ),
        },
        {
            "name": "Bossa gentle sway",
            "doctrine": (
                "Very slow side weight; soft shoulder; hands near waist or loose; "
                "almost still upper body with hip tide. Unhurried."
            ),
        },
        {
            "name": "Forró-ish side close",
            "doctrine": (
                "Side-close steps; optional partner hold if pair; "
                "hips soft on the close; head with torso if turning together."
            ),
        },
    ],
    "german": [
        {
            "name": "March-pulse step",
            "doctrine": (
                "Clear downbeat steps; upright posture; arms controlled pump or still; "
                "firm weight changes; no floppy freestyle."
            ),
        },
        {
            "name": "Club industrial hit",
            "doctrine": (
                "Plant; sharp shoulder/chest hit on kick; freeze; "
                "jaw set optional; torso owns the hit. One hit per section."
            ),
        },
        {
            "name": "Waltz box (solo mark)",
            "doctrine": (
                "1-2-3 box weight changes; mild rise/fall; arms in frame shape even solo; "
                "slow and even."
            ),
        },
    ],
    "dutch": [
        {
            "name": "Straight pocket groove",
            "doctrine": (
                "Even knee bounce; hips simple; no extra flourishes; "
                "hands on thighs or natural hang; face view."
            ),
        },
        {
            "name": "Side-step festival bounce",
            "doctrine": (
                "Side steps with small hops; arms up optional; "
                "land soft; keep head with torso if turning."
            ),
        },
        {
            "name": "Shoulder shrug rhythm",
            "doctrine": (
                "Alternating shoulder lifts on beat; feet plant or micro-step; "
                "dry confident face optional; one phrase then hold."
            ),
        },
    ],
    "swedish": [
        {
            "name": "Nordic soft sway",
            "doctrine": (
                "Long easy weight shifts; soft knees; arms float low; "
                "melodic body — unhurried. One sway cycle per section."
            ),
        },
        {
            "name": "Club Nordic bounce",
            "doctrine": (
                "Light bounce; minimal upper drama; clean lines; "
                "hands near pockets or loose; face view on strong beat."
            ),
        },
        {
            "name": "Partner polska hint",
            "doctrine": (
                "If pair: simple turning walk with hands on shoulder/waist named; "
                "solo: small circle walk with soft arms. Torso turns as unit."
            ),
        },
    ],
    "norwegian": [
        {
            "name": "Easy fjord sway",
            "doctrine": (
                "Slow side-to-side; soft knees; relaxed shoulders; "
                "natural arms; finish facing view."
            ),
        },
        {
            "name": "Kick-step light",
            "doctrine": (
                "Small kick then plant; alternate legs; arms counter lightly; "
                "keep kicks low and controlled."
            ),
        },
        {
            "name": "Shoulder roll continuum",
            "doctrine": (
                "One shoulder rolls back then the other; chest follows; "
                "hips quiet; head with the roll of the torso."
            ),
        },
    ],
    "russian": [
        {
            "name": "Kalinka-energy squat pulse",
            "doctrine": (
                "Deep knee bend (controlled — not injury dump); heels may lift; "
                "upright proud chest; arms out or akimbo; pulse up-down on the beat; "
                "head stays with torso. One squat phrase per section."
            ),
        },
        {
            "name": "Kazachok-lite kick (safe)",
            "doctrine": (
                "From slight squat: low controlled kick forward then plant — never neck whip; "
                "arms balance out; alternate once. Keep kicks modest and filmable."
            ),
        },
        {
            "name": "Slow Slavic sway + hand on heart",
            "doctrine": (
                "Upright posture; slow weight shift; one hand to sternum or open palm out; "
                "chin level with torso if she turns to view; ballad-serious body, not slapstick."
            ),
        },
    ],
    "polish": [
        {
            "name": "Polka-light hop step",
            "doctrine": (
                "Small hop-steps side or forward; lively but controlled; "
                "arms swing opposite; land soft; head with torso on turns."
            ),
        },
        {
            "name": "Proud stamp circle",
            "doctrine": (
                "Stamp-plant around a small circle; upright; hands on hips optional; "
                "finish to view."
            ),
        },
        {
            "name": "Oberek-ish spin prep",
            "doctrine": (
                "Prepared turn with stepped feet — no snap spin; arms rounded; "
                "spot the view at end of turn with whole upper body."
            ),
        },
    ],
    "czech": [
        {
            "name": "Polka mark in place",
            "doctrine": (
                "Step-close-step pattern; light bounce; arms natural; "
                "clear footwork, modest travel."
            ),
        },
        {
            "name": "Upright folk sway",
            "doctrine": (
                "Upright spine; side weight; hands clasp or on hips; "
                "small smile optional; one phrase."
            ),
        },
        {
            "name": "Partner turn offer",
            "doctrine": (
                "If pair: hand offer then underarm turn prep with torso unit; "
                "solo: mime the turn alone with arm arc and step."
            ),
        },
    ],
    "greek": [
        {
            "name": "Syrtaki-line step (solo mark)",
            "doctrine": (
                "Side steps with slight grapevine flavour; arms may link-mime at shoulders; "
                "upright; strong downbeat plants; face along the line then to view."
            ),
        },
        {
            "name": "Shoulder-pop Mediterranean",
            "doctrine": (
                "Alternating shoulder pops; hips soft answer; feet plant; "
                "chest proud; one pop phrase."
            ),
        },
        {
            "name": "Circle walk with arms open",
            "doctrine": (
                "Walk a circle; arms open; weight even; "
                "close facing view with feet together."
            ),
        },
    ],
    "arabic": [
        {
            "name": "Belly isolation (ribs/hips)",
            "doctrine": (
                "Isolate ribs slide or hip drop — name which; feet quiet; "
                "arms snake or frame; one isolation per section. Not a full gymnastic combo."
            ),
        },
        {
            "name": "Shimmy controlled",
            "doctrine": (
                "Fast small hip or shoulder shimmy for one beat count; "
                "then freeze; knees soft; keep head stable with torso."
            ),
        },
        {
            "name": "Hip figure-eight",
            "doctrine": (
                "Slow figure-8 hips; plant feet; soft knees; "
                "arms float or on head briefly; complete the 8 before next idea."
            ),
        },
    ],
    "hebrew": [
        {
            "name": "Hora-circle step (solo mark)",
            "doctrine": (
                "Grapevine or side-close traveling steps; upright; "
                "arms may open as if in circle; lively but planted."
            ),
        },
        {
            "name": "Urban club pulse",
            "doctrine": (
                "Modern knee bounce; sharp shoulder; dry confident face optional; "
                "hands near body; one phrase."
            ),
        },
        {
            "name": "Stamp-and-hold",
            "doctrine": (
                "Strong stamp; hold pose; arms frame; "
                "torso faces the hold; no neck-only look."
            ),
        },
    ],
    "swahili": [
        {
            "name": "Afro open-chest bounce",
            "doctrine": (
                "Knees bounce; chest open; shoulders easy; "
                "arms swing wide; smile optional; pocket over chaos."
            ),
        },
        {
            "name": "Hip wine soft",
            "doctrine": (
                "Circular hip wine; feet planted or micro-step; "
                "hands on thighs; torso upright."
            ),
        },
        {
            "name": "Call-step forward",
            "doctrine": (
                "Two steps to view with open arms; plant; "
                "optional clap; head with torso on approach."
            ),
        },
    ],
    "filipino_english": [
        {
            "name": "Karaoke stage sway",
            "doctrine": (
                "Mic-hand mime or real; weight shifts with the hook; "
                "free hand gestures the lyric; face view on the line; small steps only."
            ),
        },
        {
            "name": "Tinikling-light step (no poles)",
            "doctrine": (
                "Quick in-out foot taps as if poles; light hops; "
                "arms out for balance; keep it playful and controlled."
            ),
        },
        {
            "name": "Hand-wave charm",
            "doctrine": (
                "Small hand waves or pagmamano-soft gesture energy without mockery; "
                "step-touch; shoulders soft; one charm phrase."
            ),
        },
    ],
    "new_zealand": [
        {
            "name": "Laid-back two-step",
            "doctrine": (
                "Easy two-step; soft knees; minimal drama; "
                "hands loose; unhurried face to view."
            ),
        },
        {
            "name": "Surf-balance rock",
            "doctrine": (
                "Feet wide; rock weight heel-toe as if board; "
                "arms out for balance; torso level."
            ),
        },
        {
            "name": "Pub sway with pint-mime",
            "doctrine": (
                "Slow sway; one hand mime glass or in pocket; "
                "shoulder soft; small smile optional."
            ),
        },
    ],
    "nigerian_english": [
        {
            "name": "Afrobeats waist",
            "doctrine": (
                "Deep soft knees; waist/hip rolls on the pocket; "
                "chest can pop lightly; arms fluid; one waist phrase per section."
            ),
        },
        {
            "name": "Azonto-adjacent arm story",
            "doctrine": (
                "Clear arm mime phrases (work, phone, drive — pick one); "
                "feet bounce under; face sells the mime; one story per section."
            ),
        },
        {
            "name": "Shaku-shaku foot glide",
            "doctrine": (
                "Feet glide/twist out and in; knees bent; torso upright; "
                "arms swing opposite; keep glides readable."
            ),
        },
    ],
    "ghanaian_english": [
        {
            "name": "Azonto pocket",
            "doctrine": (
                "Bent knees; rhythmic torso; storytelling arms; "
                "bounce continuous but section-clear; face engaged."
            ),
        },
        {
            "name": "Hiplife shoulder",
            "doctrine": (
                "Shoulder rolls and hits on beat; hips answer; "
                "feet step-touch; one shoulder phrase."
            ),
        },
        {
            "name": "Circle walk pride",
            "doctrine": (
                "Walk a circle with bounce; chest open; "
                "arms swing; finish to view."
            ),
        },
    ],
    "south_african_english": [
        {
            "name": "Pantsula-lite step",
            "doctrine": (
                "Sharp small footwork; upright; arms crisp; "
                "attitude in posture not violence; one foot phrase."
            ),
        },
        {
            "name": "Gqom body hit",
            "doctrine": (
                "Heavy knee bend on the hit; chest drops or pops; "
                "recover; plant. One hit per section."
            ),
        },
        {
            "name": "Easy township sway",
            "doctrine": (
                "Relaxed side sway; soft clap optional; "
                "friendly face; unhurried."
            ),
        },
    ],
    "trinidadian": [
        {
            "name": "Soca jump-and-wave",
            "doctrine": (
                "Small jumps or high-energy bounce; arms wave; "
                "land soft; big energy but section-readable; smile optional."
            ),
        },
        {
            "name": "Wine the waist",
            "doctrine": (
                "Circular waist wine; knees bent; hands on thighs or up; "
                "complete circle; not floor drop unless intent says."
            ),
        },
        {
            "name": "Chip down the road",
            "doctrine": (
                "Forward chipping steps; bounce; arms swing; "
                "travel a short path then plant to view."
            ),
        },
    ],
    "indian_english": [
        {
            "name": "Filmi mudra hands",
            "doctrine": (
                "Clear hand mudra shapes; wrists precise; "
                "neck does NOT slide alone — head moves with torso if orientation changes; "
                "one mudra phrase with a step."
            ),
        },
        {
            "name": "Bhangra-light shoulder",
            "doctrine": (
                "Shoulder lifts/pops; knees bounce; arms high optional; "
                "joyful energy; plant between pops."
            ),
        },
        {
            "name": "Classical-lite stamp and pose",
            "doctrine": (
                "Stamp; hold pose with curved arms; eyes to view; "
                "torso owns the pose; then release."
            ),
        },
    ],
    "cockney": [
        {
            "name": "Knees-up pub bounce",
            "doctrine": (
                "Bouncy knees; clap or arms link-mime; "
                "cheeky face optional; small circle or in-place; lively not messy."
            ),
        },
        {
            "name": "Market swagger walk",
            "doctrine": (
                "Rolling walk toward view; shoulders easy; "
                "hands in pockets or gesture; plant and turn with full torso."
            ),
        },
        {
            "name": "Shoulder-shimmy joke",
            "doctrine": (
                "Quick shoulder shimmy one beat; laugh optional; "
                "recover to stance; keep it short."
            ),
        },
    ],
    "scottish": [
        {
            "name": "Reel step mark",
            "doctrine": (
                "Light skip-steps; upright; arms may lift; "
                "travel small figure; controlled landings; head with torso on turns."
            ),
        },
        {
            "name": "Proud highland plant",
            "doctrine": (
                "Strong plant; chest up; one arm curved high optional; "
                "hold; slow weight change. Dignity over slapstick."
            ),
        },
        {
            "name": "Ceilidh sway with partner offer",
            "doctrine": (
                "If pair: both hands named, simple turn prep; "
                "solo: sway and open palm offer to view; warm."
            ),
        },
    ],
    "irish": [
        {
            "name": "Soft-shoe treble hint",
            "doctrine": (
                "Quick small foot taps/trebles low to ground; upper body relatively still; "
                "arms soft at sides; precise feet — not stomping chaos."
            ),
        },
        {
            "name": "Lilt sway",
            "doctrine": (
                "Melodic side sway; soft knees; gentle arms; "
                "eye-line warm to view; unhurried."
            ),
        },
        {
            "name": "Set-dance advance/retire",
            "doctrine": (
                "Advance two steps to view, retire two; "
                "arms down or loose; clear geometry."
            ),
        },
    ],
    "scouse": [
        {
            "name": "Lively Liverpool bounce",
            "doctrine": (
                "Quick bounce; sharp shoulder; playful face optional; "
                "hands talk a bit; keep feet under hips."
            ),
        },
        {
            "name": "Dockside swagger",
            "doctrine": (
                "Rolling walk; one shoulder lead; "
                "turn to view with full torso; plant."
            ),
        },
        {
            "name": "Clap-step chorus",
            "doctrine": (
                "Clap on beat with step-touch; "
                "big energy short phrase; hold end pose."
            ),
        },
    ],
    "geordie": [
        {
            "name": "Toon bounce",
            "doctrine": (
                "Firm friendly bounce; chest open; "
                "arms loose; step-touch; warm energy."
            ),
        },
        {
            "name": "Shoulder barge rhythm (soft)",
            "doctrine": (
                "Alternating soft shoulder pushes into space (not hitting anyone); "
                "feet plant; playful; one phrase."
            ),
        },
        {
            "name": "Circle stomp party",
            "doctrine": (
                "Stomp around a small circle; clap optional; "
                "finish to view laughing optional."
            ),
        },
    ],
    "northern_english": [
        {
            "name": "Dry two-step",
            "doctrine": (
                "Simple two-step; no fluff; solid weight; "
                "hands practical; face straight to view."
            ),
        },
        {
            "name": "Working-shoulder roll",
            "doctrine": (
                "Slow shoulder rolls; feet planted; "
                "release tension visibly; one roll pair."
            ),
        },
        {
            "name": "Pub-rail sway",
            "doctrine": (
                "Sway as if hand on bar; weight side to side; "
                "other hand free; understated."
            ),
        },
    ],
    "welsh": [
        {
            "name": "Male-voice-sway (body)",
            "doctrine": (
                "Upright proud sway; soft rises; "
                "hands at sides or clasp; melodic body timing; face view."
            ),
        },
        {
            "name": "Folk step light",
            "doctrine": (
                "Simple traveling steps; arms soft; "
                "small circle; gentle."
            ),
        },
        {
            "name": "Harp-hand float",
            "doctrine": (
                "Hands float as if harp strings; torso sways under; "
                "feet micro-step; lyrical not chaotic."
            ),
        },
    ],
    "rp_british": [
        {
            "name": "Ballroom frame sway",
            "doctrine": (
                "Upright frame even solo; slow sway; "
                "arms in soft dance-hold shape; polished; small steps."
            ),
        },
        {
            "name": "Controlled chaîné prep",
            "doctrine": (
                "Prepared half-turn with stepped feet; "
                "arms rounded; spot view at end with torso unit — no whip."
            ),
        },
        {
            "name": "Garden-party step-touch",
            "doctrine": (
                "Neat step-touch; minimal bounce; "
                "pleasant face; hands relaxed elegant."
            ),
        },
    ],
    "australian": [
        {
            "name": "Laid-back pub sway",
            "doctrine": (
                "Easy sway; soft knees; one hand mime drink or pocket; "
                "unfussy; face view."
            ),
        },
        {
            "name": "Surf rock balance",
            "doctrine": (
                "Wide stance; rock weight; arms out; "
                "torso level; casual grin optional."
            ),
        },
        {
            "name": "Festival two-step",
            "doctrine": (
                "Simple two-step with small bounce; "
                "arms loose up; land soft."
            ),
        },
    ],
    "jamaican_rasta": [
        {
            "name": "Dancehall wine",
            "doctrine": (
                "Deep knee bend; waist/hip wine circle; "
                "hands on thighs or knees; chest relatively quiet; complete circle; "
                "optional look-back with full torso unit."
            ),
        },
        {
            "name": "Skank step",
            "doctrine": (
                "Offbeat skank feel: choppy step; knees bent; "
                "arms chop or guitar-mime lightly; pocket with the riddim if music on."
            ),
        },
        {
            "name": "One-drop body rock",
            "doctrine": (
                "Rock weight on the one-drop; chest easy; "
                "dread/hair moves with torso not neck alone; slow confident."
            ),
        },
    ],
    "southern_us": [
        {
            "name": "Two-step country",
            "doctrine": (
                "Quick-quick-slow two-step; hands in partner frame if pair else loose; "
                "boots/plant clear; easy upper body."
            ),
        },
        {
            "name": "Slow drawl sway",
            "doctrine": (
                "Very slow side sway; longer settles; "
                "one hand trail skirt or belt; warm eye-line."
            ),
        },
        {
            "name": "Line-dance grapevine mark",
            "doctrine": (
                "Grapevine right then left; heel taps optional; "
                "face wall then view; arms natural."
            ),
        },
    ],
}


def _verify_coverage() -> None:
    try:
        from .accents_ld import ACCENTS
    except ImportError:
        try:
            from accents_ld import ACCENTS
        except ImportError:
            return
    missing = [k for k in ACCENTS if k not in ACCENT_DANCE]
    extra = [k for k in ACCENT_DANCE if k not in ACCENTS]
    bad = [k for k, v in ACCENT_DANCE.items() if len(v) != 3]
    if missing or extra or bad:
        raise RuntimeError(
            f"ACCENT_DANCE coverage broken — missing={missing} extra={extra} bad_count={bad}"
        )
    for k, paths in ACCENT_DANCE.items():
        for p in paths:
            if not (p.get("name") and p.get("doctrine") and len(p["doctrine"]) > 40):
                raise RuntimeError(f"ACCENT_DANCE thin doctrine: {k} / {p.get('name')}")


try:
    _verify_coverage()
except Exception as _e:
    print(f"[PromptForgeLD] accent_dance_ld: {_e}")


def resolve_dance_accent_key(force_key: str = "", intent: str = "") -> str:
    try:
        from .accents_ld import resolve_accent_key
    except ImportError:
        from accents_ld import resolve_accent_key
    raw = (force_key or "").strip().lower()
    if raw in ("off", "none", "same", "same as lead"):
        return ""
    if raw in ("", "auto"):
        key = resolve_accent_key(intent, "auto")
    else:
        key = resolve_accent_key(intent, force_key)
    return key if key in ACCENT_DANCE else ""


def format_accent_dance_paths(key: str, *, role: str = "LEAD", seed: int = 0) -> str:
    paths = ACCENT_DANCE.get(key) or []
    if not paths:
        return ""
    try:
        from .accents_ld import ACCENTS
        name = (ACCENTS.get(key) or {}).get("name") or key
    except Exception:
        name = key
    # Always expose all 3 — user asked for full body language bank, not token skimp
    lines = [
        f"【{role} REGIONAL DANCE — {name}】",
        "Use these body-language paths when they dance (with or without singing).",
        "CANON: one main move per section; head+torso together; name weight/hips/hands.",
    ]
    for i, p in enumerate(paths, 1):
        lines.append(f"  ({i}) {p.get('name', '')}")
        lines.append(f"      {p.get('doctrine', '')}")
    return "\n".join(lines)


def accent_dance_block(
    intent: str = "",
    *,
    accent_mode: str = "auto",
    accent_partner: str = "off",
    seed: int = 0,
) -> str:
    """Inject when dance is already active — full regional paths for lead (+ partner)."""
    lead = resolve_dance_accent_key(accent_mode, intent)
    partner = ""
    pr = (accent_partner or "").strip().lower()
    if pr not in ("", "off", "none", "same", "same as lead", "auto"):
        partner = resolve_dance_accent_key(accent_partner, "")

    if not lead and not partner:
        lead = resolve_dance_accent_key("auto", intent)
    if not lead and not partner:
        return ""

    lines = [
        "",
        "━━ ACCENT × DANCE (REGIONAL BODY LANGUAGE — FULL SET) — PRIORITY OVER FREESTYLE ━━",
        "Accent is locked/detected AND dance is on. These regional mechanisms BEAT generic "
        "hip-sway / step-touch / freestyle unless intent names a different named style.",
        "HARD: write at least ONE of the named moves below with real weight/hips/hands — not a vague 'sways to the music'.",
        "Karaoke + 'dances a little' = small readable REGIONAL moves under the vocal — not a second full choreo dump, "
        "and not the same cookie for every accent.",
        "If singing is also on: interleave regional move sections with sung lines — do not only dance OR only sing.",
    ]
    if lead:
        lines.append(format_accent_dance_paths(lead, role="LEAD", seed=seed))
    if partner and partner != lead:
        lines.append(format_accent_dance_paths(partner, role="PARTNER", seed=seed ^ 0xDACE))
        lines.append(
            "PARTNER vs LEAD: distinct movement colours; do not mirror-merge both into one bland groove."
        )
    elif partner and partner == lead:
        lines.append(
            "PARTNER shares accent family — still keep who moves how clear when both dance."
        )
    return "\n".join(lines)


def accent_dance_remember_line(
    intent: str = "",
    *,
    accent_mode: str = "auto",
    accent_partner: str = "off",
) -> str:
    lead = resolve_dance_accent_key(accent_mode, intent)
    if not lead:
        return ""
    return f"• DANCE×ACCENT: regional body paths for {lead} (weight/hips/hands named)"
