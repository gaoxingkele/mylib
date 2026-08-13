# MANIFEST — statistics

统计报告规范组件。用途：选检验方法、查假设前提、按规范报告显著性/效应量，回应审稿人的统计质疑。

| 文件 | 来源仓库 | 原路径 | 用途 | 怎么用 |
|---|---|---|---|---|
| SKILL.md | scientific-agent-skills | skills/statistical-analysis/SKILL.md | 统计分析主协议：检验选择、假设检查、效应量、功效分析、贝叶斯替代、APA 格式报告 | 做统计分析/写结果时整体加载 |
| assumption_checks.py | scientific-agent-skills | skills/statistical-analysis/scripts/assumption_checks.py | 统计假设前提检查（正态性、方差齐性等） | `python assumption_checks.py <数据>` |
| test_selection_guide.md | scientific-agent-skills | skills/statistical-analysis/references/test_selection_guide.md | 统计检验选择指南（t 检验/ANOVA/卡方/非参/回归等） | 不确定用哪个检验时查 |
| reviewer-checklist.md | nature-skills | skills/nature-statistics/references/reviewer-checklist.md | 审稿人统计检查清单（Nature 系标准） | 投稿前按审稿人视角自查 |
| statistical-reporting.md | nature-skills | skills/nature-statistics/references/statistical-reporting.md | 统计报告规范（Nature 系） | 写结果统计部分时对照 |
| statistical_reporting_standards.md | academic-research-skills | academic-paper-reviewer/references/statistical_reporting_standards.md | 统计报告标准（审稿视角） | 回应统计类审稿意见时参考 |
