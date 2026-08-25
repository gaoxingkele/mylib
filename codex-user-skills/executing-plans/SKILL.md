---
name: executing-plans
description: Use when there is a written implementation plan and the task is to carry it through to completion.
---

<Purpose>
Execute an approved plan methodically. Translate the plan into tracked work, implement in the right order, and verify before claiming completion.
</Purpose>

<Use_When>
- The repo already has a concrete implementation plan
- The user wants execution rather than more planning
- A plan artifact needs to be turned into tested code
</Use_When>

<Do_Not_Use_When>
- The plan is still ambiguous or internally inconsistent
- The task should be designed first rather than executed
- A faster direct implementation is possible because the scope is tiny and obvious
</Do_Not_Use_When>

<Codex_Notes>
- Read the plan critically before coding
- Track progress with `update_plan`
- Use subagents only when tasks from the plan are independent
- Prefer the existing repo workflow for plan locations and acceptance criteria
</Codex_Notes>

<Execution_Policy>
- If the plan has blockers or contradictions, stop and resolve them before coding
- Execute dependent tasks sequentially and independent tasks in parallel only when safe
- Verify each meaningful milestone instead of deferring all checks to the end
- Finish with a full verification pass and a concise status summary
</Execution_Policy>

<Steps>
1. Read the plan and extract tasks, dependencies, and verification steps.
2. Convert the plan into a tracked execution checklist with `update_plan`.
3. Implement tasks in dependency order.
4. Run the plan's stated checks after each milestone or batch.
5. If a task reveals a flaw in the plan, adjust locally or escalate if the branch is material.
6. Re-run final verification and report results with evidence.
</Steps>
