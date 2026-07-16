"""
PFLD_PACK — bundled PromptForge LD output for a single ComfyUI socket.
Wire Prompt Lab → PFLD Unpack to recover image / prompts / dimensions.
"""

PFLD_PACK = "PFLD_PACK"


def make_pack(image, positive, negative, width, height):
    return {
        "image": image,
        "positive": (positive or "").strip(),
        "negative": (negative or "").strip(),
        "width": int(width),
        "height": int(height),
    }


def unpack(pack):
    if not isinstance(pack, dict):
        raise ValueError("[PFLD Unpack] Expected PFLD_PACK bundle — connect PromptForge LD pack output.")
    for key in ("image", "positive", "negative", "width", "height"):
        if key not in pack:
            raise ValueError(f"[PFLD Unpack] Bundle missing '{key}'.")
    return (
        pack["image"],
        pack["positive"],
        pack["negative"],
        int(pack["width"]),
        int(pack["height"]),
    )
