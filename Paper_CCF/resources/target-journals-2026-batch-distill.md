# Target-journal batch distill notes (2026-08)

Full-text PDFs under `powergrid_benchmark/papers/literature/target_journal_related/fulltext_by_journal/<slug>/`.

Deep notes: `metadata/journal_deep_distill_notes.md` + `metadata/journal_deep_distill.json`.

Each `journals/<slug>/SKILL.md` has **Distilled deep structure & style** (pages/words/sections/paragraphs/formulas/figures/block-diagrams/abstract·conclusion craft/innovation mode).


## Counts & deep means

| slug | n | pages | words | secs | figs | formulas | innov |
|---|---:|---:|---:|---:|---:|---:|---|
| `elsevier-journal-of-energy-storage` | 10 | 25.4 | 9965.7 | 23.7 | 10.4 | 22.1 | integration_application |
| `ieee-internet-of-things-journal` | 10 | 10.4 | 7031.8 | 8.9 | 8.5 | 7.2 | integration_application |
| `ijacsa` | 10 | 7.6 | 5665.1 | 14.4 | 6.5 | 7.5 | integration_application |
| `keai-unconventional-resources` | 0 | 0 | 0 | 0 | 0 | 0 |  |
| `mdpi-algorithms` | 10 | 26.6 | 9510.2 | 17.2 | 5.6 | 42.4 | integration_application |
| `mdpi-atmosphere` | 10 | 26.7 | 9310.9 | 13.8 | 9.1 | 12.4 | integration_application |
| `mdpi-future-internet` | 10 | 27.4 | 11584.9 | 25.3 | 9.1 | 9.1 | integration_application |
| `mdpi-information` | 10 | 26.5 | 11516.5 | 22.1 | 11.3 | 28.0 | integration_application |
| `mdpi-machines` | 8 | 28.0 | 10077.1 | 20.5 | 13.8 | 19.2 | integration_application |
| `mdpi-remote-sensing` | 10 | 27.8 | 10376.9 | 18.5 | 9.4 | 11.8 | integration_application |
| `mdpi-symmetry` | 10 | 28.8 | 14935.9 | 23.0 | 6.0 | 74.2 | integration_application |
| `nature-scientific-reports` | 10 | 12.7 | 7270.0 | 8.7 | 20.8 | 35.7 | integration_application |
| `peerj-computer-science` | 10 | 23.4 | 8822.4 | 12.4 | 5.7 | 17.7 | integration_application |
| `springer-discover-computing` | 10 | 24.1 | 10155.2 | 20.6 | 9.3 | 29.0 | integration_application |
| `tsp-cmc` | 10 | 20.0 | 5583.9 | 13.9 | 5.9 | 13.7 | integration_application |
| `wiley-ccpe` | 10 | 17.7 | 5842.5 | 22.7 | 6.1 | 20.8 | integration_application |

**Gaps (2026-08-05):**
- `keai-unconventional-resources`: **0/10** — OA PDFs only on ScienceDirect; aria2c / cloudscraper / direct all return **403**. No EuropePMC/arXiv title mirrors found. Skill has empty deep sample; use aims/scope until a non-Elsevier mirror appears.
- `mdpi-machines`: **8/10** — MDPI stampPDF 403; EuropePMC only has 1 Machines OA deposit; arXiv title-match found 0. Deep distill used the 8 local PDFs.
- Download toolpath used: `aria2c` at `%LOCALAPPDATA%\aria2\...\aria2c.exe` with proxy `http://127.0.0.1:17890`.

## ResearchStudio-Idea / IdeaSpark acceptance-pattern distill

Method borrowed from `D:/aicoding/lib/skills/ResearchStudio-Idea` (arXiv:2607.04439).

| slug | n | dominant_idea | dominant_journal_house | baseline% |
|---|---:|---|---|---:|
| `elsevier-journal-of-energy-storage` | 10 | `architectural_operator_substitution` | `storage_or_energy_device_review` | 30% |
| `ieee-internet-of-things-journal` | 10 | `generative_process_redesign` | `systems_security_or_iot_stack` | 40% |
| `ijacsa` | 10 | `heterogeneous_decomposition` | `named_stack_plus_case` | 30% |
| `keai-unconventional-resources` | 0 | `outside_taxonomy` | `` | 0% |
| `mdpi-algorithms` | 10 | `generative_process_redesign` | `survey_or_review_synthesis` | 30% |
| `mdpi-atmosphere` | 10 | `outside_taxonomy` | `survey_or_review_synthesis` | 70% |
| `mdpi-future-internet` | 10 | `generative_process_redesign` | `systems_security_or_iot_stack` | 40% |
| `mdpi-information` | 10 | `heterogeneous_decomposition` | `survey_or_review_synthesis` | 30% |
| `mdpi-machines` | 8 | `architectural_operator_substitution` | `named_stack_plus_case` | 62% |
| `mdpi-remote-sensing` | 10 | `generative_process_redesign` | `named_stack_plus_case` | 30% |
| `mdpi-symmetry` | 10 | `structural_prior_encoding` | `survey_or_review_synthesis` | 30% |
| `nature-scientific-reports` | 10 | `outside_taxonomy` | `named_stack_plus_case` | 40% |
| `peerj-computer-science` | 10 | `outside_taxonomy` | `named_stack_plus_case` | 40% |
| `springer-discover-computing` | 10 | `outside_taxonomy` | `survey_or_review_synthesis` | 40% |
| `tsp-cmc` | 10 | `structural_prior_encoding` | `named_stack_plus_case` | 90% |
| `wiley-ccpe` | 10 | `heterogeneous_decomposition` | `named_stack_plus_case` | 50% |
