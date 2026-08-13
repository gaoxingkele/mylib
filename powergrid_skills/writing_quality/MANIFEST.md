# MANIFEST — writing_quality

去 AI 腔与写作质量组件。用途：降低 AIGC 检测痕迹、删除 AI 高频套话、提升学术写作质量。

| 文件 | 来源仓库 | 原路径 | 用途 | 怎么用 |
|---|---|---|---|---|
| writing_quality_check.md | academic-research-skills | academic-paper/references/writing_quality_check.md | 写作质量检查清单 | 逐段自查 |
| forbidden-patterns.md | Supervisor-Skills | skills/pre-submission-reviewer/references/forbidden-patterns.md | 禁用表达模式清单（reviewer 视角的红线） | 投稿前全文搜一遍 |
| phrases-to-cut.md | claude-scholar | skills/writing-anti-ai/references/phrases-to-cut.md | 应删除的 AI 高频短语库（英文） | 全文检索替换 |
| patterns-english.md | claude-scholar | skills/writing-anti-ai/references/patterns-english.md | 英文 AI 腔句法模式及改写建议 | 润色时对照 |
| humanize_check.py | PaperSpine | src/scripts/humanize_check.py | 校验 humanize_matrix.md 并扫描残留 AI 模式 | `python humanize_check.py <文件>` |
| ai-tone-guardrails.md | Supervisor-Skills | skills/paper-polish/references/ai-tone-guardrails.md | AI 语气护栏：润色时哪些腔调必须压掉 | 润色流程的约束文档 |
