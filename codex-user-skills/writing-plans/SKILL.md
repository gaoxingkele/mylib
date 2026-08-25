---
name: writing-plans
description: Use when approved requirements need to be turned into a concrete implementation plan before coding.
---

<Purpose>
Write an implementation plan that another capable engineer or agent could execute without guessing. The plan should specify scope, files, sequence, and verification.
</Purpose>

<Use_When>
- A spec or approved design exists
- The task is large enough to benefit from planned execution
- Multiple files, milestones, or verification phases are involved
</Use_When>

<Do_Not_Use_When>
- The task is small enough to implement directly
- Requirements are still unclear and need design work first
</Do_Not_Use_When>

<Execution_Policy>
- Respect the repo's preferred plan location and artifact names
- Map the affected files and responsibilities before enumerating steps
- Keep steps executable, testable, and right-sized to the task
- Include verification strategy, not just implementation steps
- Avoid placeholders, vague steps, and unstated assumptions
</Execution_Policy>

<Plan_Contents>
- Goal and scope
- Key constraints and risks
- File and module touchpoints
- Ordered implementation steps
- Test and verification strategy
- Open questions only if they are truly blocking
</Plan_Contents>

<Codex_Notes>
- Use repository inspection to ground the plan in actual files and patterns
- If the repo uses `.omx/plans/`, follow that convention
- For high-risk work, include rollback or safety notes
</Codex_Notes>
