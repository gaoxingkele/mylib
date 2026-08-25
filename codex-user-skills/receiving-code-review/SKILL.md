---
name: receiving-code-review
description: Use when handling review feedback so comments are evaluated technically before changes are made.
---

<Purpose>
Process review feedback with rigor. Understand the comment, verify it against the codebase, then either implement the fix or push back with concrete reasoning.
</Purpose>

<Use_When>
- A user shares review comments, requested changes, or inline feedback
- PR feedback is partially unclear or potentially incorrect
- You need to address multiple review items without blindly batching them
</Use_When>

<Do_Not_Use_When>
- There is no actionable review feedback yet
- The task is general code review rather than response to feedback
</Do_Not_Use_When>

<Execution_Policy>
- Clarify unclear comments before implementing any of them
- Verify whether the suggestion is correct for this codebase and branch
- Implement one logical item at a time, verifying after each meaningful change
- Push back factually when a suggestion is wrong, incomplete, or conflicts with repo constraints
- Prefer direct technical acknowledgment over performative agreement
</Execution_Policy>

<Steps>
1. Read all feedback and group related items.
2. Identify unclear or conflicting comments and resolve those first.
3. Check the code, tests, and requirements before accepting a suggestion.
4. Apply valid fixes in a controlled order: breakages first, then lower-risk items.
5. Verify each fix and summarize what changed.
6. If responding on GitHub or similar tools, reply in the correct thread with concise technical context.
</Steps>
