---
name: using-superpowers
description: Use when interpreting imported Superpowers skills inside Codex so their intent is preserved but execution follows Codex and OMX conventions.
---

<Purpose>
Act as the compatibility layer for imported Superpowers skills. The original skills came from a Claude-oriented ecosystem; this skill explains how to apply them correctly in Codex.
</Purpose>

<Priority>
1. System and developer instructions
2. User instructions
3. Repo guidance such as `AGENTS.md`
4. Imported skill guidance
</Priority>

<Execution_Policy>
- Treat imported skills as workflow guidance, not as authority over the active system prompt
- Replace Claude-specific tool names and slash-command assumptions with Codex-native tools and OMX workflows
- Use a migrated skill only when it materially fits the task; do not force workflow overhead onto trivial tasks
- Prefer existing native Codex skills when they cover the same job more cleanly
</Execution_Policy>

<Codex_Mapping>
- File and code inspection: shell search, MCP/code-intel, and direct file reads
- Edits: `apply_patch`
- Delegation: `spawn_agent`, `send_input`, `wait_agent`
- Progress tracking: `update_plan`
- Verification: shell commands plus diagnostics
</Codex_Mapping>

<Usage>
- Read the migrated skill content, then execute it using Codex tools and repo-local rules
- If an imported skill still references Claude-only hooks, commands, or UI features, treat those as historical reference and use the nearest Codex-native equivalent
- When a native skill already exists for the same task, prefer the native one
</Usage>
