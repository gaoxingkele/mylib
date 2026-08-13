# paper_harness 0.2.0 Design

## Scientific control plane

The harness treats a manuscript revision as a sequence of evidence-preserving state transitions. A plan is not
permission to improve results; it is a bounded specification of which scientific claims, analyses, prose, and
artifacts may change. Human approval binds the exact plan bytes.

The experience contract encodes recurring failures found in two Applied Sciences manuscripts and six power-system
papers: title/method mismatch, combined-ablation misattribution, negative-result drift, proxy-to-operational
overclaim, unfair budgets, audit narrative dominance, trace/utility conflation, companion overlap, and stale QA.

## State machine

```text
PENDING -> RUNNING -> CANDIDATE -> ACCEPTED | REJECTED
                    -> BLOCKED
RUNNING after crash -> FAILED
```

Only the first PENDING stage can run. A CANDIDATE freezes forward progress until a human accepts or rejects it.

## Git isolation

The paper directory may be a repository root or a monorepo subdirectory. The harness resolves both repository root
and paper prefix. The manuscript and configured required files must be tracked, and the paper subtree must be clean.
Each candidate is built in a dedicated worktree and committed before CANDIDATE. Cross-subtree modifications block
the stage. Acceptance performs a no-fast-forward merge into the current baseline.

## Review contract

The reviewer records the manuscript SHA-256 and supplied coverage. Its issue matrix separates manuscript evidence,
reviewer inference, required action, acceptance test, and licensed evidence boundary. A negative result is not a
quality defect; evidence mismatch and concealment are.

## Deterministic versus semantic checks

LaTeX, placeholders, declarations, structure, graphics, PDF integrity, and custom scripts are deterministic gates.
Title-to-evidence alignment and scientific interpretation are semantic reviewer outputs. The harness never pretends
that a keyword heuristic proves scientific validity.

## Human-only fields

Author identity, affiliations, CRediT roles, funding, conflicts, expert adjudication, and submission authority remain
human-controlled. A missing value is a blocker, not an invitation to infer from another paper.
