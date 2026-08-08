# Codex + Academic Research Skills (ARS) — Powergrid Digest

把「Codex 官方最佳实践」+「Academic Research Skills for Codex」消化成可执行知识包，
供 `D:/aicoding/lib` 与 `powergrid_benchmark` 共用。

## 入口

| 文件 | 用途 |
|---|---|
| `DIGEST.md` | 教程消化版（6 姿势 + ARS 装用 + 红线） |
| `playbooks.md` | 电网论文任务路由（接 Paper_CCF / IdeaSpark / RepLLM） |
| `AGENTS.academic.template.md` | 可复制到项目根的学术规则模板 |
| `../Academic-Research-Skills-Codex/` | 上游 ARS-Codex 源码（单 skill：`academic-research-suite`） |

## 已安装位置

- Codex：`~/.codex/skills/academic-research-suite` → lib 源码
- Claude/Cursor：`~/.claude/skills/academic-research-suite` → 同左
- lib skills junction：`skills/academic-research-suite`

验证：新开对话后应只看到 **一个** ARS 条目 `academic-research-suite`，
不要看到四个拆开的 `deep-research` / `academic-paper` / …（那是 Claude Code 布局）。

## 与本机其它能力的关系

见 `../LLM_Wiki/graph.md`。ARS 管「研究→写作→审稿流程」；
`Paper_CCF` 管期刊 fit；`ResearchStudio-Idea` / `RepLLM-CPA` 管本地语料蒸馏；
`AERS-powergrid-bridge` 管引文核验/图表审计/降 AIGC。
