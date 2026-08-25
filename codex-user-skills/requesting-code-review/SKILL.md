---
name: requesting-code-review
description: Use when work is ready for an internal review pass before moving on, merging, or opening a PR.
---

<Purpose>
Request a focused review before problems compound. In Codex, this usually means running the native `code-review` workflow or spawning a `code-reviewer` agent with tight scope.
</Purpose>

<Use_When>
- A major task or feature is complete
- You want a review checkpoint before merging or opening a PR
- A fresh reviewer perspective could catch regressions or design drift
</Use_When>

<Do_Not_Use_When>
- The work is still obviously incomplete
- There is no meaningful diff or review scope yet
</Do_Not_Use_When>

<Codex_Notes>
- Prefer the native `code-review` skill when available
- Otherwise use a `code-reviewer` subagent with clear scope and diff context
- Include base/head refs or changed-file scope so the reviewer knows what to inspect
</Codex_Notes>

<Execution_Policy>
- Define the review scope first: files, diff, task, or requirement set
- Ask for findings first, not praise
- Fix high-severity issues before moving on
- Re-verify after applying review feedback
</Execution_Policy>

<Steps>
1. Capture the review scope: changed files, relevant requirements, and any risky areas.
2. Run the native review workflow or spawn a `code-reviewer` agent.
3. Triage findings by severity.
4. Fix the valid issues and verify the branch again.
5. Record any deferred low-priority items explicitly instead of silently ignoring them.
</Steps>
