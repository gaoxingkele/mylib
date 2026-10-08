---
name: review-grant
description: Local Codex adapter for the pinned upstream six-role grant review framework used only through proposal-writing review routes.
metadata:
  upstream-original: UPSTREAM_SKILL.md
---

# Review Grant Adapter

This directory preserves the pinned upstream skill in [UPSTREAM_SKILL.md](UPSTREAM_SKILL.md). The upstream frontmatter is kept byte-exact and is not registered directly because its Claude-specific metadata is not valid YAML for the local runtime audit.

Use this adapter only after loading `proposal-writing` and `references/review-revise.md`. The domestic proposal route supplies the controlling rules: current guide and template first, no funding probabilities or official scores, issue records must include location, quote, basis, and actionable revision advice, and unresolved external evidence stays marked as a gap.

When borrowing the upstream framework, read [UPSTREAM_SKILL.md](UPSTREAM_SKILL.md) for the six reviewer perspectives, then apply the Chinese proposal adaptation in `../../references/review-revise.md`.
