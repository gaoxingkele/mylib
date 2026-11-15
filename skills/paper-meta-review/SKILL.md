---
name: paper-meta-review
description: Compare manuscripts with journal exemplars, score chapters, revise from evidence, adjudicate cross-reviews, and track versioned sample ranks. Use for meta解构、论文评分、评审改稿、范文逐段对比和排名更新; scores are advisory, not acceptance probabilities.
metadata:
  version: "1.1.0"
---

# Paper meta review

Canonical source: `D:/aicoding/mylib/skills/paper-meta-review/`.

Read `references/meta-rubric.md` before scoring. This skill connects a source-bound
article atlas to review and revision; it does not replace scientific judgment
with article-length or artifact-count quotas.

For Information, read the current profile and evidence reference in
`D:/aicoding/mylib/Paper_CCF/journals/mdpi-information/`. Local atlas:
`D:/aicoding/powergrid_benchmark/knowledge_base/journal_article_atlas/deconstruction/v1/`.
Read its `INFORMATION_COVERAGE_REPORT.md` and relevant paragraph/object mappings.
If unavailable, report missing calibration rather than inventing sample averages.
Other journals require their own source-identified profile; do not transfer
Information's topic mix or historical metrics as universal requirements.

## Choose the requested operation

- **Review only:** inspect and advise; do not revise the manuscript.
- **Revise and rescore:** preserve a baseline, fix evidence-linked findings, then
  rescore on the same frozen scale. Separate writing, scientific evidence and
  reassessment effects.
- **Ranking refresh:** reuse the latest valid scores and corpus; check source
  identity and recompute ranks. Do not trigger a new review or experiments.
- **New scale or corpus:** label a new assessment series and bridge it to the old
  one; do not present the difference as manuscript improvement.

For repeated review/revision, exemplar paragraph comparison, independent-agent
adjudication, or questions about changing ranks, read
`D:/aicoding/mylib/Paper_CCF/resources/comparative-revision-calibration.md`.
It defines raw versus adjudicated judgments, three ranking universes, and
score/rank-change attribution. Keep the current scoring weights unless the user
requests a new rubric. This method extension does not replace V3 with a new scale.

## Workflow

For chapter-by-chapter journal scoring, or a comparison with earlier holistic
scores, read `references/chapter-journal-scoring-v3.md`. Use the deterministic
`scripts/chapter_score.py` helper with a rubric frozen before scoring. This is
an optional assessment mode; it does not silently replace a previous rubric.

When preserving or extending the user's human-polished MA-SQLGrid manuscript,
read `references/ma-sqlgrid-human-style.md`. Apply its rhetorical moves, not
its paper-specific numbers, to new passages; do not claim permanent model training.

1. Bind active manuscript SHA, journal/profile version, review scope and source
   coverage. Separate current results, historical results and planned work.
2. Map task→gap→method→experiment→result→claim. Add exact section/label anchors
   and edges to data, equations, tables, figures and citations. Record unreviewed
   paragraphs/objects; a chapter-level review is not full paragraph coverage.
3. Freeze rubric, weights and applicable dimensions BEFORE editing. Produce
   initial scores and prioritized findings (anchor, consequence, repair, closure).
4. When revision is requested, make additive/versioned changes, preserve data,
   author choices and unfavorable results. Experimental execution, publication,
   external upload and author attestations remain separately scoped actions.
5. Verify numerical/table preservation, labels/bibliography, build and visual
   changes proportionally. Rescore the identical rubric; tie every score change
   to new evidence. A clearer limitation does not improve external-validity score.
6. Deliver before/after table, closed/open findings, diff and artifact paths.
   Same-agent revision/review is consultation, not blinded independent consensus.

Report **score, manuscript version, comparison set and denominator together**.
Keep single-manuscript+references, manuscript-batch-only and batch+references
ranks separate; preserve complete tie intervals and unknown references. A changed
comparison set or improved companion paper does not erase an earlier revision.
Use `D:/aicoding/mylib/Codex-Academic-Research/tools/journal_rankings.py` for
deterministic rank arithmetic; it does not validate scientific scores.

Never add experiments, citations, formulas or pages merely to reach a score.
Do not hide unresolved gates behind the total. If the task only requests review,
do not edit the manuscript. Explicitly report partial/unknown coverage.
