---
name: aers-powergrid-bridge
description: 选择并调用 Auto-Empirical-Research-Skills(AERS) 中对电网/AI 论文编写最有价值的子技能。用于文献检索与抽取、引文核验、表图一致性审计、终稿语言打磨与降AIGC。避免整包加载，仅按任务路由到最小必要子技能。
---

# AERS Powergrid Bridge

## Purpose

Bridge skill for integrating `D:/aicoding/lib/Auto-Empirical-Research-Skills` into
the existing power-grid paper workflow with **selective routing**.

This bridge is intentionally narrow: it excludes most econ-specific causal pipeline
content and keeps only reusable writing/review/tooling capabilities.

## Trigger

Use when user asks to:

- improve literature review efficiency
- audit bibliography/citations before submission
- verify figure/table/text consistency
- run full post-draft polishing workflow
- reduce AI-writing signatures for journal submission

## Routed skills (recommended)

1. `skills/71-brycewang-lit-review-agent-tools/literature-review-tools/SKILL.md`
   - For tool recommendation + runnable workflows (MinerU, PaperQA2, ASReview, MCP).
2. `skills/62-PHY041-claude-skill-citation-checker/SKILL.md`
   - For CrossRef/S2/OpenAlex citation verification.
3. `skills/54-scdenney-open-science-skills/skills/figure-table-audit/SKILL.md`
   - For figure/table/caption/cross-reference QA.
4. `skills/48-de-AIGC-skills/SKILL.md`
   - For bilingual academic de-AIGC rewrite.
5. `skills/67-econfin-workflow-toolkit/paper-pipeline/SKILL.md`
   - For orchestrated post-first-draft polishing (use with caution; adapt prompts).

## Guardrails for our environment

- Default language: Simplified Chinese for interaction.
- Keep manuscript technical content in English/LaTeX as needed.
- Do not run econ-only identification workflows unless explicitly requested.
- Prefer repository-local scripts and existing `Paper_CCF` skills when overlap exists.
- Always preserve coefficients, tables, and citations during rewriting.

## Suggested usage patterns

- **Literature build phase**: 71 + existing ResearchStudio-Idea workflow.
- **Pre-submission QA**: 62 + 54 + current journal-specific `Paper_CCF` skill.
- **Language/risk polishing**: 48 on abstract/introduction/conclusion first, then full text.
- **One-shot finishing**: 67 `paper-pipeline` only after user confirms backup/rollback plan.

