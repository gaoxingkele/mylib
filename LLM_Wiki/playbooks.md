# Playbooks (Graph Traversal)

## 1) 从“想法”到“目标期刊”

1. `academic-research-suite`（deep-research / socratic）收敛问题。
2. `ResearchStudio-Idea`：生成 idea pattern 与 bottleneck。
3. `Paper_CCF`：按期刊 slug 做 fit 路由。
4. 产物：`ideaspark_*` + `journals/<slug>/SKILL.md`。

## 2) 从“初稿”到“投稿前 QA”

1. `academic-research-suite` → academic-paper 改稿 / 大纲。
2. `RepLLM-CPA`：抽取章节结构与证据几何。
3. `AERS-Bridge` / `ars-citation-check`：核验参考文献。
4. `figure-table-audit` + `de-AIGC`：图表一致性与语言风险。
5. `academic-paper-reviewer`：模拟审稿 / desk-reject 风险。

## 3) 全流程“一条龙”

1. Codex 姿势：`Codex-Academic-Research/DIGEST.md`（现场 / AGENTS / 四要素 / Plan）
2. `academic-research-suite` pipeline（`ars-full`）
3. `Paper_CCF` 期刊约束
4. IdeaSpark + RepLLM 本地证据
5. AERS 投稿闸门

## 规则

- 任何改写不得改变系数、样本量、显著性结论与引用指向。
- 当不同体系冲突时：以目标期刊 `Paper_CCF/journals/<slug>/SKILL.md` 为准。
- AERS 目录库与 ARS suite 仅按需调用，不做整包递归加载。
- ARS 验证：技能列表只应出现单个 `academic-research-suite`。

## 4) 从“指南与材料”到“申报书草稿”

1. 读取 [申报书入口](../proposal-writing/SKILL.md)，核对当年指南、空白模板、已有基础和研究/工作构想的编号及版本。
2. 以指南评审对象选科研基金、科技项目、教改或人才路线，仅加载对应适配和上游 skill。
3. 先输出缺口、要求对照表、分类工作表与模板提纲，再逐节起草；事实引用材料，缺项【待补】，不迁移海外规则或历史申请书事实。
4. 新对话审查草稿与指南/模板中的断点、矛盾和缺失信息，按原句—问题—建议输出；人工核对事实预算和导出格式，交同行审阅。
5. 原始材料不变，产物写当前申报项目；来源与边界见 [模块说明](../proposal-writing/README.md)。
