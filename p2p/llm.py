"""The only place in this repo that talks to a language model.

    complete(system, user, model) -> LLMResult

Two backends, picked by the P2P_LLM_BACKEND environment variable or auto-detected:
- "claude": the Claude Code command line (`claude -p`). Uses your Claude Code login: no API key, nothing to install.
- "api":    the Anthropic Python SDK (`pip install anthropic`). Needs ANTHROPIC_API_KEY in the environment or in `.env`.

The "claude" path is standard library only. Model names are the Claude Code aliases: haiku, sonnet, opus.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
ALIASES = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5"}


@dataclass
class LLMResult:
    text: str
    model: str
    backend: str
    duration_s: float
    cost_usd: Optional[float] = None
    structured: Optional[dict] = None
    error: Optional[str] = None


def load_dotenv() -> None:
    """Read KEY=VALUE lines of `.env` (repo root) into the environment, without overriding. No dependency needed."""
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def backend() -> str:
    load_dotenv()
    forced = os.environ.get("P2P_LLM_BACKEND")
    if forced:
        return forced
    if shutil.which("claude"):
        return "claude"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "api"
    raise RuntimeError("No LLM backend: install Claude Code (the `claude` command) or set ANTHROPIC_API_KEY (see .env.example).")


def complete(system: str, user: str, model: str = "haiku", schema: Optional[dict] = None, timeout: int = 180) -> LLMResult:
    """One completion. Never raises: an error comes back in `LLMResult.error` so an eval can count it."""
    name = "none"
    started = time.time()
    try:
        name = backend()
        if name == "claude":
            result = _claude_cli(system, user, model, schema, timeout)
        elif name == "api":
            result = _anthropic_api(system, user, model)
        else:
            raise RuntimeError(f"Unknown P2P_LLM_BACKEND '{name}' (use 'claude' or 'api')")
    except Exception as exc:  # noqa: BLE001 - the caller decides what an error means
        result = LLMResult(text="", model=model, backend=name, duration_s=0.0, error=f"{type(exc).__name__}: {exc}")
    result.duration_s = round(time.time() - started, 1)
    return result


def _claude_cli(system: str, user: str, model: str, schema: Optional[dict], timeout: int) -> LLMResult:
    exe = shutil.which("claude") or "claude"
    # With a schema, Claude Code needs a second turn to emit the structured output: hence 3 turns instead of 1.
    cmd = [exe, "-p", user, "--output-format", "json", "--model", model, "--system-prompt", system,
           "--tools", "", "--max-turns", "3" if schema else "1", "--no-session-persistence"]
    if schema:
        cmd += ["--json-schema", json.dumps(schema)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout, cwd=str(ROOT))
    if proc.returncode != 0:
        raise RuntimeError(f"claude -p exited {proc.returncode}: {(proc.stderr or proc.stdout).strip()[-600:]}")
    data = json.loads(proc.stdout)
    return LLMResult(text=data.get("result", "") or "", model=model, backend="claude", duration_s=0.0,
                     cost_usd=data.get("total_cost_usd"), structured=data.get("structured_output"))


def _anthropic_api(system: str, user: str, model: str) -> LLMResult:
    try:
        import anthropic  # type: ignore
    except ImportError as exc:
        raise RuntimeError("the 'api' backend needs `pip install anthropic`; or use the 'claude' backend") from exc
    client = anthropic.Anthropic()
    model_id = ALIASES.get(model, model)
    message = client.messages.create(model=model_id, max_tokens=1024, system=system,
                                     messages=[{"role": "user", "content": user}])
    text = "".join(getattr(block, "text", "") for block in message.content)
    return LLMResult(text=text, model=model_id, backend="api", duration_s=0.0)
