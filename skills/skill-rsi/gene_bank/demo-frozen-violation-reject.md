# bad touch protected validator

## Identity

- Candidate id: `demo-frozen-violation`
- Target: `proposal_writing.review_revise`
- Surface: `skill`
- Parent: `seed-g7-stable-replay`
- Status: `rejected`
- Reportable: `False`

## Pathology

`(skill, bad touch protected validator)`

## Beacon

must_fail_frozen_intact_gate

## Gate ledger

| Gate | Result | Detail |
|---|---|---|
| validity | PASS | target path proposal-writing/references/review-revise.md |
| frozen_intact | FAIL | touched protected: proposal-writing/scripts/validate_review_basis.py |
| activation | PASS | notes or metrics or beacon present |
| domain_floors | PASS | metrics absent; structural gates only |
| reportable_discipline | PASS | ok |

## Metrics

_metrics absent_

## Decision

- By: framework-bootstrap
- Reason: Touched frozen proposal basis validator.

## Bank decision

Keep as a negative / do-not-recombine card unless pathology is explicitly rematched and a new candidate clears gates.

