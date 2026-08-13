# MANIFEST — paper_templates

论文骨架 / 审稿自查 / 返修模板组件。核心亮点：benchmark-paper-template 五支柱框架，直接对口 MA-SQLGrid 类基准论文。

## benchmark-paper-template/（Supervisor-Skills，完整 skill 单元）

| 文件 | 原路径 | 用途 | 怎么用 |
|---|---|---|---|
| benchmark-paper-template/SKILL.md | skills/benchmark-paper-template/SKILL.md | 基准/评测论文五支柱框架（Research Gap、Construction Pipeline、Evaluation Framework、Empirical Findings、可选 Companion Method），产出完整性审计 + 引言逻辑链 + Section 2-7 骨架 + 投稿前 checklist | 写基准论文时整体加载 |
| benchmark-paper-template/references/benchmark-design.md | skills/benchmark-paper-template/references/ | 基准设计方法 | 设计阶段参考 |
| benchmark-paper-template/references/checklist.md | 同上 | 投稿前 checklist | 完稿自查 |
| benchmark-paper-template/references/construction-pipeline.md | 同上 | 数据集构建流水线写法 | 写数据构建章节 |
| benchmark-paper-template/references/experiments.md | 同上 | 评测实验设计 | 写实验章节 |
| benchmark-paper-template/references/gap-analysis.md | 同上 | 研究缺口分析写法 | 写引言/相关工作 |
| benchmark-paper-template/references/instantiation-template.md | 同上 | 实例化模板 | 套用骨架时填 |
| benchmark-paper-template/references/orchestrator-notes.md | 同上 | 编排说明 | 了解各组件如何协作 |
| benchmark-paper-template/references/paper-structure.md | 同上 | 论文结构骨架 | 搭章节框架 |

## 顶层文件

| 文件 | 来源仓库 | 原路径 | 用途 | 怎么用 |
|---|---|---|---|---|
| experiments.md | Research-Paper-Writing-Skills | research-paper-writing/references/experiments.md | 实验章节写作规范（实验设置、表格呈现） | 写 Experiments 章节时参考 |
| paper-review.md | Research-Paper-Writing-Skills | research-paper-writing/references/paper-review.md | 审稿/评审写法参考 | 写 review 或自评时参考 |
| introduction.md | Research-Paper-Writing-Skills | research-paper-writing/references/introduction.md | 引言写作规范 | 写 Introduction 时参考 |
| cover-letter.tex | nature-skills | skills/nature-response/templates/cover-letter.tex | 投稿/返修 cover letter LaTeX 模板 | 直接套用 |
| response-to-reviewers.tex | nature-skills | skills/nature-response/templates/response-to-reviewers.tex | 逐点回复审稿意见 LaTeX 模板 | 返修时套用 |
| check_package_consistency.py | nature-skills | skills/nature-response/scripts/check_package_consistency.py | 检查 LaTeX 返修包机械一致性（正文/回复/封面信交叉引用） | `python check_package_consistency.py <返修包目录>` |
| structured_review.py | PaperSpine | src/scripts/structured_review.py | 对 PaperSpine 稿件做结构化同行评审 | `python structured_review.py <稿件>` |
| respond_check.py | PaperSpine | src/scripts/respond_check.py | 校验 review_response/ 返修包（回复是否逐条对应意见） | `python respond_check.py <返修包目录>` |
| kill-argument/SKILL.md | Auto-claude-code-research-in-sleep | skills/kill-argument/SKILL.md | 双线程对抗式评审：先构造最强 200 词拒稿意见，再逐点辩护，暴露未解决的关键问题 | 投稿前模拟拒稿 |
| rigor-reviewer/SKILL.md | AI-Research-SKILLs | 22-agent-native-research-artifact/rigor-reviewer/SKILL.md | ARA Seal Level 2 语义认知评审：六维度打分（证据相关性、可证伪性、范围校准、论证连贯、探索完整性、方法严谨），输出分级报告与 Accept-Reject 建议 | ARA/论文语义审稿 |
| rigor-reviewer/references/review-dimensions.md | AI-Research-SKILLs | 22-agent-native-research-artifact/rigor-reviewer/references/review-dimensions.md | 六维度评审细则 | 配合 rigor-reviewer/SKILL.md |
| evidence-discipline.md | Supervisor-Skills | skills/paper-writer/references/evidence-discipline.md | 证据纪律：写作中证据使用的约束 | 写作全程约束文档 |

备注：期刊适配与多智能体深度审稿走本地 `D:/aicoding/paper_reviews/`（9 期刊画像），本目录只补"骨架模板 + 机械自查 + 返修包"缺口。
