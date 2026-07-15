"""
Generation core — one streaming path, backend-agnostic.

Generate → stream → CANON scrub → done.
Optional refine path revises a prior script without rebuilding the world.
keep_warm skips VRAM free so rapid iterate stays fast.
"""

from __future__ import annotations

import asyncio
import json
import os
import random
import re
import time

try:
    from . import brain_ld as brain
    from . import llama_manager as llm
    from .inject_ld import (
        env_block, scenario_block as scn_block, scenario_forces_explicit, resolve_env_key,
    )
    from .scenarios_ld import resolve_scenario_key
    from .camera_ld import bolt as camera_bolt
    from .music_ld import music_block
    from .styles_ld import style_block as build_style_block, style_forces_explicit
    from .llm_boot import ThinkFilter, boot_llama
    from .vram import flush_vram
except ImportError:
    import brain_ld as brain
    import llama_manager as llm
    from inject_ld import (
        env_block, scenario_block as scn_block, scenario_forces_explicit, resolve_env_key,
    )
    from scenarios_ld import resolve_scenario_key
    from camera_ld import bolt as camera_bolt
    from music_ld import music_block
    from styles_ld import style_block as build_style_block, style_forces_explicit
    from llm_boot import ThinkFilter, boot_llama
    from vram import flush_vram


# Word-boundary explicit cues (avoid "class"/"title"/"sextant" false positives)
_EXPLICIT_RE = re.compile(
    r"(?i)(?<![a-z])("
    r"fuck\w*|cock|dicks?|puss(?:y|ies)|cunt|cum(?:ming|s)?|"
    r"blowjobs?|handjobs?|titfuck\w*|anal|penetrat\w*|thrust\w*|"
    r"orgasm\w*|nipples?|nude|naked|nsfw|erotic|"
    r"slut\w*|whore\w*|breed(?:ing|s)?|creampie|deepthroat\w*|"
    r"missionary|doggy|cowgirl|rimjobs?|facesit\w*|"
    r"sex(?:y|ual|ing)?|porn|xxx"
    r")(?![a-z])"
)

# Separate short tokens that need careful matching
_EXPLICIT_SHORT = re.compile(
    r"(?i)(?<![a-z])(ass|tits?|boobs?|suck(?:s|ing)?|ride|riding|daddy)(?![a-z])"
)
# "ass" only when sexual context nearby
_ASS_CONTEXT = re.compile(
    r"(?i)(ass|butt|booty).{0,24}(fuck|spank|grab|slap|spread|cheek|hole)|"
    r"(fuck|spank|grab|slap|spread).{0,24}(ass|butt|booty)"
)


def _infer_explicit(text: str) -> bool:
    t = text or ""
    if _EXPLICIT_RE.search(t):
        return True
    if _ASS_CONTEXT.search(t):
        return True
    # "suck" / "ride" alone are weak — need intimacy neighbors
    if re.search(r"(?i)(?<![a-z])(suck|ride|riding)(?![a-z])", t):
        if re.search(r"(?i)(cock|dick|pussy|him|her|me|you|hard|slow)", t):
            return True
    if re.search(r"(?i)(?<![a-z])(tits?|boobs?|daddy)(?![a-z])", t):
        return True
    return False


def _skip_flush(body):
    return (
        bool(body.get("skip_flush"))
        or bool(body.get("keep_warm"))
        or os.environ.get("PFLD_TEST") == "1"
    )


def _keep_llm(body):
    """If true, do not free/kill the LLM after generate."""
    return bool(body.get("keep_warm")) or os.environ.get("PFLD_KEEP_WARM") == "1"


async def generate_prompt(body: dict, *, on_event=None) -> dict:
    t0 = time.time()

    async def emit(ev):
        if on_event:
            await on_event(ev)

    model_file = body.get("model_file", "None")
    mmproj_file = body.get("mmproj_file", "None (text-only)")
    mode = body.get("video_mode", "i2v")
    # User-facing duration (UI/wire). Internal write is -2s (hidden end-buffer).
    user_duration_s = float(body.get("duration_s", 12))
    write_dur = brain.write_duration_s(user_duration_s)
    intent = (body.get("user_intent") or "").strip()
    image_b64 = body.get("image_b64", "")
    pov = bool(body.get("pov", False))
    pov_gender = body.get("pov_gender", "female")
    cast = (body.get("cast") or "pair").lower()
    if cast not in ("solo", "pair", "group"):
        cast = "pair"
    lead_gender = body.get("lead_gender") or "auto"
    accent_mode = body.get("accent_mode") or "auto"
    accent_partner = body.get("accent_partner") or "off"
    video_style = body.get("video_style") or body.get("style") or "None — off (no style path)"
    continuity_state = (body.get("continuity_state") or "").strip()
    environment_raw = body.get("environment", "None — LLM decides")
    scenario_raw = body.get("scenario", "None — your words decide")
    dialogue_tier = body.get("dialogue_tier", "standard")
    music_key = body.get("music", "") or ""
    music_txt = music_block(music_key)
    # Dual intensity axes (qualitative). Legacy intensity 1–10 still accepted.
    motion_level = body.get("motion_level") or body.get("body_intensity")
    mouth_heat = body.get("mouth_heat") or body.get("mouth_level")
    energy_raw = body.get("intensity", body.get("energy", 5))
    try:
        energy = int(energy_raw)
    except (TypeError, ValueError):
        energy = energy_raw  # may be "normal" / "soft" etc.
    talkative = (dialogue_tier or "").lower() in ("talkative", "chatty", "dense", "rich")
    refine = bool(body.get("refine")) and bool((body.get("prior_prompt") or "").strip())
    prior = body.get("prior_prompt", "")
    temperature = float(body.get("temperature", 0.6))
    if refine:
        temperature = min(temperature, 0.45)
    # One seed for this generate: LLM sampler + dialogue/accent banks + RANDOM scenario/env
    try:
        seed = int(body.get("seed")) if body.get("seed") is not None and str(body.get("seed")).strip() != "" else None
    except (TypeError, ValueError):
        seed = None
    if seed is None or seed < 0:
        seed = random.randint(0, 2**31 - 1)
    seed = int(seed) & 0x7FFFFFFF
    # Resolve RANDOM picks once so explicit-gate, blocks, and UI status agree
    environment = resolve_env_key(environment_raw, seed=seed)
    scenario = resolve_scenario_key(scenario_raw, seed=seed, mode=mode)
    explicit = (
        _infer_explicit(intent)
        or scenario_forces_explicit(scenario, seed=seed, mode=mode)
        or style_forces_explicit(video_style)
    )
    # Style after seed so Gravure can stamp seed-picked Asian accent lock
    style_blk = build_style_block(
        video_style, mode=mode, intent=intent,
        music_key=music_key, music_text=music_txt,
        seed=seed, accent_hint=body.get("accent_mode") or "",
    )
    skip_flush = _skip_flush(body)
    keep_warm = _keep_llm(body)

    if mode == "i2v" and not image_b64 and not (refine and prior):
        return {"error": "I2V needs an image", "elapsed_s": 0}
    if model_file == "None" and llm.is_managed():
        return {"error": "No model selected", "elapsed_s": 0}

    need_vision = mode == "i2v" and bool(image_b64)
    if need_vision and mmproj_file == "None (text-only)" and llm.is_managed():
        return {"error": "I2V needs an mmproj (vision) file", "elapsed_s": 0}

    status_log = []
    try:
        if not skip_flush:
            await emit({"type": "status", "msg": "Flushing VRAM…"})
            flush_vram("PromptForgeLD")
            await asyncio.sleep(0.15)

        async for st in boot_llama(model_file, mmproj_file, need_vision):
            if st.startswith("error:"):
                await emit({"type": "error", "msg": st[6:]})
                return {"error": st[6:], "status": status_log, "elapsed_s": time.time() - t0}
            status_log.append(st)
            await emit({"type": "status", "msg": st})

        tl = brain.timeline(write_dur)
        await emit({"type": "timeline", "beats": tl})

        # Tell the UI what Random resolved to (and seed)
        resolved_bits = []
        if str(scenario_raw) != str(scenario) and scenario:
            resolved_bits.append(f"scn→ {scenario}")
        if str(environment_raw) != str(environment) and environment:
            resolved_bits.append(f"env→ {environment}")
        if resolved_bits:
            await emit({"type": "status", "msg": " · ".join(resolved_bits)})

        system = brain.build_system(
            mode=mode, duration_s=write_dur, pov=pov, pov_gender=pov_gender,
            explicit=explicit, dialogue_tier=dialogue_tier, energy=energy, intent=intent,
            environment_block=env_block(environment, mode, seed=seed),
            scenario_block=scn_block(scenario, seed=seed, lead_gender=lead_gender, mode=mode),
            camera_block=camera_bolt(body.get("camera_move", "None"), pov=pov),
            music_block=music_txt,
            music_key=music_key or "",
            style_block=style_blk,
            seed=seed,
            cast=cast,
            continuity_state=continuity_state,
            lead_gender=lead_gender,
            accent_mode=accent_mode,
            accent_partner=accent_partner,
            motion_level=motion_level,
            mouth_heat=mouth_heat,
            detailer=body.get("detailer", False),
            video_style_key=video_style,
            lora_triggers=body.get("lora_triggers", "") or "",
            _duration_is_write=True,
        )
        messages = brain.build_messages(
            system, intent, write_dur, mode,
            image_b64=image_b64, has_vision=need_vision,
            prior=prior, refine=refine,
            dialogue_tier=dialogue_tier, pov=pov,
            cast=cast, continuity_state=continuity_state,
            accent_mode=accent_mode, energy=energy,
            motion_level=motion_level, mouth_heat=mouth_heat,
            accent_partner=accent_partner,
            detailer=body.get("detailer", False),
            lora_triggers=body.get("lora_triggers", "") or "",
            seed=seed,
            _duration_is_write=True,
        )

        model_id = llm.conn_model()
        family = llm.detect_model_family(model_id)
        await emit({
            "type": "status",
            "msg": (
                ("Revising" if refine else "Writing")
                + f" script… · seed {seed}"
                + (f" · {family}" if family != "other" else "")
                + (" · thinking off" if family == "qwen" else "")
            ),
        })
        import aiohttp
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": brain.max_tokens(write_dur, mode, pov, talkative, _duration_is_write=True),
            "stream": True,
            "seed": seed,
        }
        if not llm.is_managed():
            payload["ttl"] = 300 if keep_warm else 30
        url = llm.conn_url().rstrip("/") + "/v1/chat/completions"

        tfilter = ThinkFilter()
        acc = []
        last_err = None
        # Qwen: force enable_thinking false first; Gemma/others: try then fall back
        attempts = llm.chat_request_attempts(model_id)
        async with aiohttp.ClientSession() as sess:
            for attempt, extra in enumerate(attempts):
                async with sess.post(url, json={**payload, **extra}) as resp:
                    if resp.status != 200:
                        txt = await resp.text()
                        last_err = f"LLM HTTP {resp.status}: {txt[:300]}"
                        if attempt < len(attempts) - 1 and resp.status == 400:
                            continue
                        await emit({"type": "error", "msg": last_err})
                        return {
                            "error": last_err, "status": status_log,
                            "elapsed_s": time.time() - t0,
                        }
                    async for raw in resp.content:
                        line = raw.decode("utf-8", errors="ignore").strip()
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                        except Exception:
                            continue
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        text = delta.get("content", "") or delta.get("reasoning_content", "")
                        if text:
                            cc = tfilter.feed(text)
                            if cc:
                                acc.append(cc)
                                await emit({"type": "delta", "text": cc})
                    tail = tfilter.flush()
                    if tail:
                        acc.append(tail)
                        await emit({"type": "delta", "text": tail})
                    break

        raw_full = brain.clean("".join(acc))
        # repair (default on): CANON scrub. Off = leave model text (after think-strip only).
        do_repair = body.get("repair", body.get("post_repair", True))
        if isinstance(do_repair, str):
            do_repair = do_repair.strip().lower() not in ("0", "false", "off", "no", "")
        do_repair = bool(do_repair)
        full = brain.finalize(
            raw_full, mode=mode, intent=intent, pov=pov, scenario=scenario,
            dialogue_tier=dialogue_tier, repair=do_repair,
        )
        # Guarantee LoRA activation tokens appear in the pack positive
        try:
            from .lora_triggers_ld import ensure_triggers_in_script
        except ImportError:
            from lora_triggers_ld import ensure_triggers_in_script
        full = ensure_triggers_in_script(full, body.get("lora_triggers", "") or "")
        if not full:
            await emit({"type": "error", "msg": "Empty response"})
            return {
                "error": "Empty response", "status": status_log,
                "elapsed_s": time.time() - t0,
            }
        if do_repair and raw_full.strip() != full.strip():
            await emit({
                "type": "status",
                "msg": f"Post-repair scrub applied ({len(raw_full)} → {len(full)} chars)",
            })
        elif not do_repair:
            await emit({"type": "status", "msg": "Post-repair scrub OFF — raw model text kept"})

        # ── Talkative under-floor: one silent auto-refine to add lines ──────
        # Grok density: if free mouths under-wrote, push once without user seeing.
        # NEVER densify by packing dialogue into oral/occupied-mouth sections.
        retried = False
        if talkative and not refine and do_repair:
            n_spoken = len(re.findall(r'["\u201c][^"\u201d]+["\u201d]', full))
            min_lines = max(7, round(write_dur / 1.7))
            oral_blob = f"{intent or ''} {full or ''}".lower()
            oral_heavy = bool(re.search(
                r"\b(?:blowjob|deepthroat|bobs?|bobbing|sucks?|sucking|"
                r"cock in (?:her|his) mouth|mouths? (?:on|around|full)|"
                r"gags?|gagging|slurp|gluk|oral)\b",
                oral_blob,
            ))
            if n_spoken < min_lines:
                need = min_lines - n_spoken
                await emit({
                    "type": "status",
                    "msg": f"Talkative thin ({n_spoken}/{min_lines}) — densifying…",
                })
                # Wipe first-pass stream in the UI so densify doesn't append into it
                await emit({"type": "replace", "text": ""})
                oral_rule = ""
                if oral_heavy:
                    oral_rule = (
                        "ORAL / BUSY-MOUTH HARD RULE (overrides line-count pressure): "
                        "Do NOT add quoted dialogue for the person whose mouth is on cock/pussy/kiss mid-act. "
                        "Oral giver across the WHOLE oral sequence (including any brief pull-off for air): "
                        "at most 1–2 spoken words TOTAL — e.g. \"more\" / \"fuck\" / \"mm\" — never a full sentence. "
                        "Mid-bob/suck sections: wet throat noises only (*hmm* *mm* *gluk* gag slurp) — no quotes. "
                        "If they pull off mid-sequence, prefer breath + re-engage with ZERO words; "
                        "save real talk for AFTER the oral sequence fully ends (aftercare). "
                        "Meet the talk budget with FREE mouths only: partner lines"
                        + (", POV voice as SOUND from just behind the view" if pov else "")
                        + ", setup before oral, aftercare after oral ends. "
                        "Never pack giver-lines into bobbing sections. "
                        "If a section already has sucking/bobbing, add zero new on-screen speech for the busy mouth. "
                    )
                pov_rule = (
                    "POV mode is ON: keep Eye-level open. Two legal voices: "
                    "(1) on-screen 'She/He says (soft): \"…\"' ONLY when mouth is free "
                    "(2) unseen viewpoint as SOUND from just behind the view "
                    "(e.g. a low voice from just behind the view says (rough): \"yeah that's right\") — enrichment. "
                    if pov else
                    "This is NOT POV. Do NOT invent 'a low voice from just behind the view' or unseen viewpoint speech. "
                    "Only on-screen characters speak: She/He says (soft): \"…\". "
                )
                densify_intent = (
                    f"REFINE FOR DENSITY ONLY: the script is under-written on FREE-mouth dialogue. "
                    f"Add at least {need + 1} NEW unique spoken lines (quoted) tied to props/stakes "
                    f"from this scene — but ONLY where mouths are free. "
                    f"Keep identity, wardrobe, place, and section layout (including any HARD JUMP CUT structure). "
                    f"Kill any phrase loops. Never write I/me/my in prose"
                    + (" (except inside on-screen dialogue quotes)." if pov else ".")
                    + f" {pov_rule}"
                    f"{oral_rule}"
                    f"Mouth busy (sucking/sipping/kissing) = sounds only for that person. "
                    f"Hands never speak. Never bare (soft): \"…\" without a verb. "
                    f"Never write 'saying says' — use one speech verb only (says / murmurs / …). "
                    f"I2V: do not invent a new location or wardrobe not in the start image. "
                    f"Never meta speech about cuts/cameras. Output the FULL revised script only. "
                    f"Target AT LEAST {min_lines} total quoted spoken lines from free mouths"
                    + (" / POV voice." if pov else " only.")
                )
                densify_msgs = brain.build_messages(
                    system, densify_intent, write_dur, mode,
                    image_b64="" if not need_vision else image_b64,
                    has_vision=False,  # text densify is enough; keep fast
                    prior=full, refine=True,
                    dialogue_tier=dialogue_tier, pov=pov,
                    cast=cast, continuity_state=continuity_state,
                    accent_mode=accent_mode, energy=energy,
                    motion_level=motion_level, mouth_heat=mouth_heat,
                    accent_partner=accent_partner,
                    detailer=body.get("detailer", False),
                    lora_triggers=body.get("lora_triggers", "") or "",
                    _duration_is_write=True,
                )
                densify_payload = {
                    "model": model_id,
                    "messages": densify_msgs,
                    "temperature": min(0.7, temperature + 0.12),
                    "max_tokens": brain.max_tokens(
                        write_dur, mode, pov, talkative=True, _duration_is_write=True,
                    ),
                    "stream": True,
                    # Offset so densify rewrites, but stays reproducible from the same UI seed
                    "seed": (seed + 7919) & 0x7FFFFFFF,
                }
                # Same family tweaks as main generate (Qwen thinking off, etc.)
                densify_payload.update(llm.chat_request_extras(model_id))
                if not llm.is_managed():
                    densify_payload["ttl"] = 300 if keep_warm else 30
                acc2 = []
                tfilter2 = ThinkFilter()
                try:
                    async with aiohttp.ClientSession() as sess2:
                        async with sess2.post(url, json=densify_payload) as resp2:
                            if resp2.status == 200:
                                async for raw in resp2.content:
                                    line = raw.decode("utf-8", errors="ignore").strip()
                                    if not line.startswith("data:"):
                                        continue
                                    data = line[5:].strip()
                                    if data == "[DONE]":
                                        break
                                    try:
                                        chunk = json.loads(data)
                                    except Exception:
                                        continue
                                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                                    text = delta.get("content", "") or delta.get("reasoning_content", "")
                                    if text:
                                        cc = tfilter2.feed(text)
                                        if cc:
                                            acc2.append(cc)
                                            await emit({"type": "delta", "text": cc})
                                tail = tfilter2.flush()
                                if tail:
                                    acc2.append(tail)
                                    await emit({"type": "delta", "text": tail})
                                densified = brain.finalize(
                                    "".join(acc2), mode=mode, intent=intent, pov=pov,
                                    scenario=scenario, dialogue_tier=dialogue_tier,
                                    repair=do_repair,
                                )
                                densified = ensure_triggers_in_script(
                                    densified, body.get("lora_triggers", "") or "",
                                )
                                n2 = len(re.findall(r'["\u201c][^"\u201d]+["\u201d]', densified or ""))
                                # Keep densified only if it actually improved spoken count
                                # and did not destroy JUMP hard-cut structure when present
                                jump_ok = True
                                scn = (body.get("scenario") or "")
                                if "jump" in scn.lower() or "⚡" in scn:
                                    had_cut = bool(re.search(
                                        r"\bhard cut\b|\bjump cut\b|clothes gone|now naked|"
                                        r"instant cut|hard-cut",
                                        full or "", re.I,
                                    ))
                                    still_cut = bool(re.search(
                                        r"\bhard cut\b|\bjump cut\b|clothes gone|now naked|"
                                        r"instant cut|hard-cut",
                                        densified or "", re.I,
                                    ))
                                    # If original already had a cut mark, densify must keep one
                                    if had_cut and densified and not still_cut:
                                        jump_ok = False
                                if densified and n2 >= n_spoken and jump_ok:
                                    full = densified
                                    retried = True
                                    await emit({
                                        "type": "status",
                                        "msg": f"Densified {n_spoken}→{n2} spoken lines",
                                    })
                                elif densified and not jump_ok:
                                    await emit({
                                        "type": "status",
                                        "msg": "Densify discarded — JUMP cut structure lost",
                                    })
                except Exception as densify_err:
                    await emit({
                        "type": "status",
                        "msg": f"Densify skipped: {densify_err}",
                    })

        # ── Optional self-check (settings tick, default OFF) ────────────────
        # Model re-reads draft against user chips before the box commits.
        self_check_info = None
        try:
            from . import self_check_ld as sc
        except ImportError:
            import self_check_ld as sc
        if sc.is_self_check_on(body) and full and not refine:
            sc_mode = sc.self_check_mode(body)  # fix | report
            chips = sc.resolve_chips(
                body,
                mode=mode,
                dialogue_tier=dialogue_tier,
                pov=pov,
                video_style=video_style,
                lora_triggers=body.get("lora_triggers", "") or "",
            )
            await emit({
                "type": "status",
                "msg": f"Self-check ({sc_mode}) · {len(chips)} questions…",
            })
            sc_t0 = time.time()
            try:
                sc_msgs = sc.build_self_check_messages(
                    script=full,
                    intent=intent,
                    chips=chips,
                    mode=mode,
                    dialogue_tier=dialogue_tier,
                    pov=pov,
                    lora_triggers=body.get("lora_triggers", "") or "",
                    fix=(sc_mode == "fix"),
                )
                # Cap completion — report is short; fix needs full script room
                sc_max = 900 if sc_mode == "report" else min(
                    4500,
                    brain.max_tokens(write_dur, mode, pov, talkative, _duration_is_write=True),
                )
                sc_text = await asyncio.to_thread(
                    llm.chat,
                    sc_msgs,
                    temperature=0.25,
                    max_tokens=sc_max,
                    seed=(seed + 1337) & 0x7FFFFFFF,
                )
                parsed = sc.parse_self_check_response(sc_text, fix=(sc_mode == "fix"))
                sc_elapsed = round(time.time() - sc_t0, 2)
                fixed_ok = False
                if sc_mode == "fix" and (parsed.get("revised") or "").strip():
                    revised = brain.finalize(
                        parsed["revised"], mode=mode, intent=intent, pov=pov,
                        scenario=scenario, dialogue_tier=dialogue_tier,
                        repair=do_repair,
                    )
                    revised = ensure_triggers_in_script(
                        revised, body.get("lora_triggers", "") or "",
                    )
                    # Accept rewrite if non-empty and not collapsed
                    if revised and len(revised) >= max(80, int(len(full) * 0.45)):
                        if revised.strip() != full.strip():
                            await emit({"type": "replace", "text": ""})
                            # stream-ish: put final in one go via replace then done
                            full = revised
                            fixed_ok = True
                            await emit({"type": "delta", "text": full})
                        else:
                            fixed_ok = True  # clean pass-through
                self_check_info = {
                    "mode": sc_mode,
                    "chips": chips,
                    "verdicts": parsed.get("verdicts") or [],
                    "fails": parsed.get("fails") or [],
                    "fail_count": parsed.get("fail_count") or 0,
                    "pass_count": parsed.get("pass_count") or 0,
                    "summary": parsed.get("summary") or "",
                    "fixed": fixed_ok and sc_mode == "fix",
                    "elapsed_s": sc_elapsed,
                }
                await emit({
                    "type": "status",
                    "msg": sc.format_status(
                        parsed, fixed=bool(self_check_info["fixed"]), elapsed_s=sc_elapsed,
                    ),
                })
                await emit({"type": "self_check", **self_check_info})
            except Exception as sc_err:
                await emit({
                    "type": "status",
                    "msg": f"Self-check skipped: {sc_err}",
                })
                self_check_info = {"error": str(sc_err)}

        cont = brain.extract_continuity(full)
        elapsed = round(time.time() - t0, 2)
        await emit({
            "type": "done",
            "prompt": full,
            "raw_prompt": raw_full,
            "repaired": bool(do_repair and raw_full.strip() != (full or "").strip()),
            "repair": do_repair,
            "continuity": cont,
            "explicit": explicit,
            "chars": len(full),
            "elapsed_s": elapsed,
            "refined": refine or retried,
            "densified": retried,
            "self_check": self_check_info,
            "seed": seed,
            "resolved_scenario": scenario,
            "resolved_environment": environment,
            "scenario_raw": scenario_raw,
            "environment_raw": environment_raw,
        })
        return {
            "prompt": full,
            "raw_prompt": raw_full,
            "repaired": bool(do_repair and raw_full.strip() != (full or "").strip()),
            "repair": do_repair,
            "timeline": tl,
            "status": status_log,
            "elapsed_s": elapsed,
            "continuity": cont,
            "explicit": explicit,
            "densified": retried,
            "self_check": self_check_info,
            "seed": seed,
            "resolved_scenario": scenario,
            "resolved_environment": environment,
        }
    finally:
        if not skip_flush and not keep_warm:
            flush_vram("PromptForgeLD")


def assemble_preview(body: dict) -> dict:
    """Build the system + user messages without hitting the LLM."""
    mode = body.get("video_mode", "i2v")
    user_duration_s = float(body.get("duration_s", 12))
    write_dur = brain.write_duration_s(user_duration_s)
    intent = (body.get("user_intent") or "").strip()
    pov = bool(body.get("pov", False))
    cast = (body.get("cast") or "pair").lower()
    lead_gender = body.get("lead_gender") or "auto"
    accent_mode = body.get("accent_mode") or "auto"
    accent_partner = body.get("accent_partner") or "off"
    video_style = body.get("video_style") or body.get("style") or "None — off (no style path)"
    continuity_state = (body.get("continuity_state") or "").strip()
    dialogue_tier = body.get("dialogue_tier", "standard")
    talkative = (dialogue_tier or "").lower() in ("talkative", "chatty", "dense", "rich")
    motion_level = body.get("motion_level") or body.get("body_intensity")
    mouth_heat = body.get("mouth_heat") or body.get("mouth_level")
    energy_raw = body.get("intensity", body.get("energy", 5))
    try:
        energy = int(energy_raw)
    except (TypeError, ValueError):
        energy = energy_raw

    try:
        prev_seed = int(body.get("seed")) if body.get("seed") is not None and str(body.get("seed")).strip() != "" else 0
    except (TypeError, ValueError):
        prev_seed = 0
    prev_seed = int(prev_seed) & 0x7FFFFFFF
    env_key = resolve_env_key(body.get("environment", "None — LLM decides"), seed=prev_seed)
    scn_key = resolve_scenario_key(
        body.get("scenario", "None — your words decide"), seed=prev_seed, mode=mode,
    )
    explicit = (
        _infer_explicit(intent)
        or scenario_forces_explicit(scn_key, seed=prev_seed, mode=mode)
        or style_forces_explicit(video_style)
    )
    system = brain.build_system(
        mode=mode, duration_s=write_dur, pov=pov,
        pov_gender=body.get("pov_gender", "female"),
        explicit=explicit, dialogue_tier=dialogue_tier, intent=intent,
        energy=energy,
        environment_block=env_block(env_key, mode, seed=prev_seed),
        scenario_block=scn_block(
            scn_key,
            seed=prev_seed,
            lead_gender=lead_gender,
            mode=mode,
        ),
        camera_block=camera_bolt(
            body.get("camera_move", "None"), pov=bool(body.get("pov", False)),
        ),
        music_block=music_block(body.get("music", "")),
        music_key=body.get("music", "") or "",
        style_block=build_style_block(
            video_style, mode=mode, intent=intent,
            music_key=body.get("music", "") or "",
            music_text=music_block(body.get("music", "")),
            seed=prev_seed, accent_hint=accent_mode or "",
        ),
        cast=cast,
        continuity_state=continuity_state,
        lead_gender=lead_gender,
        accent_mode=accent_mode,
        accent_partner=accent_partner,
        motion_level=motion_level,
        mouth_heat=mouth_heat,
        detailer=body.get("detailer", False),
        video_style_key=video_style,
        lora_triggers=body.get("lora_triggers", "") or "",
        seed=prev_seed,
        _duration_is_write=True,
    )
    refine = bool(body.get("refine")) and bool((body.get("prior_prompt") or "").strip())
    if refine:
        user_text = (
            f"[REFINE MODE]\nRevision: {intent}\n\n"
            f"Prior script ({len(body.get('prior_prompt',''))} chars) will be sent."
        )
    else:
        user_text = brain.build_user(
            intent, write_dur, mode,
            dialogue_tier=dialogue_tier, pov=pov, cast=cast,
            continuity_state=continuity_state, accent_mode=accent_mode,
            energy=energy, motion_level=motion_level, mouth_heat=mouth_heat,
            accent_partner=accent_partner,
            detailer=body.get("detailer", False),
            lora_triggers=body.get("lora_triggers", "") or "",
            seed=prev_seed,
            _duration_is_write=True,
        )
    return {
        "ok": True,
        "system": system,
        "user_text": user_text,
        "timeline": brain.timeline(write_dur),
        "system_chars": len(system),
        "user_chars": len(user_text),
        "max_tokens": brain.max_tokens(write_dur, mode, pov, talkative, _duration_is_write=True),
        "explicit": explicit,
        "cast": cast,
        "user_duration_s": user_duration_s,
        "write_duration_s": write_dur,
        "seed": prev_seed,
        "resolved_scenario": scn_key,
        "resolved_environment": env_key,
        "talkative": talkative,
        "continuity": continuity_state[:200] if continuity_state else "",
    }
