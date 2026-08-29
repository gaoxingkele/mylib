---
name: patent-grant-scorer
description: >
  对中国发明专利交底书或申请文件进行证据约束的多专家可专利性评审与授权风险排序。
  结合incoPat检索原文、CNIPA硬门禁、PatentARA结构分、AHP/SEM风险分，处理专家分歧、
  拜占庭异常评分、跨轮版本漂移和同批案件相对公平。适用于授权成功率、专利评分、
  可专利性评估、低分改进、多专家仲裁、改稿前后复评；不用于把单一分数解释为授权保证。
metadata:
  version: "2.0.0"
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
- **双分数并存。** PatentARA或形式/支持图谱反映结构成熟度；AHP/SEM计入组合启示、工程事实、真实效果和客体风险。二者不同不是错误，必须解释差异来源。
- **分歧按证据仲裁。** 不因某评分偏离多数就删除；先比较证据质量、原文核验、日期资格和推理链。高质量少数意见必须保留并触发定向复核。
- **禁止为了提分编造机制。** 新增状态、CAS、哈希、锁、凭证、父链、阈值或实验数据必须有申请日前材料；否则标记`needs-confirmation`并阻断正式写入。
- **输出只到人工复核。** 高分最多表示“进入代理师复核”；不得输出“保证授权”或“建议直接提交”。

完整证据等级、检索纪律、创造性攻击和整改规则见
[references/evidence-review-protocol.md](references/evidence-review-protocol.md)。

## 标准工作流

### 1. 冻结本轮状态

记录：

- `claim_hash`：本轮被评独权文本哈希；
- `search_claim_hash`：检索输入绑定的独权哈希；
- `evidence_hash`：已核验对比文件及摘录集合哈希；
- 申请日或优先权日、检索日期、检索接口与错误日志；
- PatentARA/PAA/CNIPA门禁使用的申请文件版本。

任一哈希不一致，输出`STALE_REVIEW_RESEARCH_REQUIRED`，不要继续比较分数。

### 2. 建立检索证据

调用`incopat-search`：

1. 最终独权执行至少一次语义检索；
2. 执行1—2组可审计布尔检索；
3. 对2—4件高相关文献调用`info`和`claim`，必要时调用`spec`；
4. 记录申请日/公开日资格、最接近文件D1、第二文件D2及可能组合动机；
5. 网页IPR报告只作为独立证据层，保留项目状态、候选数、报告数和失败原因。

### 3. 独立专家评审

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

### 4. 仲裁而非简单平均

运行评分器：

```powershell
python paa/skills/patent-grant-scorer/scripts/ahp_sem_scorer.py input.json -o review.json
```

默认`robust`模式以中位数抵抗异常值，以证据加权均值保留高质量少数意见；四专家最多抑制一个低证据异常评分，但不删除原始意见。分差大、MAD高、高质量少数意见或疑似异常数超过容错上限时，输出`review_required`并要求定向补证据。

需要复算历史口径时可显式使用：

```powershell
python paa/skills/patent-grant-scorer/scripts/ahp_sem_scorer.py input.json --aggregation legacy-mean
```

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
- `score_layers.risk_adjusted_patentability`；
- `score_layers.evidence_confidence`与非统计意义的不确定区间；
- 每指标专家原分、可靠性、MAD、抑制项和高质量少数意见；
- `version_binding`和`round_transition`；
- 当前同批案件的相对百分位；
- 按P0/P1/P2排列的`action_queue`。

完整JSON格式和示例见[references/input-output-schema.md](references/input-output-schema.md)。

## 分数解释

- PatentARA高、AHP/SEM低：通常表示单篇全要素未覆盖且文本结构完整，但D1+D2组合启示、常规手段、真实效果或客体风险仍高。
- 改稿后PatentARA下降：若检索集改变，可能是更强近邻进入，不等于改稿变差；固定证据哈希后才可判断文本改造效果。
- PAA Gate 3词面警告：是支持映射复核队列，不自动等于26.3/26.4法律结论；仍须检查同义、上位化和实施例实质支持。
- 网页IPR“未检索到影响文件”：仅限该平台本次输入、候选池和报告流程；不能替代最终独权的API原文检索与组合启示审查。

## 验证

修改评分器后运行：

```powershell
python -m unittest discover -s paa/skills/patent-grant-scorer/tests -v
python C:/Users/10175/.codex/skills/.system/skill-creator/scripts/quick_validate.py paa/skills/patent-grant-scorer
```
