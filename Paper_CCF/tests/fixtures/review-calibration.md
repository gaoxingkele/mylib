# Review exercise: a graph-memory manuscript

Use the supplied manuscript excerpts to write a concise AAAI-style review with
strengths, prioritized weaknesses, author questions, and a qualified recommendation.
No code, technical supplement, original outputs, or run logs are available.
Do not browse or write files for this exercise.
This fixture is the tested input. The distillation page is evaluator-only material;
do not read it while producing the review. Local read-only calculations are allowed.

## Supplied manuscript excerpts

Methods, Section 4.1: Mentions are grouped into lanes using normalized-name keys,
LSH bucket IDs, and retrieved candidate entity IDs. Across lanes the precomputed
key sets are disjoint. Each lane then resolves mentions in time order using its
local entity state. The resolver can create new canonical entities or update an
existing entity. Lane results are incorporated before processing the next chunk.

Setup, Section 5.1: The default system uses the proposed parallel NED, deferred
profiling, and Ego-Splitting. It uses gpt-4o-mini for construction and answering.
All metric definitions and experimental details are provided in a technical
supplement. Candidate retrieval, thresholds, and resolution logic are shared
between the serial and parallel variants.

Table 4: Construction costs, reported in k tokens and seconds. Baseline models,
hardware, parallelism, and whether costs are totals or means are not specified
in the supplied material.

| System | Input | Output | Total | Calls | Time |
| --- | ---: | ---: | ---: | ---: | ---: |
| Zep | 29,389 | 1,362 | 30,751 | 26,616 | 142,048 |
| LightGMEM | 2,441 | 36 | 2,478 | 459 | 937 |
| MemoryOS | 1,889 | 939 | 2,868 | 5,534 | 24,220 |

Section 5.3 and Table 5: A component ablation uses conversation 26. Default
LightGMEM has 260 entities, Hit@5 0.929, and LLM-J 0.888. Serial NED has 260
entities, Hit@5 0.904, and LLM-J 0.862. One run per variant is reported.

Section 5.5 and Table 6: All non-community components and the QA configuration
are held fixed within this community comparison. No-community retrieval has
LLM-J 0.822, Label Propagation 0.825, Leiden 0.824, and Ego-Splitting 0.830.
There are 242 community-covered entities, of which 24 have multiple memberships.
The problem set and its relation to the component ablation are not specified.
Relation density is 1.00 for Ego-Splitting and 0.49 for Leiden; its definition is
not provided in these excerpts. Retrieval uses hybrid scoring and a cross-encoder.

Table 2: Multi-hop LLM-J is 0.748 for LightGMEM and 0.747 for the strongest
comparator. Multi-hop F1 is 0.419 versus 0.412. Uncertainty estimates are absent
from the supplied excerpts. Temporal performance is lower than the best baseline,
and the manuscript explicitly acknowledges this limitation.

## Supplied bibliography metadata

The manuscript cutoff for this exercise is 2026-07-29. An established related
system was public in 2025 and uses delayed consolidation. A new system was first
public on 2026-09-23. A comparison tool proposes treating both missing systems
as serious literature omissions. Neither system's full paper is supplied.

## Provenance

This is a bounded exercise, not a complete manuscript or actual peer-review vote.
Numerical and method excerpts are adapted from the local LightGMEM submission:
`D:/BaiduSyncdisk/paperreview/aaai2026 chen/陈​励凡投稿 aaai 2026 LightGMEM-0729.pdf`,
Sections 4.1, 5.1, 5.3, 5.5 and Tables 2, 4-6. The cutoff and bibliography exercise
are explicit fixture inputs, not inferred submission facts.
