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
