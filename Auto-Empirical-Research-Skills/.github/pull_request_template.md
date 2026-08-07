## Summary

- 

## Linked issue

- (e.g. closes #12) — leave empty if not applicable

## Checklist

- [ ] I verified the source repo, license, and install path for any new skill.
- [ ] I added or updated the relevant `docs/` category entry.
- [ ] I updated `evals/flagship-evals.json` if this changes a flagship skill or recommended workflow.
- [ ] I ran `make catalog`.
- [ ] I ran `make check-fast` (or `make check` before opening a release PR).
- [ ] I avoided adding skills whose core path requires a paid/proprietary API.

## Catalog impact

- [ ] Changes a skill's hygiene score → re-run `make catalog` to refresh `docs/SKILL_HYGIENE.md`.
- [ ] Adds / removes a skill from `catalog/skills.json`.
- [ ] Changes vendored_commit metadata for any collection.
- [ ] Affects a method-family evaluation scenario (in `eval-harness/scenarios/`).
- [ ] Affects a numeric benchmark task (in `benchmark/tasks/`).

## Notes for reviewers

- Source:
- License:
- Local path: