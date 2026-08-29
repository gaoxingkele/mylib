---
name: codex-ars-powergrid
description: 将 Codex 学术最佳实践与 academic-research-suite(ARS) 路由到电网/AI 论文项目。用于研究问题收敛、文献综述、改稿、审稿模拟、引用诚信闸门；并与 Paper_CCF、IdeaSpark、RepLLM-CPA、AERS-bridge 协同。
---

# Codex + ARS → Powergrid

## When to use

- 用户提到 Codex 姿势、ARS、`academic-research-suite`、`ars-plan` / `ars-lit-review` / `ars-full`
- 需要苏格拉底式收敛问题、综述、审稿、诚信检查
- 需要把通用 ARS 接到本仓库的期刊与本地语料能力

## Mandatory reads

1. `D:/aicoding/mylib/Codex-Academic-Research/DIGEST.md`
2. `D:/aicoding/mylib/Codex-Academic-Research/playbooks.md`
3. Suite router：`academic-research-suite` → 只加载当前阶段 `WORKFLOW.md`

## Route map

| Need | First skill / path |
|---|---|
| 收敛问题 / 文献 | `academic-research-suite` → deep-research |
| 写/改稿 | `academic-research-suite` → academic-paper |
| 审稿模拟 | `academic-research-suite` → academic-paper-reviewer |
| 端到端 | `academic-research-suite` → academic-pipeline |
| 选刊 / APC | `Paper_CCF` |
| 本地接受模式 | IdeaSpark / RepLLM distill under `powergrid_paper/metadata/` |
| 投稿闸门 | `aers-powergrid-bridge` |

## Guardrails

- 单 skill 入口：`academic-research-suite`（不要拆成四个 Claude 布局 skill）
- 不编造引用；数字与表格以手稿/数据为准
- 期刊冲突时以 `Paper_CCF/journals/<slug>/SKILL.md` 为准
- AI 不署名、不做最终科学裁决
