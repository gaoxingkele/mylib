#!/usr/bin/env python3
"""
Codex Review Loop - Stop Hook
==============================
Runs Codex CLI to review the current project when Claude finishes a turn.
If Codex finds issues, feeds them back to Claude to keep iterating.
Stops when Codex says PASS or max rounds reached.

Per-project config lives in .claude/codex-review.state.json:
    {
      "enabled": true,
      "round": 0,
      "max_rounds": 3,
      "codex_cmd": "codex exec \"...\""
    }

Hook stdin (from Claude Code):
    {
      "session_id": "...",
      "transcript_path": "...",
      "cwd": "...",
      "stop_hook_active": false,
      "last_assistant_message": "..."   # may be absent on older versions
    }

Hook stdout protocol:
    - exit 0 with no output  -> allow Claude to stop
    - print JSON {"decision":"block","reason":"...","systemMessage":"..."} -> feed reason back
"""
import json
import os
import subprocess
import sys
from pathlib import Path

STATE_FILENAME = ".claude/codex-review.state.json"
DEFAULT_CODEX_CMD = (
    'codex exec "Review the recent code changes in this project. '
    'List concrete issues (bugs, smells, missing tests, security). '
    'End your response with exactly one line: VERDICT: PASS  or  VERDICT: FAIL"'
)


def load_state(project_dir: Path) -> dict | None:
    state_file = project_dir / STATE_FILENAME
    if not state_file.exists():
        return None
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_state(project_dir: Path, state: dict) -> None:
    state_file = project_dir / STATE_FILENAME
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def emit_block(reason: str, system_msg: str) -> None:
    print(json.dumps({
        "decision": "block",
        "reason": reason,
        "systemMessage": system_msg,
    }))
    sys.exit(0)


def main() -> None:
    # Read stdin payload (must consume even if unused)
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        payload = {}

    # Don't recurse: if Claude Code is already in a stop-hook-triggered turn, just allow stop
    if payload.get("stop_hook_active"):
        sys.exit(0)

    cwd = Path(payload.get("cwd") or os.getcwd())
    state = load_state(cwd)

    # Not configured for this project -> normal exit
    if not state or not state.get("enabled"):
        sys.exit(0)

    round_n = int(state.get("round", 0))
    max_rounds = int(state.get("max_rounds", 3))
    codex_cmd = state.get("codex_cmd") or DEFAULT_CODEX_CMD

    # Round budget exhausted -> reset and allow stop
    if round_n >= max_rounds:
        state["round"] = 0
        save_state(cwd, state)
        sys.exit(0)

    # Run codex CLI
    try:
        proc = subprocess.run(
            codex_cmd,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=600,
        )
        review = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
        review = review.strip()
    except subprocess.TimeoutExpired:
        review = "[codex review timed out after 600s]"
    except FileNotFoundError:
        # codex not installed -> let Claude stop quietly
        sys.stderr.write("codex CLI not found; skipping review\n")
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"codex review failed: {e}\n")
        sys.exit(0)

    # PASS verdict -> reset round counter and let Claude stop
    if "VERDICT: PASS" in review.upper().replace("：", ":"):
        state["round"] = 0
        save_state(cwd, state)
        sys.exit(0)

    # Otherwise, block and feed Codex's notes back to Claude
    next_round = round_n + 1
    state["round"] = next_round
    save_state(cwd, state)

    reason = (
        f"Codex 评审 (第 {next_round}/{max_rounds} 轮) — 发现问题，请继续优化:\n\n"
        f"{review}\n\n"
        f"---\n"
        f"修复完后，如果你认为已经满足要求，正常结束即可，"
        f"Codex 会再次评审；连续 {max_rounds} 轮仍未通过会自动停止。"
    )
    system_msg = f"Codex review round {next_round}/{max_rounds} — issues found"
    emit_block(reason, system_msg)


if __name__ == "__main__":
    main()
