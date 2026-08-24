# Workflow Blueprint

## Inputs

Accept any mix of:
- papers and manuscripts;
- technical disclosures;
- source code and architecture docs;
- product plans, meeting notes, test reports, screenshots, drawings;
- existing patent drafts and office-action comments.

## Evidence Table

Before drafting, create a table:

| Source | Extracted fact | Status | Patent use | Risk |
|---|---|---|---|---|
| path/page | specific technical fact | confirmed/inferred/needs-confirmation | claim/spec/background/effect | issue |

Rules:
- `confirmed`: directly stated in a source or by the user.
- `inferred`: technically reasonable from sources but not explicitly stated.
- `needs-confirmation`: affects claim scope, inventorship, applicant, dates, data, or implementation.

## PGTree-Style Planning

For each candidate invention:

1. Problem: what technical problem exists in a concrete system.
2. Mechanism: what process, module, formula, data flow, device, or control loop solves it.
3. Differentiator: what is unlikely to be in the closest prior art.
4. Support: where the source materials support it.
5. Claim anchor: what must appear in independent claims.
6. Fallback: narrower feature for dependent claims or amendment.

## Default Stages

1. Intake.
2. Evidence map.
3. Candidate patent points.
4. Search/publication gate.
5. Disclosure.
6. Claim set.
7. Specification.
8. Examiner attack.
9. Package.

Skip only when the user explicitly narrows the task or when an artifact already exists and is current.
