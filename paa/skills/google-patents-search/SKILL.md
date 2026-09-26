---
name: google-patents-search
description: >
  免费专利检索与原文核验（无需 API key，**不使用浏览器自动化**）。用于发明专利研究过程中的
  查新（现有技术检索 / 候选对比文件发现）与验证（按公开号取权利要求与说明书原文、
  逐字引用核验、公开日资格判断）。后端：Google Patents 站点 JSON 接口（curl_cffi 指纹）、
  WIPO PATENTSCOPE 官方库（免 key 兜底，覆盖 CN）、Tavily 中继（站点被拦时取同一公开页全文／
  在 patents.google.com 域内检索）、Google 官方 BigQuery 专利数据集（含向量语义近邻）。
  另有 `gp_pipeline.py` 把"种子件引证轴／相似文献轴／语义轴／关键词轴"四路召回、
  取原文与核验接成一条流水线。
  当 incoPat 不可用、授权过期、额度耗尽，或需要做第二轮独立复检索时使用本 skill。
  TRIGGERS: google patents, Google Patents 检索, 免费专利检索, 查新, 现有技术检索,
  prior art, 对比文件, 新颖性检索, 创造性检索, 公开号核验, 权利要求原文, 说明书原文,
  专利溯源, PATENTSCOPE, patentscope, patents-public-data, BigQuery 专利,
  incoPat 不可用时的检索, 第二轮复检索, 种子件扩检, 引证扩检, 相似文献扩检, 语义检索,
  Tavily 中继, 中继取件, 流水线检索, gp_pipeline
---

# 免费专利检索与核验（纯 HTTP / API，无浏览器）

本 skill 解决三件事，**全部通过 HTTP 客户端完成，不驱动任何浏览器**：

1. **查新/检索**：找出候选对比文件（`gp_search.py`）；
2. **验证/核验**：把候选升级为**可引用的原文证据**，或明确判定"核验不通过"
   （`gp_fetch.py` + `gp_verify.py`）；
3. **种子件扩检（一条命令）**：以已知最接近文献为种子，四轴铺开候选池 → 取原文 → 出核验骨架
   （`gp_pipeline.py`，见 `references/seed-expansion-pipeline.md`）。

它是本仓红线（**不得编造公开号**、**不得用检索片段当已核验原文**）在免费渠道上的执行器。

## 先说清楚：Google Patents 到底有没有 API

**没有面向公众的免费 REST API。** `patents.google.com` 只有网站自己用的内部 JSON 接口；
Google 对非浏览器客户端的拦截很激进。2026-09-26 在同一台机器上实测：

| 通道 | 结果 |
| --- | --- |
| `requests` 直连 `/xhr/query` 与 `/patent/<PN>` | 503 "Sorry… automated queries" |
| `curl_cffi` 以 Chrome 124/131/136、Safari18 指纹重试 | 仍 503（拦截不是单纯 UA 问题） |
| 公共 CORS 代理转发 | 200，但内容是 Google 的 Sorry 页 |
| **WIPO PATENTSCOPE（官方库，免 key）** | ✅ 200，检索页 228KB、详情页 41KB，覆盖 CN |
| **Tavily 中继 `extract`（`extract_depth=advanced`）** | ✅ 200 且**正文完整**：摘要＋说明书＋权利要求逐项＋引证表＋相似文献表＋PDF 直链 |
| **Tavily 中继 `search`（限 `patents.google.com` 域）** | ✅ 200，中文可查 → 本机被 503 时的"Google 检索腿"替代 |
| **Google BigQuery `patents-public-data`** | ✅ 可达（401 只表示缺 GCP 凭据）——**这才是 Google 官方程序化入口** |
| `patentimages.storage.googleapis.com`（PDF 存储） | ✅ 200，可直接下 PDF（需带哈希的路径） |
| Espacenet / CNIPA 公告站 / patentguru | 403 / 202+JS 挑战 / 468 —— 均需反爬绕过，**本 skill 不做**，不纳入 |

所以本 skill 的做法是**多后端 + 如实上报**，而不是"必须靠浏览器"：

| backend | 说明 | 需要 key |
| --- | --- | --- |
| `google` | Google Patents 站点内部 JSON 接口（curl_cffi 指纹）。**不被拦的网络**上最直接 | 否 |
| `patentscope` | WIPO PATENTSCOPE 官方库，免 key，覆盖 CN；默认兜底 | 否 |
| `tavily` | **中继**：`extract` 取同一公开页全文（本机被 503 时仍可拿到权利要求与说明书）；`search` 在 `patents.google.com` 域内检索 | `TAVILY_API_KEY` |
| `bigquery` | Google 官方专利数据集（著录项/摘要/可得权利要求） | GCP 项目凭据 |

中继取的是公开页面、用的是有授权凭据的官方 API，不是绕 WAF 破解；但输出里**始终**保留
`relay` provenance（`gp_verify.py` 会给出 `provenance`/`warnings`，`--require-direct` 可拒收中继证据）。

**想"更深入"用 Google Patents，就得走 BigQuery**（Google 唯一的官方程序化入口）：
SQL 直查约 1 亿+ 公开文本、权利要求全文、CPC/日期/国别过滤，以及
`google_patents_research.publications.embedding_v1` 的**向量语义近邻检索**（incoPat 语义检索的免费等价物）。
开通方式（含**免信用卡的沙盒**）与成本控制见 `references/gcp_bigquery_setup.md`。

`--backend auto`（默认）先试 google；被拦则自动改走 patentscope，并在输出的 `attempts`
里记录两次尝试——**绝不把"被拦"写成"0 命中"**。
检索的 auto 链是 `google → patentscope → tavily`；取件的 auto 链是 `google → tavily → bigquery`
（`gp_fetch.py` 与 `gp_pipeline.py` 共用同一实现，`--no-relay` 可去掉中继那一段）。

`TAVILY_API_KEY`（中继腿用）的来源优先级：`--tavily-key` > 环境变量 > 当前目录（及上层）的
`.env` 中的键；输出只记来源位置（如 `dotenv:.env`），**不回显 key**。

## 何时使用

- incoPat 走不通时（账号授权过期 / 接口未授权 / 429 配额）——**检索与取件无需任何 key**
  （只有 `semantic` 轴要 GCP、中继腿要 `TAVILY_API_KEY`）；
- 已有一轮检索结论，需要**第二轮独立复检索**（换库、换检索轴）以降低单轮锚定偏置；
- 需要复核某公开号**到底公开了什么**（逐字引用 + 定位 + 取回时间 + sha256）；
- 需要按"申请日前公开"筛候选（`gp_verify.py --cutoff`）。

## 快速开始

```bash
P="D:/aicoding/mylib/paa/skills/google-patents-search/scripts"
export PYTHONIOENCODING=utf-8

# 0) 一次性依赖（无浏览器内核下载）
pip install -r D:/aicoding/mylib/paa/skills/google-patents-search/requirements.txt   # 只有 curl_cffi
#    可选：想走 Google 官方 BigQuery 通道时
#    pip install google-cloud-bigquery db-dtypes && gcloud auth application-default login

# 1) 检索（auto：google 被拦则自动走 patentscope）
python "$P/gp_search.py" --query 'graphene eye mask country=CN' \
  --out hits.json --audit audit.jsonl

# 1b) 明确指定后端
python "$P/gp_search.py" --query 'EN_ALLTXT:(石墨烯 眼罩) AND CTR:(CN)' --backend patentscope
python "$P/gp_search.py" --query '石墨烯 眼罩 country=CN' --backend google
python "$P/gp_search.py" --query '配电变压器 故障诊断' --backend tavily   # 中继检索腿（中文可用）

# 1c) 走 Google 官方数据集（需 GCP 凭据；先 probe 自检）
python "$P/gp_bigquery.py" probe
python "$P/gp_bigquery.py" lookup CN210644322U --out evidence/bq/CN210644322U.json
python "$P/gp_bigquery.py" search --keyword 石墨烯 --keyword 眼罩 --country CN --cpc A61F --max-gb 50
python "$P/gp_bigquery.py" similar CN210644322U --country China --limit 20 --max-gb 20   # 语义近邻

# 1d) 种子件扩检流水线：四轴召回 → 取原文 → 核验骨架（一条命令）
python "$P/gp_pipeline.py" --seed CN103399241B --country CN --cutoff 2026-09-25 \
  --fetch-top 8 --out runs/p06 --audit runs/p06/audit.jsonl --save-pdf
python "$P/gp_pipeline.py" --query '配电变压器 故障诊断' --out runs/x     # 没有种子也能跑
python "$P/gp_pipeline.py" --seed CN103399241B --no-relay --no-semantic   # 保守模式（不碰中继/ GCP）

# 2) 取候选原文（核验腿）
python "$P/gp_fetch.py" CN210644322U --backend google --out evidence/gp \
  --from-hits hits.json --save-html --audit audit.jsonl
python "$P/gp_fetch.py" --doc-id CN241725947 --backend patentscope --out evidence/ps   # doc_id 见 gp_search 输出
python "$P/gp_fetch.py" CN210644322U --backend bigquery --out evidence/bq              # 需 GCP 凭据
python "$P/gp_fetch.py" CN214180783U --backend tavily --save-pdf --out evidence/gp     # 中继取全文（被 503 时）

# 3) 核验门禁：只有全部 verified 才允许写进检索报告
python "$P/gp_verify.py" --citations citations.json --docs evidence/gp \
  --cutoff 2026-09-25 --strict-locator --out verify.json
echo "exit=$?"     # 0=全部通过；1=有未通过项（应阻断落稿）
python "$P/gp_verify.py" --citations citations.json --docs evidence/gp --require-direct
                   # 只承认直连证据；中继（relay）条目判为 relay_not_allowed

# 4) 离线复算（把上次保存的 HTML 拿来解析，可回归测试）
python "$P/gp_search.py" --html saved_result.html
python "$P/gp_fetch.py" CN210644322U --html saved_patent_page.html --out tmp/gp
```

## 输出契约（与仓内 `cnipa_epub_search.py` 一致）

- **stdout 仅一行**：`GP_HITS_JSON:` / `GP_DOC_JSON:` / `GP_VERIFY_JSON:` /
  `GP_BIGQUERY_JSON:` / `GP_PIPELINE_JSON:` + JSON（UTF-8，可含中文）；
- **stderr 只写 ASCII 诊断**：`GP_NOTE:` / `GP_HINT:` / `GP_BLOCKED:`（减轻 PowerShell 把中文 stderr 当错误流）；
- **退出码**：检索 `0` 有命中 / `3` 被拦 / `4` 无命中 / `2` 参数 / `5` 运行时；
  取件 `0` 有原文 / `3` 被拦 / `4` 只有元数据 / `2` / `5`；
  **核验 `0` 全部通过 / `1` 有未通过项（供流水线阻断）/ `2` 输入错误**；
  **流水线 `0` 有候选且有原文 / `4` 有候选无原文 / `3` 各轴被拦或不可用 / `2` / `5`**。

## 种子件扩检流水线（`gp_pipeline.py`）

已有"最接近的已知文献"时，不要在关键词上碰运气：以该件为种子，四条互相独立的轴同时铺开。

| axis | 来源 | 免 key？ |
| --- | --- | --- |
| `seed_citation` | 种子件页面的**引证表**（该件引用的在先公开） | 需能取到种子页（中继即可） |
| `seed_similar` | 种子件页面的**相似文献表** | 同上 |
| `semantic` | BigQuery `embedding_v1` **向量近邻**（incoPat 语义检索的免费等价物） | ❌ 需 GCP |
| `keyword` | `--query` 显式检索式，或由种子件题名自动派生 | ✅ |

产出（都在 `--out` 目录）：`screening.md`（轴覆盖/候选池/已取原文/限制）、`pipeline.json`、
`docs/<PN>.json|.md|.relay.md|.pdf`、`citations.draft.json`、`verify.json`。

两条使用纪律：

1. `score` 是**启发式排序分**（轴权重＋截止日资格＋题名词重合），只决定"先看哪件"，
   **不是相关性结论**；`--limit` 截断时会按轴保底（`--per-axis`，默认 3），避免整条轴被挤空；
2. `citations.draft.json` 里 `quote` = 权利要求 1 的逐字原文、`role` 留空、`auto=true`，
   只证明"已取到原文且可逐字定位"，**必须人工替换**成真正相关的片段与 X/Y/A 角色。

细节（含退出码、排序权重、派生检索式规则与实测数据）见 `references/seed-expansion-pipeline.md`。

## 工作流（融合 incoPat skill 的三步漏斗 + 本仓证据门禁）

**有两种入口**：① 只有技术主题 → 从第 1 步开始；② 已有最接近的已知文献 →
`gp_pipeline.py --seed <公开号>` 直接把 1–4 步跑完（引证轴/相似文献轴/语义轴/关键词轴），
再人工判读并替换引用骨架。

1. **粗召回**：写 3–6 组不同角度的检索式（主题词、手段词、效果词、分类号、申请人），逐组跑 `gp_search.py`，
   结果落盘并追加审计；结果项一律标 `snippet-degraded`。
2. **并集去重**：以 `pub_number` 为主键合并候选池——这一步只产生候选，不产生结论。
3. **精读取原文**：对 top 5–8 件跑 `gp_fetch.py`，拿到 `evidence_level=original-text` 的权利要求与说明书；
   可把 `<PN>.md` 交给 `patent-disclosure-skill/tools/patent_reader/extract_patent_text.py`
   拆成 claim_tree / raw_sections，用于逐特征比对表。
4. **核验与分类**：对每条拟引用写 `{pn, role, quote, locator}` 跑 `gp_verify.py`；
   只有 `verified` 的条目可进入报告，并按 `references/verification_protocol.md` 判 X/Y/A。
5. **落稿**：按 `templates/01_现有技术检索报告_template.md` 出报告，附限制声明、`attempts` 与审计文件路径。

## 常见坑

- **0 命中 ≠ 没有现有技术**：先看 `attempts` 判断是"被拦"还是"真的没搜到"，再按 `query_syntax.md` 放宽检索式；
- **`doc_not_on_google_patents` ≠ 被拦**：中继返回 `404 page not found` 表示该公开号在 Google Patents
  确无页面（常见于只收录在 PATENTSCOPE 的 CN 文献），应换 incoPat/CNIPA 或按 `docId` 查，
  **不得**写成"未公开"或"无现有技术"；
- **中继证据必须标注 provenance**：`relay=tavily_extract` 的条目要连 `retrieved_at`/`sha256`/同页 PDF
  一起记录；需要"只采直连证据"时用 `gp_verify.py --require-direct`；
- **裸中文检索式在 PATENTSCOPE 会被自动归一化**（包 `EN_ALLTXT:(…)`，必要时按最长词收窄重试），
  输出里的 `query_used` 才是最终生效的检索式，报告应据它书写；
- **摘要片段不能当证据**：`gp_verify.py` 会直接拒绝 `snippet-degraded` 条目，这是设计如此；
- **PATENTSCOPE 详情页只有著录项**：`evidence_level=metadata-only`，不能当对比文件原文；要权利要求全文请用 `google` 或 `bigquery` 后端；
- **公开号规范化**：`US:20230013787:A1` 与 `us20230013787a1` 都会规范为 `US20230013787A1`；
- **不要为取数引入浏览器自动化**：若各后端都不通，请在报告里如实记录受限并升级到有凭据的通道（中继/BigQuery/incoPat），
  而不是回退到浏览器操作（CNIPA 公告站的前置 JS 挑战同理：不做反爬绕过）。

## 与 incoPat 的分工

| 维度 | incoPat（本仓首选） | 本 skill |
| --- | --- | --- |
| 凭证 | 需要账号（测试账号授权 2026-08-31 已到期） | 检索/取件无需 key；语义轴要 GCP，中继腿要 Tavily |
| 语义检索 | 有（整段方案） | 有但需 GCP：`gp_pipeline` 的 `semantic` 轴（BigQuery `embedding_v1`） |
| 引证 / 相似文献扩检 | 有，需分次调用 | 有：种子件页面的引证表与相似文献表自动并入候选池 |
| 法律状态 / 价值度 | 有 | 无（本 skill 不抓法律状态） |
| 定位 | 法定检索、范围与法律状态 | 免费候选发现 + **原文核验** + 第二轮独立复检索 |

两者都可用时：incoPat 定范围，本 skill 做第二轴复检索与逐字核验，按公开号取并集后统一走 `gp_verify.py`。

## 边界（必须如实写进报告）

本 skill **不是法定检索**；`patentscope` 通道覆盖以著录项为主；Google 站点通道可用与否取决于出口网络；
本 skill **不判断**抵触申请、不做法律状态结论、不代替代理师的检索报告。
所有"未发现"只能表述为"本轮检索未发现"。

### 分通道可信度实测（2026-09-26，P06-4/P06-5 案两轮真实使用）

不要笼统相信"本 skill 可用"——同一次会话里各通道表现差异很大，按实测结果分级：

- **确认可用，可当 incoPat 原文核验的免费等价物**：按公开号取著录项+权利要求原文
  （`google` 直连、`gp_bigquery.py lookup`）。8/8 与 6/8 真实核验通过，内容与已知事实吻合。
- **确认可用，但曾经是坏的、当天现修**：`gp_bigquery.py similar`（语义近邻，`embedding_v1`）。
  修复前 `lookup`/`similar` 因 `publication_number` 未转换成数据集实际存储格式
  （`CN-117291184-A` 而非 `CN117291184A`）恒 `not_found`，且 `similar` 在候选与种子向量维度
  不一致时 `cosine_distance` 直接报错——已在 `gp_backends.py` 修复（`_bq_pub_number()` 转换 +
  `ARRAY_LENGTH` 一致性过滤），修复前的版本**不能用**。若后续在别的环境/别的表结构上复现
  `not_found` 或 `Array inputs are not equal in length`，先怀疑格式/维度问题，不要当"确无数据"。
- **实测不可信，未修复**：`patentscope` 后端的关键词全文检索（`gp_search.py --backend patentscope`
  与 `gp_pipeline.py` 的 `keyword` 轴）。同一天对两个不同技术领域各测 3 组查询式，多数返回的候选与
  检索词毫无关联（工具自算的 `term_overlap` 为 0），只有 SKILL.md 自带的示例查询表现正常——**不要
  拿这条通道的"命中"当相关性结论**，用之前先用已知应该命中的查询词复测一次，确认当前网络/索引状态
  正常。根因未查明，可能是 PATENTSCOPE 侧对中文语料的排序退化，也可能是本地网络出口问题。
- **未查明、别默认为"真空"**：种子件的 `seed_citation`/`seed_similar` 轴（`google` 后端页面抓取）。
  对两个真实种子公开号都返回 0 条，不确定是页面本身确无引证/相似文献表，还是这条抓取路径本身有
  未发现的 bug——如遇到这个情况，报告里只能写"本轮未取到"，不能写"该件无引证关系"。
- **明确不支持**：法律状态（是否有效/同族/价值度）——这是设计上的边界，不是待修的 bug。

中继（`tavily`）通道取回的是同一公开页面，但经过第三方转换：报告必须写明 `relay` provenance，
关键引用建议加 `--save-pdf` 留 PDF 字节证据；`gp_pipeline.py` 的 `score` 只是排序分，
`citations.draft.json` 只是核验骨架，二者都不是检索或比对结论。
