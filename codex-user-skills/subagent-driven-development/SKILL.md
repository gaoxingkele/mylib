---
name: subagent-driven-development
description: Use when executing a plan inside the current session with bounded implementation and review work delegated to subagents.
---

<Purpose>
Implement a plan through coordinated subagents without losing control of scope or verification. The leader owns sequencing and integration; child agents own bounded slices of work.
</Purpose>

<Use_When>
- There is a plan with tasks that can be split cleanly
- The current session should remain the coordination point
- Review checkpoints are needed between implementation steps
</Use_When>

<Do_Not_Use_When>
- The work is too tightly coupled to split safely
- There is no plan or the plan is still unstable
- A single local implementation path is faster and lower risk
</Do_Not_Use_When>

<Codex_Notes>
- Use `spawn_agent` and `update_plan` rather than legacy task-dispatch or checklist terminology
- Give each agent explicit file ownership and expected output
- Keep review work separate from implementation work when possible
</Codex_Notes>

<Execution_Policy>
- Parse the plan into bounded tasks before delegating
- Use one implementer agent per task or batch with a disjoint scope
- Run review after meaningful milestones, not only at the very end
- The leader integrates, verifies, and decides when to move to the next task
</Execution_Policy>

<Steps>
1. Read the plan and identify tasks that are independent enough to delegate.
2. Track tasks in `update_plan`.
3. Spawn implementer agents for bounded work with explicit ownership.
4. Review outputs locally or with a reviewer agent where justified.
5. Integrate accepted changes, run verification, and then advance to the next task.
6. End with a final verification sweep across the whole implementation.
</Steps>
