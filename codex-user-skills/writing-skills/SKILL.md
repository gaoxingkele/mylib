---
name: writing-skills
description: Use when creating or revising a Codex skill so it is discoverable, specific, and executable in this environment.
---

<Purpose>
Create high-signal skill docs that tell Codex when to use the skill and how to execute it with available tools.
</Purpose>

<Use_When>
- Adding a new local skill under `~/.codex/skills`
- Refactoring an imported skill into Codex-native form
- Tightening an existing skill's trigger conditions or execution guidance
</Use_When>

<Execution_Policy>
- Keep the `description` field trigger-focused: when to use, not how it works
- Write for discoverability first and completeness second
- Prefer concise, structured sections over long narrative prose
- Use Codex tool names and OMX workflow concepts, not Claude-only terminology
- Include only references and helper files that materially improve execution
</Execution_Policy>

<Recommended_Structure>
- `name`
- `description`
- `<Purpose>`
- `<Use_When>`
- `<Do_Not_Use_When>` when needed
- `<Execution_Policy>`
- `<Steps>` or equivalent task flow
- `<Codex_Notes>` when platform-specific behavior matters
</Recommended_Structure>

<Validation>
- The trigger is specific enough to avoid accidental activation
- The steps are actionable with current tools
- The doc contains no stale product-specific assumptions
- The skill is shorter than the problem it is trying to solve
</Validation>
