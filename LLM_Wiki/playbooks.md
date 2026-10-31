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

### 按目标会场独立评审

用户要求 Paper CCF 审稿/评审报告时：先读 `Paper_CCF/SKILL.md` 与一个目标会场画像，再读
`Paper_CCF/resources/evidence-calibrated-review.md`，从原稿建立证据记录后核验已有意见。
输出保留实际优点、关键问题、作者问题与有条件建议；PDF 另做文本与页面验证。
经验与证据边界见 `Paper_CCF/resources/worked-examples/lightgmem-review-distill.md`。

## 3) 全流程“一条龙”

1. Codex 姿势：`Codex-Academic-Research/DIGEST.md`（现场 / AGENTS / 四要素 / Plan）
2. `academic-research-suite` pipeline（`ars-full`）
3. `Paper_CCF` 期刊约束
4. IdeaSpark + RepLLM 本地证据
5. AERS 投稿闸门

## 4a) 进化 mylib 评审/写作 skill（Skill-RSI）

1. 读 [`skills/skill-rsi/SKILL.md`](../skills/skill-rsi/SKILL.md) 与 `references/PROTOCOL.md`。
2. `python skills/skill-rsi/scripts/skillrsi.py --root C:/aicoding/mylib init`（仅首次）。
3. `targets` 确认目标在一等公民目录内；每次只选一个 surface。
4. 改 skill/协议正文后 `propose` → `gate` → 人确认后 `admit` 或 `reject`。
5. 申请书候选必须仍能通过 `validate_review_basis.py`；专利不得削弱锚点/硬门禁；论文合成分默认不可报告。
6. 不要把 `Auto-Empirical-Research-Skills` 里成打 peer-review 推进本环。

## 4) 构造可编译多智能体评审与 Benchmark

1. 从 `C-MARS-ReviewSpec/literature/protocol.md` 冻结问题、检索式和纳排条件。
2. 执行 `search_literature.py`，再用 `web_discovery.py` 补充发现；网络结果必须回到主来源核验。
3. 在 `reviewspec/examples/` 编写规范，由 `reviewspec/compiler.py` 通过 schema、引用闭合、veto 和权重检查。
4. 按“独立盲审 → issue 冲突 → 有限质询 → 独立裁决 → 测量校准”生成任务图；失败时保留 receipt 并允许弃权/人工复核。
5. 用 `benchmark/schemas/longreview_instance.schema.json` 表达版本对、受控变形和 group-aware split。
6. 先跑证据/约束验证门，再报告有效性、复测可靠性、不变性、局部单调性、偏差、校准和成本。
7. 任何规则、知识库、模型或数据升级都必须冻结版本与哈希，禁止把不同快照的分数直接解释为内容进步。

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
