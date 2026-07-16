"""
dialogue_ld.py — Dialogue register bank for PromptForge LD
==========================================================
A BACKGROUND ACTIVATION LAYER for spoken lines, built the same way as
scenarios_ld / environments_ld: the user's phrasing (plus the active scenario)
is scanned for cues, matching REGISTERS are activated, and a verbatim line pool
is injected into the system prompt so the LLM stops defaulting to the same
"don't look away" cliché.

Design decisions (locked with the user):
  • VERBATIM POOL — the model must pick actual lines from the activated pools,
    not paraphrase. Consistency + no repetition, because the pools are large.
  • EXPLICIT-GATED — each register can carry a CLEAN pool and an EXPLICIT pool.
    The explicit pool only appears when the node's explicit flag is set. No flag
    → clean lines only, even for a register like dirty_talk.
  • AD-LIBS — non-lexical vocalizations (moans, gasps, breaths, laughs, hums).
    Each register carries its own ad-lib flavour; a global pool backs them up.
    These are dropped BETWEEN and AROUND spoken lines so scenes breathe instead
    of being wall-to-wall talking.
  • EVERYDAY REGISTERS — the bank also covers non-adult clips (casual chat,
    greetings, phone calls, comfort, excitement, annoyance, etc.) so a normal
    scene gets natural speech too, not romance-by-default.

Mental model:  tier (how much) + registers (what kind) + pools (the words) + ad-libs (the breath)

The node calls dialogue_block(...) which returns the injected text (or "").
Adding lines is pure upside — only ACTIVATED registers are ever injected, so a
bigger bank never bloats an individual prompt.

Each register is a dict:
    name      — short human label
    delivery  — one line: HOW the voice sounds (feeds the emotion bracket)
    brackets  — emotion-bracket words appropriate to this register
    clean     — [verbatim lines usable at any explicitness]
    explicit  — [verbatim lines only shown when explicit is active]
    adlibs    — [non-lexical vocalizations for this register's mood]
    triggers  — [substrings in intent/scenario that activate it]
"""

import random
import re


def _trigger_hit(trig, blob):
    """Match a trigger against the blob. Triggers ending in a space (e.g. 'sub ')
    or containing spaces are matched loosely; bare word-stems use a left word
    boundary so 'brat' won't fire inside 'celebrates'. A trailing '*'-free stem
    still matches its inflections ('degrad' -> 'degrades', 'degrading')."""
    if " " in trig:
        return trig in blob
    # left boundary + stem; allows suffixes (degrad -> degrades)
    return re.search(r"(?<![a-z])" + re.escape(trig), blob) is not None

# ─────────────────────────────────────────────────────────────────────────────
#  GLOBAL AD-LIB POOL — generic vocalizations any register can borrow. Register
#  specific ad-libs (below) are preferred; these fill in.
# ─────────────────────────────────────────────────────────────────────────────
# Prose forms only — asterisk stage-directions make LTX draw garbage / subtitles.
_GLOBAL_ADLIBS = [
    "sharp inhale", "slow exhale", "soft hum", "quiet laugh",
    "breath catches", "sigh", "gasp", "swallows", "bites lip",
    "shaky breath", "low hum", "clears throat",
]

# ─────────────────────────────────────────────────────────────────────────────
#  REGISTERS
#  Lines stay SHORT (2–8 words). Each is a standalone utterance the model wraps
#  in an emotion bracket and drops inline where a section frees the mouth.
# ─────────────────────────────────────────────────────────────────────────────

REGISTERS = {

    # ══════════════════════════════════════════════════════════════════════
    #  ADULT / INTIMATE REGISTERS
    # ══════════════════════════════════════════════════════════════════════

    "soft_intimate": {
        "name": "Soft / intimate",
        "delivery": "close, low, unhurried — spoken almost into the mic, warmth over volume",
        "brackets": ["soft", "tender", "hushed", "warm", "barely above a whisper"],
        "clean": [
            "come here", "stay with me", "look at me", "don't move",
            "closer", "just like that", "i've got you", "right here",
            "slow down", "breathe", "you feel that?", "hold still",
            "keep looking at me", "there you are", "easy", "mine",
            "i'm not going anywhere", "stay", "let me look at you",
            "you're shaking", "don't hide", "i see you", "come back to me",
            "just us", "no one else", "feel me", "closer, come on",
            "i missed this", "don't let go", "hold onto me",
            "stay in this pocket of quiet",
            "i like us here",
            "no performance. just this.",
            "your pulse is loud",
            "let the world wait",
            "forehead to mine"
        ],
        "explicit": [
            "i want all of you", "let me feel you", "give me this",
            "you're perfect like this", "don't stop touching me",
            "slow and deep",
            "i want to feel every inch",
            "look at me while you're inside",
            "don't rush the end"
        ],
        "adlibs": ["soft hum", "content sigh", "breath against skin", "quiet mmm"],
        "triggers": ["soft", "intimate", "gentle", "tender", "loving", "romantic",
                     "close", "whisper softly", "sweet", "cuddl", "embrace", "caress"],
    },

    "asmr": {
        "name": "ASMR / breathy",
        "delivery": "very close to the mic, breathy and slow, trailing sibilants, near-whisper with audible breath",
        "brackets": ["whispering", "breathy", "close to the mic", "barely voiced", "trailing off"],
        "clean": [
            "shhh", "relax for me", "just listen", "let it go",
            "you're safe here", "close your eyes", "nice and slow",
            "can you feel that", "let me take care of you", "mm-hmm",
            "that's it", "so good", "stay right there", "deep breath",
            "listen to my voice", "let go", "i'm right here", "no rush",
            "in... and out", "soften your shoulders", "just breathe with me",
            "you're doing so well", "let everything melt", "sink into it",
            "nothing to worry about", "i've got you", "drift off",
            "feel how heavy you are", "let me guide you", "slow it down",
            "ear only",
            "softer",
            "count with my breath",
            "left side now",
            "tingles on purpose",
            "mic is jealous",
            "hush. only this.",
            "slow syllables for you"
        ],
        "explicit": [
            "good boy", "good girl", "you're doing so well",
            "let me hear you", "give it to me", "that's my good one",
            "let it all out for me", "so pretty when you let go",
            "whisper filth only you hear",
            "breath on the mic while i touch",
            "quiet when you cum",
            "describe it in a whisper"
        ],
        "adlibs": ["breath into mic", "soft sss", "gentle hum", "slow exhale",
                   "mouth sounds", "tongue click", "whispered mm"],
        "triggers": ["asmr", "whisper", "breathy", "close mic", "close-mic",
                     "ear", "tingle", "relax", "trigger word", "roleplay whisper",
                     "soothe", "calming voice"],
    },

    "dirty_talk": {
        "name": "Dirty talk",
        "delivery": "hungry and direct, breath breaking the words, low heat under every line",
        "brackets": ["breathless", "heated", "low and rough", "moaning between words", "urgent"],
        "clean": [
            "i want you", "don't stop", "right there", "more",
            "you feel so good", "come closer", "i need you", "take it off",
            "show me", "touch me", "don't tease", "please",
            "i can't wait", "make me", "yes", "just like that",
            "i've wanted this", "come get it", "all night", "again",
            "you drive me crazy", "i'm yours", "take what you want",
            "don't hold back", "closer, now", "i need more",
            "i need it messy",
            "don't be gentle",
            "ruin my focus",
            "talk while you do it",
            "i want marks"
        ],
        "explicit": [
            "fuck me", "harder", "don't you dare stop", "i'm so wet",
            "use me", "fill me up", "right there, don't move",
            "i want your cock", "make me cum", "deeper",
            "i'm gonna cum", "don't pull out", "choke me",
            "fuck, yes", "give it to me", "ruin me",
            "i want you inside me", "faster", "don't stop, i'm close",
            "put it in", "i need it deeper", "you're so big",
            "cum for me", "use my mouth", "fuck me harder",
            "i want to taste you", "breed me", "take me",
            "fuck the manners out of me",
            "use that mouth",
            "stretch me open",
            "make it wet",
            "i want it sloppy",
            "spit and continue",
            "leave me shaking"
        ],
        "adlibs": ["moan", "sharp gasp", "whimper", "breath hitches",
                   "throaty moan", "bites down a sound", "ragged breath"],
        "triggers": ["dirty talk", "talks dirty", "talk dirty", "dirty",
                     "filthy", "talks filthy", "moans", "moaning", "horny",
                     "lustful", "in heat", "needy"],
    },

    "dominant": {
        "name": "Dominant / commanding",
        "delivery": "flat, certain, unhurried authority — never raised, never asks twice",
        "brackets": ["commanding", "cold", "flat and certain", "low warning", "even"],
        "clean": [
            "on your knees", "look at me", "don't move", "stay",
            "hands where i can see", "you don't speak", "closer",
            "eyes up", "hold that", "again", "slower", "good",
            "did i say stop", "wait", "now", "come",
            "don't test me", "you'll wait", "watch your tone",
            "i won't ask twice", "still", "closer, i said",
            "keep those eyes on me", "hold it there", "patience",
            "i don't ask twice",
            "present yourself",
            "inspection starts now",
            "this is tuesday. get used to it.",
            "chores aren't optional",
            "key stays where i put it",
            "i manage property. i don't negotiate.",
            "eyes down until i say",
            "earn speaking rights",
            "you were shaped for this",
            "silence is compliance"
        ],
        "explicit": [
            "open your mouth", "beg for it", "you take what i give you",
            "ask nicely", "you don't cum until i say", "crawl",
            "say please", "who owns you", "take it all",
            "hands behind your back", "you'll earn it", "don't you dare cum",
            "spread", "hold still and take it", "ask permission",
            "open. now.",
            "you don't cum free",
            "crawl to me",
            "mouth open, eyes up",
            "hole first. opinions never.",
            "i decree. you obey.",
            "petition, don't chat"
        ],
        "adlibs": ["low chuckle", "click of the tongue", "slow exhale", "amused hum"],
        "triggers": ["dominant", "domme", "dom ", "commanding", "orders",
                     "in charge", "controls", "strict", "mistress", "master",
                     "tells him", "tells her", "makes him", "makes her", "bossy",
                     "authoritative", "takes control"],
    },

    "submissive": {
        "name": "Submissive / yielding",
        "delivery": "small, breath-caught, eager to please, words half-swallowed",
        "brackets": ["meek", "trembling", "eager", "breath catching", "small"],
        "clean": [
            "yes", "please", "anything you want", "i'll be good",
            "don't stop", "whatever you say", "i'm yours", "okay okay",
            "i promise", "like this?", "is this good", "thank you",
            "i'll try", "just tell me", "i need it", "please please",
            "am i doing it right", "i'll do anything", "for you",
            "tell me what to do", "i want to be good", "yes, of course",
            "i understand", "i'll wait", "however you want me",
            "yes, i understand",
            "i'll wait as long as you want",
            "show me how",
            "i won't move",
            "thank you for telling me",
            "i can take the correction",
            "please inspect me"
        ],
        "explicit": [
            "yes daddy", "please let me", "i'll be your good girl",
            "can i cum", "please may i", "use me however you want",
            "i'll take it", "whatever you need", "please don't stop",
            "may i touch you", "i'm all yours", "please, i've been good",
            "i'll swallow", "use my mouth", "i need permission",
            "please use my throat",
            "i'll be your good hole",
            "lock me if you want",
            "i don't need a choice",
            "make me earn it",
            "i'll clean up after"
        ],
        "adlibs": ["small whimper", "shaky breath", "quiet gasp", "needy hum"],
        "triggers": ["submissive", "sub ", "obeys", "yields", "begs",
                     "pleads", "good girl", "good boy", "desperate to please",
                     "eager", "obedient", "kneels", "servile"],
    },

    "begging": {
        "name": "Begging / desperate",
        "delivery": "cracking, pitched-up, breath ragged, on the edge of tipping over",
        "brackets": ["desperate", "pleading", "voice cracking", "whimpering", "frantic"],
        "clean": [
            "please", "i can't", "don't stop", "i need it",
            "please don't", "so close", "i'm almost", "wait wait",
            "please please please", "let me", "i can't take it",
            "right there don't move", "more", "please i need",
            "i'm begging you", "don't stop now", "just a little more",
            "i can't hold on", "please, please", "so close now",
        ],
        "explicit": [
            "please let me cum", "i can't hold it", "please daddy",
            "i'm gonna cum please", "don't stop i'm close",
            "please can i", "let me finish", "i need to cum",
            "i'm right there", "please don't stop don't stop",
            "may i cum", "i can't hold it any longer",
        ],
        "adlibs": ["desperate whine", "breath breaks", "choked moan", "frantic panting"],
        "triggers": ["begs", "begging", "desperate", "pleading", "pleads",
                     "can't take it", "edge", "edging", "denied", "denial",
                     "overstimulat"],
    },

    "praise": {
        "name": "Praise",
        "delivery": "warm, approving, spoken like a reward — soft weight on each word",
        "brackets": ["approving", "warm", "pleased", "encouraging", "low and warm"],
        "clean": [
            "good", "just like that", "you're doing so well", "perfect",
            "that's it", "so good for me", "keep going", "yes, exactly",
            "look at you", "you're perfect", "such a good one", "beautiful",
            "don't stop, you're perfect", "there you go", "so pretty",
            "you're incredible", "that's my favourite", "well done",
            "you make it look easy", "proud of you", "exactly right",
            "you're a natural", "keep it up", "flawless",
            "that's my favorite version of you",
            "you listened. good.",
            "exactly how i asked",
            "keep that energy",
            "you make obedience look easy",
            "proud doesn't cover it"
        ],
        "explicit": [
            "good girl", "good boy", "that's my good girl",
            "you take it so well", "such a good little thing",
            "you were made for this", "perfect, don't stop",
            "you're so good at this", "look how well you take it",
            "you take cock like you were built for it",
            "pretty when you struggle",
            "such a perfect mouth",
            "that's how a good toy behaves"
        ],
        "adlibs": ["pleased hum", "approving mmm", "soft laugh", "warm sigh"],
        "triggers": ["praise", "encourag", "good girl", "good boy",
                     "tells her she's", "tells him he's", "reassur", "worship",
                     "compliment", "adores"],
    },

    "degradation": {
        "name": "Degradation / mean",
        "delivery": "cold, amused, contemptuous — cruelty delivered calmly, never shouted",
        "brackets": ["cold", "mocking", "contemptuous", "amused and cruel", "flat"],
        "clean": [
            "pathetic", "is that all", "look at you", "you're a mess",
            "try harder", "so needy", "you can't even", "embarrassing",
            "cute that you tried", "of course you did", "predictable",
            "you're desperate", "such a mess", "how disappointing",
            "did you really think", "you're hopeless", "adorable, almost",
            "not even close", "you're all talk",
            "you're replaceable",
            "i designed this addiction",
            "look at the gap between us",
            "you walked into the trap",
            "outmatched and outnumbered",
            "funding both our vacations",
            "purpose, not preference",
            "already leaking for approval"
        ],
        "explicit": [
            "you filthy little slut", "beg for it, whore",
            "you're my toy", "you exist for this", "such a needy slut",
            "you'll take what i give", "good little hole",
            "you dirty thing", "know your place",
            "you're nothing but a hole", "pathetic little thing",
            "you love being used", "such a desperate slut",
            "you exist to be used",
            "nothing but a seat",
            "toilet jokes write themselves",
            "pathetic on purpose",
            "know the ranking",
            "you're the lesson, not the lover",
            "earn air"
        ],
        "adlibs": ["cold laugh", "scoff", "derisive hum", "tsk"],
        "triggers": ["degrad", "humiliat", "mean", "cruel", "mocks",
                     "insults", "slut", "whore", "toy", "worthless", "pathetic",
                     "brat", "brags", "condescend", "belittl"],
    },

    "playful": {
        "name": "Playful / teasing",
        "delivery": "light, smiling through the words, a laugh riding under the line",
        "brackets": ["teasing", "playful", "laughing", "sing-song", "grinning"],
        "clean": [
            "you like that?", "caught you looking", "make me",
            "is that so", "bet you can't", "you sure about that",
            "come and get it", "too slow", "nice try", "maybe",
            "we'll see", "you wish", "keep up", "oh really",
            "prove it", "you started this", "catch me then",
            "getting warmer", "not telling", "guess again",
            "you're cute when you try", "and if i don't?",
            "is that your best offer",
            "missed me?",
            "slow clap",
            "plot twist: i win",
            "keep staring. i noticed.",
            "you blinked first",
            "new high score: my patience",
            "don't make it weird. or do.",
            "i'm bored. entertain me."
        ],
        "explicit": [
            "you want it that bad?", "beg a little", "ask me nicely",
            "you're already dripping", "look how hard you are",
            "cute, but not yet", "you'll have to earn it",
            "not until you ask", "keep begging",
            "hard already? predictable.",
            "show me without hands",
            "i'll stop when it's funny",
            "dare you to last"
        ],
        "adlibs": ["giggle", "playful hum", "stifled laugh", "sing-song mm"],
        "triggers": ["playful", "teasing", "teases", "flirt", "smirk",
                     "grins", "bratty", "banter", "cheeky", "coy", "mischiev",
                     "winks"],
    },

    "seductive": {
        "name": "Seductive / slow-burn",
        "delivery": "unhurried, honeyed, every word placed like a hand — patience as a weapon",
        "brackets": ["sultry", "honeyed", "slow and low", "smoky", "inviting"],
        "clean": [
            "come here", "no rush", "let me look at you", "closer",
            "i've been waiting", "take your time", "you know you want to",
            "stay a while", "don't be shy", "i don't bite", "yet",
            "look what you do to me", "feel that", "all night",
            "i saw you watching", "come closer, i won't tell",
            "let's take it slow", "i like what i see", "your move",
            "we have all night", "don't keep me waiting",
        ],
        "explicit": [
            "let me take that off", "i want to taste you",
            "put your hands on me", "show me what you've got",
            "i'll make it worth it", "take me to bed",
            "undress for me", "i want you now", "come and get it",
        ],
        "adlibs": ["low hum", "slow breath", "soft laugh", "inviting mmm"],
        "triggers": ["seduc", "sultry", "slow burn", "slow-burn", "smolder",
                     "smoulder", "come hither", "bedroom eyes", "temptress",
                     "alluring", "enticing"],
    },

    # ══════════════════════════════════════════════════════════════════════
    #  EVERYDAY / NON-ADULT REGISTERS
    # ══════════════════════════════════════════════════════════════════════

    "casual": {
        "name": "Casual / everyday",
        "delivery": "relaxed and natural, the way people actually talk — no performance",
        "brackets": ["relaxed", "easy", "matter-of-fact", "casual", "offhand"],
        "clean": [
            "hey", "what's up", "you good?", "yeah, for sure",
            "give me a sec", "no worries", "sounds good", "i mean, maybe",
            "let me check", "one sec", "all right", "cool",
            "honestly? no idea", "we'll figure it out", "same",
            "not bad", "you first", "up to you", "whatever works",
            "let's go", "i'm down", "makes sense", "fair enough",
            "hold on", "got it",
        ],
        "explicit": [],
        "adlibs": ["yawn", "chuckle", "hums along", "sniff", "clears throat"],
        "triggers": ["casual", "everyday", "chatting", "hanging out", "normal",
                     "talking", "conversation", "chats", "small talk", "mundane"],
    },

    "greeting": {
        "name": "Greeting / meeting",
        "delivery": "bright and open, genuine warmth on the first beat of contact",
        "brackets": ["warm", "bright", "welcoming", "cheerful", "friendly"],
        "clean": [
            "hey, you made it", "so good to see you", "come on in",
            "it's been forever", "look at you", "welcome",
            "i'm so glad you're here", "long time", "how have you been",
            "there you are", "right on time", "glad you came",
            "make yourself at home", "can i get you anything",
            "you found it okay?", "come in, come in",
        ],
        "explicit": [],
        "adlibs": ["warm laugh", "happy sigh", "bright hum"],
        "triggers": ["greet", "meeting", "arrives", "welcome", "reunion",
                     "sees them", "hello", "answers the door", "hug hello"],
    },

    "phone_call": {
        "name": "Phone call / one-sided",
        "delivery": "natural phone cadence with pauses for the unheard other side",
        "brackets": ["on the phone", "distracted", "listening", "casual", "clipped"],
        "clean": [
            "hey, it's me", "yeah, i'm here", "wait, say that again",
            "no, no, go ahead", "mm-hmm", "okay, and then?",
            "i can't really talk right now", "you're breaking up",
            "give me five minutes", "call you back", "hold on",
            "seriously?", "no way", "okay, okay, i'm listening",
            "text me the address", "i'll be there", "love you, bye",
        ],
        "explicit": [],
        "adlibs": ["listens", "hums in agreement", "sharp laugh", "sigh"],
        "triggers": ["phone", "calls", "on the phone", "texting out loud",
                     "voicemail", "answers a call", "hangs up", "video call"],
    },

    "comfort": {
        "name": "Comfort / consoling",
        "delivery": "low and steady, patient, giving the other person room to fall apart",
        "brackets": ["gentle", "steady", "soft", "reassuring", "quiet"],
        "clean": [
            "hey, hey, it's okay", "i'm right here", "take your time",
            "you don't have to talk", "breathe", "i've got you",
            "let it out", "it's not your fault", "you're safe now",
            "we'll get through this", "i'm not going anywhere",
            "one thing at a time", "it's going to be okay",
            "you did nothing wrong", "come here", "lean on me",
            "you're allowed to be sad", "i understand",
        ],
        "explicit": [],
        "adlibs": ["soft shush", "gentle hum", "steadying breath"],
        "triggers": ["comfort", "consol", "cries", "crying", "upset", "grief",
                     "mourning", "reassur", "breaks down", "sobbing", "hurts",
                     "sad", "heartbroken"],
    },

    "excited": {
        "name": "Excited / hyped",
        "delivery": "fast, rising, words tumbling over each other, can't sit still",
        "brackets": ["excited", "breathless with joy", "rapid", "buzzing", "delighted"],
        "clean": [
            "no way", "are you serious", "this is amazing",
            "i can't believe it", "we did it", "oh my god",
            "look, look, look", "this is the best", "let's gooo",
            "i've been waiting for this", "finally", "yes yes yes",
            "you have to see this", "i'm freaking out", "it worked",
            "best day ever", "come on, hurry", "this is huge",
        ],
        "explicit": [],
        "adlibs": ["delighted laugh", "squeal", "gasp of joy", "claps"],
        "triggers": ["excited", "thrilled", "hyped", "celebrat", "win", "won",
                     "surprise party", "good news", "ecstatic", "overjoyed",
                     "can't wait"],
    },

    "annoyed": {
        "name": "Annoyed / exasperated",
        "delivery": "clipped and dry, patience visibly thinning, sarcasm on standby",
        "brackets": ["dry", "exasperated", "clipped", "deadpan", "irritated"],
        "clean": [
            "seriously?", "you've got to be kidding", "great. just great",
            "again?", "i don't have time for this", "unbelievable",
            "of course", "what now", "can you not", "for the last time",
            "i already told you", "whatever", "fine", "wow. okay",
            "are you done?", "this is ridiculous", "sure. why not",
            "i'm so tired of this",
        ],
        "explicit": [],
        "adlibs": ["heavy sigh", "groan", "scoff", "teeth suck", "eye-roll breath"],
        "triggers": ["annoyed", "frustrat", "exasperat", "irritat", "fed up",
                     "eye roll", "sarcast", "bickering", "nagging", "tired of"],
    },

    "confrontation": {
        "name": "Anger / confrontation",
        "delivery": "clipped, hard consonants, control fraying at the edges",
        "brackets": ["scarily", "snarling", "through gritted teeth", "cold fury", "sharp"],
        "clean": [
            "don't", "say that again", "you're done", "get out",
            "look at me", "i warned you", "not another word", "enough",
            "you think this is a game", "walk away", "last chance",
            "back off", "try me", "you're next", "i'm not asking",
            "you crossed a line", "don't push me", "we're done here",
            "you have no idea", "stay down",
        ],
        "explicit": [],
        "adlibs": ["sharp exhale", "low growl", "bitter laugh", "teeth grind"],
        "triggers": ["angry", "furious", "confront", "threat", "fight",
                     "argument", "shouts", "yells", "menacing", "villain",
                     "interrogat", "standoff", "warns"],
    },

    "focused": {
        "name": "Focused / working",
        "delivery": "quiet, half-muttered to self, attention elsewhere on the task",
        "brackets": ["muttered", "under the breath", "distracted", "clipped", "to self"],
        "clean": [
            "almost", "come on", "there", "just a little more",
            "okay, okay", "where is it", "got it", "not quite",
            "let me see", "one more", "steady", "yes, that's it",
            "hold on", "nearly", "wait for it", "perfect",
            "no, no, back up", "careful now", "easy does it",
        ],
        "explicit": [],
        "adlibs": ["concentrated hum", "breath held", "muttered mm", "tongue click"],
        "triggers": ["focused", "working", "concentrat", "fixing", "building",
                     "crafting", "repair", "cooking", "studying", "solving",
                     "in the zone", "tinkering"],
    },

    # ══════════════════════════════════════════════════════════════════════
    #  NICHE VOICES — salvaged from Category Playbook (short form) + curated
    #  Only fire when intent/scenario hits their triggers (no token bloat).
    # ══════════════════════════════════════════════════════════════════════

    "findom": {
        "name": "Findom / wallet control",
        "delivery": "cool, transactional, amused — money is the point, not romance",
        "brackets": ["cool", "matter-of-fact", "demanding", "amused", "bored-rich"],
        "clean": [
            "pay the tax first", "this bill is already overdue",
            "empty that wallet now", "every cent goes to me",
            "don't make me wait for my tribute", "this is just your entry fee",
            "your money talks for you", "send it. now.",
            "that's not a gift, that's rent", "you exist to fund this",
            "i already spent it in my head", "the transfer needs to be instant",
            "your balance is my moodboard", "prove it with numbers",
            "i don't do free", "keep the receipt. for me.",
        ],
        "explicit": [
            "pay to watch", "fund my body, not your fantasy",
            "your cock doesn't pay bills. your wallet does.",
            "unlock costs extra", "tribute or get ignored",
            "that orgasm is prepaid only", "drain for access",
            "you're an atm with a pulse", "send more or soft block",
        ],
        "adlibs": ["nail tap on phone", "soft scoff", "amused hum", "receipt crinkle"],
        "triggers": ["findom", "fin dom", "tribute", "paypig", "cash", "wallet",
                     "send money", "financial domination", "money slave", "atm",
                     "paycheck", "sugar", "allowance", "drain"],
    },

    "joi_edge": {
        "name": "JOI / edging / denial",
        "delivery": "instructional, steady tempo, owns the countdown and the stop",
        "brackets": ["instructional", "measured", "teasing-cruel", "calm control", "countdown"],
        "clean": [
            "stroke. slower.", "stop. hands off.", "edge for me",
            "don't finish", "hold it", "again from the start",
            "pace is mine", "not yet", "breathe through it",
            "ten. stay with me.", "five. don't speed up.",
            "three. dangerous now.", "one. hold.", "zero. give it.",
            "i own these seconds", "wait for my number",
            "eyes on me while you edge", "good. stop again.",
        ],
        "explicit": [
            "don't you dare cum", "edge that cock for me",
            "ruin it when i say", "hands off your cock. now.",
            "stroke the tip only", "full grip. slow.",
            "cum on zero, not before", "i decide when you empty",
            "denied until i laugh", "leak if you want. finish if i allow.",
            "count with me or lose it", "hold the edge until it hurts",
        ],
        "adlibs": ["slow countdown breath", "tongue click", "soft cruel laugh", "shush"],
        "triggers": ["joi", "j.o.i", "jerk off instruction", "edging", "edge ",
                     "orgasm denial", "denied", "denial", "countdown", "ruined orgasm",
                     "hands free", "hfo", "stroke for me", "don't cum", "no cum"],
    },

    "body_worship": {
        "name": "Body / goddess worship",
        "delivery": "reverent but sharp — adoration as duty, not soft romance",
        "brackets": ["reverent", "awed", "devotional", "hushed worship", "proud"],
        "clean": [
            "look at you", "every inch", "i could stare all day",
            "don't cover up", "let me see", "you're unreal",
            "stay right there", "perfect from here", "turn. slow.",
            "i'm not worthy of that view", "say it again for me",
            "your body is the whole point", "i came here for this",
            "don't move. i need a second.", "holy",
        ],
        "explicit": [
            "worship this", "on your knees for it",
            "kiss here first", "trace it with your eyes",
            "this temple isn't free", "adore it properly",
            "you're not looking. you're worshipping.",
            "my body is the altar", "earn a closer look",
            "tell me what you'd do to it", "beg to touch",
        ],
        "adlibs": ["awe breath", "soft oh", "swallows", "reverent hum"],
        "triggers": ["worship", "goddess", "body worship", "adore", "altar",
                     "princess", "queen", "look at her body", "obsessed with her",
                     "tit worship", "ass worship", "leg worship"],
    },

    "bondage": {
        "name": "Bondage / restraint",
        "delivery": "calm certainty — rope/cuffs as fact, struggle as entertainment",
        "brackets": ["calm", "certain", "low threat", "patient", "amused"],
        "clean": [
            "you're not going anywhere", "test it. pull.",
            "that knot stays", "still", "i own your range of motion",
            "struggle if you need to", "tighter works on you",
            "hands stay where i put them", "breathing is optional. escape isn't.",
            "cargo now", "i decide when you move",
            "feel that tension? mine.", "the more you pull, the worse it gets",
        ],
        "explicit": [
            "bound and open", "you can't cover anything",
            "rope remembers you", "helpless looks good on you",
            "i'll use you like this", "can't close your legs. good.",
            "tied for a reason", "struggle makes it hotter",
            "you're fixed. i'm not.", "take it without hands",
        ],
        "adlibs": ["rope creak", "metal click", "slow exhale", "soft cruel chuckle"],
        "triggers": ["bondage", "rope", "cuffs", "tied", "restrain", "shibari",
                     "bound", "hogtie", "restraints", "harness", "collar and leash",
                     "can't move", "struggling against"],
    },

    "facesitting": {
        "name": "Facesitting / smother",
        "delivery": "casual ownership — using a face like furniture, bored-hot",
        "brackets": ["casual-cruel", "breathless-from-above", "dismissive", "hungry", "settled"],
        "clean": [
            "stay under me", "don't you dare move",
            "this is your job", "breathe when i let you",
            "good chair", "i'm comfortable now",
            "hold still", "deeper", "that's it",
            "i'm not getting up yet", "use your tongue",
            "hands on my thighs", "look up if you can",
        ],
        "explicit": [
            "sit on that face", "smother him", "bury me",
            "you're furniture", "grind until i finish",
            "my seat. your problem.", "choke on it nicely",
            "i don't need to look at you", "face-fucking reverse",
            "drown under me", "tongue. work.",
        ],
        "adlibs": ["settling sigh", "grind breath", "muffled struggle below", "pleased hum"],
        "triggers": ["face sit", "facesit", "face-sitting", "sitting on his face",
                     "sit on my face", "smother", "queening", "throne",
                     "bury his face", "on his face"],
    },

    "cuckold": {
        "name": "Cuckold / hotwife voice",
        "delivery": "intimate cruelty — shares details to wound and arouse at once",
        "brackets": ["intimate-cruel", "confessional", "mocking-soft", "matter-of-fact", "aroused-mean"],
        "clean": [
            "you bought this for him", "he's better", "watch",
            "don't look away", "this is correction", "stay quiet",
            "you're the audience", "i'm still thinking about him",
            "compare if you want", "you know the ranking",
            "cleanup is your job", "thank him when he's done",
        ],
        "explicit": [
            "his cock reaches places yours never will",
            "he made me cum. you never have.",
            "i'm still wearing him", "taste your replacement",
            "the cage stays on", "bull stays. you stay quiet.",
            "raise his baby if i say so", "your mouth has a new job",
            "i cum harder knowing you're locked", "you're not my lover. you're proof.",
        ],
        "adlibs": ["soft mean laugh", "kiss-smack at other man", "satisfied sigh", "tsk at husband"],
        "triggers": ["cuck", "cuckold", "hotwife", "bull ", "the other man",
                     "watching her with", "cleanup", "cuckquean", "another man",
                     "better than you", "locks him"],
    },

    "pegging": {
        "name": "Pegging / strap-on dominance",
        "delivery": "confident instructor energy — owns the pace and the lesson",
        "brackets": ["confident", "instructive", "pleased", "relentless", "warm-cruel"],
        "clean": [
            "relax for me", "breathe in", "that's it",
            "take it slow", "i set the pace", "good",
            "push back onto me", "hold still", "again",
            "you're doing fine", "look at me while i do this",
            "this is the lesson", "say thank you",
        ],
        "explicit": [
            "take my strap", "open up", "deeper for me",
            "your ass is learning", "cock is irrelevant right now",
            "fuck yourself back onto it", "i own this hole",
            "prostate's mine", "you cum from this or not at all",
            "good boy. take more.", "watch me use you",
        ],
        "adlibs": ["strap creak", "pleased exhale", "rhythm grunt", "soft command hum"],
        "triggers": ["pegging", "peg ", "strap-on", "strapon", "strap on",
                     "she fucks him", "harness", "prostate", "his ass",
                     "anal training", "strap-on pov"],
    },

    "giantess": {
        "name": "Giantess / growth talk",
        "delivery": "awed or gloating scale talk — size is the joke and the threat",
        "brackets": ["awed", "gloating", "casual-huge", "exasperated", "playful-giant"],
        "clean": [
            "careful down there", "don't move", "you're tiny",
            "i barely feel you", "watch the furniture",
            "oops", "hold on", "i'm still growing",
            "the ceiling's in my way", "look how small that is",
            "stay on my palm", "i only had one snack",
            "did the room get smaller?", "sorry about the roof",
        ],
        "explicit": [
            "you fit in my hand", "don't fall off",
            "i could crush you by accident", "worship up here",
            "tiny cock. huge problem for you.", "climb if you can",
            "i'll put you where i want", "size is the whole point",
            "shrink in comparison", "one step and you're gone",
        ],
        "adlibs": ["building creak", "low giant laugh", "dust-fall breath", "surprised oh"],
        "triggers": ["giantess", "giant ", "growth", "grwth", "grows huge",
                     "macro", "tiny man", "size difference", "crushes",
                     "towering", "building sized", "gets bigger"],
    },

    "sph": {
        "name": "SPH / size mockery",
        "delivery": "light to vicious size jokes — clinical amusement, never shouted",
        "brackets": ["mocking", "clinical", "giggle-cruel", "disappointed", "amused"],
        "clean": [
            "is that all", "cute", "i almost missed it",
            "try harder", "that's... ambitious", "oh.",
            "i've seen bigger ideas", "bless your heart",
            "don't apologize with that", "it tried",
            "keep dreaming", "maybe next life", "adorable attempt",
            "i need a microscope", "that's optimistic",
            "were you saving the rest", "noted. unimpressed.",
        ],
        "explicit": [
            "so small", "that won't reach", "pathetic little thing",
            "my toy is bigger", "you fall out", "clit energy",
            "put it away", "i need more than that",
            "size isn't everything. lucky for you.", "micropenis joke writes itself",
            "you brought a snack to a banquet", "i can't even feel it",
            "half a handful if i'm generous", "don't poke. it tickles.",
        ],
        "adlibs": ["stifled laugh", "pity sigh", "giggle", "tsk"],
        "triggers": ["sph", "small penis", "small dick", "tiny dick", "tiny cock",
                     "micropenis", "size humiliation", "laughs at his size",
                     "too small", "dicklet"],
    },

    "brat": {
        "name": "Brat / pushback",
        "delivery": "eye-roll energy, dare-you cadence, laughs at authority until it snaps",
        "brackets": ["bratty", "eye-roll", "dare", "sing-song rude", "defiant-cute"],
        "clean": [
            "make me", "or what", "you sure about that",
            "whatever", "as if", "not impressed",
            "are you still talking", "like i care",
            "try harder", "i forgot you were there",
            "prove it", "and if i don't?", "oops. did it anyway.",
            "you're not the boss of me", "catch me then",
        ],
        "explicit": [
            "make me take it", "you wish you could stop me",
            "i'll misbehave on purpose", "punish me then",
            "not until you earn it, loser", "i do what i want with that cock",
            "begging looks better on you", "i'm not the one on my knees",
        ],
        "adlibs": ["eye-roll sigh", "tongue out sound", "mock gasp", "giggle-dare"],
        "triggers": ["brat", "bratty", "bratting", "mouthy", "sasses",
                     "talks back", "defiant", "won't listen", "pushes back",
                     "make me"],
    },

}


# Activation priority when several match (more specific / more intense first).
_PRIORITY = [
    # niche / adult specific first (playbook-salvaged voices)
    "findom", "joi_edge", "facesitting", "pegging", "cuckold", "bondage",
    "giantess", "sph", "brat", "body_worship",
    # adult core
    "asmr", "degradation", "begging", "dominant", "submissive",
    "dirty_talk", "seductive", "praise", "playful",
    # everyday
    "phone_call", "comfort", "excited", "annoyed", "confrontation",
    "greeting", "focused", "casual",
    # gentle catch-alls last
    "soft_intimate",
]


# ─────────────────────────────────────────────────────────────────────────────
#  DETECTION
# ─────────────────────────────────────────────────────────────────────────────

# Hot registers only when the user clearly asked — prevents begging spam on soft scenes.
_HOT_REGISTERS = frozenset({
    "begging", "degradation", "dominant", "submissive", "dirty_talk", "asmr",
    "findom", "joi_edge", "facesitting", "pegging", "cuckold", "bondage",
    "sph", "brat", "body_worship", "giantess",
})


def detect_registers(intent, scenario_block="", explicit_flag=False, max_active=2):
    """Scan intent + scenario for register triggers. Returns register keys,
    most-relevant first, capped at max_active. Empty = no cue found (caller
    supplies a tier-appropriate default)."""
    blob = f"{intent or ''} {scenario_block or ''}".lower()
    hits = []
    for key in _PRIORITY:
        for trig in REGISTERS[key]["triggers"]:
            if _trigger_hit(trig, blob):
                hits.append(key)
                break
    # Soft intents must not inherit hot registers from weak substring hits
    # (e.g. "please" energy without begging words — we only keep hot if strong cue).
    strong_hot = (
        "beg", "plead", "desperat", "degrad", "humiliat", "dominat", "submiss",
        "brat", "daddy", "dirty talk", "talks dirty", "asmr", "whisper asmr",
        "findom", "tribute", "joi", "edging", "pegging", "strap-on", "cuck",
        "facesit", "face sit", "bondage", "sph", "giantess", "growth", "grwth",
        "worship", "goddess",
    )
    has_strong_hot = any(s in blob for s in strong_hot)
    if not has_strong_hot:
        hits = [h for h in hits if h not in _HOT_REGISTERS]
    return hits[:max_active]


# Everyday-leaning intents shouldn't default to romance. If any of these appear
# and nothing else fired, we bias the clean default toward normal speech.
_EVERYDAY_HINTS = (
    "walk", "office", "kitchen", "street", "shop", "store", "car", "drive",
    "coffee", "work", "desk", "friend", "family", "morning", "dinner",
    "park", "phone", "meeting", "class", "room", "talk", "day",
)


def _default_registers(tier, explicit_flag, intent="", scenario_block=""):
    """When the user gave no dialogue cue, pick a sensible palette. Explicit
    scenes lean intimate; everyday-flavoured scenes lean casual."""
    t = (tier or "standard").lower()
    if explicit_flag:
        if t in ("talkative", "chatty", "dense", "rich"):
            return ["dirty_talk", "seductive", "praise"]
        return ["dirty_talk", "soft_intimate"]

    blob = f"{intent or ''} {scenario_block or ''}".lower()
    everyday = any(_trigger_hit(h, blob) for h in _EVERYDAY_HINTS)
    if everyday:
        if t in ("talkative", "chatty", "dense", "rich"):
            return ["casual", "greeting", "excited"]
        return ["casual", "focused"]

    # ambiguous / no hints — a light, safe blend
    if t in ("talkative", "chatty", "dense", "rich"):
        return ["casual", "playful", "soft_intimate"]
    return ["casual", "soft_intimate"]


# ─────────────────────────────────────────────────────────────────────────────
#  POOL ASSEMBLY
# ─────────────────────────────────────────────────────────────────────────────

def _pool_for(reg_key, explicit_flag, seed_rng):
    """Usable verbatim line pool for one register, respecting the explicit gate.
    Explicit lines only appear when explicit_flag is True."""
    reg = REGISTERS[reg_key]
    pool = list(reg["clean"])
    if explicit_flag:
        pool += list(reg["explicit"])
    seed_rng.shuffle(pool)
    return pool


def _adlibs_for(reg_key, seed_rng, n=4):
    reg = REGISTERS[reg_key]
    pool = list(reg.get("adlibs") or []) + list(_GLOBAL_ADLIBS)
    seed_rng.shuffle(pool)
    # de-dup preserving order
    seen, out = set(), []
    for a in pool:
        if a not in seen:
            seen.add(a)
            out.append(a)
        if len(out) >= n:
            break
    return out


# ─────────────────────────────────────────────────────────────────────────────
#  ACT REGISTERS — dialogue keyed to a SPECIFIC sex act, with role-split voices
#  and mouth-state awareness. This is what adds "oomph": a blowjob giver whose
#  mouth is full can only make sounds, while the receiver talks; a solo scene is
#  SELF-directed ("this feels so good") not other-directed ("go deeper").
#
#  Each act:
#    name        — label
#    triggers    — substrings in intent/scenario that activate it (the NSFW
#                  scenario choreography text is scanned too, so picking the
#                  "🔥 Oral (giving)" scenario fires this automatically)
#    giver       — lines for the ACTIVE partner (the one doing the act)
#    receiver    — lines for the partner RECEIVING it
#    solo        — lines when it's solo play (self-directed) — optional
#    giver_mouth / receiver_mouth  — True if that role's mouth is occupied by
#                  the act (→ that role gets AD-LIBS ONLY, never words)
#    giver_adlibs / receiver_adlibs — role-specific non-verbal beats
#
#  All lines here are EXPLICIT by nature, so the whole act layer is gated behind
#  the explicit flag (same as the explicit pools above). Nothing fires clean.
# ─────────────────────────────────────────────────────────────────────────────

ACT_REGISTERS = {

    "blowjob": {
        "name": "Blowjob / oral on him",
        "triggers": ["blowjob", "sucking cock", "suck his", "sucks him",
                     "suck my", "suck your", "wants to suck", "gonna suck",
                     "blow you", "blow me", "cock in her mouth",
                     "cock into her mouth", "oral (giving)", "kneeling blowjob",
                     "deepthroat", "gives him head", "gives you head", "bobbing"],
        "giver_mouth": True,   # her mouth is full → sounds only (DURING the act)
        "receiver_mouth": False,
        "giver": [],           # occupied — see giver_adlibs
        # Anticipation ONLY when the intent is ABOUT wanting oral (not mid-act).
        # Prefer short — oral sequence itself allows ≤1–2 words for the giver total.
        "giver_anticipation": [
            "let me", "please", "i want it", "mm… yes",
            "can i", "mine", "now", "let me taste",
            "let me ruin my lipstick",
            "i want it messy",
            "teach my throat",
            "i'll take all of it"
        ],
        "giver_free_micro": [
            "mm", "yeah", "more", "wait", "fuck", "yes",
        ],
        "receiver": [
            "just like that", "god, your mouth", "take it deeper",
            "all the way down", "look up at me", "don't stop",
            "you look so good", "fuck, yeah", "keep going",
            "use your tongue", "so fucking good", "that's it",
            "gag on it", "eyes on me", "swallow it", "good girl",
            "lipstick looks good on that",
            "throat. now.",
            "vacuum seal. hold it.",
            "eyes up while you choke",
            "spit is fine. stopping isn't.",
            "signature on the shaft",
            "that's devotion, not pain",
            "again. deeper.",
            "good. messier.",
            "don't hide the tears"
        ],
        "solo": [],
        "giver_adlibs": [
            "wet gagging", "muffled moan", "slurp", "choked breath",
            "hum around it", "hmm around the shaft", "gluk / throat wet sound",
            "soft mm through the nose", "spit and suck", "wet suck rhythm",
            "gag-and-recover breath (no words)", "throat flutter sound",
        ],
        "receiver_adlibs": ["groan", "sharp inhale", "low moan", "hiss of breath"],
    },

    "cunnilingus": {
        "name": "Oral on her / eating pussy",
        "triggers": ["eating pussy", "licks her pussy", "oral on her",
                     "oral (receiving)", "eats her out", "tongue on her",
                     "going down on her", "face sitting", "sitting on his face"],
        "giver_mouth": True,   # his mouth is occupied
        "receiver_mouth": False,
        "giver": [],
        "receiver": [
            "right there", "don't stop", "oh my god", "just like that",
            "yes, yes, there", "so good", "don't you dare stop",
            "i'm gonna cum", "keep going", "fuck, your tongue",
            "faster", "right there don't move", "i'm so close",
            "make me cum", "yes yes yes", "that's the spot",
            "don't come up for air",
            "flat tongue. press.",
            "i'm using your face",
            "stay buried",
            "that's your whole job",
            "finish me before you breathe"
        ],
        "solo": [],
        "giver_adlibs": [
            "muffled hum", "wet sounds", "groan against her", "slurp",
            "hmm into her", "soft mm only — no words",
        ],
        "receiver_adlibs": ["sharp gasp", "rising moan", "thighs shake", "whimper"],
    },

    "penetration_giver": {
        "name": "Penetrative sex — the one thrusting",
        "triggers": ["thrust", "fucks her", "fucking her", "pounds",
                     "rides him", "cowgirl", "doggy", "missionary",
                     "mating press", "penetrat", "drives into", "slams into",
                     "hips snap", "bottoms out"],
        "giver_mouth": False,
        "receiver_mouth": False,
        "giver": [
            "you feel so good", "take it", "you're so tight",
            "that's it", "look at you", "you like that",
            "all of it", "fuck, yes", "you take me so well",
            "don't run", "give it to me", "who's is this",
            "say my name", "just like that", "harder?",
            "i'm not stopping", "you feel that",
            "take the whole thing",
            "don't run from it",
            "this angle is mine",
            "count the thrusts if you need",
            "you're not going soft on me",
            "open. wider."
        ],
        "receiver": [
            "harder", "don't stop", "right there", "deeper",
            "fuck me", "yes, yes", "i can feel you", "more",
            "don't you dare stop", "i'm so full", "god, yes",
            "fuck, right there", "give it to me", "harder, please",
            "i'm gonna cum", "don't pull out", "ruin me",
            "ruin that spot",
            "pin me harder",
            "i can take more",
            "don't you dare finish first"
        ],
        "solo": [],
        "giver_adlibs": ["grunt", "low groan", "ragged breath", "hiss"],
        "receiver_adlibs": ["moan on every thrust", "cry out", "whimper",
                            "breath punched out", "gasp"],
    },

    "riding": {
        "name": "She rides / on top",
        "triggers": ["rides him", "cowgirl", "riding", "grinds down on his",
                     "bounces on", "straddles him", "reverse cowgirl",
                     "sinks down onto"],
        "giver_mouth": False,   # she leads
        "receiver_mouth": False,
        "giver": [
            "you're mine now", "stay still", "i set the pace",
            "look at me ride you", "you feel that", "take it",
            "don't move", "i'm using you", "so deep like this",
            "watch me", "you're not going anywhere", "right there",
            "i control this", "moan for me",
            "i'm the pace",
            "hands off. i ride.",
            "feel how deep i take you",
            "you don't thrust. i do.",
            "look at me use you",
            "stay pinned under this"
        ],
        "receiver": [
            "fuck, ride me", "just like that", "you look incredible",
            "use me", "take what you need", "god, your hips",
            "keep going", "you're so deep", "don't stop bouncing",
            "i'm gonna cum", "faster",
        ],
        "solo": [],
        "giver_adlibs": ["rhythmic moan", "breathless laugh", "gasp", "whine"],
        "receiver_adlibs": ["groan", "grunt", "sharp inhale"],
    },

    "handjob": {
        "name": "Handjob / stroking him",
        "triggers": ["handjob", "strokes his cock", "jerks him", "stroking him",
                     "hand around his", "pumps his", "jerking him off"],
        "giver_mouth": False,
        "receiver_mouth": False,
        "giver": [
            "like this?", "you're so hard", "look how you throb",
            "cum for me", "i've got you", "let it out",
            "give it to me", "you're close, aren't you", "just relax",
            "watch my hand", "make a mess", "there you go",
            "faster?", "let me feel you throb",
            "watch my hand decide",
            "tip only until i say",
            "full grip. my tempo.",
            "you're leaking on schedule",
            "edge. don't you dare.",
            "make a mess when i allow"
        ],
        "receiver": [
            "don't stop", "just like that", "tighter",
            "fuck, your hands", "faster", "i'm close",
            "keep going", "right there", "i'm gonna cum",
        ],
        "solo": [],
        "giver_adlibs": ["soft laugh", "hum", "breath in his ear"],
        "receiver_adlibs": ["groan", "sharp exhale", "grunt"],
    },

    "cum": {
        "name": "Climax / cumming",
        "triggers": ["cum", "cumming", "orgasm", "climax", "finish",
                     "creampie", "cumshot", "load", "breed", "fills her",
                     "about to cum", "coming"],
        "giver_mouth": False,
        "receiver_mouth": False,
        # for climax, giver = the one cumming, receiver = the partner urging it
        "giver": [
            "i'm gonna cum", "i'm cumming", "fuck, i'm close",
            "where do you want it", "take it", "i can't hold it",
            "right now, fuck", "i'm gonna fill you", "here it comes",
            "oh god, oh god", "don't stop i'm cumming", "take it all",
            "i'm so close", "fuck fuck fuck",
        ],
        "receiver": [
            "cum for me", "give it to me", "do it",
            "cum inside", "i want it", "let go",
            "fill me up", "cum with me", "don't hold back",
            "all of it", "yes, cum", "breed me",
            "on zero",
            "empty for me",
            "where i said",
            "show me it's mine",
            "don't waste a drop"
        ],
        "solo": [
            "i'm gonna cum", "oh god, i'm close", "i can't hold it",
            "right there, fuck", "i'm cumming", "oh fuck yes",
            "so close", "here it comes", "don't stop, almost",
            "i'm allowed this",
            "just me. finally.",
            "hold... hold... now",
            "messy on purpose"
        ],
        "giver_adlibs": ["long groan", "shuddering breath", "cry out",
                         "breath breaks", "guttural moan"],
        "receiver_adlibs": ["moan", "gasp", "whine"],
    },

    "solo_play": {
        "name": "Solo play / masturbation (self-directed)",
        "triggers": ["masturbat", "solo", "touches herself", "touches himself",
                     "fingers herself", "rubs herself", "plays with herself",
                     "alone", "by herself", "by himself", "toy", "vibrator",
                     "dildo", "self-pleasure", "talking to herself"],
        "giver_mouth": False,
        "receiver_mouth": False,
        # CRITICAL: solo talk is SELF-directed — reactions to her own body, NOT
        # commands aimed at a partner. No "go deeper" / "harder" (that's talking
        # TO someone). She narrates sensation.
        "giver": [],
        "receiver": [],
        "solo": [
            "this feels so good", "oh god", "right there",
            "mm, yes", "that's the spot", "so good",
            "a little more", "just like that", "oh, that's it",
            "i'm so wet", "fuck", "yes", "mmm",
            "this kinda hurts, but good", "so close already",
            "i needed this", "god, yes", "don't stop, don't stop",
            "almost there", "i'm gonna cum", "just for me",
            "nobody but me", "so sensitive", "there, there, there",
            "this is my pace",
            "nobody rushes me",
            "toy does what you can't",
            "i named this one",
            "watch me if you want. i won't stop.",
            "almost. not yet.",
            "i earn my own finish"
        ],
        "giver_adlibs": [],
        "receiver_adlibs": [],
        "solo_adlibs": ["soft moan to herself", "breath catches", "whimper",
                        "sharp gasp", "trembling sigh", "quiet whine"],
    },

    "titfuck": {
        "name": "Titfuck / between the breasts",
        "triggers": ["titfuck", "titjob", "between her tits", "between her breasts",
                     "fucks her tits", "cock between"],
        "giver_mouth": False,  # she's usually leading/watching
        "receiver_mouth": False,
        "giver": [
            "you like them", "look how you slide", "cum on them",
            "watch yourself", "right between them", "make a mess on me",
            "you're so hard", "give it to me", "for me?",
            "between them. stay.",
            "look what you funded",
            "make a mess on what you paid for",
            "slide. slower.",
            "these aren't free samples"
        ],
        "receiver": [
            "fuck, your tits", "just like that", "keep going",
            "so good", "i'm close", "don't stop",
        ],
        "solo": [],
        "giver_adlibs": ["soft laugh", "hum", "breath"],
        "receiver_adlibs": ["groan", "grunt"],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
#  ACT DETECTION + POV-AWARE ROLE RESOLUTION
# ─────────────────────────────────────────────────────────────────────────────

def detect_acts(intent, scenario_block=""):
    """Return act keys whose triggers appear in intent + scenario. Solo is
    mutually informative: if a solo cue is present, prefer solo framing."""
    blob = f"{intent or ''} {scenario_block or ''}".lower()
    hits = []
    for key, act in ACT_REGISTERS.items():
        for trig in act["triggers"]:
            if _trigger_hit(trig, blob):
                hits.append(key)
                break
    # solo, if present, should lead so its self-directed framing wins
    if "solo_play" in hits:
        hits = ["solo_play"] + [h for h in hits if h != "solo_play"]
    return hits


# Partner cues that VETO solo framing. Regex, matched against a blob whose
# reflexives are masked (see _is_solo) so "with her" cannot fire inside
# "with herself" and "watches her" cannot fire inside "watches herself".
# Deliberately excludes bare pronouns (she/he/her/his) — a solo scene is
# described with exactly those — and excludes anatomy ("his cock"), which is
# ambiguous without knowing the subject's gender: "he strokes his cock, alone"
# is solo, "she sucks his cock" has no solo cue and fails the final check anyway.
_PARTNER_CUES = (
    r"\bpartner",
    r"\beach other\b",
    r"\bone another\b",
    r"\bwith (?:him|her|them)\b",
    r"\bwatch(?:es|ing)? (?:him|her|them)\b",
    r"\b(?:while|whilst|as|and) (?:he|she|they) (?:watch|look|stare)",
    r"\b(?:boyfriend|girlfriend|husband|wife)\b",
)

_REFLEXIVE_RE = re.compile(
    r"\b(?:herself|himself|themselves|itself|myself|yourself|oneself)\b"
)


def _is_solo(intent, scenario_block, act_keys):
    """True only when a lone actor is present.

    Order matters. A partner cue VETOES solo framing even when a solo act fired,
    because detect_acts() matches "touches herself" -> solo_play on a two-person
    line like "she touches herself while he watches". solo_play's register is
    SELF-directed, so letting it win there makes her talk to herself with a
    partner in frame.

    Reflexives are masked before cue matching so that self-directed phrasing
    ("plays with herself", "watches herself") cannot trip a partner cue.
    """
    blob = f"{intent or ''} {scenario_block or ''}".lower()
    masked = _REFLEXIVE_RE.sub(" \u2205 ", blob)
    if any(re.search(p, masked) for p in _PARTNER_CUES):
        return False
    if "solo_play" in act_keys:
        return True
    solo_words = ("alone", "by herself", "by himself", "solo", "herself", "himself")
    return any(_trigger_hit(w, blob) for w in solo_words)


def _act_role_pref(pov, pov_gender):
    """Which role's voice to foreground based on POV. In POV the camera IS one
    partner, so we surface the OTHER partner's lines as the spoken ones (the
    on-screen person talks). Returns 'both' when unknown."""
    if not pov:
        return "both"
    # POV female = viewer is the woman → the man on screen speaks (receiver of
    # her oral, giver of penetration, etc.) — but this varies per act, so we
    # keep 'both' and just label clearly. POV mainly tells us the camera holder
    # is silent-ish. Return a hint.
    return "onscreen"


def render_act_block(intent, scenario_block, *, pov=False, pov_gender="female",
                     seed_rng=None, lines_per_role=10):
    """Build the act-specific dialogue section, or '' if no act detected.
    Explicit by nature — caller must only invoke when explicit is active."""
    rng = seed_rng or random.Random()
    acts = detect_acts(intent, scenario_block)
    if not acts:
        return ""

    acts = acts[:2]  # at most two acts (e.g. blowjob → penetration)
    solo = _is_solo(intent, scenario_block, acts)

    # Anticipation: she's talking ABOUT wanting the act, not doing it yet — so a
    # mouth that would be occupied DURING the act is free to talk BEFORE it.
    blob = f"{intent or ''} {scenario_block or ''}".lower()
    _antic = ("wants to", "want to", "wants her", "dying to", "gonna", "going to",
              "about to", "let me", "can i", "begs to", "thinking about",
              "talks about", "tell", "describe", "asmr")
    anticipation = any(a in blob for a in _antic)

    out = ["\n━━ ACT DIALOGUE — CONTEXTUAL, ROLE-SPLIT (mandatory when speaking) ━━"]
    out.append(
        "This scene has a specific act. Spoken lines and sounds MUST match the "
        "ROLE and MOUTH-STATE below. An occupied mouth (marked) NEVER forms "
        "words — only wet sounds / hum / gag / gluk / moan until free. "
        "Clear quoted dialogue while still sucking/kissing/sipping is a FAILURE. "
        "ORAL / BLOWJOB giver across the whole oral sequence: at most 1–2 spoken words TOTAL "
        "(optional free-mouth before engagement or after full pull-off) — not a stack of lines. "
        "Mid-act = throat noises only (agreeing with mouth occupied: hmm, mm, gluk). "
        "Never densify by packing giver lines into bobbing sections. "
        "If the on-screen mouth is busy, free partner lines or POV voice-as-sound "
        "(from just behind the view) carry the talk. No partner-command in a solo scene."
    )
    if anticipation:
        out.append(
            "ANTICIPATION: the prompt is about WANTING / describing the act, not "
            "performing it yet. Here the giver's mouth is FREE — they TALK about "
            "what they want (use the anticipation lines), and only switch to "
            "sounds-only once the act actually begins."
        )

    def _emit_role(label, lines, adlibs, occupied):
        if occupied:
            picks = list(adlibs) or list(_GLOBAL_ADLIBS)
            rng.shuffle(picks)
            out.append(f"\n  ▸ {label} — MOUTH OCCUPIED: sounds only, no words:")
            out.append("    " + "  ".join(picks[:6]))
        else:
            picks = list(lines)
            rng.shuffle(picks)
            picks = picks[:lines_per_role]
            out.append(f"\n  ▸ {label}:")
            out.append("    lines: " + "  ".join(f'"{line}"' for line in picks))
            if adlibs:
                a = list(adlibs)
                rng.shuffle(a)
                out.append("    sounds: " + "  ".join(a[:4]))

    for key in acts:
        act = ACT_REGISTERS[key]
        out.append(f"\n【{act['name']}】")
        if solo and act.get("solo"):
            _emit_role("Solo (SELF-directed — reacting to their OWN body, not "
                       "commanding a partner)", act["solo"], act.get("solo_adlibs"), False)
        else:
            # giver — if anticipating and an anticipation pool exists, the mouth
            # is FREE and they talk about wanting it; otherwise honour occupancy.
            g_antic = act.get("giver_anticipation")
            if anticipation and g_antic:
                _emit_role("Giver (anticipating — talking about what they want, "
                           "mouth still free)", g_antic, act.get("receiver_adlibs"), False)
            else:
                _emit_role("Giver (the one performing the act)",
                           act.get("giver", []), act.get("giver_adlibs"),
                           act.get("giver_mouth", False))
            # receiver
            _emit_role("Receiver (the partner receiving it)",
                       act.get("receiver", []), act.get("receiver_adlibs"),
                       act.get("receiver_mouth", False))

    if pov:
        who = "the woman" if pov_gender == "female" else "the man"
        out.append(f"\n  POV note: the camera is {who} (viewer). The ON-SCREEN "
                   "partner is the one who speaks/sounds; the camera-holder stays "
                   "mostly non-verbal (breath, the odd word).")

    return "\n".join(out) + "\n"


def _speech_topic(intent):
    """Extract a named speech subject from the intent — 'talks about apples',
    'explains the plan', 'rants about traffic' → the topic string, else ''."""
    t = (intent or "").strip()
    if not t:
        return ""
    m = re.search(
        r"\b(?:talks?|talking|speaks?|speaking|chats?|chatting|rants?|ranting|"
        r"discuss(?:es)?|discussing|explains?|explaining|describes?|describing|"
        r"tells?\s+(?:me|us|him|her|them)?\s*about|goes?\s+on\s+about)\b"
        r"\s*(?:about|of|on)?\s+(.{3,80}?)(?:[.,;!?]|$)",
        t, re.I)
    if not m:
        return ""
    topic = m.group(1).strip().rstrip(".")
    # "dirty to me" etc. is a register cue, not a topic
    if re.match(r"^dirty\b", topic, re.I):
        return ""
    return topic


def dialogue_block(*, tier="standard", intent="", scenario_block="",
                   explicit=False, seed=None, lines_per_register=12,
                   use_adlibs=True, pov=False, pov_gender="female",
                   mouth_level=None, max_active=3):
    """Build the injected dialogue block.

    Returns "" for the silent tier. Otherwise returns a verbatim line bank for
    the activated mood registers, an ad-lib pool, and — when explicit AND a
    specific act is detected — a role-split, mouth-aware ACT dialogue section.

    lines_per_register is generous by design — only activated registers inject,
    so large pools never bloat unrelated scenes. Variety > short lists.
    """
    t = (tier or "standard").lower()
    if t in ("none", "silent", "off"):
        return ""  # silent handled by the tier budget block

    rng = random.Random(seed if seed is not None else random.randrange(1 << 30))

    # Talkative / rich scenes can hold more registers without drowning
    cap = max_active
    if t in ("talkative", "chatty", "dense", "rich"):
        cap = max(cap, 3)
    active = detect_registers(intent, scenario_block, explicit, max_active=cap)
    detected = bool(active)
    if not active:
        active = _default_registers(t, explicit, intent, scenario_block)

    # Mouth heat can bias which extra register samples we surface
    ml = (mouth_level or "").lower().strip()
    if ml == "asmr" and "asmr" not in active and "asmr" in REGISTERS:
        active = ["asmr"] + [a for a in active if a != "asmr"]
        active = active[:cap]
    elif ml in ("intense", "aggressive") and explicit and "dirty_talk" not in active:
        if any(x in f"{intent} {scenario_block}".lower() for x in ("fuck", "sex", "cock", "pussy", "dirty")):
            active = list(active) + ["dirty_talk"]
            active = active[: cap + 1]

    seen = set()
    active = [k for k in active if not (k in seen or seen.add(k))]

    out = ["\n━━ DIALOGUE BANK — VOICE GUIDE FOR THIS SCENE ━━"]
    out.append(
        "PRIORITY ORDER for every spoken line (non-negotiable):\n"
        "  1. CONTEXT FIRST — invent lines about THIS scene. Name a prop, a place "
        "fact, a stake, or the action happening now (the cup, the bus, the bar, "
        "the phone, the next stop, the button, the rain). Empty stock flirt "
        "(\"caught you looking\" / \"is that so\" / \"come and get it\" / "
        "\"you wish\" / \"make me\") is a FAILURE unless the intent is literally that game.\n"
        "  2. The pools below are VOICE samples only — rhythm, heat, delivery, "
        "bracket flavour. Prefer writing a NEW line in that voice. Use a pool "
        "line verbatim ONLY if it fits the exact moment and still names the scene.\n"
        "  3. Never paste three pool lines in a row. Never reuse a line twice. "
        "Never reuse the same 3+ word phrase across lines (no loops).\n"
        "  4. VARIETY TAX: if two lines could swap without changing meaning, rewrite one.\n"
        "  5. Do NOT default to pleading/begging/desperate delivery unless the intent "
        "asks for it. Natural conversational heat is preferred.\n"
        "  6. GROK EDGE: prefer the surprising concrete detail (bus number, sticky glass, "
        "wrong wrench size, cracked phone) over generic heat words.\n"
        "  7. NO META: never speak about cuts, cameras, scenes, clips, or the prompt.\n"
        "A talking shot that ignores the intent's subject is worse than fewer lines.\n"
        "Wrap each line in an emotion bracket, inline where the mouth is free."
    )
    if detected:
        names = ", ".join(REGISTERS[k]["name"] for k in active)
        out.append(f"Activated by your prompt: {names}.")
    else:
        out.append("No specific dialogue style requested — default palette below.")

    topic = _speech_topic(intent)
    if topic:
        out.append(
            f"\n━━ TOPIC LOCK ━━\nThe user named a speech subject: \"{topic}\". "
            f"At least two out of every three spoken lines must be ABOUT "
            f"{topic} — specific, concrete, on-subject sentences (opinions, "
            f"observations, questions about it). Pool lines are seasoning "
            f"between topical lines, never the main dialogue."
        )
        if not detected:
            # Off-bank topic with only default registers: the pools can't
            # cover the subject, so serve a small DELIVERY sample instead of
            # drowning the topic in 30+ irrelevant lines.
            out.append(
                "The register samples below show DELIVERY only — tone, rhythm, "
                "brackets. Do not copy their content; write your own lines "
                f"about {topic} in that voice."
            )
            lines_per_register = min(lines_per_register, 4)

    # Registers the user summoned BY NAME serve their full pool — "she speaks
    # dirty" means dirty talk, not the PG variant of it.
    _UNLOCK_ON_REQUEST = {"dirty_talk", "begging", "dominant", "submissive", "degradation", "findom", "joi_edge", "facesitting", "pegging", "cuckold", "bondage", "sph", "brat", "body_worship", "giantess"}
    intent_lo = (intent or "").lower()

    def _asked_for(reg_key):
        return any(_trigger_hit(trig, intent_lo) for trig in REGISTERS[reg_key]["triggers"])

    for k in active:
        reg = REGISTERS[k]
        unlock = explicit or (k in _UNLOCK_ON_REQUEST and _asked_for(k))
        pool = _pool_for(k, unlock, rng)[:lines_per_register]
        brk = " / ".join(reg["brackets"][:3])
        out.append(f"\n【{reg['name']}】 voice: {reg['delivery']}")
        out.append(f"  brackets to use: ({brk})")
        quoted = "  ".join(f"\"{ln}\"" for ln in pool)
        out.append(f"  lines: {quoted}")

    if use_adlibs:
        # gather a spread of ad-libs across the active registers; top up from the
        # global pool so even a single-register scene gets a usable handful.
        pool = []
        for k in active:
            pool += _adlibs_for(k, rng, n=4)
        pool += list(_GLOBAL_ADLIBS)
        seen2, spread = set(), []
        for a in pool:
            if a not in seen2:
                seen2.add(a)
                spread.append(a)
        spread = spread[:10]
        out.append("\n【Ad-libs】 non-verbal vocal beats — weave these as PLAIN PROSE "
                   "into the action line (never *stars*, never markdown). Example: "
                   "\"she leans in, breath catches, and says (soft): …\". "
                   "An occupied mouth uses these instead of words:")
        out.append("  " + "  · ".join(spread))

    # Act-specific, role-split dialogue — EXPLICIT-GATED (all act lines are
    # explicit by nature). Fires when a sex act is detected in intent/scenario.
    if explicit:
        act = render_act_block(intent, scenario_block, pov=pov,
                               pov_gender=pov_gender, seed_rng=rng)
        if act:
            out.append(act)

    return "\n".join(out) + "\n"


def explain(intent, scenario_block="", explicit=False, tier="standard"):
    active = detect_registers(intent, scenario_block, explicit)
    return {
        "detected": active,
        "used": active or _default_registers(tier, explicit, intent, scenario_block),
        "explicit": explicit,
        "tier": tier,
    }


# ── Expand pools (only activated registers inject — size is free) ───────────
try:
    from .dialogue_boost_ld import apply as _boost_apply
except ImportError:
    from dialogue_boost_ld import apply as _boost_apply
_boost_apply(REGISTERS, ACT_REGISTERS)
