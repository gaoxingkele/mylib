# autodeepreport 方法论：ARA × 持续学习 的蒸馏与融合

本文件蒸馏两篇论文，并说明它们如何共同支撑"更高质量、更深度、可版本升级"的研究报告。

## 来源

1. **The Last Human-Written Paper: Agent-Native Research Artifacts (ARA)**，arXiv:2604.24658，
   仓库 github.com/AmberLJC/Agent-Native-Research-Artifact（本地 `D:/aicoding/_tools/Agent-Native-Research-Artifact`）。
2. **Never Stop Learning: A Survey of Continual Learning and Self-Iteration in LLMs**（Deli Chen，
   2026，V5，由 Deli AutoResearch 框架自动生成），本地 `D:/aicoding/_tools/continual_learning_survey.pdf`。

---

## 一、ARA 的内核（解决"报告怎样结构化才高质量"）

ARA 把研究对象从"线性叙事 PDF"重构为**机器可执行知识包**，四个互锁层 + 跨层取证绑定：

| ARA 层 | 含义 | 在研究报告中的落地 |
|--------|------|------|
| **logic/**（认知层 What&Why） | 可证伪断言(claims)、概念、方法、约束、related_work | 报告的**核心结论/数据点**，每条带置信度与可核查判据 |
| **src/**（物理层 How） | 配置、环境、可执行代码桩 | 本工件的**检索查询词、源分派、转换脚本** |
| **trace/**（探索图 Journey） | 研究 DAG，含 typed 节点与**死胡同(×)** | **核验历程**：confirmed/修正/存疑/**refuted（已否证）也保留** |
| **evidence/**（证据层） | 精确表格、抽取的数据点、出处 | 分集群 `_research/cluster_*.md`（带 URL 的一手核验底稿） |

ARA 的两条"税"正是普通报告的通病：
- **Storytelling Tax**：叙事压平了分叉探索，读者(尤其 agent)要重走所有死胡同 → 故 **trace 层保留死胡同**。
- **Engineering Tax**：纸面与实证间的隐性知识无处记录 → 故 **claims 必须挂 evidence**（跨层取证绑定）。

ARA 的可操作约束（来自 rigor-reviewer 6 维）直接成为本报告的质量门：
- **D1 证据相关性**：引用的证据必须**实质支撑**断言，而非仅形式引用。
- **D2 可证伪性**：断言要有可独立核验的判据（"VOA 播 48 种语言"可查，"VOA 很有影响力"不可查）。
- 其余维度：充分性、范围匹配、独立性、provenance。

**进度披露三级**（报告同样适用）：PAPER.md 清单(~200 token) → 层文件 → 细节文件。报告对应：
摘要/目录 → 各章 → `_research/` 底稿。

---

## 二、持续学习综述的内核（解决"报告怎样升级才不退化"）

综述把**持续学习(CL)**与**自我迭代(SI)**统一在三轴(What×How×When)下。其核心痛点
**灾难性遗忘**（在新数据上更新会抹掉旧能力）与本项目"报告版本升级时丢失/弄脏已核验内容"
**同构**。综述的五大方法族给出避免遗忘的工程手段，逐一映射为报告升级策略：

| CL 方法族 | 原义 | 报告版本升级中的对应策略 |
|-----------|------|------|
| **正则化 (EWC)** | 用 Fisher 信息保护对旧任务重要的参数 | **保护高置信+多源+静态的断言**：升级时冻结、不重研（`ledger.py protected`） |
| **回放 (Replay)** | 用旧样本缓冲区重训以巩固记忆 | **replay 旧断言**：升级时把已核验事实重新纳入并比对，而非丢弃重写 |
| **参数隔离 (Adapter/LoRA)** | 为新任务加独立模块、冻结主干 | **新维度/新章节作为独立模块挂载**，不改动已核验主干（如"工作效果"章作为新 adapter） |
| **架构扩展** | 渐进式加列 | 新国别 = 新工件实例，共享方法论主干 |
| **自我迭代 (SI)** | 模型自产训练信号迭代提升 | **自我评审—修订循环**（rigor 自评 → 修订 → 再评） |

**稳定—可塑权衡**（max α·Stability + (1−α)·Plasticity）→ 报告升级的 **`--alpha` 旋钮**：
α 高=尽量保留旧内容、只补增量；α 低=大幅重研刷新。

**自我迭代的收敛条件**（综述 Eq.6：`E[Quality(S_t)] > E[Quality(x)]`）→ **质量门**：
一次升级只有当其产出质量**严格高于**上一版才提交；否则回退。并警惕 **reward hacking**
（看似更好实则错误）→ 用**对抗式核验**（多独立 verifier 试图否证）兜底。

**"何时更新"三粒度**（offline / online / 事件触发）→ 报告刷新触发：
- **time-sensitive 断言**按 `last_verified` 龄期触发复检（`ledger.py stale`）。
- 重大事件（如某机构被裁撤）触发该维度局部重研。

**三场景 → 版本号语义**：
- **Class-IL**（加新类）= 加新国别 → **major** 版本。
- **Task-IL**（加新任务）= 加新维度/章节 → **minor** 版本（参数隔离式挂载）。
- **Domain-IL**（分布漂移）= 时事更新/勘误 → **patch** 版本（时效复检）。

---

## 三、融合：autodeepreport 的"持续学习式深度报告"范式

把两者合一，报告不再是"一次性叙事"，而是**带持久证据账本的、可持续升级的知识工件**：

```
报告工件/
  <报告>_v<X.Y.Z>.md / .docx     # 叙事视图（从账本编译而来；ARA: 叙事是结构对象的一个视图）
  ledger.json                     # 证据账本（logic+evidence 层；持续学习的记忆，跨版本不遗忘）
  CHANGELOG.md                    # 版本变更（trace 层；新增/修订/翻案/保留/移除）
  _research/cluster_*.md          # 分集群一手核验底稿（evidence 细节层）
```

**首版(v1.0.0) 工作流**：SCOPE→DECOMPOSE→并行多源核验(fan-out)→写入 ledger（每条断言带
置信/状态/出处/时效）→质量门(rigor 自评+对抗核验)→由 ledger 合成叙事 MD→导出 DOCX。

**升级(vX→vX') 工作流**（持续学习核心）：
1. **LOAD** 旧 ledger（载入既有知识）。
2. **PROTECT**：`protected` 列出高置信受保护断言 → 不重研（避免遗忘 & 省算力 = EWC）。
3. **STALE**：`stale` 列出过龄的 time-sensitive 断言 → 仅这些 + 用户指定新维度进入重研队列。
4. **RESEARCH**：对重研队列 fan-out；新维度作为独立章节挂载（参数隔离）。
5. **MERGE**：把新发现 upsert 进 ledger；状态翻转(confirmed→refuted)与数值修订均留痕。
6. **GATE**：质量须 ≥ 旧版（自我迭代收敛条件）；对抗核验防 reward hacking。
7. **VERSION**：`bump`(major/minor/patch) → `changelog` 据 ledger diff 自动成稿 → 带版本名导出。

这样，每次升级都**单调累积**（replay 旧的、保护重要的、隔离新的、留痕变化的），
实现"文档版本升级而不灾难性遗忘"。
