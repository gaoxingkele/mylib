---
name: dispatching-parallel-agents
description: Use when there are multiple independent subtasks that can be delegated safely in parallel.
---

<Purpose>
Use Codex native subagents to increase throughput on independent work. This skill is about decomposition and coordination, not delegation for its own sake.
</Purpose>

<Use_When>
- Two or more subtasks are independent and bounded
- Each subtask has a clear owner, scope, and verification target
- Parallel work will shorten the critical path without creating merge conflicts
</Use_When>

<Do_Not_Use_When>
- The next local step is blocked on the delegated result
- Multiple subtasks need the same files or the same tight context
- The work is small enough to complete directly faster than coordinating agents
</Do_Not_Use_When>

<Codex_Notes>
- Use `spawn_agent` for parallel lanes
- Give each agent a concrete task, expected output, and clear file ownership
- Keep the leader focused on integration, verification, and the next non-overlapping step
</Codex_Notes>

<Execution_Policy>
- Decompose by independent problem domain or disjoint write scope
- Prefer smaller/faster agents for bounded tasks and stronger agents for integration-heavy tasks
- Never spawn multiple agents into the same write scope unless the overlap is intentionally coordinated
- Do not wait on agents reflexively; keep doing non-overlapping work locally
</Execution_Policy>

<Steps>
1. Identify whether the work truly splits into independent lanes.
2. Define each lane with scope, constraints, and expected deliverable.
3. Spawn one agent per lane with explicit ownership.
4. Continue local work that does not duplicate delegated effort.
5. Integrate results, resolve conflicts, and run verification.
6. Close agents once their outputs are integrated.
</Steps>

<Checklist>
- Independent scope confirmed
- Write ownership assigned
- Verification target defined
- Integration step planned
- No duplicated work between leader and children
</Checklist>
