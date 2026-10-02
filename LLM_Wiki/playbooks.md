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

## 4) 从"自有论文"到"电力/水利发明专利"（批量）

1. 归属以用户口述为准（文件名里的 reviewer/peer-review 不作判据）；每篇论文拆成可独立成立的机制模块。
2. 场景映射矩阵三列缺一不进候选：同构问题 / 场景特有约束 / 约束倒逼的机制改造；独权只押第三列。
3. 每案一个子代理从头到尾：`patent-disclosure-skill` 交底书 → `cnipa-drafting-workflow` 00–07 → `paa/validate.py` 四门禁。
4. 查新两轮、无浏览器：R1 Tavily+Brave 初检 → `gp_fetch --backend tavily` 取全文 → `gp_verify` 逐字核验；R2 换轴（功能/跨领域/英文/上位）独立复检 + arXiv/Crossref NPL 核验。
5. Word 交付 `scripts/build_paper12_word.py`；评分 `patent-grant-scorer`（AHP-only，内部指数非授权率；incoPat 未跑时 evidence_confidence 封顶 45）。
6. 详见 `patent-paper2patent-power-water-12.md`。

## 规则

- 任何改写不得改变系数、样本量、显著性结论与引用指向。
- 当不同体系冲突时：以目标期刊 `Paper_CCF/journals/<slug>/SKILL.md` 为准。
- AERS 目录库与 ARS suite 仅按需调用，不做整包递归加载。
- ARS 验证：技能列表只应出现单个 `academic-research-suite`。
