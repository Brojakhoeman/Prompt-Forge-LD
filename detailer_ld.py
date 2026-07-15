# -*- coding: utf-8 -*-
"""
detailer_ld.py — DETAIL BOOST for PromptForge LD (optional, default OFF → "")

When ON, this is HARD doctrine (not a soft suggestion):
  • After the main motion in most sections, add ONE concrete visual clause
  • Lighting continuity + skin/fabric texture (LTX is literal — unwritten = flat plastic)
  • Still CANON: mechanism first; never stack micro-detail lists

I2V: also re-state one start-image skin/hair cue early so the video model does not wash it out.
"""

from __future__ import annotations

_NONE_KEYS = ("", "off", "none", "false", "0", "no")


def is_detailer_on(flag) -> bool:
    if flag is True or flag == 1:
        return True
    if isinstance(flag, str):
        return flag.strip().lower() not in _NONE_KEYS
    return bool(flag)


def detailer_remember_line(flag=False, mode: str = "t2v") -> str:
    """One bullet for the user REMEMBER list (high attention)."""
    if not is_detailer_on(flag):
        return ""
    i2v = (mode or "t2v").lower() == "i2v"
    base = (
        "• DETAILER ON (mandatory): after the main motion in MOST sections, add ONE short visual clause — "
        "light on skin/fabric, a material texture, a specular/sweat catch, or a shadow edge. "
        "Pattern: [motion]. [one detail]. Never list pores+freckles+weave in the same sentence. "
        "At least ~half of action sections need that second clause."
    )
    if i2v:
        base += (
            " I2V: open with skin tone/hair colour from the still; no plastic beauty-filter skin; "
            "no inventing freckles/scars not in the frame."
        )
    return base


def detailer_block(flag=False, mode: str = "t2v") -> str:
    """Return doctrine text or '' when off."""
    if not is_detailer_on(flag):
        return ""

    m = (mode or "t2v").lower()
    i2v = m == "i2v"

    parts = [
        "━━ DETAILER BOOST — ON (MANDATORY WHILE CHECKED) ━━\n"
        "This is NOT optional flavour. LTX is literal: plastic-smooth skin and missing light = what you get "
        "if you only write motion. CANON still wins (mechanism first, no banned verbs, no vibe-paint stacks).\n"
        "\n"
        "HARD FORMAT — most blank-line sections:\n"
        "  1) Main motion (mechanism) — required.\n"
        "  2) ONE new visual detail clause — required on ~half or more of sections "
        "(after the motion, same section or trailing sentence).\n"
        "  3) Optional spoken line — if dialogue is on.\n"
        "\n"
        "ALLOWED DETAIL TYPES (pick ONE per section):\n"
        "  • LIGHT: how a practical hits skin/fabric (overhead gym fluorescent on shoulder, window skim on cheek, "
        "rim on hip, lamp warmth on collarbone).\n"
        "  • SKIN: natural read only — subsurface warmth, sweat sheen, tanned tone already established, "
        "soft shadow under breast/jaw. No beauty-filter plastic. No pore-spam lists.\n"
        "  • FABRIC / MATERIAL: jersey grain, elastic band dig, matte sports-bra fabric, leather catch, lace edge — "
        "when clothing is the action.\n"
        "  • SPACE: mat texture, metal rack edge, floor reflection — one prop material if it grounds the frame.\n"
        "\n"
        "QUOTA (fail if missed):\n"
        "  • At least half of action sections include a detail clause (light / skin / fabric / space).\n"
        "  • Name the light source family once early, then re-use it (same gym overheads / same window) — continuity.\n"
        "  • Never dump 3+ texture words in one clause.\n"
        "\n"
        "GOOD (motion + one detail):\n"
        "  She arches her lower back toward the lens. Cool fluorescent light skims sweat on her lower back.\n"
        "  She pulls the sports bra up over her ribs. Matte black jersey bunches at her sternum.\n"
        "  She stands tall, chest bare. Overhead light pools on her collarbones.\n"
        "\n"
        "BAD (no detail — motion only forever):\n"
        "  She turns. She pulls the bra. She stands.\n"
        "BAD (spam):\n"
        "  She turns, freckles, pores, peach fuzz, oil, five highlights, lace weave…\n"
        "\n"
        "STILL HONOUR CANON: mechanism first; head+torso together; no snaps/suddenly/twists.\n"
        "NEVER add a face/eye detail that implies a head-only turn — if the face turns to the lens, "
        "the upper body turns with it in the same section.\n"
    ]
    if i2v:
        parts.append(
            "\n"
            "I2V START-IMAGE FIDELITY (Detailer reinforces):\n"
            "  First action section: restate one skin/hair cue from the still (tone, hair colour, "
            "visible freckles only if present). Keep that cue consistent — LTX loves washing skin flat.\n"
            "  Do not invent ethnicity, scars, or plastic gloss over the frame.\n"
            "  Restraints: only if in still or ENTER from edge before they limit motion.\n"
        )
    return "".join(parts)
