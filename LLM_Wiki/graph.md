# Capability Graph

```mermaid
graph TD
    U[User Goal: 电网/AI论文] --> P0[Project Workspace<br/>D:/aicoding/powergrid_benchmark]

    P0 --> RS[ResearchStudio-Idea]
    P0 --> RC[RepLLM-CPA]
    P0 --> PC[Paper_CCF Skills]
    P0 --> AB[AERS Powergrid Bridge]
    P0 --> ARS[academic-research-suite ARS]
    P0 --> CX[Codex-ARS Digest]

    RS --> RS1[IdeaSpark Pattern Tags]
    RS --> RS2[Lit Table / Pattern Cards]
    RS1 --> M1[ideaspark_fullcorpus_distill.json]
    RS2 --> M2[ideaspark_fullcorpus_lit_tables/*]

    RC --> RC1[paper.json per PDF]
    RC --> RC2[Section/figure/table/evidence signals]
    RC1 --> M3[repllm_cpa_paper_json/*]
    RC2 --> M4[repllm-cpa-journal-distill.md]

    PC --> PC1[Journal Router]
    PC --> PC2[Per-journal writing policy]
    PC --> PC3[Acceptance patterns sections]
    PC1 --> O1[Paper_CCF/SKILL.md]
    PC2 --> O2[Paper_CCF/journals/*/SKILL.md]

    ARS --> W1[deep-research]
    ARS --> W2[academic-paper]
    ARS --> W3[academic-paper-reviewer]
    ARS --> W4[academic-pipeline]
    ARS --> W5[experiment-agent]
    CX --> ARS
    CX --> PC

    AB --> A1[literature-review-tools]
    AB --> A2[citation-checker]
    AB --> A3[figure-table-audit]
    AB --> A4[de-AIGC]
    AB --> A5[paper-pipeline optional]

    A1 --> Q1[文献检索/抽取/工具执行]
    A2 --> Q2[CrossRef/S2/OpenAlex 引文核验]
    A3 --> Q3[图表-正文一致性 QA]
    A4 --> Q4[中英文学术降AIGC]
    A5 --> Q5[终稿流水线编排]

    W2 --> S[Submission Readiness]
    W3 --> S
    M1 --> S
    M4 --> S
    O2 --> S
    Q2 --> S
    Q3 --> S
    Q4 --> S
```

## 读图说明

- 左侧是「能力入口」，中间是「运行产物」，右侧是「投稿就绪能力」。
- `ResearchStudio-Idea` 负责“方法/创新模式蒸馏”。
- `RepLLM-CPA` 负责“结构化证据蒸馏（章节-图表-实验信号）”。
- `Paper_CCF` 负责“目标期刊决策与写作约束”。
- `academic-research-suite` 负责“研究→写作→审稿流程（ARS）”。
- `Codex-ARS Digest` 负责“姿势手册 + 电网 playbook”。
- `AERS-Bridge` 负责“投稿前质量闸门工具链”。
