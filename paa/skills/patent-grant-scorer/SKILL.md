---
name: patent-grant-scorer
description: >
  对中国发明专利交底书或申请文件进行证据约束的多专家可专利性评审与授权风险排序。
  结合incoPat检索原文、CNIPA硬门禁、PatentARA结构分和AHP风险指数，处理专家分歧、
  拜占庭异常评分、跨轮版本漂移和同批案件相对公平。适用于授权成功率、专利评分、
  可专利性评估、低分改进、多专家仲裁、改稿前后复评；不用于把单一分数解释为授权保证。
metadata:
  version: "2.3.0"
  domain: chinese-invention-patent-review
---

# 证据约束的专利多专家评审

目标不是制造一个更高的总分，而是回答三个彼此独立的问题：

1. 是否存在不能被平均分覆盖的法律或证据硬门禁；
2. 在当前最终独权和当前检索证据下，授权风险处于什么相对位置；
3. 下一轮最值得修改、补证据或重新检索的具体对象是什么。

## 必守原则

- **先门禁，后评分。** 客体、单篇X文件、充分公开/支持、证据真实性、确定性形式错误均单列；任何FAIL不得被高平均分抵消。
- **分数绑定版本。** 每轮至少记录当前独权哈希、检索所用独权哈希和证据集哈希。独权实质修改后旧检索与旧分数自动过期。
- **网页流程失败不是利好。** incoPat Agent空仓、技术要点提取失败、429、超时或报告未生成只表示证据缺失；不得解释成“未发现对比文件”。
- **API原文优先。** incoPat语义相似度和网页摘要用于召回；新颖性/创造性结论必须回到申请日资格、权利要求/说明书原文和区别特征映射。
- **双分数并存。** PatentARA或形式/支持图谱反映结构成熟度；AHP风险指数计入组合启示、工程事实、真实效果和客体风险。二者不同不是错误，必须解释差异来源。
- **AHP不是授权概率。** 在没有足量历史结果、测量模型拟合和样本外概率校准前，只输出AHP内部风险/准备度指数；旧AHP/SEM公式仅保留用于复现历史报告，不作为默认结论。
- **分歧按证据仲裁。** 不因某评分偏离多数就删除；先比较证据质量、原文核验、日期资格和推理链。高质量少数意见必须保留并触发定向复核。
- **禁止为了提分编造机制。** 新增状态、CAS、哈希、锁、凭证、父链、阈值或实验数据必须有申请日前材料；否则标记`needs-confirmation`并阻断正式写入。
- **输出只到人工复核。** 高分最多表示“进入代理师复核”；不得输出“保证授权”或“建议直接提交”。
- **OA 答复预案与禁止反悔风险评估引用 `paa/references/oa-response-playbook.md`。** 公知常识第二作用反驳、协同效应论证、禁止反悔管理是评分中的可救济性加分项。
- **独权收窄类整改必须实测，不凭直觉判断"更精简=分数更好"。** 收窄前后都跑一次量化门禁（Jev 或本评分器）对照，数据不支持就用 git 精确回退到收窄前版本，不要因为"已经做完"而将就；完整流程见
  [references/claim-narrowing-empirical-loop.md](../../references/claim-narrowing-empirical-loop.md)（P06-4/P06-5 实战蒸馏）。
- **创造性评分不能只看专利检索+模拟委员会，NPL 是必过腿，算法原理审查是必过项。** 只查专利文献、只用模拟角色评分，对算法/软件类发明系统性会漏掉相邻学科（运筹学/分布式系统/控制论等）里的经典范式作为真正 D1/D2；每案评分前确认 NPL 检索与算法原理审查（范式识别→跨领域失败模式→限定锚点核对）已执行，未执行的按门禁不完整处理，不得给出"创造性大概率通过"的结论。完整方法见
  [references/novelty-inventive-step-full-diligence.md](../../references/novelty-inventive-step-full-diligence.md)。
- **已有外部专业意见必须先进入评分输入，并与之对账。** 评分前检查 `revised/`、`raw_inputs/`、`历史资料归档/` 中有无代理机构或审查员意见；有则把其对比文件与结论一并提供给各角色。内部结论比外部乐观时，须逐条给出外部意见未掌握的具体证据，否则以外部结论为准。步骤见
  [references/novelty-inventive-step-full-diligence.md](../../references/novelty-inventive-step-full-diligence.md) 第零节。

完整证据等级、检索纪律、创造性攻击和整改规则见
[references/evidence-review-protocol.md](references/evidence-review-protocol.md)。

## 标准工作流

### 1. 冻结本轮状态

记录：

- `claim_hash`：本轮被评独权文本哈希；
- `search_claim_hash`：检索输入绑定的独权哈希；
- `evidence_hash`：已核验对比文件及摘录集合哈希；
- 申请日或优先权日、检索日期、检索接口与错误日志；
- PatentARA/PAA/CNIPA门禁使用的申请文件版本；
- 推荐（2.3.0）：其他独权哈希`independent_claim_hashes`、02–05 文本束哈希`text_bundle_hash`、事实层/论证层证据哈希`evidence_hash_facts`/`argument_hash`、冻结的锚点文件哈希`anchor_sha256`。

比较同一对象在不同工序绑定的哈希，不要求独权哈希与证据集哈希相等。独权与检索输入版本不一致时，输出`STALE_REVIEW_RESEARCH_REQUIRED`。说明书、效果依据、工程证据或评分口径改变时也须检查复评范围；同日评分不代表覆盖当日终稿。

### 2. 建立检索证据

调用`incopat-search`：

1. 最终独权执行至少一次语义检索；
2. 执行1—2组可审计布尔检索；
3. 对2—4件高相关文献调用`info`和`claim`，必要时调用`spec`；
4. 记录申请日/公开日资格、最接近文件D1、第二文件D2及可能组合动机；
5. 网页IPR报告只作为独立证据层，保留项目状态、候选数、报告数和失败原因；
6. 对准备进入创造性比对的文献调用 `patent-jev-screen`：每篇只送目标特征和标题、摘要或已定位段落。`suggested_route` 决定停、人看、取原文或填特征表；概率不进入 AHP，也不构成 X/Y/A 结论。

### 3. 独立专家评审

对改稿前后比较、算法/状态机闭环检查或低分整改，先读取
[references/mechanism-convergence-review.md](references/mechanism-convergence-review.md)，核验时序、规则冲突和技术因果链；不得把新增机制数量当作创造性收益。

四个基本角色分别评分，不先看他人结论：

- 审查员：25/2.2、22.2/22.3、26.3/26.4，从严攻击；
- 代理人：主叙事、A/B/C退守、OA可修性与商业价值；
- 无效请求人：单篇预见、D1+D2组合启示、支持过宽与证据漏洞；
- 数据/工程分析师：检索覆盖、原文核验、真实字段/日志/实验和版本一致性。

指标仍为S/N/I/D/Q五潜变量、16项1—9分。推荐使用证据丰富条目：

```json
"I3": {
  "score": 4.5,
  "confidence": 0.82,
  "evidence_quality": 0.90,
  "status": "confirmed",
  "evidence_refs": ["claim:CNxxxxxxA:1", "spec:CNyyyyyyA:0042"]
}
```

旧版纯数字输入仍可运行，但证据置信度会被封顶并产生警告。

评审软件、算法或电网案件时，如需用已授权/驳回案例校准指标解释，读取
[references/historical-outcome-anchors.md](references/historical-outcome-anchors.md)。历史案例只校准评分锚点，不替代当前案件检索，也不用于直接提高分数。

### 4. 仲裁而非简单平均

默认运行AHP-only评分器：

```powershell
python paa/skills/patent-grant-scorer/scripts/ahp_only_scorer.py input.json -o review.json --root <案件目录>
```

默认`robust`模式以中位数抵抗异常值，以证据加权均值保留高质量少数意见；四专家最多抑制一个低证据异常评分，但不删除原始意见。分差大、MAD高、高质量少数意见或疑似异常数超过容错上限时，输出`review_required`并要求定向补证据。

只有需要复现旧报告时才运行旧AHP/SEM口径：

```powershell
python paa/skills/patent-grant-scorer/scripts/ahp_sem_scorer.py input.json --aggregation legacy-mean
```

旧脚本输出中的`grant_probability`是历史内部映射，不得按真实授权概率引用。

拜占庭仲裁、跨轮马尔可夫状态和相对公平规则见
[references/byzantine-markov-arbitration.md](references/byzantine-markov-arbitration.md)。

### 5. 形成可执行整改

每个低分或分歧必须落到以下一种动作，禁止只写“加强创造性、优化表述”：

- **重新检索**：最终独权未绑定、候选原文未核验、申请日资格未知；
- **重塑创造点**：常规构件并列，不能证明前一机制改变后一机制的输入、状态或允许动作；
- **补充分公开**：字段、状态机、公式、阈值、正常/边界/异常路径或退化处理缺失；
- **取得事实证据**：代码、接口、表结构、日志、申请日前测试或可复现实验缺失；
- **调整权项**：A/B/C退守、常规旁支下沉、独权过宽或客体风险；
- **停止包装**：技术人员无法确认最小闭环时删除增强特征或重选发明点。

## 输出要求

同时输出：

- `hard_gates`及阻断原因；
- `score_layers.structural_readiness`；
- `ahp_index`及`score_layers.ahp_substantive_index`；
- `score_layers.evidence_confidence`与证据缺口警告；
- 每指标专家原分、可靠性、MAD、抑制项和高质量少数意见；
- `version_binding`和`round_transition`；
- 当前同批案件的相对百分位；
- 按P0/P1/P2排列的`action_queue`。

改稿复评另附“原问题—修改关系—实际收益—范围代价—证据状态—未关闭风险”表；收益须区分文本、机制、实测效果，不以旧分数为最新稿背书。

提供了 2.3.0 可选字段时，另外输出 `score_layers.residual_distinction`、`score_layers.retrieval_coverage`、`expert_independence` 和 `audit_warnings`，并在复评说明中逐条解读警告。

完整JSON格式和示例见[references/input-output-schema.md](references/input-output-schema.md)。

## 2.3.0 变更与依据

依据是两起中国发明申请（记为案 A、案 B）在“改稿前后＋新检索证据”复评中各自整理的“评分方法问题”清单（记为 A-问题n、B-问题n；原始记录留在所用项目内，不随本技能分发）。

**不变的部分**：AHP 指数公式、组权重、16 项指标、载荷和档位阈值都没有改。没有历史授权结果可用于校准，改了以后新旧分数就不能比较。本版只加可以确定计算的层、门禁和警告。所有新字段都是可选的；都不提供时，输出与 2.2.x 逐字段一致（`protocol_version` 除外；有 history 而没有冻结锚点时多一条 `anchor_not_frozen` 警告）。字段与规则见 schema 第 6 节。

| 变更 | 依据 | 作用 |
|---|---|---|
| 残余区别特征层 `residual_distinction`（输入 `feature_matrix`、`feature_matrix_frozen_at`），不入指数 | A-问题1、B-问题1 | 新 Y 文献使区别特征集合缩小时，16 项指标里没有一项会直接下降。现在由特征矩阵确定性地算出未被任何文献单篇公开（●）的特征和覆盖率；只剩 ≤1 个时警告 `single_pivot_independent_claim`。拆分基线要登记，各版本拆分不一致时给警告，以免靠多拆特征抬高“未覆盖数” |
| 检索覆盖层 `retrieval_coverage`（输入 `retrieval`），degraded 改为分级封顶 45→最高 65 | A-问题2、B-问题5 | 原来只要是 degraded，证据置信度就固定封顶 45，补做的全文语义检索、取全文、多库都看不出来。现在每满足一项加 5。覆盖度单独列出，不并入指数；独权特征没有检索过的逐条警告 |
| 检索绑定 `input_jsonpath` + `normalization: strip_ws_sha256` | A-问题8、B-问题4 | MCP 证据的查询在 `request.semantic_query`，原评分器只读顶层 `input`，只能记为“评审人声明”。现在评分器自己按“去全部空白、sha256”复算 |
| `narrowed_from_searched_claim` + `new_features_searched` | B-问题4 | 收窄后的独权以前只能判 STALE。新增特征确实检索过时记为 `narrowed_rechecked`，不判 STALE；没检索过的仍判 STALE |
| 版本与证据分层：`independent_claim_hashes`、`text_bundle_hash`、`evidence_hash_facts`、`argument_hash` | A-问题3、A-问题4、B-问题7 | 以前只看权 1 哈希：权 22 和说明书改了也判 `same_state_recheck`；playbook 等申请人自写的论证改了也算“证据变化”。现在新增 `non_claim1_text_revision_fixed_evidence` 等类型，证据按事实层判断，只有论证层变化的计为申请人侧改进 |
| 防提分漏洞警告：`anchor_not_frozen`、`effect_score_raised_without_new_data`、`evidence_set_shrunk` | A-问题7、B-问题7 | 防止三种做法：事后往锚点里补缺陷再修复、不提交新数据只给效果重新贴标签、删掉证据文件来回避 I 组降分。三者都只警告，不改分 |
| 角色独立性 `expert_meta.<role>.independent` → `disagreement_not_informative` 与角色偏移诊断 | A-问题6、B-问题6 | 四个角色由同一模型扮演时，分歧统计提供不了信息，拜占庭抑制也从不触发。现在明确标出这一点，并给出各角色的固定偏移（例如无效请求人系统性偏低）。不改聚合，也不压置信度，避免历史结果不可比 |
| 可选门禁 `background_prior_art_alignment`（PASS/WARN/FAIL） | A-问题5、B-问题2 | 背景技术如实补述不再通过 Q3 计正分，改由门禁表达：WARN 计入 conditional，FAIL 计入 blocking。由评审人判定后输入 |

**本版未实现的建议**：新增 I5/N4 指标、拆分 Q1、给 I 组设保守先验、按领域选择 action_queue 模板（A-问题1、A-问题2、B-问题3、B-问题8）。这些都会改变指数或指标集合，要等有历史结果可以校准时再做。

## 分数解释

- PatentARA高、AHP低：通常表示单篇全要素未覆盖且文本结构完整，但D1+D2组合启示、常规手段、真实效果或客体风险仍高。
- 改稿后PatentARA下降：若检索集改变，可能是更强近邻进入，不等于改稿变差；固定证据哈希后才可判断文本改造效果。
- PAA Gate 3词面警告：是支持映射复核队列，不自动等于26.3/26.4法律结论；仍须检查同义、上位化和实施例实质支持。
- 网页IPR“未检索到影响文件”：仅限该平台本次输入、候选池和报告流程；不能替代最终独权的API原文检索与组合启示审查。

## 验证

修改评分器后运行：

```powershell
python -m unittest discover -s paa/skills/patent-grant-scorer/tests -v
python ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py paa/skills/patent-grant-scorer
```
