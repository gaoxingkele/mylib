# Testing Skills With Subagents

Use this note when validating that a skill actually changes agent behavior.

## Codex Version

1. Run a realistic task without the skill and capture the failure mode.
2. Add or revise the skill.
3. Run the same task again, ideally with a fresh `spawn_agent` prompt or a new session.
4. Compare behavior, not just output style.
5. Tighten the skill where the agent still rationalizes around it.

## What to Record

- Trigger that should activate the skill
- Baseline failure without the skill
- Revised behavior with the skill
- Remaining loopholes
