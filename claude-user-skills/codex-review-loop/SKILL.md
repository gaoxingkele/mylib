---
name: codex-review-loop
description: Set up or manage a Codex CLI pair-review loop in the current project. After Claude finishes a turn, Codex reviews the code and feeds issues back, looping until Codex says PASS or max rounds is reached. Use when the user wants pair-programming-style review with Codex, or asks to enable/disable/reset/configure the loop.
allowed-tools: Bash, Read, Write, Edit, Glob
---

# Codex Review Loop

A Stop-hook based pair-review loop. When Claude finishes a turn in a project where this is enabled, the hook runs Codex CLI to review the code; if Codex finds issues, the feedback is fed back to Claude as a new prompt and Claude keeps iterating. Loop ends when Codex outputs `VERDICT: PASS` OR a configurable round budget is exhausted.

## Architecture (read this first)

- **Global hook script**: `C:/Users/iamaf/.claude/skills/codex-review-loop/codex_review_hook.py`
  Single file, shared by all projects. Don't copy it per-project — projects only opt in.
- **Per-project state**: `<project>/.claude/codex-review.state.json`
  Holds `enabled`, `round`, `max_rounds`, `codex_cmd`. The hook script keys off this file — if it's missing or `enabled: false`, the hook is a no-op.
- **Per-project hook entry**: `<project>/.claude/settings.json` `hooks.Stop` array, pointing at the global script via `python "C:/Users/iamaf/.claude/skills/codex-review-loop/codex_review_hook.py"`.

## When invoked, figure out the user's intent

The user may want to:
1. **Enable** the loop in the current project (most common — first-time setup)
2. **Disable** it temporarily (flip `enabled: false` in state file)
3. **Reset** the round counter (set `round: 0`)
4. **Reconfigure** max rounds or the codex command
5. **Check status** (read state file + show current round)
6. **Remove** it entirely (delete state file + remove hook from settings.json)

If the user's request is ambiguous, ask once with AskUserQuestion. Default action when unclear: enable.

## Setup steps (enable in current project)

1. Determine project dir = current working directory. Confirm with user if it doesn't look like a project root (no `.git`, no obvious source files). If `.claude/codex-review.state.json` already exists and is enabled, tell the user and ask whether to reconfigure or just reset.

2. Ask the user (use AskUserQuestion if values aren't already given) for:
   - **Max rounds** (default `3`) — hard cap on review iterations per turn
   - **Codex command** (default below) — what to run for review

   Default codex command:
   ```
   codex exec "Review the recent code changes in this project. List concrete issues (bugs, smells, missing tests, security). End your response with exactly one line: VERDICT: PASS  or  VERDICT: FAIL"
   ```

   The codex output **MUST** end with `VERDICT: PASS` or `VERDICT: FAIL` — that's how the hook knows whether to stop. If the user customizes the command, remind them to keep this convention.

3. Write `<project>/.claude/codex-review.state.json`:
   ```json
   {
     "enabled": true,
     "round": 0,
     "max_rounds": 3,
     "codex_cmd": "codex exec \"...\""
   }
   ```

4. Update `<project>/.claude/settings.json` to register the Stop hook. Read the file first if it exists; merge carefully without clobbering existing hooks. The entry should look like:
   ```json
   {
     "hooks": {
       "Stop": [
         {
           "matcher": "",
           "hooks": [
             {
               "type": "command",
               "command": "python \"C:/Users/iamaf/.claude/skills/codex-review-loop/codex_review_hook.py\""
             }
           ]
         }
       ]
     }
   }
   ```
   - If `Stop` already exists, append our hook entry rather than replacing.
   - If a previous `codex_review_hook.py` entry already exists, leave it (idempotent).
   - Use forward slashes in the path even on Windows — bash handles them fine.

5. Verify codex CLI is on PATH (`which codex` or `codex --version`). If not, warn the user but still complete setup; the hook is defensive and silently no-ops when codex is missing.

6. Tell the user concisely:
   - Loop is enabled, max N rounds
   - State file path
   - How to disable: `/codex-review-loop off` (or edit state file `enabled: false`)
   - How to reset round counter mid-session
   - One-line reminder that codex output must contain `VERDICT: PASS` to count as passing

## Disable / reset / status / remove

- **Disable**: edit state file → `enabled: false`. Don't remove from settings.json (so re-enabling is one flag flip).
- **Reset**: edit state file → `round: 0`. Useful if a previous run left the counter mid-loop.
- **Status**: read state file and report `enabled`, `round`/`max_rounds`, `codex_cmd`. If file is missing, say "not configured in this project".
- **Remove entirely**: delete `.claude/codex-review.state.json` AND remove the Stop hook entry from `.claude/settings.json` (be careful to leave other hooks intact). If `settings.json` becomes `{}`, leave the file (don't delete).

## Important behaviors of the hook (so you can explain them)

- The hook respects `stop_hook_active` — if Claude Code is already in a stop-hook re-prompted turn, the hook exits immediately. This prevents recursion.
- When round budget is hit, the hook resets `round` to 0 and allows Claude to stop. Next turn starts fresh.
- When Codex returns `VERDICT: PASS`, round resets and Claude stops normally.
- When codex CLI is missing or errors, the hook fails open (allows stop, logs to stderr). Never blocks indefinitely.
- All review feedback is fed back via the `reason` field of the Stop hook JSON, which Claude sees as a new user message.

## What NOT to do

- Don't write the hook script per-project — it lives globally at `~/.claude/skills/codex-review-loop/codex_review_hook.py`. Per-project setup is just state file + settings.json entry.
- Don't add the hook to user-level `~/.claude/settings.json` — it should be per-project opt-in.
- Don't change the global hook script unless the user is fixing a bug in the loop itself.
- Don't enable in a directory that isn't actually a project (no `.git`, no source files) without confirming.
