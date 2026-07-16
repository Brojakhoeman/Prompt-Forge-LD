"""VRAM flush before handing the GPU to llama — same idea as the big node, kept tiny."""


def flush_vram(tag="PromptLab", *, light: bool = False):
    """Unload / free GPU memory.

    light=True: only soft CUDA cache clear (fast, ~ms–few hundred ms).
    light=False: full Comfy unload_all_models (can stall several seconds when VRAM is packed).
    Use light on Queue/Run hand-off so the click doesn't freeze 10s waiting to unload.
    """
    if not light:
        try:
            import comfy.model_management as mm
            mm.unload_all_models()
            mm.soft_empty_cache()
            print(f"[{tag}] ComfyUI models unloaded.")
        except Exception as e:
            print(f"[{tag}] model_management flush skipped: {e}")
    else:
        try:
            import comfy.model_management as mm
            mm.soft_empty_cache()
        except Exception:
            pass
    try:
        import gc
        gc.collect()
    except Exception:
        pass
    try:
        import torch
        if torch.cuda.is_available():
            if not light:
                try:
                    torch.cuda.synchronize()
                except Exception:
                    pass
            torch.cuda.empty_cache()
            try:
                torch.cuda.ipc_collect()
            except Exception:
                pass
            free, total = torch.cuda.mem_get_info()
            print(
                f"[{tag}] VRAM after {'light ' if light else ''}flush — "
                f"free: {free / 1024 ** 3:.1f} GB / {total / 1024 ** 3:.1f} GB"
            )
    except Exception as e:
        print(f"[{tag}] CUDA flush skipped: {e}")
