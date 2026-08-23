# RepLLM (SIGCOMM 2026) — shared library entry

**Paper:** [arXiv:2509.21074](https://arxiv.org/abs/2509.21074) — *RepLLM: Toward Automatically Reproducing Network Research Results*  
**Venue:** ACM SIGCOMM 2026 ([accepted list](https://conferences.sigcomm.org/sigcomm/2026/accepted/))  
**PDF:** `../papers/RepLLM_2509.21074.pdf`  
**Upstream code:** **not publicly released** as of 2026-08 (no official GitHub; name collisions on GitHub are unrelated).

## What RepLLM is

End-to-end **paper → executable code** multi-agent system for networking research:

| Agent | Role |
|---|---|
| **Content Parsing (CPA)** | PDF/MD → structured `paper.json` (+ optional `appendix.json`): hierarchical sections, figures/tables/algorithms/equations arrays, cross-refs |
| **Architecture Design (ADA)** | `paper.json` → `arch.json` DAG of reproduction steps + I/O schemas |
| **Code Generation (CGA)** | Schema-first + Structured CoT → per-step code |
| **Audit & Repair (ARA)** | Static + Docker sandbox dynamic repair |

Shared Memory = on-disk `shared_memory/` with paper / architecture / code layers.

Paper extraction stack (upstream): **MinerU** → Markdown → JSON.

## Powergrid use (what we actually install)

| Use | Verdict |
|---|---|
| Full ADA+CGA+ARA on all journal PDFs | **No** — wrong task (not network-system reproduction); token/sandbox cost prohibitive |
| **CPA-style structured parse** for journal distill | **Yes** — richer section / experiment / multimodal evidence than flat first-N-page regex |

Adaptation notes: `journal_adapt_note.md`  
Agent skill: `../skills/RepLLM` (junction) → this folder’s `SKILL.md`  
Corpus runner: `powergrid_benchmark/scripts/literature/repllm_cpa_journal_distill.py`
