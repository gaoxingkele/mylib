---
name: grant-paper-book-skills-router
description: >-
  路由国自然/基金申报与论文写作到 docs 书蒸馏技能包，并与仓库已有
  proposal-writing、proposal-compiler、paper_compiler、academic-humanizer 等技能整合。
  在用户撰写/审查基金本子、凝练科学问题、用 AI 协同写论文且要求经得起审核、去 AI 味时使用。
---

# 基金本子 × 论文写作 · 书蒸馏技能路由

本目录 `docx/` 存放由 `docs/` 五本书经 book-to-skill 方法论蒸馏出的**句子级**技能包。本文件是整合层：决定先读哪本书技能、再挂接仓库哪条已有技能，禁止一次全量加载。

## 源书 → 技能包

| 书 | 技能目录 | 主职责 |
|---|---|---|
| 《从技术问题到科学问题》 | `docx/nsfc-tech-to-science-problem/` | STE 升维、能量/物质类、主导尺度结构、灵魂五问、宏观一招鲜、摘要七通过、函评循环嵌套 |
| 《国家自然科学基金项目申请之路》 | `docx/nsfc-application-path/` | 科学问题主线、系统三要素×七阶段、机理三件套/模型七步、栏目职能分离、初筛二违反·三不·四无 |
| 《凝练科学问题案例》 | `docx/nsfc-science-problem-cases/` | 四类属性、六路凝练、案例族 A–Q、病句改写与三栏对齐 |
| 《论文不是写出来的》 | `docx/ai-research-thinking-writing/` | 倒金字塔、三项标准、四大目标、四法提示词、创新四法、防黑箱工作流 |
| 《如何用AI写论文》 | `docx/ai-paper-practice-norms/` | 能不能用、自证合规六步、九大场景、披露留痕、全流程实操 |

交叉对照：`docx/ai-paper-crosswalk.md`。

## 仓库已有技能挂接（不重复造轮）

| 任务 | 先读书技能 | 再挂接 |
|---|---|---|
| 国自然/省部基金栏目起草 | nsfc-tech-to-science + application-path + cases | `proposal-writing`（分类路由）→ `fund-research-content-writer` |
| 科技部国际合作/重点研发 GPA | 同上（科学问题层） | `proposal-compiler` / `proposal-manager` / `proposal-reviewer` |
| 论文 ARA 结构化 | ai-research-thinking-writing | `paper_compiler` / `paper_rigor-reviewer` |
| CCF/期刊审稿口径 | （书技能提供问题与论证句级） | `Paper_CCF/.../SKILL.md` + evidence-calibrated-review |
| 去 AI 味 / 作者声口 | 两本 AI 书的事后校验规则 | **必须** `academic-humanizer`（audit→rewrite）；禁止承诺过检测 |
| 技能进化回放 | 书技能产出的候选规则 | `skills/skill-rsi`（门控写入，勿直接改冻结基因） |

## 默认流水线

### A. 基金本子（推荐顺序）

1. **属性归类**：读 `nsfc-science-problem-cases`：四类属性决策 + 六路凝练（主一路+辅一路）→ 选定一类，禁止四类口号并列；用病句改写模板压成可检验主问。
2. **升维科学问题**：读 `nsfc-tech-to-science-problem`：STE 载体论 → 能量类或物质类 → 主导尺度关键结构 / 底层构效；共性科学问题加特色定语。
3. **方法骨架**：读 `nsfc-application-path`：系统三要素×演化七阶段；机理类三件套或模型七步；假说类型。
4. **立项依据句级**：`nsfc-tech-to-science-problem` 灵魂五问与 `nsfc-application-path` 立项依据六问对齐（每层结论=下层首句）；宏观一招鲜绑定假说干预点。
5. **栏目对齐**：题目/摘要句链 → 目标/内容/关键科学问题/方案互锁；用 application-path cheatsheet 做初筛（二违反·三不·四无）与函评自检。
6. **指南与证据**：切回 `proposal-writing`：当年指南/模板为准（覆盖书中 2019 口径），事实标材料编号，缺口标【待补】。
7. **去 AI 味门禁**：`academic-humanizer` audit；删空话、补机制句、证据绑定；不编造预实验。

### B. 论文写作（推荐顺序）

详序见 `docx/ai-paper-crosswalk.md`。压缩版：

1. **规则卡（B）**：管理主体×场景；禁区；能不能用、用到哪一步。
2. **标准与收敛（A）**：三项标准 + 倒金字塔；禁止一键成文。
3. **问题与创新（A）**：框架/深入/创新四法 → 可检验命题。
4. **协同起草（A 四法 + B 九大场景）**：投喂与分步；人工核验引用与数据。
5. **防黑箱 + 披露留痕（A-Ch7 + B）**：分窗校验；自证六步与声明。
6. **结构化/评审**：按需 `paper_compiler` / Paper_CCF venue skill。
7. **去 AI 味门禁**：`academic-humanizer`；不过检测承诺。

## 句子尺度硬约束（跨书）

写作任一关键句必须能回答：

1. **载体是什么**（技术/工程现象）→ **科学问题是什么**（机制/结构/关系，可证伪）
2. **前人未解本质**（非“研究较少”）
3. **假说干预点**（改什么结构/通量/边界条件）
4. **证据绑定**（预实验/文献结论/数据；无则【待补】）
5. **学科主语**（用学科底层词，不用“优化性能/提高效率”当科学结论）

禁止默认输出：完善/优化/研制堆砌、四大属性口号墙、无文献投喂的综述、不可追溯的“研究表明”。

## 加载策略

- 只加载本路由 + **当前阶段** 1 个主书技能的 `SKILL.md`；章节文件按需打开。
- 同时涉及基金与论文时：先完成科学问题层（基金三书），再进论文 AI 工作流。
- 书技能与上游技能冲突时：**当年指南/期刊政策 > 书中方法论 > 上游例文**。
