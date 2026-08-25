---
name: using-git-worktrees
description: Use when feature work or risky changes should happen in an isolated git worktree instead of the current checkout.
---

<Purpose>
Create a clean, isolated workspace for implementation without disturbing the current checkout. In Codex, this skill is about safe setup, not blind automation.
</Purpose>

<Use_When>
- A feature branch should be developed separately from the current workspace
- The current tree is dirty and isolation would reduce risk
- Parallel implementation branches or experiments are needed
</Use_When>

<Do_Not_Use_When>
- The task is tiny and isolation adds unnecessary overhead
- The user explicitly wants work done in the current checkout
</Do_Not_Use_When>

<Execution_Policy>
- Prefer an existing project-local worktree directory such as `.worktrees/` or `worktrees/`
- Check repo guidance files, including `AGENTS.md`, before inventing a location
- For project-local worktree directories, verify they are ignored by git before using them
- Do not proceed with baseline-failing worktrees without telling the user
</Execution_Policy>

<Steps>
1. Inspect the repo for existing worktree conventions and ignore rules.
2. Choose the worktree location based on existing convention first, then repo guidance, then a short user clarification if still ambiguous.
3. Create the worktree and branch.
4. Run project setup only if it is needed for the task.
5. Run a baseline verification pass so new failures can be distinguished from pre-existing ones.
6. Report the worktree path, branch, and baseline verification state.
</Steps>

<Codex_Notes>
- Use normal git commands and shell inspection
- Be explicit about branch names and filesystem paths
- Pair with `finishing-a-development-branch` when the isolated work is done
</Codex_Notes>
