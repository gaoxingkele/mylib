---
name: finishing-a-development-branch
description: Use when implementation is complete and verified, and the remaining work is to package, hand off, or integrate the branch safely.
---

<Purpose>
Close out development work cleanly. Verify the branch, summarize the result, and take only the integration action the user actually wants.
</Purpose>

<Use_When>
- Coding work is done and fresh verification has passed
- The user needs a commit, handoff, PR, merge, or branch cleanup
- The remaining questions are about integration rather than implementation
</Use_When>

<Do_Not_Use_When>
- Tests, lint, or build checks still fail
- There are unresolved review findings or known functional gaps
- The user has not chosen an integration action and the next action is side-effectful
</Do_Not_Use_When>

<Codex_Notes>
- Follow the repo's Lore Commit Protocol if committing
- Do not push, merge, or delete branches without explicit user intent
- Destructive cleanup requires confirmation
</Codex_Notes>

<Execution_Policy>
- Re-run the relevant verification before offering any completion action
- Summarize branch status: changed files, verification state, and open risks
- Offer concrete next actions such as keep local, commit, push/PR, merge, or discard
- Execute only the chosen action, then verify the repo state again if needed
</Execution_Policy>

<Steps>
1. Run fresh verification for the branch.
2. Check git status, current branch, and any relevant diff summary.
3. Present the safe next-action options that match the user's goal.
4. If the user chooses a side-effectful option, execute it carefully.
5. Report the resulting branch state, verification status, and any remaining follow-up.
</Steps>
