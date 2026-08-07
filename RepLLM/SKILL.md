---
name: repllm-content-parse
description: Use when structuring a research PDF into RepLLM-style paper.json (hierarchical sections + multimodal arrays) for reproduction planning or for enriching journal acceptance distillation. Prefer this over dumping full PDF text into a single prompt.
---

# RepLLM Content Parsing (CPA-lite)

Grounded in [RepLLM](https://arxiv.org/abs/2509.21074) (SIGCOMM 2026). Full RepLLM also designs/generates/repairs code; **this skill covers only Content Parsing + Shared Memory paper layer**.

## When to trigger

- Need machine-readable paper structure before coding or before venue-pattern distill.
- Long papers where “lost in the middle” makes whole-PDF prompting unreliable.
- Want cross-ref-aware Method/Experiments context (figures/algorithms cited from those sections).

## Shared Memory paper.json (target shape)

```json
{
  "source_pdf": "...",
  "n_pages": 0,
  "sections": [
    {"id": "s1", "title": "Introduction", "level": 1, "text": "...", "refs": {"figures": [], "tables": [], "algorithms": [], "equations": []}}
  ],
  "figures": [{"id": "f1", "caption": "..."}],
  "tables": [{"id": "t1", "caption": "..."}],
  "algorithms": [{"id": "a1", "caption": "..."}],
  "equations": [{"id": "e1", "latex_or_text": "..."}],
  "signals": {
    "has_baseline_table": false,
    "has_ablation": false,
    "has_dataset_name": false,
    "has_data_availability": false,
    "has_code_availability": false,
    "section_roles": {"intro": true, "method": true, "experiments": true, "conclusion": true}
  }
}
```

## Procedure

1. Extract text (prefer MinerU if available; else page-wise PDF text).
2. Split hierarchical sections; drop References/Bibliography.
3. Collect figure/table/algorithm/equation captions into arrays.
4. For Method + Experiments sections, expand nearby caption IDs into the section `refs`.
5. Derive `signals` for evidence readiness (baselines, ablation, DAS, code).
6. Persist under Shared Memory / `paper.json`; do **not** auto-run ADA/CGA unless the user asked for code reproduction.

## Journal distill note

For Paper_CCF journal skills, CPA output feeds IdeaSpark tagging (see `journal_adapt_note.md`). Do not claim full RepLLM reproduction for OA megajournal corpora.
