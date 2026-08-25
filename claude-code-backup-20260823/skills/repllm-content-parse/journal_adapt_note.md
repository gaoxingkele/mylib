# RepLLM → powergrid journal distill adaptation

Paper: https://arxiv.org/abs/2509.21074 (SIGCOMM 2026)  
Local PDF: `../papers/RepLLM_2509.21074.pdf`

## Reuse (Content Parsing only)

From RepLLM §4.1 / §5.2 **paper space**:

1. **Hierarchical sections** (exclude bibliography) as the retrieval unit  
2. **Segregated multimodal arrays**: figures, tables, algorithms, equations (order-preserving)  
3. **Cross-reference expansion** idea: when scoring a Method/Experiments section, pull caption/algorithm cues referenced nearby  
4. **Shared Memory paper.json** as durable intermediate (not only ephemeral PDF text)

Upstream uses MinerU; our CPA-lite uses `pypdf` + heading/caption heuristics so the full local corpus can run offline without Docker/GPU.

## Do **not** reuse for mass journal distill

- Architecture Design DAG / code schema generation  
- Code Generation + SCoT → source files  
- Audit & Repair / Docker sandbox  

Those stages optimize **compile-ready network systems**, not **acceptance-pattern cards** for OA journals.

## How it upgrades IdeaSpark distill

IdeaSpark (ResearchStudio-Idea) tags **ideation moves**.  
RepLLM-CPA adds **evidence geometry** of accepted papers:

- section skeleton (IMRaD / MDPI variants)  
- table/figure/algorithm density  
- baseline / ablation / dataset / data-availability / code-availability cues scoped to Results/Experiments sections  
- reproducibility surface (DAS / GitHub / Zenodo mentions)

Combined pipeline: CPA parse → enriched signals → IdeaSpark pattern counters → Paper_CCF `journals/*/SKILL.md`.

Script: `D:/aicoding/powergrid_benchmark/scripts/literature/repllm_cpa_journal_distill.py`
