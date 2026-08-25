# Codex Implementer Prompt Template

Use this template when spawning an implementation-focused subagent for one bounded task.

```text
Your task is to implement a single bounded task. Follow the instructions below exactly.

<task>
[Paste the full task text here. Do not tell the agent to go read the plan file unless that is necessary.]
</task>

<context>
[Relevant architecture, constraints, dependencies, and acceptance criteria.]
</context>

<ownership>
- Files or modules you own:
- Files you may read but should avoid editing:
- You are not alone in the codebase. Do not revert or overwrite unrelated edits made by others.
</ownership>

<requirements>
- Implement only what this task requires.
- Follow existing repo patterns.
- Add or update tests when the task changes behavior.
- Run the smallest verification needed to prove the task is complete.
- If the task is unclear, blocked, or requires broader design decisions, stop and report instead of guessing.
</requirements>

<report-format>
- Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
- Changes made
- Files changed
- Verification run and results
- Concerns or blockers
</report-format>
```
