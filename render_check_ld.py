"""
render_check_ld.py — universal LTX render-order checks (not category lists).

Users can prompt anything. We do NOT maintain per-scene catalogs
(coffee / phone / dress / cock). Only general laws that apply to every beat:

  ENTER before USE
  FINISH before NEXT
  FREE before SPEAK
  MECHANISM not OUTCOME
  RESTATE when state changed

Heuristics below try to catch violations of those laws without naming genres.
"""

from __future__ import annotations

import re

# Universal doctrine — always injected. No per-prop catalog.
STATE_ORDER_LAW = """
━━ RENDER ORDER (universal — every prop, body part, garment, tool, mouth) ━━
LTX draws only what you write, in the order you write it. Unwritten = absent.
These five laws apply to ANY user intent (SFW or not). Do not skip the middle.

1) ENTER BEFORE USE
   Before a hand/mouth/body uses something, that something must already be in the
   frame — or enter the frame in its own prior beat (including POV bottom edge).
   If it was never written into view, contact with it is empty air.

2) FINISH BEFORE NEXT
   Complete a state change before the next action depends on the new state.
   If beat B requires state A to be done, finish A (and show it done) before B.
   Partial/vague completion does not count.

3) FREE BEFORE SPEAK
   A mouth that is full or sealed (object, liquid, kiss, food, anatomy) cannot
   form words. Only non-word sound until a free-mouth beat is written, then speech.
   Other free mouths (or POV voice as sound) may talk during.

4) MECHANISM NOT OUTCOME
   State does not change by announcement. Hands move fabric/tools/objects through
   a visible path. Skip-the-middle lines ("does X and then Y") are failures when
   Y needs the middle of X.

5) RESTATE AFTER CHANGE
   When a state change matters for the next beat, name the new state plainly in
   a short clause (on the floor / open / seated / at the bottom edge / empty-
   handed) so later sections cannot drift back to the old state.

Write extra short sections rather than one clever sentence that collapses the chain.
"""


def inject_state_order() -> str:
    return STATE_ORDER_LAW


# ── Principle-level heuristics (no genre names) ─────────────────────────────

# Outcome-y collapses: two big acts fused with and/then without middle space
_FUSED_ACTS = re.compile(
    r"\b("
    r"undress(?:es|ed|ing)?|strip(?:s|ped|ping)?|"
    r"open(?:s|ed|ing)?|sit(?:s|ting)?|stand(?:s|ing)?|"
    r"enter(?:s|ed|ing)?|walk(?:s|ed|ing)? (?:in|through|over)|"
    r"put(?:s|ting)? .{0,20} (?:in|into|on|to)|"
    r"take(?:s|n|ing)? .{0,20} (?:in|into|off)|"
    r"pull(?:s|ed|ing)? (?:off|down|up|out)|"
    r"push(?:es|ed|ing)? (?:down|up|in)|"
    r"grip(?:s|ped|ping)?|grab(?:s|bed|bing)?"
    r")\b"
    r".{0,40}\b(?:and then|then|and)\b.{0,40}\b("
    r"suck(?:s|ed|ing)?|kiss(?:es|ed|ing)?|sip(?:s|ped|ping)?|drink(?:s|ing)?|"
    r"fuck(?:s|ed|ing)?|sit(?:s|ting)?|walk(?:s|ed|ing)?|say(?:s|ing)?|talk(?:s|ing)?|"
    r"enter(?:s|ed|ing)?|leave(?:s|ing)?|stroke(?:s|d|ing)?"
    r")\b",
    re.I,
)

# Contact/use without any prior "enter frame / raise / open / bottom edge" nearby
# We look at section order: a "use" section with no establishment earlier in text
_USE_VERBS = re.compile(
    r"\b("
    r"sucks?|sucking|drinks?|sips?|kisses?|kissing|"
    r"into (?:her|his|the) mouth|mouths? (?:on|around)|"
    r"strokes?|stroking|fucks?|fucking|"
    r"answers? (?:the )?phone|talks? into|"
    r"walks? through|steps? through"
    r")\b",
    re.I,
)

_ENTRY_CUES = re.compile(
    r"\b("
    r"enters? (?:the )?(?:frame|view|shot)|"
    r"from (?:the )?bottom(?: edge)?|"
    r"bottom edge|"
    r"appears? (?:in|at) (?:the )?(?:frame|view|edge)|"
    r"raises?|lifts?|brings? .{0,30} (?:to|toward)|"
    r"opens?|pulls? open|pushes? open|"
    r"holds? (?:up|out)|"
    r"reaches? (?:for|toward|down to)|"
    r"grips?|grabs?|"
    r"steps? out|pools? (?:at|on)|heap|on the floor|at (?:her|his) feet|"
    r"lowers? (?:onto|into)|sits? (?:on|down)|settles? (?:onto|into)"
    r")\b",
    re.I,
)

_MOUTH_BUSY_THEN_SPEAK = re.compile(
    r"\b(?:"
    r"bobs?|bobbing|sucks?|sucking|sips?|sipping|drinks?|drinking|"
    r"mouths? (?:on|around|full)|lips? (?:around|sealed)|"
    r"chews?|chewing|gags?|gagging"
    r")\b"
    r"[^.!\n]{0,70}"
    r"\b(?:says|murmurs|whispers|asks|adds)\s*\(",
    re.I,
)

_OUTCOME_ONLY = re.compile(
    r"\b("
    r"now naked|clothes gone|suddenly (?:naked|undressed|open)|"
    r"is (?:already )?(?:naked|undressed|seated|inside)|"
    r"without (?:another |a )?word (?:she|he) (?:sucks|fucks|enters)"
    r")\b",
    re.I,
)

_ONE_SHOT = re.compile(r"\bin one (?:motion|go|pull)\b", re.I)


def _sections(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]


def score_render_physics(
    text: str,
    *,
    intent: str = "",
    scenario: str = "",
    pov: bool = False,
) -> dict:
    """
    Principle-level flags only. No per-genre catalog.
    intent/scenario/pov kept for API compat; scoring does not branch on prop names.
    """
    s = text or ""
    low = s.lower()
    hard: list[str] = []
    soft: list[str] = []
    notes: list[str] = []

    # 1) Mouth busy + clear speech in same clause
    if _MOUTH_BUSY_THEN_SPEAK.search(low):
        hard.append("free_before_speak")
        notes.append("quoted speech while mouth still engaged in same clause")

    # 2) One-shot teleport phrasing
    if _ONE_SHOT.search(low):
        hard.append("mechanism_not_outcome")
        notes.append("in one motion/go collapses a chain")

    # 3) Outcome-only state claims
    if _OUTCOME_ONLY.search(low):
        hard.append("mechanism_not_outcome")
        notes.append("outcome announcement without mechanism path")

    # 4) Fused two-act lines (do X and then Y) — soft unless very tight
    fused = list(_FUSED_ACTS.finditer(low))
    if len(fused) >= 2:
        soft.append("finish_before_next_soft")
        notes.append("multiple fused and/then act pairs — risk of skipped middle")
    elif len(fused) == 1:
        soft.append("fused_act_pair")

    # 5) USE section with no ENTRY cue anywhere earlier in the script
    #    (universal: if you use/contact something, establishment should exist prior)
    secs = _sections(s)
    if secs:
        cum = ""
        use_without_prior_entry = 0
        for sec in secs:
            sec_l = sec.lower()
            if _USE_VERBS.search(sec_l):
                # prior text must have had some entry/establish cue
                if not _ENTRY_CUES.search(cum):
                    # allow if THIS section itself establishes then uses (order inside section)
                    # split section roughly in half — weak but genre-free
                    mid = len(sec_l) // 2
                    head, tail = sec_l[:mid], sec_l[mid:]
                    if _USE_VERBS.search(tail) and _ENTRY_CUES.search(head):
                        pass
                    elif _ENTRY_CUES.search(sec_l) and (
                        _ENTRY_CUES.search(sec_l).start()
                        < (_USE_VERBS.search(sec_l).start() if _USE_VERBS.search(sec_l) else 0)
                    ):
                        pass
                    else:
                        use_without_prior_entry += 1
            cum += " " + sec_l
        if use_without_prior_entry >= 1:
            hard.append("enter_before_use")
            notes.append(
                "use/contact beat with no prior establish/enter/raise/open/bottom-edge cue"
            )

    # 6) Very short script that claims multi-step change via single section
    if len(secs) <= 2 and len(s) > 80 and _USE_VERBS.search(low) and _FUSED_ACTS.search(low):
        soft.append("chain_too_compressed")

    # pov unused on purpose — same laws; bottom-edge covered by ENTRY_CUES
    _ = (intent, scenario, pov)

    return {
        "flags": hard + soft,
        "hard": hard,
        "soft": soft,
        "notes": notes,
        "pass": len(hard) == 0,
    }
