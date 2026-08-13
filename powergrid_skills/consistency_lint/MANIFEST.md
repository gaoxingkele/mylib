# MANIFEST — consistency_lint

全文一致性与 LaTeX 静态检查组件。用途：投稿前机械性扫描正文的一致性风险与 LaTeX 隐患（不覆盖"数字 vs 表格"语义核对，那是 claim_evidence 的事）。

| 文件 | 来源仓库 | 原路径 | 用途 | 怎么用 |
|---|---|---|---|---|
| check_consistency.py | nature-skills | skills/nature-shared/scripts/check_consistency.py | 在稿件文本中机械检出一致性风险（术语、缩写、单位等前后不一） | `python check_consistency.py <manuscript 文本>` |
| consistency-sweep.md | nature-skills | skills/nature-shared/core/consistency-sweep.md | 一致性清扫协议：扫什么、按什么顺序、如何报告 | 作为指令文档加载 |
| latex_guard.py | PaperSpine | src/scripts/latex_guard.py | LaTeX 稿件守卫检查（结构、引用、常见隐患） | `python latex_guard.py <tex 目录或文件>` |
| latex-rules.md | Supervisor-Skills | skills/pre-submission-reviewer/references/latex-rules.md | LaTeX 静态检查规则清单 | 配合 latex_guard 或人工自查 |
| grammar-rules.md | Supervisor-Skills | skills/pre-submission-reviewer/references/grammar-rules.md | 语法规则检查清单（投稿前 reviewer 视角） | 人工/agent 逐项自查 |
