# Shared skills in D:/aicoding/lib

## ResearchStudio-Idea (Microsoft Research / NTU et al.)

- **Paper:** [arXiv:2607.04439](https://arxiv.org/abs/2607.04439) — *ResearchStudio-Idea: An Evidence-Grounded Research-Ideation Skill Suite from ML Conference Outcomes*
- **PDF:** `../papers/ResearchStudio-Idea_2607.04439.pdf`
- **Upstream code:** `../ResearchStudio/ResearchStudio-Idea` (clone of [microsoft/ResearchStudio](https://github.com/microsoft/ResearchStudio/tree/main/ResearchStudio-Idea))
- **This junction:** `ResearchStudio-Idea` → upstream folder
- **Agent junctions:** `~/.claude/skills/{idea_spark,paper_search,scoop_check}`

### Skills

| Skill | Role |
|---|---|
| `idea_spark` | End-to-end idea card: evidence → bottleneck → pattern cards → collision/audit |
| `paper_search` | Multi-source literature grounding |
| `scoop_check` | Claim-level prior-art collision check |

### Powergrid adaptation

Journal acceptance distill reuses IdeaSpark's **pattern vocabulary + lit_table + success/failure cards**, applied to OA full-texts under `powergrid_benchmark/papers/literature/`.

- Focused (16-journal folder): `scripts/literature/ideaspark_journal_pattern_distill.py`
- **Full corpus (all `papers/literature/**/*.pdf`)**: `scripts/literature/ideaspark_fullcorpus_journal_distill.py`
- Notes: `../papers/ResearchStudio-Idea_journal_adapt_note.md`
- Latest overview: `powergrid_benchmark/.../resources/ideaspark-fullcorpus-journal-distill.md` (in Paper_CCF skills)

## RepLLM (XMU / SIGCOMM 2026, arXiv:2509.21074)

- **Paper:** [arXiv:2509.21074](https://arxiv.org/abs/2509.21074) — *RepLLM: Toward Automatically Reproducing Network Research Results*
- **PDF:** `../papers/RepLLM_2509.21074.pdf`
- **This folder:** `RepLLM` → `../RepLLM` (skill + CPA schema; upstream multi-agent code **not released**)
- **Agent junction:** `~/.claude/skills/repllm-content-parse`

### What we reuse for journals

**Content Parsing Agent** ideas only: hierarchical sections + multimodal arrays + Shared Memory `paper.json` → richer evidence rates for Paper_CCF skills.

- Runner: `powergrid_benchmark/scripts/literature/repllm_cpa_journal_distill.py`
- Notes: `../RepLLM/journal_adapt_note.md`
- Index: `Paper_CCF/resources/repllm-cpa-journal-distill.md`

## Auto-Empirical-Research-Skills (AERS)

- **Repo:** `../Auto-Empirical-Research-Skills`
- **Bridge skill:** `AERS-powergrid-bridge` → selective routing into AERS sub-skills
- **Agent junction:** `~/.claude/skills/aers-powergrid-bridge`

### Absorption policy

Use only high-ROI modules for our power-grid manuscript flow:

- `71 ... literature-review-tools` (tool selection + run)
- `62 ... citation-checker` (CrossRef/S2/OpenAlex checks)
- `54 ... figure-table-audit` (text-evidence consistency QA)
- `48 ... de-AIGC-skills` (CN/EN language risk reduction)
- `67 ... paper-pipeline` (optional end-stage orchestrator)

## LLM Wiki (graph)

- `../LLM_Wiki/README.md`
- `../LLM_Wiki/graph.md`
- `../LLM_Wiki/nodes.md`
- `../LLM_Wiki/playbooks.md`

## Codex + ARS

- Digest: `../Codex-Academic-Research/`
- Suite junction: `academic-research-suite` → `../Academic-Research-Skills-Codex/skills/academic-research-suite`
- Powergrid bridge: `codex-ars-powergrid`
