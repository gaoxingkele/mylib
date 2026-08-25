---
name: verification-before-completion
description: Use when you are about to claim something is fixed, complete, or passing and need fresh evidence first.
---

<Purpose>
Prevent false completion claims. This skill enforces a simple rule: no success statement without fresh verification evidence.
</Purpose>

<Execution_Policy>
- Identify the exact command or check that proves the claim
- Run it fresh in the current branch or workspace
- Read the output instead of assuming success from the exit code alone
- If verification fails, report the real state and continue working
- Apply this rule before task completion, commits, PRs, or merge claims
</Execution_Policy>

<Examples>
- "Tests pass" requires the relevant test command output
- "Build succeeds" requires a build command, not only lint
- "Bug fixed" requires reproduction or regression proof
- "Agent completed the task" requires reviewing the actual diff and running validation
</Examples>

<Checklist>
- Proof identified
- Proof executed fresh
- Output inspected
- Claim matches evidence exactly
- Any known gaps stated explicitly
</Checklist>
