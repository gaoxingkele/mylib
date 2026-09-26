# Codex + Academic Research Skills (ARS) — Powergrid Digest

把「Codex 官方最佳实践」+「Academic Research Skills for Codex」消化成可执行知识包，
供 `D:/aicoding/mylib` 与 `powergrid_benchmark` 共用。

## 入口

| 文件 | 用途 |
|---|---|
| `DIGEST.md` | 教程消化版（6 姿势 + ARS 装用 + 红线） |
| `playbooks.md` | 电网论文任务路由（接 Paper_CCF / IdeaSpark / RepLLM） |
| `digests/mdpi-information-upgrade-2026-09.md` | 真实案例蒸馏：长稿迁 MDPI Information 的长度控制、图表预算、补充材料迁移、新证据入稿判据、打包与投递纪律 |
| `digests/powergrid-diagnostic-eval-2026-09.md` | 真实案例蒸馏：诊断/负结果评测的五个统计陷阱、把零结果写成界、分层证据表、预注册与发布边界工程（C²GES, Information 2026-09） |
| `tools/manuscript_display_audit.py` | 确定性审计：页数/Overfull/未定义引用、末页余量、图-表清单与未引用 label、孤儿图、tex/pdf/docx 哈希、补充材料 md↔PDF 双源一致 |
| `tools/paired_diagnostic_stats.py` | 配对差诊断统计：零质量、不一致对、精确/随机符号翻转、单侧 bootstrap 上界、留一法包络、功效天花板与所需样本量（纯标准库，`--self-test`） |
| `AGENTS.academic.template.md` | 可复制到项目根的学术规则模板 |
| `../Academic-Research-Skills-Codex/` | 上游 ARS-Codex 源码（单 skill：`academic-research-suite`） |

## 快速用法

```text
# 长稿升级 / 瘦身 / 回迁图前后的同一把尺子
python -B D:/aicoding/mylib/Codex-Academic-Research/tools/manuscript_display_audit.py \
  --project <paper_dir> --tex paper.tex --figure-root figures \
  --supplement-zip <supp.zip> --supplement-source build_supplementary/_source.md
```

任一硬项失败（编译错误、Overfull、未定义引用、缺图、孤儿图、补充材料双源不一致）时退出码为 1，可直接挂进 CI 或 `paper_harness` 的 `custom:<path>` 验收项。

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
