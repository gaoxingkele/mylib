---
name: ralph-loop-setup
description: Use when a repository needs project-level Ralph loop setup or migration guidance, especially when porting Claude-era Ralph artifacts to Codex/OMX.
---

<Purpose>
Provide a Codex-native interpretation of the old Ralph loop setup workflow. In this environment, the first choice is the native `$ralph` skill; this imported skill is mainly for repo-level setup, migration, and compatibility work.
</Purpose>

<Use_When>
- A project wants persistent Ralph artifacts or repo-local loop documentation
- Existing Ralph files were built for Claude and need migration to Codex/OMX
- The user explicitly wants project-level autonomous loop setup instead of ad hoc usage
</Use_When>

<Do_Not_Use_When>
- The user only wants to run Ralph now; use the native `$ralph` workflow instead
- The task is normal implementation work with no repo-level loop setup
</Do_Not_Use_When>

<Execution_Policy>
- Prefer native Codex/OMX Ralph behavior over porting old Claude hooks verbatim
- Treat bundled template scripts in this imported skill as reference material, not drop-in executables
- If project-level artifacts are needed, write them under repo-local conventions such as `.omx/` and existing planning directories
- Migrate only the pieces that are still useful: loop instructions, guardrails, plan/test artifacts, and verification commands
</Execution_Policy>

<Migration_Guidance>
1. Inspect existing Ralph-related files and repo conventions.
2. Decide whether native `$ralph` alone is sufficient.
3. If repo-local setup is required, create Codex-compatible artifacts instead of copying `.claude/*` assumptions.
4. Preserve verification commands, task selection logic, and guardrails where they still make sense.
5. Document what remains archival reference only.
</Migration_Guidance>

<Codex_Notes>
- Use `.omx/plans/`, `.omx/state/`, and repo guidance files where appropriate
- Do not rely on Claude stop hooks, slash commands, or CLI-specific background loop behavior unless you intentionally port them
- If a real migration is requested, inspect the bundled templates selectively and adapt them rather than executing them unchanged
</Codex_Notes>
