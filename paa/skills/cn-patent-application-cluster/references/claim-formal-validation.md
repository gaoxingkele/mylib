# Claim Formal Validation

Read this reference after drafting or materially revising a Chinese claim set.

## Deterministic Gate

Run:

```powershell
python .codex/skills/cn-patent-application-cluster/scripts/claim_formal_check.py <权利要求书.md> --json
```

The checker verifies only mechanical rules:

- claims are numbered consecutively from 1;
- referenced claims exist and precede the referring claim;
- a claim does not reference itself;
- a multiple-dependent claim does not depend on another multiple-dependent claim;
- each claim contains exactly one final Chinese full stop;
- independent claims expose the expected transition for manual review.

Treat any deterministic `error` as a drafting defect. Do not waive it because an LLM reviewer considers the claim understandable.

## Human Review Gate

Do not automate these as pass/fail without a calibrated parser:

- antecedent basis and consistent meaning of `所述` terms;
- whether a referenced feature is actually present in the dependency chain;
- essential-feature completeness;
- support under Article 26.4;
- clarity, functional claiming, unity, and technical-subject-matter questions.

For antecedent basis, inspect each `所述X` and confirm that `X` was introduced in the same claim or inherited through the complete dependency chain. Regex-only antecedent scoring is diagnostic because patent noun phrases create systematic false positives.

## Claim/Data Provenance

When comparing drafts or training/evaluation data, distinguish:

- as-filed claims;
- amended claims;
- allowed or granted claims;
- office-action-rejected language.

Do not treat an accepted application label as proof that the stored as-filed claim language was allowed unchanged. Preserve publication/grant identifiers and prosecution state in the evidence record.
