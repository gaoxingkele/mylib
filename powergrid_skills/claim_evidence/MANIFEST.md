# MANIFEST — claim_evidence

claim-证据绑定与数字核查组件。用途：核对论文中每个数字、比较、范围性 claim 是否与原始结果文件一致；防止"表格一个数、正文另一个数"。

## scientific-writing/（scientific-agent-skills，完整 skill 单元）

| 文件 | 原路径 | 用途 | 怎么用 |
|---|---|---|---|
| scientific-writing/SKILL.md | skills/scientific-writing/SKILL.md | 科学写作 skill 主协议：证据溯源、报告规范覆盖、作者责任、一致性检查 | 作为指令文档加载 |
| scientific-writing/scripts/check_consistency.py | skills/scientific-writing/scripts/check_consistency.py | 稿件本地一致性检查（配合 manifest） | `python check_consistency.py <稿件>` |
| scientific-writing/scripts/audit_claims.py | skills/scientific-writing/scripts/audit_claims.py | 审计 claim→证据映射与本地引用标记 | `python audit_claims.py ...`（配合 claim_evidence_template.csv） |
| scientific-writing/scripts/lint_manuscript.py | skills/scientific-writing/scripts/lint_manuscript.py | 扫描占位符、语言风险、敏感内容 | `python lint_manuscript.py <manuscript.md>` |
| scientific-writing/assets/authorship_template.json | skills/scientific-writing/assets/ | 作者贡献声明模板 | 填写作者贡献时用 |
| scientific-writing/assets/claim_evidence_template.csv | skills/scientific-writing/assets/ | claim-证据映射表模板（核心） | 逐条登记"正文 claim ↔ 结果文件位置" |
| scientific-writing/assets/consistency_manifest_template.json | skills/scientific-writing/assets/ | 一致性清单模板 | 配合 check_consistency.py |
| scientific-writing/assets/manuscript_manifest_template.json | skills/scientific-writing/assets/ | 稿件文件清单模板 | 整理提交包时用 |
| scientific-writing/assets/reporting_coverage_template.json | skills/scientific-writing/assets/ | 报告规范覆盖度模板 | 检查 CONSORT/PRISMA 类规范覆盖 |
| scientific-writing/assets/reporting_guidelines.json | skills/scientific-writing/assets/ | 报告指南清单数据 | 被脚本/流程引用 |
| scientific-writing/assets/source_manifest_template.json | skills/scientific-writing/assets/ | 数据来源清单模板 | 登记数据出处 |

## 顶层文件

| 文件 | 来源仓库 | 原路径 | 用途 | 怎么用 |
|---|---|---|---|---|
| paper-claim-audit/SKILL.md | Auto-claude-code-research-in-sleep | skills/paper-claim-audit/SKILL.md | 零上下文论文数字核对协议：fresh reviewer 逐条比对正文数字与原始结果文件，防确认偏误 | 提交前让无上下文 agent 按此协议执行 |
| citation-audit/SKILL.md | Auto-claude-code-research-in-sleep | skills/citation-audit/SKILL.md | 零上下文引用审计：书目真实、归属正确、引用语境确实支持该引用 | 与 citation_verification 互补（偏"引用语境是否恰当"） |
| PAPER_PLAN_TEMPLATE.md | Auto-claude-code-research-in-sleep | templates/PAPER_PLAN_TEMPLATE.md | 论文计划模板（claim 先行规划） | 立项/开写前填 |
| EXPERIMENT_LOG_TEMPLATE.md | Auto-claude-code-research-in-sleep | templates/EXPERIMENT_LOG_TEMPLATE.md | 实验日志模板（结果可追溯） | 跑实验时同步记录 |
| ai_research_failure_modes.md | academic-research-skills | academic-pipeline/references/ai_research_failure_modes.md | AI 辅助研究常见失败模式清单 | 自查研究流程漏洞 |
| claim_verification_protocol.md | academic-research-skills | academic-pipeline/references/claim_verification_protocol.md | claim 核验协议（每条 claim 必须有可复核证据） | 作为核查流程规范加载 |
| contribution.md | PaperSpine | src/skill/references/contribution.md | 贡献声明写作与核查规范 | 写/查 Introduction 贡献列表 |
| reviewer-audit.md | PaperSpine | src/skill/references/reviewer-audit.md | reviewer 视角审计要点 | 投稿前自查 |
| results_validation_check.py | PaperSpine | src/scripts/results_validation_check.py | 校验 PaperSpine results_validation.md —— Results-as-Validation | `python results_validation_check.py <文件>` |
