# -*- coding: utf-8 -*-
"""
self_check_ld.py — optional post-draft QA pass (before the box commits)

Toggle OFF by default. When ON, the model re-reads its own script against a
checklist of questions (user-selected chips + auto context chips) and either:
  • report — emit pass/fail notes only (script unchanged)
  • fix    — rewrite once to fix FAILs, then re-scrub

Never runs on silent stream mid-tokens — only after first finalize.
"""
from __future__ import annotations

import json
import re
from typing import Iterable

# Chip id → question the model must answer pass/fail
CHECK_CATALOG: dict[str, dict] = {
    "intent_beats": {
        "label": "Intent beats",
        "q": "Does the script actually perform the user's intent (named actions, props, stakes) — not just vague atmosphere?",
    },
    "i2v_lock": {
        "label": "I2V lock",
        "q": "I2V: first line is the start-image anchor; wardrobe/hair/place match the start image; no invented location jump?",
    },
    "talk_floor": {
        "label": "Enough talk",
        "q": "Is there enough quoted spoken dialogue for the dialogue tier (talkative = many short lines with emotion brackets; standard = a few real lines)?",
    },
    "silent_ok": {
        "label": "Silent clean",
        "q": "Silent tier: ZERO quoted speech and no 'says/murmurs/whispers' speech frames?",
    },
    "pov_clean": {
        "label": "POV clean",
        "q": "POV mode: viewpoint is hands/view/sound only — no I/me/my body prose outside dialogue quotes?",
    },
    "body_unit": {
        "label": "Body unit",
        "q": "Head and torso reorient together; no neck-only head turns; rises use body units?",
    },
    "hard_triggers": {
        "label": "LoRA triggers",
        "q": "Any HARD LoRA trigger tokens from the user appear at least once (exact spelling, not spoken as 'LoRA triggers:')?",
    },
    "camera_alive": {
        "label": "Camera hunts",
        "q": "Camera reframes across sections (new angle / close-up / push) — not one frozen medium shot?",
    },
    "no_meta": {
        "label": "No meta speech",
        "q": "No dialogue about cuts, cameras, scenes, clips, or the prompt itself?",
    },
    "sections": {
        "label": "Sections",
        "q": "Blank-line sections with one clear action beat each — not a wall of text?",
    },
    "gravure_voice": {
        "label": "Gravure voice",
        "q": "Gravure: accented mixed-English Asian L2 voice (not flat native English); soft breathy short lines?",
    },
}

# UI default chips when user hasn't customized
DEFAULT_CHIPS = ["intent_beats", "talk_floor", "body_unit", "sections", "no_meta"]


def parse_chip_list(raw) -> list[str]:
    """Accept list, JSON string, or comma-separated ids."""
    if raw is None:
        return list(DEFAULT_CHIPS)
    if isinstance(raw, (list, tuple)):
        ids = [str(x).strip() for x in raw if str(x).strip()]
    else:
        s = str(raw).strip()
        if not s:
            return list(DEFAULT_CHIPS)
        if s.startswith("["):
            try:
                arr = json.loads(s)
                ids = [str(x).strip() for x in arr if str(x).strip()]
            except Exception:
                ids = [p.strip() for p in s.split(",") if p.strip()]
        else:
            ids = [p.strip() for p in re.split(r"[,|;]+", s) if p.strip()]
    out, seen = [], set()
    for i in ids:
        if i in CHECK_CATALOG and i not in seen:
            seen.add(i)
            out.append(i)
    return out or list(DEFAULT_CHIPS)


def auto_chips(
    *,
    mode: str = "t2v",
    dialogue_tier: str = "standard",
    pov: bool = False,
    video_style: str = "",
    lora_triggers: str = "",
    base: Iterable[str] | None = None,
) -> list[str]:
    """Merge user chips with context-required questions."""
    chips = list(base) if base is not None else list(DEFAULT_CHIPS)
    seen = set(chips)
    def add(cid: str):
        if cid in CHECK_CATALOG and cid not in seen:
            chips.append(cid)
            seen.add(cid)

    if (mode or "").lower() == "i2v":
        add("i2v_lock")
    tier = (dialogue_tier or "standard").lower()
    if tier in ("none", "silent", "off"):
        add("silent_ok")
        # talk_floor is wrong for silent
        chips = [c for c in chips if c != "talk_floor"]
        seen.discard("talk_floor")
    elif tier in ("talkative", "chatty", "dense", "rich"):
        add("talk_floor")
    if pov:
        add("pov_clean")
    if lora_triggers and str(lora_triggers).strip():
        add("hard_triggers")
    vs = (video_style or "").lower()
    if "gravure" in vs:
        add("camera_alive")
        add("gravure_voice")
    return chips


def _truthy(v, default=False) -> bool:
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() not in ("0", "false", "off", "no", "")


def is_self_check_on(body: dict) -> bool:
    return _truthy(body.get("self_check", body.get("selfcheck")), default=False)


def self_check_mode(body: dict) -> str:
    m = str(body.get("self_check_mode") or body.get("selfcheck_mode") or "fix").lower().strip()
    return "report" if m in ("report", "report_only", "qa", "check") else "fix"


def resolve_chips(body: dict, **ctx) -> list[str]:
    base = parse_chip_list(body.get("self_check_chips") or body.get("selfcheck_chips"))
    return auto_chips(
        mode=ctx.get("mode") or body.get("video_mode") or "t2v",
        dialogue_tier=ctx.get("dialogue_tier") or body.get("dialogue_tier") or "standard",
        pov=bool(ctx.get("pov") if ctx.get("pov") is not None else body.get("pov")),
        video_style=ctx.get("video_style") or body.get("video_style") or body.get("style") or "",
        lora_triggers=ctx.get("lora_triggers") or body.get("lora_triggers") or "",
        base=base,
    )


def build_self_check_messages(
    *,
    script: str,
    intent: str,
    chips: list[str],
    mode: str = "t2v",
    dialogue_tier: str = "standard",
    pov: bool = False,
    lora_triggers: str = "",
    fix: bool = True,
) -> list[dict]:
    """Build a short system+user for the QA pass (not the full brain doctrine)."""
    questions = []
    for i, cid in enumerate(chips, 1):
        meta = CHECK_CATALOG.get(cid)
        if not meta:
            continue
        questions.append(f"{i}. [{cid}] {meta['q']}")

    q_block = "\n".join(questions) if questions else "1. [intent_beats] Does the script match the intent?"

    system = (
        "You are a ruthless LTX shot-script QA editor. "
        "Read the DRAFT script and answer ONLY the checklist questions.\n"
        "Rules:\n"
        "• Be concrete — cite what's missing (e.g. 'only 2 quoted lines', 'no roof break').\n"
        "• Do NOT invent praise. FAIL when unsure.\n"
        "• Keep I2V honesty, head+torso units, blank-line sections if you rewrite.\n"
        "• Never add meta speech about cameras/cuts/clips inside dialogue.\n"
        "• Never dump 'LoRA triggers:' as prose.\n"
    )
    if fix:
        system += (
            "OUTPUT FORMAT (exact):\n"
            "1) One line per checklist item: PASS|FAIL|SKIP · id · short reason\n"
            "2) A line with only: ---SCRIPT---\n"
            "3) The FULL revised shot script (all sections). "
            "If everything PASSed, repeat the draft unchanged after ---SCRIPT---.\n"
            "Fix every FAIL. Do not shrink the script into a summary.\n"
        )
    else:
        system += (
            "OUTPUT FORMAT (exact):\n"
            "One line per checklist item: PASS|FAIL|SKIP · id · short reason\n"
            "Do NOT rewrite the script. No ---SCRIPT--- block.\n"
        )

    user = (
        f"MODE: {mode} · DIALOGUE TIER: {dialogue_tier} · POV: {bool(pov)}\n"
        f"LORA TRIGGERS: {(lora_triggers or '').strip() or '(none)'}\n\n"
        f"USER INTENT:\n{(intent or '').strip()}\n\n"
        f"CHECKLIST:\n{q_block}\n\n"
        f"DRAFT SCRIPT:\n{(script or '').strip()}\n"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


_LINE_RE = re.compile(
    r"^\s*(PASS|FAIL|SKIP)\s*[·|:.\-–—]\s*([a-z0-9_]+)\s*[·|:.\-–—]?\s*(.*)$",
    re.I,
)


def parse_self_check_response(text: str, *, fix: bool = True) -> dict:
    """Parse model QA response into verdicts + optional revised script."""
    raw = (text or "").strip()
    script_part = ""
    report_part = raw
    if fix and "---SCRIPT---" in raw:
        report_part, script_part = raw.split("---SCRIPT---", 1)
        script_part = script_part.strip()
        # drop markdown fences if model wraps
        script_part = re.sub(r"^```\w*\s*", "", script_part)
        script_part = re.sub(r"\s*```\s*$", "", script_part).strip()

    verdicts = []
    fails = []
    for line in report_part.splitlines():
        m = _LINE_RE.match(line.strip())
        if not m:
            continue
        status = m.group(1).upper()
        cid = m.group(2).lower()
        reason = (m.group(3) or "").strip()
        row = {"id": cid, "status": status, "reason": reason}
        verdicts.append(row)
        if status == "FAIL":
            fails.append(row)

    summary = ", ".join(
        f"{v['id']}:{v['status']}" + (f"({v['reason'][:40]})" if v.get("reason") and v["status"] == "FAIL" else "")
        for v in verdicts
    ) or "no structured verdicts"

    return {
        "verdicts": verdicts,
        "fails": fails,
        "fail_count": len(fails),
        "pass_count": sum(1 for v in verdicts if v["status"] == "PASS"),
        "summary": summary,
        "revised": script_part,
        "raw": raw,
    }


def format_status(result: dict, *, fixed: bool, elapsed_s: float | None = None) -> str:
    n_fail = result.get("fail_count") or 0
    n_pass = result.get("pass_count") or 0
    bits = [f"Self-check {n_pass} pass / {n_fail} fail"]
    if fixed and n_fail:
        bits.append("fixed → committed")
    elif fixed and not n_fail:
        bits.append("clean")
    elif not fixed:
        bits.append("report only")
    if elapsed_s is not None:
        bits.append(f"+{elapsed_s:.1f}s")
    # first fail reason for glance
    fails = result.get("fails") or []
    if fails:
        f0 = fails[0]
        bits.append(f"{f0.get('id')}: {(f0.get('reason') or 'fail')[:48]}")
    return " · ".join(bits)


def catalog_for_ui() -> list[dict]:
    """Chip metadata for the settings panel / optional API."""
    return [
        {"id": cid, "label": meta["label"], "q": meta["q"]}
        for cid, meta in CHECK_CATALOG.items()
    ]
