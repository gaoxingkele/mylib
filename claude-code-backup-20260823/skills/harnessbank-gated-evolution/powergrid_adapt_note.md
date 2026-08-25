# HarnessBank → powergrid / automated research adaptation

Paper: https://arxiv.org/abs/2607.13683  
Local PDF: `../papers/HarnessBank_2607.13683.pdf`

## Relation to paper writing (direct vs indirect)

HarnessBank is **not** an automated paper writer. It improves the **agent harness** around a frozen LLM.

For `D:/aicoding/powergrid_benchmark`:

| Layer | Usefulness |
|---|---|
| Literature distill / IdeaSpark / RepLLM-CPA / Paper_CCF drafting | **Indirect** — only if the agent stack that runs those tools is being evolved |
| Experiment runners, Text2SQL agents, rebuild/audit loops | **Direct** — failure diagnosis + gated retention of harness patches |
| Manuscript claim discipline (“we improved X”) | **Direct methodology** — treat claim upgrades like gated screening |

## Reuse from the paper

1. **WHERE × WHY gene bank** — store reusable patches by component × pathology, analogous to IdeaSpark pattern cards but for *agent harness* artifacts rather than journal ideation moves.  
2. **Four gates** — validity, activation, paired significance, gain — before promoting a prompt/tool/control change into production skills or experiment configs.  
3. **Diagnose ≠ credit** — LLM may propose; deterministic metrics/tests own admission (same spirit as AERS citation-checker / figure-table-audit, plus statistical paired tests).  
4. **Sealed held-out** — when tuning agent pipelines on a fixed task set (e.g. GridDB splits), keep a sealed eval; do not credit on the same tasks used to select the patch.  
5. **Pathology→patch matching** — do not ship one “universal” research-agent prompt across models; re-run diagnosis when the backbone changes.

## Do **not** absorb yet

- Full multi-round self-evolution with hundreds–thousands of rollouts as a default manuscript step  
- Upstream implementation (not released)  
- Blind recombination of unrelated cells without activation beacons  
- Task-indexed archives (paper argues these overfit by construction)

## Suggested integration points in Lib / powergrid

| Existing piece | How HarnessBank helps |
|---|---|
| `skills/AERS-powergrid-bridge` | Add gated credit before promoting pipeline edits |
| `skills/codex-ars-powergrid` / ARA | Treat orchestrator prompt/tool changes as harness evolution candidates |
| IdeaSpark pattern cards | Parallel vocabulary: journal *patterns* vs harness *pathologies* |
| Experiment harnesses under `paper_projects/**` | Pair parent/candidate runs; require activation + significance for “method upgrade” claims |
| `LLM_Wiki` | Optional node: HarnessBank as agent-self-evolution method |

## Status

Absorbed as **methodology + skill** (RepLLM-style). Revisit full code clone when EverMind releases HarnessBank sources.
