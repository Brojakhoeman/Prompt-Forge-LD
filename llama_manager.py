"""
llama_manager.py — ONE shared llama-server lifecycle for all LoRa-Daddy brains
==============================================================================
Before this module, the LTX director, the Flux brain and the Ideogram brain each
ran their OWN boot/kill/health code against the SAME llama-server.exe. That meant
booting from one brain and killing from another could leave stale state, VRAM that
wouldn't free, and a Kill button that had to fan out to three routes.

Now every brain calls THIS module. There is a single process handle, a single
"is vision loaded" flag, and a single health check, so the three modes cooperate
instead of fighting over the stove.

Public API (all module-level — shared state, no per-brain copies):
    ensure(model_path, mmproj_path=None, server_url=..., exe=..., ctx=16384,
           backend="llama.cpp (managed)") -> str   # "OK ..." or "ERR ..."
    is_healthy(server_url=...) -> bool
    kill(backend="llama.cpp (managed)") -> None
"""

import os
import time
import subprocess
import urllib.request

# Defaults — env overrides first, then common Windows paths.
LLAMA_EXE     = os.environ.get("PFLD_LLAMA_EXE") or os.environ.get("LLAMA_SERVER_EXE") or r"C:\llama\llama-server.exe"
MODELS_DIR    = os.environ.get("PFLD_MODELS_DIR") or os.environ.get("LLAMA_MODELS_DIR") or r"C:\models"
DEFAULT_URL   = os.environ.get("PFLD_SERVER_URL") or "http://localhost:8080"
DEFAULT_PORT  = "8080"

# ── single shared state ───────────────────────────────────────────────────────
_proc = None              # the one llama-server subprocess we own (managed backend)
_vision_loaded = False    # whether the running server was launched with --mmproj


# ── single shared CONNECTION config ───────────────────────────────────────────
# THE one place backend / url / model live. The cog panel writes here via
# set_conn(); every brain (cinematic, flux, ideogram) reads here via the getters.
# No brain keeps its own backend/url/model anymore.
MANAGED  = "llama.cpp (managed)"
LMSTUDIO = "LM Studio (OpenAI-compatible)"
OLLAMA   = "Ollama"
BACKENDS = [MANAGED, LMSTUDIO, OLLAMA]

DEFAULT_PORTS = {
    MANAGED:  "http://127.0.0.1:8080",
    LMSTUDIO: "http://127.0.0.1:1234",
    OLLAMA:   "http://127.0.0.1:11434",
}

CONN = {
    "backend":      MANAGED,                 # one of BACKENDS
    "server_url":   DEFAULT_PORTS[MANAGED],  # where the server lives
    "remote_model": "local",                 # model id for connect-only backends
    "models_dir":   MODELS_DIR,              # gguf folder for managed backend
    "llama_exe":    LLAMA_EXE,               # path to llama-server.exe
}


def is_managed(backend=None):
    return (backend or CONN["backend"]) == MANAGED


def conn_url():
    return (CONN.get("server_url") or DEFAULT_PORTS.get(CONN["backend"], DEFAULT_URL)).rstrip("/")


def conn_backend():
    return CONN.get("backend") or MANAGED


def conn_model():
    return CONN.get("remote_model") or "local"


def detect_model_family(model_id=None) -> str:
    """Coarse family for request tweaks: qwen | gemma | llama | mistral | other."""
    m = (model_id if model_id is not None else conn_model()) or ""
    m = str(m).lower().replace(" ", "").replace("_", "-")
    if "qwen" in m:
        return "qwen"
    if "gemma" in m:
        return "gemma"
    if "llama" in m or "l3." in m or m.startswith("l3"):
        return "llama"
    if "mistral" in m or "mixtral" in m:
        return "mistral"
    return "other"


def chat_request_extras(model_id=None) -> dict:
    """Extra OpenAI-compatible fields for /v1/chat/completions by model family.

    Qwen3.6 defaults thinking ON — that burns tokens and can pollute shot scripts.
    We force enable_thinking=false for Qwen. Gemma/others: same kwargs are usually
    ignored or accepted; callers may still fall back if the server returns 400.
    """
    family = detect_model_family(model_id)
    extras = {}
    if family == "qwen":
        # Official Qwen3.6 path (LM Studio / llama.cpp --jinja)
        extras["chat_template_kwargs"] = {
            "enable_thinking": False,
            "preserve_thinking": False,
        }
        # Some LM Studio builds also honor these aliases
        extras["reasoning"] = False
    elif family == "gemma":
        # Harmless if unsupported; keeps parity with prior retry behavior
        extras["chat_template_kwargs"] = {"enable_thinking": False}
    return extras


def chat_request_attempts(model_id=None) -> list:
    """Ordered payload overlays to try (first preferred). Empty {} last = plain request."""
    primary = chat_request_extras(model_id)
    attempts = []
    if primary:
        attempts.append(primary)
        # Minimal Qwen-only fallback if full extras 400
        if detect_model_family(model_id) == "qwen":
            attempts.append({"chat_template_kwargs": {"enable_thinking": False}})
    attempts.append({})
    # de-dupe while preserving order
    seen, out = set(), []
    for a in attempts:
        key = _json.dumps(a, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out


def conn_models_dir():
    return CONN.get("models_dir") or MODELS_DIR


def conn_llama_exe():
    return CONN.get("llama_exe") or LLAMA_EXE


def set_conn(backend=None, server_url=None, remote_model=None, models_dir=None, llama_exe=None):
    """The cog panel's single entry point. Updates shared CONN, frees a managed
    server if we're switching away from managed, and returns a status dict the
    UI uses for its green/red dot. EVERY brain sees the change immediately."""
    if backend in BACKENDS:
        CONN["backend"] = backend
    url = (server_url or "").strip()
    if not url:
        url = DEFAULT_PORTS.get(CONN["backend"], DEFAULT_URL)
    CONN["server_url"] = url.rstrip("/")
    if remote_model is not None:
        CONN["remote_model"] = (remote_model or "local").strip() or "local"
    if models_dir:
        if os.path.isdir(models_dir):
            CONN["models_dir"] = models_dir
    if llama_exe:
        if os.path.isfile(llama_exe):
            CONN["llama_exe"] = llama_exe
    # Switching away from managed? Free any llama-server we were running.
    if not is_managed() and is_healthy(DEFAULT_PORTS[MANAGED], MANAGED):
        kill(MANAGED)
    healthy = is_healthy(CONN["server_url"], CONN["backend"])
    return {"backend": CONN["backend"], "server_url": CONN["server_url"],
            "remote_model": CONN["remote_model"], "models_dir": CONN["models_dir"],
            "llama_exe": CONN["llama_exe"], "healthy": healthy}


def _port_from_url(url):
    try:
        tail = url.rstrip("/").split("//", 1)[-1]
        if ":" in tail:
            return tail.split(":", 1)[1].split("/", 1)[0] or DEFAULT_PORT
    except Exception:
        pass
    return DEFAULT_PORT


def is_healthy(server_url=DEFAULT_URL, backend="llama.cpp (managed)"):
    """Cheap GET that proves the server is alive. Each backend has its own probe."""
    path = {"Ollama": "/api/tags",
            "LM Studio (OpenAI-compatible)": "/v1/models"}.get(backend, "/health")
    try:
        req = urllib.request.Request(server_url.rstrip("/") + path)
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def ensure(model_path, mmproj_path=None, server_url=DEFAULT_URL, exe=LLAMA_EXE,
           ctx=16384, backend="llama.cpp (managed)"):
    """Make sure a llama-server is up with the right vision capability. Boots one
    if needed, restarts if the vision state doesn't match the request. Returns a
    short status string starting with 'OK' or 'ERR'."""
    global _proc, _vision_loaded

    if backend != "llama.cpp (managed)":
        # Ollama / LM Studio own their own persistent server — only connect.
        if is_healthy(server_url, backend):
            return "OK connected"
        name = "Ollama" if backend == "Ollama" else "LM Studio"
        return f"ERR can't reach {name} at {server_url} — is it running?"

    want_vision = bool(mmproj_path) and mmproj_path not in ("None (text-only)", "None")

    # Already running? Keep it unless the vision capability is wrong.
    if is_healthy(server_url, backend):
        if want_vision == _vision_loaded:
            return "OK already running"
        kill(backend)
        time.sleep(1)

    if not os.path.isfile(exe):
        return f"ERR llama-server not found: {exe}"
    if not os.path.isfile(model_path):
        return f"ERR model not found: {model_path}"

    port = _port_from_url(server_url)
    cmd = [exe, "-m", model_path, "-ngl", "99", "--ctx-size", str(int(ctx)),
           "--flash-attn", "on", "--reasoning-budget", "0", "--port", port]

    if want_vision:
        # mmproj_path may be a bare filename (resolve against MODELS_DIR) or absolute.
        mp = mmproj_path if os.path.isabs(mmproj_path) else os.path.join(MODELS_DIR, mmproj_path)
        if not os.path.isfile(mp):
            return f"ERR mmproj not found: {mp}"
        cmd += ["--mmproj", mp]

    try:
        if os.name == "nt":
            _proc = subprocess.Popen(cmd, creationflags=0x00000200)  # CREATE_NEW_PROCESS_GROUP
        else:
            _proc = subprocess.Popen(cmd, start_new_session=True)
    except Exception as e:
        return f"ERR launch failed: {e}"

    for _ in range(60):  # up to ~120s for a cold model load
        time.sleep(2)
        if is_healthy(server_url, backend):
            _vision_loaded = want_vision
            return "OK started" + (" (vision)" if want_vision else "")
    return "ERR health check timed out (model still loading after 120s?)"


def adopt(proc, vision=False):
    """Register a process spawned elsewhere (e.g. the LTX async boot path that
    must yield status lines and can't use the blocking ensure()) so a later
    kill() from ANY brain still tears it down and resets shared state."""
    global _proc, _vision_loaded
    _proc = proc
    _vision_loaded = bool(vision)


def kill(backend="llama.cpp (managed)"):
    """Hard-kill the managed llama-server and reset shared state. The OS frees the
    process's VRAM when the executable dies, so no torch IPC dance is needed.
    Ollama / LM Studio are never touched — they own their own lifecycle."""
    global _proc, _vision_loaded
    if backend != "llama.cpp (managed)":
        return
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/IM", "llama-server.exe"],
                           capture_output=True, timeout=10)
        else:
            subprocess.run(["pkill", "-f", "llama-server"], capture_output=True, timeout=10)
    except Exception:
        pass
    if _proc is not None:
        try:
            _proc.kill()
        except Exception:
            pass
        _proc = None
    _vision_loaded = False


# ── shared chat + eviction (backend-agnostic) ─────────────────────────────────
import json as _json

# How long (seconds) a connect-only backend keeps the model resident after our
# last request. Short = auto-frees VRAM between prompts. Managed ignores this.
IDLE_TTL = 30


def chat(messages, *, temperature=0.8, max_tokens=1024, seed=None,
         stream=False, extra=None):
    """ONE chat entry point for every brain. Hits the OpenAI-compatible
    /v1/chat/completions on whatever backend CONN points at, attaches a short
    TTL for connect-only backends so they auto-evict, and returns the assistant
    text (with <think> stripped). Raises on transport/HTTP error.

    Always sends a seed. llama-server (and most OpenAI-compatible backends)
    only randomize their sampler RNG when no seed is given at all — omit it
    and two back-to-back requests can land on the same draw and reproduce the
    same completion even at temperature > 0. If the caller doesn't supply one
    we generate a fresh random seed here so every call genuinely varies."""
    import random
    if seed is None:
        seed = random.randint(0, 2**31 - 1)
    payload = {
        "model": conn_model(),
        "messages": messages,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "stream": bool(stream),
        "seed": int(seed),
    }
    if not is_managed():
        payload["ttl"] = IDLE_TTL          # auto-unload after we go quiet
    # Model-family tweaks (e.g. Qwen thinking off) unless caller overrides
    for k, v in chat_request_extras().items():
        payload.setdefault(k, v)
    if extra:
        payload.update(extra)
    data = _json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(conn_url() + "/v1/chat/completions", data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=180) as r:
        resp = _json.loads(r.read().decode("utf-8"))
    content = "".join(c.get("message", {}).get("content", "")
                      for c in resp.get("choices", []))
    import re
    return re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()


def _evict_remote():
    """Unload the model from a connect-only backend's VRAM. LM Studio exposes a
    native unload endpoint; we also send a ttl=0 nudge as a version-agnostic
    fallback. Best-effort — returns True if either path returned 200."""
    ok = False
    base = conn_url()
    model = conn_model()
    # 1) Native LM Studio unload (0.4.0+). instance_id == the loaded model id.
    try:
        body = _json.dumps({"instance_id": model}).encode()
        req = urllib.request.Request(base + "/api/v1/models/unload", data=body,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        with urllib.request.urlopen(req, timeout=10) as r:
            ok = ok or (r.status == 200)
    except Exception:
        pass
    # 2) ttl=0 nudge via the chat API — works without auth on every version that
    #    honours TTL. Empty turn, 1 token, model evicts right after.
    if not ok:
        try:
            body = _json.dumps({"model": model, "ttl": 0, "max_tokens": 1,
                                "messages": [{"role": "user", "content": "."}]}).encode()
            req = urllib.request.Request(base + "/v1/chat/completions", data=body,
                                         headers={"Content-Type": "application/json"},
                                         method="POST")
            with urllib.request.urlopen(req, timeout=15) as r:
                ok = ok or (r.status == 200)
        except Exception:
            pass
    return ok


def free():
    """ONE button for the whole toolkit. Managed → kill the process. Connect-only
    (LM Studio / Ollama) → ask it to unload the model from VRAM. Whatever the cog
    panel is pointed at, this frees it."""
    if is_managed():
        kill(MANAGED)
        return "killed managed llama-server"
    return "evicted remote model" if _evict_remote() else "evict request sent (check server)"
