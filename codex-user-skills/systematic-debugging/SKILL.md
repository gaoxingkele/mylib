---
name: systematic-debugging
description: Use when debugging a bug, failing test, build issue, regression, or unexpected behavior before proposing fixes.
---

<Purpose>
Find the root cause before changing code. This skill exists to prevent random fixes, timeout inflation, and speculative edits.
</Purpose>

<Use_When>
- Tests fail
- Build, runtime, or integration behavior is broken
- The same issue keeps reappearing
- A bug spans multiple components or unclear boundaries
</Use_When>

<Do_Not_Use_When>
- The task is pure design or planning with no concrete failure to investigate
</Do_Not_Use_When>

<Execution_Policy>
- No fix before root-cause investigation
- Reproduce the issue or gather enough evidence to explain why reproduction is missing
- Read logs, stack traces, diffs, recent changes, and failing assertions carefully
- Instrument boundaries when the failure crosses components
- Fix the source of bad state, not the downstream symptom
</Execution_Policy>

<Phases>
1. Reproduce: capture the exact failing command, steps, and scope.
2. Observe: read the full error output, logs, and relevant code paths.
3. Narrow: compare recent changes, inspect state transitions, and isolate the failing boundary.
4. Explain: form a root-cause hypothesis that fits all observed evidence.
5. Fix: make the smallest defensible change at the source.
6. Verify: rerun the failing case and any regression checks.
</Phases>

<Codex_Notes>
- Use repository inspection and diagnostics tools aggressively before editing
- Prefer targeted instrumentation over guesswork
- If multiple independent failures exist, consider `dispatching-parallel-agents`
</Codex_Notes>
