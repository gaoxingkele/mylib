"""Codex CLI transport with an explicit mock mode and bounded process cleanup."""

from __future__ import annotations

import os
import shlex
import shutil
import signal
import subprocess
from pathlib import Path

MOCK_ENV = "PAPER_HARNESS_TRANSPORT"


def is_mock() -> bool:
    return os.environ.get(MOCK_ENV, "").strip().lower() == "mock"


def codex_exec(
    prompt: str,
    cwd: str | Path,
    sandbox: str = "read-only",
    model: str | None = None,
    command: str = "codex exec",
    timeout: int | None = None,
) -> tuple[int, str]:
    """Run ``codex exec`` with the prompt on stdin and return code plus output."""
    if is_mock():
        return 0, (
            f"[MOCK TRANSPORT] CLI not invoked. sandbox={sandbox} "
            f"model={model} prompt_chars={len(prompt)}"
        )
    if timeout is None:
        timeout = int(os.environ.get("PAPER_HARNESS_CODEX_TIMEOUT", "1800"))
    return _run_codex(prompt, cwd, sandbox, model, command, timeout)


def _run_codex(
    prompt: str,
    cwd: str | Path,
    sandbox: str,
    model: str | None,
    command: str,
    timeout: int,
) -> tuple[int, str]:
    argv = _command_argv(command) + ["-s", sandbox]
    if model:
        argv += ["-m", model]
    argv.append("-")
    popen_kwargs: dict[str, object] = {}
    if os.name == "nt":
        # Descendants of codex.exe may otherwise survive a TimeoutExpired and
        # retain handles to the stage worktree.
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True
    try:
        proc = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(cwd),
            **popen_kwargs,
        )
        try:
            stdout, stderr = proc.communicate(input=prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            _terminate_process_tree(proc)
            return 124, (
                f"codex exec timed out after {timeout}s; "
                "controlled process tree terminated"
            )
    except FileNotFoundError:
        return 127, f"command unavailable: {argv[0]} (is the Codex CLI on PATH?)"
    out = stdout or ""
    if proc.returncode != 0 and stderr:
        out = out + "\n[stderr]\n" + stderr
    return int(proc.returncode or 0), out


def _terminate_process_tree(proc: subprocess.Popen[str], grace_seconds: float = 5.0) -> None:
    """Terminate only the process tree created for one transport call."""
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
            capture_output=True,
            text=True,
            timeout=max(grace_seconds, 1.0),
            check=False,
        )
    else:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        proc.communicate(timeout=grace_seconds)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"transport process tree {proc.pid} did not terminate") from exc


def _command_argv(command: str) -> list[str]:
    """Resolve a complete Windows Codex bundle when a stale shim lacks helpers."""
    parts = [part.strip('"') for part in shlex.split(command, posix=False)]
    if not parts:
        return ["codex", "exec"]
    executable = Path(parts[0])
    name = executable.name.lower()
    if os.name == "nt" and name in {"codex", "codex.exe"}:
        local = Path(os.environ.get("LOCALAPPDATA", "")) / "OpenAI" / "Codex" / "bin"
        bundled = sorted(
            (
                path for path in local.glob("*/codex.exe")
                if (path.parent / "codex-windows-sandbox-setup.exe").exists()
            ),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if bundled:
            parts[0] = str(bundled[0])
        elif shutil.which(parts[0]):
            parts[0] = str(Path(shutil.which(parts[0]) or parts[0]))
    return parts
