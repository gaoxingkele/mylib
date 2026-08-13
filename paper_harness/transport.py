"""Codex CLI 传输层：codex_exec subprocess 包装 + mock 模式开关。

mock 模式：设置环境变量 PAPER_HARNESS_TRANSPORT=mock 后，codex_exec 不调用任何 CLI，
直接返回占位输出。测试与演示用，不消耗 API。
"""

from __future__ import annotations

import os
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
    timeout: int = 1800,
) -> tuple[int, str]:
    """调用 `codex exec -s <sandbox> [-m MODEL] -`（prompt 走 stdin），返回 (exit_code, stdout)。

    command 可在 config.toml 的 [transport] command 替换（预留 kimi/claude CLI）。
    """
    if is_mock():
        return 0, f"[MOCK TRANSPORT] 未调用 CLI。sandbox={sandbox} model={model} prompt_chars={len(prompt)}"
    return _run_codex(prompt, cwd, sandbox, model, command, timeout)


def _run_codex(
    prompt: str,
    cwd: str | Path,
    sandbox: str,
    model: str | None,
    command: str,
    timeout: int,
) -> tuple[int, str]:
    argv = command.split() + ["-s", sandbox]
    if model:
        argv += ["-m", model]
    argv.append("-")  # 从 stdin 读 prompt
    try:
        proc = subprocess.run(
            argv,
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(cwd),
            timeout=timeout,
        )
    except FileNotFoundError:
        return 127, f"命令不可用: {argv[0]}（codex CLI 是否在 PATH？）"
    except subprocess.TimeoutExpired:
        return 124, f"codex exec 超时（>{timeout}s）"
    out = proc.stdout or ""
    if proc.returncode != 0 and proc.stderr:
        out = out + "\n[stderr]\n" + proc.stderr
    return proc.returncode, out
