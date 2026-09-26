# 对比文件核验协议（本 skill 的红线执行标准）

## 0. 三条不可越过的红线

1. **不得编造公开号**——写进报告与申请文件的每一个公开号都必须来自真实取数（本 skill 的 `pub_number` 字段）；
2. **不得用检索片段当已核验原文**——结果页的标题/摘要片段一律标为 `snippet-degraded`，
   只有 `gp_fetch.py` 取回并落盘的 `evidence_level=original-text` 才能作为对比文件原文；
3. **不得把"未通过核验"写成"未发现现有技术"**——被反爬拦截、超时、0 命中都必须如实记录为
   `blocked` / `empty` / `error`，不得推断成"无在先技术"。

## 1. 证据分级

| 级别 | 来源 | 能支撑什么 | 不能支撑什么 |
| --- | --- | --- | --- |
| `snippet-degraded` | `gp_search.py` 结果页 | 候选发现、检索策略记录 | 任何区别特征比对结论 |
| `metadata-only` | 说明书页只取到著录项 | 公开号/日期/申请人核对 | 权利要求或说明书内容比对 |
| `original-text` | `gp_fetch.py` 取到权利要求/说明书 | X/Y/A 分类、特征比对、逐字引用 | —— |

### 2.1 取数 provenance（直连 vs 中继）

同样是 `original-text`，**取数路径不同，证据强度不同**，必须在记录里区分：

| provenance | 含义 | 记录字段 | 使用口径 |
| --- | --- | --- | --- |
| `direct` | 直连页面/官方数据集取回（`google` / `bigquery` 后端） | `provenance="direct"` | 可直接引用 |
| `relay` | 经第三方 API（`tavily` 中继）取回同一公开页面后转 Markdown | `provenance="relay"`、`relay="tavily_extract"` | **默认允许引用，但必须标注中继来源**；`gp_verify.py` 会写 `warnings[]` |

操作要求：

1. `gp_fetch.py` 对中继取件**始终落盘** `<PN>.relay.md`（sha256 的实际计算对象），报告里应同时给
   Google Patents URL 与 `retrieved_at`；
2. 对要写进申请文件/检索报告的关键引用，建议加 `--save-pdf` 同步下载同页 PDF，
   记录 `pdf_sha256` 做字节级留痕（PDF 直链来自中继页面，存储在 `patentimages`，本机实测可直下）；
3. 若受理方要求"只采直连证据"，用 `gp_verify.py --require-direct`：中继条目会被判
   `relay_not_allowed`（退出码 1，阻断落稿），此时需解决出口网络或改用 BigQuery。

## 2. 每件对比文件的最小证据集

一份可引用的对比文件记录**必须**齐备：

1. `pub_number`（规范化公开号）与 `title`；
2. `url`（可复核的 Google Patents 链接）与 `retrieved_at`（取回时间）；
3. `sha256`（`gp_fetch.py` 对"标题+摘要+权利要求+说明书"规范文本计算的摘要）；
4. **逐字引用片段** + `locator`（`claims/3`、`description`、`abstract`）；
5. `publication_date`（公开日），以及与本案申请日的先后关系判断。

`gp_verify.py` 就是这条最小证据集的自动检查器；它返回 `status=verified` 才算通过。
每条记录都会带 `provenance`（`direct`/`relay`）、`doc_url`、`retrieved_at`、`sha256`，
中继条目另带 `relay` 与 `warnings[]`。

## 3. 三选一分类（X / Y / A）判定口径

- **X 类（单独影响新颖性/创造性）**：该件的**单篇**公开内容覆盖独权的全部技术特征。
  要求：对独权逐特征列出"特征 → 该件原文引用 + locator"的对照表，任一特征找不到逐字支持即**不能判 X**。
- **Y 类（与另一篇结合影响创造性）**：该件公开了独权的主要特征，但存在区别特征；
  必须同时给出"另一篇公开了该区别特征"的证据，以及**结合启示**（为什么本领域技术人员会想到结合）。
  缺少结合启示时只能写成"A 类/一般背景文献"。
- **A 类（背景技术）**：反映本领域一般水平，可用于写背景技术，不单独否定新颖性/创造性。

不要把"主题相同"当作"技术方案相同"；也不要用"领域不同"直接论证创造性。

## 4. 时间资格

- 现有技术资格看**公开日**是否早于本案**申请日**（有优先权则看优先权日）；
- 本 skill 的 `--cutoff` 参数用于这一判断：`gp_verify.py --cutoff <申请日前一天>` 会把
  `date_after_cutoff` 记为未通过；
- 公开日晚于申请日但在申请日后公开的、且由他人先申请的同样发明，属于**抵触申请**范畴，
  不是现有技术；本 skill 不做抵触申请判断（需要真实申请日与在先申请数据）。

## 5. 报告写法（与本仓既有格式一致）

每件对比文件一段，固定字段：

```
### [X-1] CN103399241B — <标题>
- 申请人 / 公开日：<assignee> / <publication_date>
- 来源与核验：Google Patents <url>（取回 <retrieved_at>，sha256 <前12位>…）
- 相关公开内容（逐字）："<quote>"（定位：<locator>）
- 与本案独权的对应：<特征对照>
- 分类：X（单独影响）／Y（与 [Y-2] 结合）／A（背景）
```

核验未通过但仍有参考价值的，放在"未通过核验的候选"小节，并写明未通过原因
（`doc_missing` / `quote_not_found` / `locator_mismatch` / `date_after_cutoff` /
`relay_not_allowed`）。

## 6. 流水线产物的用法（`gp_pipeline.py`）

`gp_pipeline.py` 输出的 `candidates`/`fetched`/`verify` 与 `screening.md` **只是筛查台**：

- `score`/`score_parts` 是启发式排序分（轴权重＋截止日资格＋题名词重合），**不是相关性或相似度结论**；
- `citations.draft.json` 里的 `quote` 是**权利要求 1 的逐字原文**，`role` 留空、`auto=true`；
  它只证明"已取到原文且可逐字定位"，**必须人工替换**为真正相关的片段与 X/Y/A 角色后再跑 `gp_verify.py`；
- 报告里的"未通过核验的候选"与 `limitations[]` 要原样带进最终检索报告的限制说明。
