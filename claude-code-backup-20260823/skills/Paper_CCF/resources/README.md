# Computer Science Conference Breadth Resources

This layer supports routing across 155 CS/AI conference profiles. Use it before
editing a manuscript for a specific conference when the target is still
uncertain.

## What to Load

- `conference-roster.md` - roster of covered conferences and official anchors.
- `official-source-map.md` - source anchors for live current-cycle checks.
- `source-basis.md` - source discipline and generation basis.
- `worked-examples/venue-routing.md` - diagnostic routing cases.
- `exemplars/selection-patterns.md` - sibling-conference differentiation
  patterns and common routing traps.

## Journal module extras

- `journal-roster.md` / `journal-selection-guide.md` / `mdpi-common.md` — OA journal routing.
- `powergrid-open-data-corpus-distill.md` — distilled evidence patterns from the
  local power-grid open-data PDF cache (49 datasets × ≥5 OA/arXiv papers;
  as-of 2026-07). Use when advising power×ML authors which Paper_CCF journal
  skill applies and what baselines/datasets reviewers expect.
- `target-journals-2026-batch-distill.md` — 2026-08 batch distill for newly
  profiled target journals (incl. CMC fulltext sample).
- `ideaspark-fullcorpus-journal-distill.md` — **primary index** for IdeaSpark-
  style acceptance patterns over the full local PDF corpus (~480). Per-journal
  sections also live in `journals/<slug>/SKILL.md`; detailed lit tables / pattern
  cards live in the powergrid_benchmark repo under
  `papers/literature/target_journal_related/metadata/ideaspark_fullcorpus_*`.

## Usage Rule

Start with `cs-ai-conference-workflow`, then open the one or two closest
single-conference profiles. Never quote page limits, deadlines, rebuttal rules,
or artifact requirements without re-opening the current official CFP or author
kit.
- `repllm-cpa-journal-distill.md` — RepLLM Content-Parsing (CPA) evidence geometry over the full local PDF corpus; per-paper `paper.json` under `powergrid_benchmark/.../metadata/repllm_cpa_paper_json/`.
