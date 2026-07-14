"""Minimal LTX stability negative."""

BASE = [
    "morphing", "distortion", "warping", "flicker", "jitter",
    "bad quality", "blurry", "watermark", "text", "logo",
    "extra limbs", "deformed hands", "wrong hand count",
    "twisted neck", "head facing backward", "head only turn", "neck twist", "head swivel without body", "static", "still image",
    "subtitles", "background music",
]


def build(pov=False):
    terms = list(BASE)
    if pov:
        terms.extend(["third person view", "visible camera", "filmed from behind"])
    return ", ".join(terms)