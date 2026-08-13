# HarnessBank (EverMind) — shared library entry

**Paper:** [arXiv:2607.13683](https://arxiv.org/abs/2607.13683) — *HarnessBank: Semantic Gene-Bank Search with Gated Verification for Agent-Harness Self-Evolution*  
**Authors:** Xiaotian Luo, Dizhan Xue, Fengxingyu Wang, Chuanrui Hu, Yafeng Deng (EverMind)  
**PDF:** `../papers/HarnessBank_2607.13683.pdf`  
**Upstream code:** **not released yet** (“will be publicly available upon acceptance”). Do not confuse with [EverMind-AI/EverOS](https://github.com/EverMind-AI/EverOS) (memory / EvoAgentBench), which is a related org stack but not this framework.

## What HarnessBank is

Trustworthy **agent-harness self-evolution** without updating model weights. A frozen task LLM is wrapped by a mutable harness (prompts, knowledge, runtime control, recovery, tool interfaces, configs). A separate **evolver** diagnoses failures and proposes patches; **deterministic code** owns sampling, scoring, activation beacons, and significance tests.

| Piece | Role |
|---|---|
| **Harness Gene Bank (HGB)** | Quality-diversity archive keyed by semantic cells `(WHERE × WHY)` — where a patch acts × which failure pathology it targets |
| **Reinvention / recombination** | New patches from trajectories, or stacking compatible elites from different cells |
| **Gated Harness Screening** | Subset eval → validity → activation → paired significance (`z≥1.96`) → gain; survivors get full train eval then bank admission |
| **Sealed test** | Train-select only; held-out scored once after evolution |

Reported gains on 7 agent benchmarks (frozen Qwen3.6-27B): **+5.1% – +15.4%** Pass@1; cross-model results show **pathology→patch matching**, not a universal harness.

## Powergrid / Lib use (what we actually absorb)

| Use | Verdict |
|---|---|
| Full HarnessBank loop on every paper-writing / research agent run | **No** — rollout cost high; code unavailable; wrong default for manuscript drafting |
| **Gated credit protocol** for claiming agent / experiment upgrades | **Yes** — validity, activation, paired significance, held-out check |
| **WHERE×WHY gene bank** for reusable harness / skill patches | **Yes** — maps onto pattern cards + skill library without task-index overfitting |
| **Diagnose ≠ credit** separation (LLM proposes, code credits) | **Yes** — aligns with evidence-gated paper claims and pipeline QA |
| Transplanting a “best” prompt stack across models/tasks | **No** — paper shows mismatched patches can be near-zero or harmful |

Adaptation notes: `powergrid_adapt_note.md`  
Agent skill: `../skills/HarnessBank` (junction) → this folder’s `SKILL.md`
