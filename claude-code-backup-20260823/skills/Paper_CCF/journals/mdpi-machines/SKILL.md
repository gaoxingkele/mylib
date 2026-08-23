---
name: mdpi-machines
description: Use when targeting the MDPI journal Machines or deciding whether a manuscript on electrical machines/drives, motor control, mechatronics/robotics, or machine fault diagnosis/condition monitoring fits it. The machine/drive/control system must be the object of study. Read ../../resources/mdpi-common.md for the shared MDPI model.
---

# Machines (MDPI)

## Journal positioning

Machines (est. 2013, ISSN 2075-1702, monthly, gold OA) covers machinery, mechanical engineering, and **machine/mechatronic systems**. Gating fit rule: **there must be a concrete machine, drive, or control system as the object of study** — generic AI/optimization/signal-processing with no physical machine is a scope mismatch. Mid-tier reputation; good for applied control/drives work needing fast turnaround. Read `../../resources/mdpi-common.md` first for the shared MDPI model.

- Metrics (as-of 2026-07 — **verify at https://www.mdpi.com/journal/machines**): IF ≈ **2.5** (Eng. Mechanical / Electrical & Electronic; sources split ~2.5–3.0), CiteScore ≈ **4.7** (Q1 Control and Optimization); APC ≈ **CHF 2,400**; median ≈ **15.9 days** to first decision. Indexed SCIE, Scopus.

## When to trigger / scope & section fit

- Work on **electrical machines & drives, motor control, power-electronic actuation, mechatronic/robotic systems, machine fault diagnosis/prognostics, condition monitoring / digital twin, powertrain/vehicle systems**.
- Sections include: **Electrical Machines and Drives**; Machine Design & Theory; Turbomachinery; **Robotics, Mechatronics and Intelligent Machines**; **Automation and Control Systems**; Advanced Manufacturing; Vehicle Engineering; Friction & Tribology; Condition Monitoring & Fault Diagnosis. **Verify at `/journal/machines/sections`.**
- **Power×CS/control fit:** motor drives, control strategies, mechatronics, machine fault diagnosis/prognostics with a concrete machine/drive/control system.

## Venue-specific calibration

- **Reviewer lens:** "Does the work advance the machine/drive/control itself, with sound validation?" Fingerprint: electrical machines · motor drives · control · mechatronics · fault diagnosis · condition monitoring · robotics · powertrain.

## Method & evidence bar / house style

- Sound validation (simulation + ideally bench/experimental on the actual machine/drive); clear advance over existing designs/controls. MDPI Word/LaTeX template, MDPI numbered refs (see `../../resources/mdpi-common.md`).

### Distilled full-text patterns (local corpus, 2026-08)

- Full-text sample: **n=8** (avg ~28 pages in first-pass extract).
- Topic mix in sample: power/energy-related ≈ 5/8; algorithm/ML ≈ 3/8.
- Lexical signals (first pages): baseline/comparison ≈ 3/8; ablation/sensitivity ≈ 0/8; dataset/benchmark ≈ 3/8.
- Observed acceptance-style cues from titles/keywords/abstracts:
  - [power,algo] Local Motion Planner for Autonomous Navigation in
  - [power] Fault Detection and Diagnosis with Imbalanced and
  - [power,algo] Multi-objective Optimization of Savonius Wind Turbine
  - [power] Citation: Tawﬁq, K.B.; Güleç, M.;
  - [other] Citation: Bingul, Z.; Gul, K.
  - [algo] Designing an Experimental Platform to Assess Ergonomic
  - [power] Mild Hybrid Powertrain for Mitigating Loss of Volumetric
  - [other] Academic Editors: Yancai Xiao,
- Practical bar inferred: complete method stack + quantitative comparison; incremental named combinations common; claims should match reported metrics.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/mdpi-machines/`.

### Distilled deep structure & style (local corpus, 2026-08)

- Deep sample: **n=8** PDFs under `fulltext_by_journal/mdpi-machines/`.
- **Length:** pages mean/median **28.0/22.5** (range 11–56); words mean/median **10077/8558**.
- **Structure:** sections mean **20.5**; paragraphs mean **47.8**; words/paragraph mean/median **252.0/147.7**.
- **Artifacts:** formulas≈**19.2**; figures≈**13.8**; tables≈**4.0**; block-diagrams≈**1.4** (mentions). Block-diagram sections: other×5, method×2, experiment×2, 3.2 CLSTM×1, 4.3 General procedure of the proposed mo×1, 5 Results×1.
- **Experiment load:** datasets mentioned≈**1.4**/paper; named algorithms≈**3.4**/paper; baseline signal **8/8**; ablation/sensitivity **0/8**; strength histogram: {'very_strong': 4, 'solid': 2, 'strong': 2}.
- **Innovation preference:** **集成/应用创新（混合框架、场景落地、端到端流水线）** (votes {'integration_application': 8}).
- **Abstract craft:** mean **208** words / **8.9** sentences; dominant pattern: `descriptive` (top patterns [('descriptive', 2), ('gap/background → method claim → quantitative result', 2), ('gap/background → quantitative result', 1)]).
- **Conclusion craft:** mean **207** words; dominant pattern: `short wrap-up` (top [('short wrap-up', 3), ('missing', 2), ('restate contribution → limitations', 1)]).
- **Chapter size/role (corpus means):**
  - **introduction**: avg ~1308 words / ~8.1 paragraphs；核心写法：动机→缺口→贡献列表；少公式，偶发总览框图
  - **method**: avg ~503 words / ~3.7 paragraphs；核心写法：符号/问题定义→算法或框架→复杂度或流程框图；公式与架构图密集
  - **experiment**: avg ~463 words / ~3.5 paragraphs；核心写法：数据集+基线+指标表+对比/消融图；强调可复现设置
  - **conclusion**: avg ~883 words / ~6.5 paragraphs；核心写法：重述贡献与定量结果→局限→未来工作
- **Frequent terms:** Therefore, Machines, However, Moreover, Furthermore, Additionally, IEEE, Finally, Equation, Since, Proceedings, MobileNet.
- **Frequent named algorithms:** attention(5), CNN(3), Kalman(3), Adam(2), SVM(2), GA(2), adam(1), LSTM(1).
- **Frequent dataset/benchmark cues:** dataset(4), Dataset(2), DATASET(1), NREL(1), data set(1), IEEE 
112(1), IEEE 112(1).
- **Common sentence openings:** `Local Motion Planner for Autonomous Navigation`; `Autonomous agricul- tural eld machines have`; `Nevertheless achieving suf cient autonomous navigation`; `In this context this study presents`; `The rst algorithm makes use of`; `Concurrently second back-up algorithm based on`.
- **Writing logic to emulate:** match the dominant innovation mode; keep section budget near the means above; put architecture/block diagrams in method (and sometimes experiment overview); pair claims with the observed figure/table/formula density; abstract should follow the dominant pattern and usually include a quantitative punchline when the corpus does.

Corpus path: `papers/literature/target_journal_related/fulltext_by_journal/mdpi-machines/`.


### ResearchStudio-Idea acceptance patterns (full local corpus, 2026-08)

- Method: **ResearchStudio-Idea / IdeaSpark** (arXiv:2607.04439) full-corpus pass over `papers/literature/**` → `D:/aicoding/lib/skills/ResearchStudio-Idea`.
- Sample: **n=8** mapped local PDFs (mean ~28.0 pages extracted).
- **Dominant IdeaSpark move:** `architectural_operator_substitution` — *Substitute the Operator or Representation*.
- **Dominant journal-house move:** `named_stack_plus_case` — *Named Method Stack + Utility/IEEE Case*.
- IdeaSpark primary distribution: `architectural_operator_substitution`×2, `adapt_via_conditioning`×1, `generative_process_redesign`×1, `heterogeneous_decomposition`×1, `outside_taxonomy`×1, `reframe_as_solvable_object`×1.
- Journal-house distribution: `named_stack_plus_case`×3, `survey_or_review_synthesis`×3, `systems_security_or_iot_stack`×1, `hardware_or_field_validation`×1.
- Attested multi-pattern combos: `adapt_via_conditioning+architectural_operator_substitution`, `assumption_audit_and_pivot+generative_process_redesign`, `decompose_and_delegate+reframe_as_solvable_object`, `architectural_operator_substitution+controlled_diagnostic_design`.
- Evidence readiness: baseline **62%**, ablation **25%**, dataset/benchmark **38%**.
- **Write for this venue:** pick bottleneck → compose IdeaSpark move with journal-house move → audit failure modes (wrapper / confound / untouched bottleneck) → match evidence rates.
- Artifacts: `metadata/ideaspark_fullcorpus_pattern_cards/mdpi-machines/overview.md`, `metadata/ideaspark_fullcorpus_lit_tables/mdpi-machines_lit_table.md`.

Corpus: all discoverable PDFs under `papers/literature/` mapped to `mdpi-machines`.

### RepLLM-CPA structured evidence (full local corpus, 2026-08)

- Method: **RepLLM Content Parsing** (arXiv:2509.21074) CPA-lite → `paper.json` Shared Memory paper-space; code at `D:/aicoding/lib/RepLLM` (full ADA/CGA/ARA **not** run on journal corpus).
- Sample: **n=8** mapped local PDFs.
- Section presence rates: intro **88%**, method **88%**, experiments/results **88%**, conclusion **0%**.
- Multimodal density (mean/paper): figures **6.0**, tables **1.8**, algorithms **0.2**, equation markers **5.6**.
- CPA evidence signals: baseline cues **25%**, ablation **0%**, dataset/benchmark **38%**, data-availability **0%**, code-availability **0%**.
- CPA-scoped IdeaSpark dominant move: `generative_process_redesign` · journal-house: `hardware_or_field_validation`.
- Artifacts: `metadata/repllm_cpa_paper_json/`, `metadata/repllm_cpa_lit_tables/`, `metadata/repllm_cpa_journal_distill_notes.md`.

## APC / review / Special Issues

- APC ≈ CHF 2,400 after acceptance (verify). Single-blind, ≥2 reviewers, ~15.9 d first decision, 1–2 short revision rounds. Section + Special-Issue model — pick an on-scope SI; vet Guest-Editor invitations.

## Official-cycle checklist / pre-submission self-check

- Open `/journal/machines`, `/instructions`, `/apc`, `/sections`, `/special_issues`, `/stats`; verify APC, IF/quartile, Section list. Official pages win.
- [ ] There is a **concrete machine/drive/mechatronic/control system** as the object of study. [ ] Validation on the actual system (bench/experimental where possible). [ ] Correct Section / on-scope SI. [ ] Data Availability + ethics complete.

## Common desk-reject triggers

- Generic AI/optimization/signal-processing with **no physical machine/drive/control system**; weak validation; out of Section scope.

## Re-routing decision

- **MDPI Actuators / Electronics / Energies** (drives/power electronics); higher-selectivity **IEEE Transactions on Industrial Electronics / Power Electronics / Transportation Electrification**; **IEEE Access**.

## Output format

```text
[Target] Machines (MDPI)
[Fit] High / Medium / Low (one-line: is there a concrete machine/drive/control system?)
[Cost/Speed] ~CHF 2,400 · ~16-day first decision
[Main evidence gap] <system-validation / bench-experiment / Section-fit fix>
[Best-fit Section] <Electrical Machines & Drives, Automation & Control, Robotics/Mechatronics, ...>
[Top rejection risk] no-physical-system / weak-validation / scope
[Re-route suggestion] <Actuators/Electronics/Energies; IEEE T-IE/T-PEL; IEEE Access>
```

---
_Journal profile (author-advising). Numbers are as-of 2026-07 and must be verified on the official page. Shared MDPI model: `../../resources/mdpi-common.md`; index: `../../resources/journal-roster.md`; selection guide: `../../resources/journal-selection-guide.md`._
