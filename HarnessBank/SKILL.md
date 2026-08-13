---
name: harnessbank-gated-evolution
description: Use when evolving or auditing agent harnesses (prompts, tools, control loops, recovery, configs) for research automation — especially powergrid_benchmark pipelines. Prefer gated credit (validity/activation/paired significance/held-out) and WHERE×WHY gene-bank archives over greedy “mean improved once” retention. Not a paper-drafting skill; use for improving the agent stack that supports research and manuscripts.
---

# HarnessBank — gated harness evolution (lite)

Grounded in [HarnessBank](https://arxiv.org/abs/2607.13683) (EverMind). Full upstream loop is not public; **this skill covers the reusable methodology**: semantic gene bank + gated screening + diagnose/credit separation.

## When to trigger

- Research / coding / Text2SQL / literature agents keep failing in recurring ways and you want to patch the **harness**, not fine-tune the model.
- Someone proposes a prompt/tool/control change and you need a **trustworthy accept/reject** rule.
- Building a library of reusable agent patches without overfitting to a few training tasks or a single model.

## Do not trigger for

- Drafting Introduction/Related Work/claims for a journal paper (use Paper_CCF / ARA / AERS bridges).
- Blindly running multi-round self-evolution on every manuscript revision (cost + no sealed protocol).
- Copying another model’s “winning harness” without pathology matching.

## Core protocol (lite)

### 1. Partition the harness

- **Immutable kernel `K`**: evaluation, bookkeeping, evolution control, interface-critical code.
- **Mutable surface `X`**: prompt, knowledge, runtime, config (and scoped tool/recovery edits).

Only evolve `X`. Keep train/test (or train/held-out) splits sealed for credit.

### 2. Diagnose with LLM; credit with code

1. Run parent harness on train tasks; collect scores, trajectories, metadata.
2. Evolver proposes offspring + semantic descriptor `(w, y)`:
   - `w ∈ {prompt, knowledge, runtime, config}`
   - `y` = hypothesized pathology (e.g. `thinking-runaway`, `premature-finalize`, `schema-miss`, `citation-hallucination`)
3. Deterministic evaluator owns sampling, scoring, beacons, and gates. LLM labels steer search only — wrong `y` may waste a candidate, must not auto-credit.

### 3. Gated Harness Screening (order matters)

On a **train subset** first:

1. **Validity** — protocol-valid ledger (sandbox/verifier infra failures → retry, not agent fail).
2. **Activation** — patch declares a beacon; must fire at least once (inert patches die).
3. **Paired significance** — same-task paired Δ vs parent; require mean Δ>0 and `z≥1.96` (two-sided 5%).
4. **Gain / full train** — survivors evaluate on full train; admit to gene-bank cell by competitive selection.

Reject “single-run better” / “non-regression only” / “model says useful” as sole credit.

### 4. Harness Gene Bank

Archive elites in cells `(WHERE × WHY)`. Same pathology competes in one cell; different pathologies stay available for **recombination**. Prefer quality-biased parent selection + semantic diversity over greedy single-lineage edits.

### 5. Final credit

Ship train-selected winner; score **once** on held-out / sealed test. Cross-model: transfer only when pathology matches; otherwise re-diagnose.

## Powergrid mapping (examples)

| Pathology `y` (example) | Likely `w` | Patch class |
|---|---|---|
| empty / runaway reasoning turns | runtime | selective recovery / budget gate |
| premature finalize without verify | runtime | verify-finalize / checklist |
| Text2SQL schema miss / join hallucination | knowledge + prompt | schema inject + constrained decode |
| claim without activation evidence | config + runtime | evidence gate before claim emission |
| citation / figure-table inconsistency | tool + prompt | citation-checker / figure-table-audit hooks |

Persist accepted patches as gene-bank cards, not as anonymous “new system prompt v17”.

## Deliverable shape

When applying this skill, write:

1. Parent harness id + mutable surface touched  
2. Pathology hypothesis `(w, y)` and whether reinvented or recombined  
3. Gate ledger: valid / activated / paired-z / train Δ / held-out Δ  
4. Bank admission decision (cell replace / reject / keep parent)  
5. Explicit note if code was unavailable and only methodology was applied
