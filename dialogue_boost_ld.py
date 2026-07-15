"""
dialogue_boost_ld.py — Extra verbatim lines merged into REGISTERS at import.

Only activated registers inject, so a huge bank never bloats every prompt.
Goal: kill repetitive dialogue by giving the model a wide sample per mood.
"""

from __future__ import annotations

# Extra clean + explicit lines per register key
EXTRA = {
    "soft_intimate": {
        "clean": [
            "don't rush this", "i like you here", "stay a little longer",
            "your hands are warm", "say that again", "i'm right here",
            "let me hear you breathe", "softer", "that", "yes — that",
            "keep your eyes on me", "i'm not going anywhere", "come closer still",
            "you can take your time", "this is enough", "just us two",
            "tell me what you need", "i've got you", "easy, baby",
            "don't hide your face", "let me see you", "one more minute",
            "the light on you", "your pulse under my thumb", "shh, listen",
            "we don't need to hurry", "hold my wrist", "match my breath",
            "there — perfect", "again, slow", "i want this quiet",
        ],
        "explicit": [
            "i want you inside the quiet", "slow — fill me slow",
            "keep it deep and still", "don't pull away yet",
            "feel how wet i am for you", "stay in me",
            "make it last", "i can take more if you go gentle",
            "your cock fits like that", "breathe with me while you move",
            "kiss me while you're in", "don't stop looking at me",
        ],
    },
    "asmr": {
        "clean": [
            "tip your chin up for me", "soft shoulders", "unclench your jaw",
            "listen to the brush", "slow blink", "that's it, soften",
            "count with me — one… two…", "the room can wait",
            "feel the air on your neck", "let your hands go heavy",
            "mm, good", "almost a whisper now", "stay in this quiet",
            "i'm not going anywhere", "follow my voice only",
            "drop your shoulders another inch", "the next breath longer",
            "no rush in the whole world", "you did that perfectly",
            "again, even softer", "let the sound sit", "eyes half closed",
            "i'll stay right here", "nothing sharp, nothing loud",
            "sink into the chair", "let the day fall off",
        ],
        "explicit": [
            "good — just like that for me", "let me hear that little sound",
            "soft for me", "you sound so pretty like this",
            "keep breathing while i touch you", "quiet moans only",
            "that's my gentle one", "shhh, take it soft",
        ],
    },
    "dirty_talk": {
        "clean": [
            "look what you do to me", "don't play innocent",
            "say it out loud", "you want this", "come on, admit it",
            "filthy mind, clean hands — for now", "tell me the bad idea",
            "we shouldn't — say it anyway", "god, your mouth",
            "keep talking like that", "say my name dirtier",
            "you like when i talk", "don't get shy now",
            "make me believe you", "worse — say worse",
        ],
        "explicit": [
            "take this cock", "your pussy's soaked", "fuck, you're tight",
            "swallow it", "tongue out", "ride it properly",
            "don't you dare clench and run", "spit on it",
            "watch it disappear", "that's it — take every inch",
            "your cunt grips me", "beg with better words",
            "i'm going to ruin this hole", "open wider",
            "fuck yourself back onto me", "say you want to be used",
            "good — choke on it", "dripping down your thigh",
            "hold still while i breed you", "tell me how full you are",
            "messy, louder", "look at that cream", "who owns this",
            "say cock", "say pussy", "say fuck me properly",
            "i want it dripping", "knees wider", "arch — take it deeper",
            "don't wipe it off", "keep it in", "again — filthier",
        ],
    },
    "dominant": {
        "clean": [
            "eyes on me", "knees", "still", "now", "good",
            "don't make me repeat it", "hands where i can see them",
            "ask properly", "louder", "again", "wait",
            "you move when i say", "chin up", "stay",
            "that's better", "earn it", "count", "hold",
        ],
        "explicit": [
            "open your mouth", "take it", "swallow", "present",
            "ass up", "don't you come yet", "ask to come",
            "who does this belong to", "say please like you mean it",
            "good girl — take more", "good boy — hold still",
            "i decide the pace", "thank me", "again until i stop",
        ],
    },
    "submissive": {
        "clean": [
            "yes", "please", "i'll be good", "tell me what to do",
            "i'm listening", "whatever you want", "i won't move",
            "i'm yours for this", "show me", "i can take it",
            "don't stop guiding me", "i'll wait", "use my hands",
        ],
        "explicit": [
            "please fuck me", "i need it", "use me", "i'll be good for your cock",
            "please don't stop", "i can take more", "make me take it",
            "i'm so empty", "fill me", "tell me i'm yours",
            "i won't come until you say", "please — harder if you want",
        ],
    },
    "begging": {
        "clean": [
            "please don't go", "one more minute", "i need you here",
            "please look at me", "don't leave me like this",
            "i'm asking", "please", "please — again",
        ],
        "explicit": [
            "please fuck me", "please don't pull out", "please let me come",
            "i need your cock", "please use my mouth", "please — deeper",
            "i'm begging", "please wreck me", "don't stop i'll do anything",
        ],
    },
    "praise": {
        "clean": [
            "you're doing so well", "that's perfect", "proud of you",
            "look at you", "beautiful work", "yes — exactly",
            "keep going, you've got this", "so good for me",
            "i love how you listen", "that's my favourite",
        ],
        "explicit": [
            "good girl taking it", "good boy — just like that",
            "you take cock so well", "pretty when you moan",
            "such a good mouth", "perfect cunt", "you were made for this",
        ],
    },
    "degradation": {
        "clean": [
            "pathetic", "look at the state of you", "desperate already",
            "you can't hide it", "messy", "needy little thing",
        ],
        "explicit": [
            "filthy slut", "pathetic whore", "cock-drunk already",
            "useless until you're full", "dumb for it", "dirty little hole",
            "say you're a slut", "you look better ruined",
            "that's all you're good for", "take it like the whore you are",
        ],
    },
    "playful": {
        "clean": [
            "oh we're doing this", "don't smile at me like that",
            "trouble", "you started it", "prove it", "dare you",
            "make me", "is that your best line", "okay hotshot",
            "try again", "cute", "absolute menace", "come on then",
            "i'll race you", "last one there's a coward", "bet",
            "you wish", "say that to my face", "oh it's on",
        ],
        "explicit": [
            "bet you can't last", "talk big for someone this hard",
            "make me soak through", "catch me then fuck me",
        ],
    },
    "seductive": {
        "clean": [
            "come here", "i saved you a seat", "closer", "stay in my space",
            "you smell like trouble", "one drink", "don't look away",
            "i've been thinking about this all day", "take your coat off",
            "the night's young", "tell me a secret", "lips only",
            "slow dance energy", "my place is closer", "keys are already out",
        ],
        "explicit": [
            "i'm not wearing much under this", "touch me under the table",
            "i want your mouth first", "fuck me like you mean the stare",
        ],
    },
    "casual": {
        "clean": [
            "you get that email", "traffic was mental", "coffee or tea",
            "i'm starving", "pass me that", "what time is it",
            "did you lock the door", "same as last week honestly",
            "nah i'm good", "wait, say that again", "true though",
            "i'll text you the address", "we should head soon",
            "this place is loud", "my phone's dying", "hold my bag a sec",
            "you look wrecked — in a good way", "long day",
            "i'll drive", "your call", "fair", "okay but one condition",
            "don't leave without me", "i already ordered", "split it",
            "remind me tomorrow", "i forgot the name", "that tracks",
            "wild", "no notes", "we can do better than this bar",
        ],
    },
    "greeting": {
        "clean": [
            "hey", "there you are", "missed your face", "hi stranger",
            "look who showed up", "come in, it's freezing", "you made it",
            "hey — over here", "long time", "good to see you",
            "don't just stand there", "shoes off if you want",
            "i saved you a seat", "traffic okay", "you look well",
        ],
    },
    "phone_call": {
        "clean": [
            "can you hear me", "you're breaking up", "say that again",
            "i'm on the street", "hold on — crosswalk", "no i haven't left yet",
            "tell them i'll be ten minutes", "don't hang up",
            "i'm putting you on speaker", "the signal's trash here",
            "okay go — i'm listening", "that was out of line and you know it",
            "we are not doing this over text", "i'll call you back from outside",
            "keys, wallet, phone — i've got them", "the gate's boarding",
            "i love you, i've got to go", "this is the last time i'm explaining",
        ],
    },
    "comfort": {
        "clean": [
            "i'm here", "breathe", "you're safe", "it's okay to be mad",
            "you don't have to fix it tonight", "lean on me",
            "we can sit in silence", "i've got tissues", "water?",
            "none of that was your fault", "come here", "slow down with me",
            "you did enough today", "let them wait", "i'm not going anywhere",
        ],
    },
    "excited": {
        "clean": [
            "no way", "are you serious", "shut up — really",
            "this is huge", "i knew it", "tell me everything",
            "we have to celebrate", "i'm actually shaking",
            "say it again", "screenshots or it didn't happen",
            "i called it", "this changes the whole week",
        ],
    },
    "annoyed": {
        "clean": [
            "are you kidding me", "not now", "i heard you the first time",
            "that's not what i said", "don't start", "unbelievable",
            "pick a lane", "i'm done repeating myself", "move",
            "you're late and you're loud", "seriously", "enough",
        ],
    },
    "confrontation": {
        "clean": [
            "say it to my face", "you don't get to rewrite that",
            "i saw the message", "don't lie to me", "own it",
            "that cost us", "you knew and you still did it",
            "we're not okay", "look at me when you answer",
            "keys. now.", "you don't live here like that anymore",
            "explain the charge", "who was she", "who was he",
            "i'm not calming down until you answer",
        ],
    },
    "focused": {
        "clean": [
            "brace", "breathe out on the push", "one more",
            "eyes on the bolt", "steady", "don't rush the torque",
            "hold that angle", "reset your feet", "again clean",
            "watch the gauge", "left a quarter turn", "good — lock it",
            "timer starts now", "quiet, i'm counting", "stay with the beat",
        ],
    },
}


ACT_EXTRA = {
    "blowjob": {
        "giver_anticipation": [
            "let me get it wet first", "i want to taste the tip",
            "hands behind your back", "i'll take it slow then mean",
            "don't finish in my mouth unless i say", "look at me while i open up",
            "i've been thinking about choking on it", "spit or swallow — your call later",
        ],
        "receiver": [
            "cheeks hollow", "watch the teeth", "slower — then deeper",
            "hands on my thighs", "that's a good mouth", "breathe through your nose",
            "hold it there", "again from the tip", "fuck — your tongue",
            "don't you dare stop now", "messier", "show me",
        ],
    },
    "cunnilingus": {
        "receiver": [
            "flat tongue", "don't tease the edge only", "two fingers — no, mouth",
            "right there stay", "circle — yes", "i'm close don't you dare stop",
            "slow then mean", "look up at me", "hold my hips down",
            "again that exact spot", "i can feel it building",
        ],
    },
    "penetration_giver": {
        "giver": [
            "take the stretch", "heels on me", "don't run up the bed",
            "feel that", "mine", "count the strokes", "look at us",
            "grip the sheets", "you asked for hard", "stay open",
            "good — take the base", "again", "don't clench and hide",
        ],
        "receiver": [
            "fill me", "don't you pull out", "deeper angle", "there — fuck",
            "i can take it", "harder if you want", "use me",
            "i'm so full", "keep me there", "please don't stop the rhythm",
        ],
    },
}


def apply(registers: dict, act_registers: dict | None = None) -> None:
    """Merge EXTRA into REGISTERS / ACT_REGISTERS in place (de-dupe)."""
    for key, blob in EXTRA.items():
        if key not in registers:
            continue
        reg = registers[key]
        for field in ("clean", "explicit", "adlibs"):
            extra_lines = blob.get(field) or []
            if not extra_lines:
                continue
            base = list(reg.get(field) or [])
            seen = set(base)
            for ln in extra_lines:
                if ln not in seen:
                    base.append(ln)
                    seen.add(ln)
            reg[field] = base

    if act_registers:
        for key, blob in ACT_EXTRA.items():
            if key not in act_registers:
                continue
            act = act_registers[key]
            for field, extra_lines in blob.items():
                base = list(act.get(field) or [])
                seen = set(base)
                for ln in extra_lines:
                    if ln not in seen:
                        base.append(ln)
                        seen.add(ln)
                act[field] = base
