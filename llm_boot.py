"""LLM boot helpers and think-tag filter — shared by api and generation_core."""

import asyncio
import os
import socket

try:
    from . import llama_manager as llm
except ImportError:
    import llama_manager as llm


class ThinkFilter:
    """Strip model reasoning blocks from streamed text.

    Handles common wrappers:
      <think>…</think>
      <thinking>…</thinking>
      <redacted_reasoning>…</redacted_reasoning>  (some servers)
    """

    # (open_tag, close_tag) — longest open first when scanning
    _TAGS = (
        ("<redacted_reasoning>", "</redacted_reasoning>"),
        ("<thinking>", "</thinking>"),
        ("<think>", "</think>"),
    )

    def __init__(self):
        self.inside = False
        self.close_tag = ""
        self.buf = ""

    def feed(self, chunk):
        self.buf += chunk
        out = []
        while True:
            if self.inside:
                end = self.buf.find(self.close_tag)
                if end == -1:
                    # keep tail that might be a partial close tag
                    keep = max(len(t[1]) for t in self._TAGS)
                    self.buf = self.buf[-keep:]
                    break
                self.buf = self.buf[end + len(self.close_tag):]
                self.inside = False
                self.close_tag = ""
            else:
                # find earliest open tag
                best_i, best_open, best_close = None, None, None
                for open_t, close_t in self._TAGS:
                    i = self.buf.find(open_t)
                    if i != -1 and (best_i is None or i < best_i):
                        best_i, best_open, best_close = i, open_t, close_t
                if best_i is None:
                    keep = max(len(t[0]) for t in self._TAGS)
                    safe = len(self.buf) - keep
                    if safe > 0:
                        out.append(self.buf[:safe])
                        self.buf = self.buf[safe:]
                    break
                out.append(self.buf[:best_i])
                self.buf = self.buf[best_i + len(best_open):]
                self.inside = True
                self.close_tag = best_close
        return "".join(out)

    def flush(self):
        if self.inside:
            self.buf = ""
        out, self.buf = self.buf, ""
        return out


def _models_dir():
    return llm.conn_models_dir()


def _port_in_use(port=8080):
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=0.4):
            return True
    except OSError:
        return False


async def _health_multi(url):
    try:
        import aiohttp
        base = url.rstrip("/")
        async with aiohttp.ClientSession() as s:
            for path in ("/health", "/v1/models", "/models"):
                try:
                    async with s.get(
                        f"{base}{path}", timeout=aiohttp.ClientTimeout(total=4)
                    ) as r:
                        if r.status == 200:
                            return True
                except Exception:
                    continue
    except Exception:
        pass
    return llm.is_healthy(url, llm.conn_backend())


def _spawn_sync(model_file, mmproj_file, need_vision, ctx=16384):
    """Use llama_manager.ensure — same path that works from Comfy node."""
    models = _models_dir()
    model_path = os.path.join(models, model_file)
    mmproj_path = None
    if need_vision and mmproj_file and mmproj_file != "None (text-only)":
        mmproj_path = os.path.join(models, mmproj_file)
    return llm.ensure(
        model_path,
        mmproj_path=mmproj_path,
        server_url=llm.conn_url(),
        ctx=ctx,
    )


async def boot_llama(model_file, mmproj_file, need_vision):
    """
    Boot or attach to llama-server.
    Vision (mmproj) usually requires a fresh server start — do not short-circuit
    on /health when I2V needs mmproj; delegate to ensure() so it restarts if needed.
    """
    url = llm.conn_url()

    if not llm.is_managed():
        if await _health_multi(url):
            yield f"LLM ready ({llm.conn_backend()})"
        else:
            yield f"error:can't reach {llm.conn_backend()} at {url} — is the server running with a model loaded?"
        return

    if need_vision:
        healthy = await _health_multi(url)
        if healthy:
            yield "Checking vision (mmproj) — restart if not active…"
        else:
            yield "Launching llama-server with vision (mmproj)…"
        result = await asyncio.to_thread(_spawn_sync, model_file, mmproj_file, True)
        if result.startswith("OK"):
            yield "LLM ready (vision)"
            return
        if result.startswith("ERR"):
            yield f"error:{result[4:].strip()}"
            return
        yield f"error:unexpected boot result: {result}"
        return

    if await _health_multi(url):
        yield "LLM ready"
        return

    port = "8080"
    try:
        port = llm._port_from_url(url)
    except Exception:
        pass

    if _port_in_use(port):
        yield "Waiting for existing llama-server…"
        for i in range(90):
            await asyncio.sleep(2)
            if await _health_multi(url):
                yield "LLM ready"
                return
            if (i + 1) % 5 == 0:
                yield f"Still waiting… {(i + 1) * 2}s"
        yield f"error:port {port} busy but server not healthy after 180s"
        return

    exe = llm.conn_llama_exe()
    models = _models_dir()
    model_path = os.path.join(models, model_file)
    if not os.path.isfile(exe):
        yield f"error:llama-server not found: {exe}"
        return
    if not os.path.isfile(model_path):
        yield f"error:model not found: {model_path}"
        return

    yield "Launching llama-server…"
    result = await asyncio.to_thread(_spawn_sync, model_file, mmproj_file, need_vision)
    if result.startswith("OK"):
        yield "LLM ready"
        return
    if result.startswith("ERR"):
        yield f"error:{result[4:].strip()}"
        return
    yield f"error:unexpected boot result: {result}"
