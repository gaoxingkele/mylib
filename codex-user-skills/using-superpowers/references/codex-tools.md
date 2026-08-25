# Codex Tool Mapping

Use this file when an imported Superpowers document still speaks in Claude-oriented tool language.

| Legacy reference | Codex / OMX equivalent |
|---|---|
| `Task` tool | `spawn_agent` |
| Parallel `Task` calls | Multiple `spawn_agent` calls with disjoint scopes |
| Wait for task result | `wait_agent` |
| Close finished task | `close_agent` |
| `TodoWrite` | `update_plan` |
| `Read` / `Glob` / grep-style lookup | shell search, file reads, MCP/code-intel |
| `Write` / `Edit` | `apply_patch` |
| `Bash` | `functions.shell_command` |
| Named reviewer agent prompt | `spawn_agent` with the filled prompt as `message` |

## Agent Dispatch Notes

- Prefer role-specific agents such as `executor`, `code-reviewer`, `debugger`, or `verifier`.
- Give each agent explicit ownership, scope, and expected output.
- Use `wait_agent` sparingly; keep local work moving while children run.

## Progress Tracking

- Use `update_plan` for visible progress.
- Use repository-local planning/state conventions when a workflow requires artifacts.

## File and Verification Work

- Use `apply_patch` for manual edits.
- Use shell commands for tests, git inspection, and lightweight verification.
- Use MCP/code-intel tools when they produce faster or more precise inspection than shell search.
