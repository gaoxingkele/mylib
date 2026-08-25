# Archival Claude-era setup guide

This file used to describe how to install Ralph loop support into Claude-specific project files such as `.claude/commands`, `.claude/hooks`, and `.claude/settings.json`.

In Codex/OMX, do not follow those steps literally.

## Use Instead

1. Prefer the native `$ralph` workflow already available in this environment.
2. Keep persistent artifacts under repo-local conventions such as `.omx/plans/` and `.omx/state/`.
3. If a repository still contains Claude-era Ralph files, migrate only the useful parts:
   - verification commands
   - task/PRD structure
   - guardrails or loop notes
4. Treat old `.claude/*` templates as source material to translate, not as executable setup.
