# PAA Validation Checklist (Seal Level 1)

Mechanical + semantic checks the validate.py script runs. Companion to `./gates-checklist.md`
(which is the four-gate content rules); this file is the structural + binding integrity checks.

## Mandatory-core checks (file existence + non-empty)

```
[ ]  MANIFEST.md exists, non-empty, has frontmatter (title, claims_summary, gate_status, Layer Index)
[ ]  logic/invention.md exists, non-empty
[ ]  logic/subject_matter.md exists, non-empty
[ ]  logic/claims_analysis.md exists, non-empty
[ ]  logic/inventive_concepts.md exists, non-empty, has ≥1 concept block
[ ]  logic/prior_art.md exists, non-empty, has ≥1 prior-art entry
[ ]  logic/related_work.md exists
[ ]  logic/solution/constraints.md exists
[ ]  application/claims.md exists, non-empty, has ≥1 独立权利要求
[ ]  application/specification.md exists, non-empty
[ ]  application/drawings.md exists, non-empty
[ ]  application/abstract.md exists, non-empty, ≤300 字
[ ]  trace/exploration_tree.yaml exists, parses as valid YAML
[ ]  evidence/README.md exists
[ ]  ≥1 file in evidence/prior_art_search/ (at least one prior-art was actually searched)
```

## Cognitive layer checks

```
For each 独立权利要求 in logic/claims_analysis.md:
  [ ]  preamble field is verbatim copy from application/claims.md
  [ ]  characterizing portion is verbatim copy from application/claims.md
  [ ]  difference_features broken into D01, D02, ... with concrete description

For each concept in logic/inventive_concepts.md:
  [ ]  Statement is falsifiable (specific, not "improves")
  [ ]  Proof field binds to ≥1 实施例 ID AND ≥1 prior-art pn AND ≥1 score entry
  [ ]  Status is one of CONFIRMED | UNSUPPORTED | NEEDS-EVIDENCE

For each prior-art in logic/prior_art.md:
  [ ]  pn is a real patent number (format check, not a fabrication)
  [ ]  relationship ∈ {conflicts, contrasts, background}
  [ ]  evidence_file path resolves to evidence/prior_art_claims/<pn>.md
```

## Application layer checks

```
application/claims.md:
  [ ]  ≥1 独立权利要求 with preamble + 其特征在于 + 特征部分 structure
  [ ]  no banned phrases:  约/大概/左右/优选/最好 (in 独立权利要求)
  [ ]  no absolute expressions:  100%/大幅/领先 (in any 权利要求)

application/specification.md:
  [ ]  has all five elements in order: 技术领域/背景技术/发明内容/附图说明/具体实施方式
  [ ]  background 引用 only real pns from logic/prior_art.md
  [ ]  ≥2 实施例 with numerical instances
  [ ]  no banned expressions in effect statements

application/abstract.md:
  [ ]  ≤300 字
  [ ]  includes 技术领域, 技术问题, 方案要点, 主要用途/效果
  [ ]  specifies the 摘要附图
```

## Exploration tree checks

```
trace/exploration_tree.yaml:
  [ ]  parses as valid YAML
  [ ]  every node declares support_level ∈ {explicit, inferred}
  [ ]  every explicit node carries source_ref
  [ ]  no invented dead-end / design-around / claim-version nodes (count is source-bounded, not a quota)
  [ ]  every claim-version has evidence: refs to inventive-concepts EC-ids
  [ ]  every prior-art node has a real pn AND evidence_file path that resolves
  [ ]  every design-around has from_version, to_version, mechanism_before, mechanism_after
  [ ]  oa-response nodes chain to claim-version nodes via triggered_changes
```

## Evidence checks

```
[ ]  evidence/prior_art_search/<pn>.json files are real (not placeholders), cite search API source
[ ]  evidence/prior_art_claims/<pn>.md are claim-text transcriptions (not summaries)
[ ]  evidence/scoring/scoring.json (if present) has group_weights matching the 4-expert AHP setup
[ ]  no fabricated pn in any file (pn format check + duplicate detection)
```

## Cross-layer binding integrity

```
For every difference_feature DXX in logic/claims_analysis.md:
  [ ]  → application/specification.md §embodiment_Y (must resolve to a paragraph)
  [ ]  → logic/prior_art.md §PA-ZZ (must, ≥1 prior-art)
  [ ]  → evidence/scoring/scoring.json → I_value (must, if scoring exists)

For every inventive_concept CXX:
  [ ]  → application/specification.md §embodiment
  [ ]  → evidence/prior_art_claims/<pn>.md
  [ ]  (if scoring) → evidence/scoring/scoring.json → latent[I]

]
```

## Gate integration

The four gates (see `./gates-checklist.md`) are PASS / FAIL / WAIVED. validate.py runs the gates and
emits structured output. The MANIFEST.md frontmatter should reflect:
- `gate_1_subject_matter: PASS | FAIL | WAIVED`
- `gate_2_novelty_inventive: PASS | FAIL | WAIVED`
- `gate_3_sufficient_disclosure: PASS | FAIL | WAIVED`
- `gate_4_no_fabrication: PASS | FAIL | WAIVED`

## Failure → fix

| Failure mode | Fix direction |
|---|---|
| Missing mandatory file | Generate the missing layer |
| Difference_feature lacks prior-art binding | Run additional 定向检索式 searches; record real hits in evidence |
| Embodiment paragraph doesn't support claim feature | Expand the 实施例 with concrete parameters and numerical instance |
| fabricated pn | Re-run the search; replace the placeholder with a real pn + evidence transcription |
| invalid claim structure (no 特征部分 marker) | Re-formulate the 独立权利要求 with explicit preamble + 其特征在于 + characterizing portion |
| exploration-tree node count too low | Verify this is honest (not a quota); if real, surface "scarce drafting history" in MANIFEST.md |

## Run

```bash
python ./scripts/validate.py <paa-dir>
```

Expected output: a JSON summary per check + overall PASS / FAIL.