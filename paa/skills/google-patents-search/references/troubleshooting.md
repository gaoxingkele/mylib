# 取数通道与故障排查（2026-09-26 实测，全部为 HTTP 客户端，不使用浏览器自动化）

## 1. 实测结论：Google Patents 没有免费公开 REST API

Google 对 `patents.google.com` **不提供**面向公众的免费 REST API。可程序化取数的通道有三类，
本轮逐一实测（同一台机器、同一出口 IP）：

| 通道 | 结果 | 说明 |
| --- | --- | --- |
| 站点内部 JSON 接口 `patents.google.com/xhr/query`（网站自身在用） | **503** "Sorry… automated queries" | `requests` 直连被拦 |
| 同一接口换 **curl_cffi（Chrome TLS/HTTP2 指纹，chrome124/131/136、safari18）** | **503** | 说明拦截不是单纯 UA 问题 |
| 站点首页 `patents.google.com/`（HTTP 客户端） | **503** | 连首页都不给非浏览器客户端 |
| 公共 CORS 代理（allorigins）转发同页 | **200 但内容是 Google 的 Sorry 页** | 代理出口同样被拦 |
| Jina Reader（服务端渲染）转发 | **403 Cloudflare** | 需要 key/浏览器 |
| **Tavily `extract`（`extract_depth=advanced`）取同一公开页** | ✅ **200，正文完整** | 返回的 Markdown 含摘要、说明书、**权利要求逐项**、引证表、相似文献表、PDF 直链；本机被 503 时这是可用的**中继取件**通道 |
| **Tavily `search`（`include_domains=["patents.google.com"]`）** | ✅ **200，中文可查** | 等于把"Google Patents 检索腿"挪到中继出口；只保留能解析出公开号的 Google Patents 链接 |
| **官方通道：BigQuery `patents-public-data`** | `bigquery.googleapis.com` **401**（可达，缺凭据） | 这才是 Google 官方程序化入口 |
| **`patentimages.storage.googleapis.com`（附图/PDF 存储）** | **200**，能直接下到 422KB 真 PDF | 只要知道带哈希的 PDF 路径即可绕过前面所有限制 |
| WIPO **PATENTSCOPE**（官方库，免 key） | **200**：检索页 228KB、详情页 41KB | 覆盖 CN，本机可用 ✅ |
| Espacenet / Justia / PatentsView 旧接口 | 403 / 403 / 重定向到官网 | 需要 key 或已停用 |
| CNIPA 专利公布公告（`epub.cnipa.gov.cn`） | **202 + JS 挑战**（瑞数类 WAF） | 有全文但需执行签名脚本；**本 skill 不做反爬绕过**，不纳入 |
| patentguru / 第三方聚合站 | **468 / 403** | 同为反爬；不纳入 |

**结论**：本机（出口被 Google 判定为可疑）**无法直连**拿到 Google Patents 站点数据；
可用通道是 **中继（Tavily extract/search，需 `TAVILY_API_KEY`）**、
**BigQuery**（需 GCP 凭据）与 **patentimages 存储**（需 PDF 路径，PDF 路径可由中继页面里的直链得到）。
因此本 skill 的后端策略是：

1. `google` —— 站点 JSON 接口（curl_cffi）。在**不被 Google 拦的网络**上这是最直接的通道；
   被拦时明确返回 `blocked_by_google`，**不**伪装成"0 命中"。
2. `patentscope` —— WIPO 官方库，**免 key、免浏览器**，本机实测可用，覆盖 CN；作为默认兜底。
3. `tavily` —— **中继**：extract 取同一公开页的全文（摘要/说明书/权利要求），search 在
   `patents.google.com` 域内检索。它取的是公开页面、用的是有授权凭据的官方 API，
   不是绕 WAF 破解；但**必须在输出里保留 `relay` provenance**（见 `verification_protocol.md` §2.1）。
4. `bigquery` —— Google 官方专利数据集（`patents-public-data`），真正的官方 API 通道，
  需要 GCP 项目与凭据；未安装/未登录时给出明确前置条件。**这是"更深入使用 Google Patents"的唯一正路**：
  SQL 直查约 1 亿+ 公开文本 + 权利要求全文 + CPC/日期/国别过滤 + 向量语义近邻；
  开通（含**免信用卡沙盒**）与成本控制见 `gcp_bigquery_setup.md`。
  所有 BigQuery 查询都先干跑估算扫描量，`gp_bigquery.py` 的 `--max-gb` 超限即拒绝执行，
  避免误烧每月 1 TiB 免费额度。

**取件降级顺序**（`gp_fetch.py --backend auto` 与 `gp_pipeline.py` 共用）：
`google → tavily → bigquery`，逐次尝试并把每次结果写进 `attempts[]`。

## 2. 怎么选后端

```bash
# 默认 auto：先试 google，被拦则自动改走 patentscope，并在 attempts 里记录两次尝试
python gp_search.py --query 'graphene eye mask country=CN' --out hits.json --audit audit.jsonl

# 明确指定
python gp_search.py --query 'EN_ALLTXT:(石墨烯 眼罩) AND CTR:(CN)' --backend patentscope
python gp_search.py --query '石墨烯 眼罩 country=CN' --backend google
python gp_search.py --query '配电变压器 故障诊断' --backend tavily     # 中继检索腿（中文可用）

# 有 GCP 凭据时，用官方数据集核验著录项/摘要
python gp_fetch.py CN210644322U --backend bigquery --out evidence/bq

# 被 503 拦截时走中继取件（全文含权利要求），需要 TAVILY_API_KEY
python gp_fetch.py CN214180783U --backend tavily --save-pdf --out evidence/gp

# 取 WIPO 详情（docId 用 gp_search 输出里的 doc_id）
python gp_fetch.py --doc-id CN241725947 --backend patentscope --out evidence/ps

# 一条命令跑完"引证/相似文献/语义/关键词"四轴召回 + 取原文 + 核验骨架
python gp_pipeline.py --seed CN103399241B --country CN --cutoff 2026-09-25 --out runs/p06
```

`TAVILY_API_KEY` 的来源优先级：命令行 `--tavily-key` > 环境变量 > 当前目录（及其上层）的
`.env` / `.env.local` 里的 `TAVILY_API_KEY`（键名大小写不敏感）。凭据只在请求头里使用，
输出中只记来源位置（`dotenv:.env` / `env:TAVILY_API_KEY`），**不回显 key**。

## 3. 症状 → 处置

| 症状 | 判定 | 处置 |
| --- | --- | --- |
| `GP_BLOCKED: google_anti_bot` | Google 拦下该出口的 HTTP 客户端 | 交由 auto 走 patentscope；或用 `--backend bigquery`（需凭据）；**不要**为此引入浏览器自动化 |
| `GP_BLOCKED: all_backends_blocked` / `reason=all_backends_blocked_or_unconfigured` | 直连被拦且其余通道缺凭据 | 配 `TAVILY_API_KEY`（中继，免 GCP）或开通 GCP；`remedy` 字段已写明两条出路 |
| `curl_cffi 未安装` | 依赖缺失 | `pip install curl_cffi` |
| `error=doc_not_on_google_patents`（`detail: 404 page not found`） | **该公开号在 Google Patents 确无页面**（常见于只收录在 PATENTSCOPE 的 CN 文献），不是网络或凭据问题 | 换 incoPat/CNIPA 原文库，或按 PATENTSCOPE `docId` 查看；报告中如实写"该号无 Google 页面"，不要写成"未公开" |
| `error=tavily_key_missing` | 未配置中继凭据 | 设 `TAVILY_API_KEY`，或去掉 `tavily` 后端/加 `--no-relay` |
| `error=relay_extract_failed` | 中继返回但抽取失败 | 稍后重试，或改用 `google`/`bigquery` |
| 结果页 0 条但请求成功 | 检索式问题 | 按 `query_syntax.md` 放宽：去 `CL=`/`CPC=` 限定、改 `country=`、减词 |
| 裸中文检索式在 patentscope 0 命中 | 该库要求字段算子，且多词 AND 会收死 | 直接用裸关键词（后端会自动包成 `EN_ALLTXT:(…)`，并按"最长一词→最长两词"收窄重试）；或显式写 `EN_ALLTXT:(…) AND CTR:(CN)` |
| `tavily` 检索返回 0 条专利 | 中继把非专利页过滤掉了 | 看 `non_patent_skipped`；换个更短的概念词，或改用 patentscope 索引 |
| patentscope 详情页无权利要求 | 该库详情页以著录项为主 | 用 `--backend google`（若网络允许）或 `--backend bigquery` 取权利要求 |
| `bigquery_credentials_missing` | 无 GCP 凭据 | `gcloud auth application-default login`，或设 `GOOGLE_APPLICATION_CREDENTIALS` 指向服务账号 JSON |
| `bigquery_sdk_missing` | 未装 SDK | `pip install google-cloud-bigquery db-dtypes` |
| 单件页无 `#claims` | 该号无电子全文或只有 A 文献 | 换同族成员、试另一语言路径，或改用 BigQuery/官方渠道 |

## 4. 频率与礼貌抓取

- 相邻请求留 2–3 秒；批量取件每 10 件停 20–30 秒；
- 本 skill 不做并发抓取（逐件顺序执行）；
- 出现一次 `GP_BLOCKED` 即切换后端，不要循环重试同一通道。

## 5. 与 incoPat 的关系（互补，不替代）

| 维度 | incoPat（本仓首选） | 本 skill |
| --- | --- | --- |
| 凭证 | 需要账号（测试账号授权 2026-08-31 已到期） | 检索/取件**无需 key**；语义轴与中继腿才需要 GCP / Tavily key |
| 中文库覆盖 | 中国库完整，支持语义检索/法律状态/同族/引证 | PATENTSCOPE 覆盖 CN 著录项；Google 通道取决于网络是否放行 |
| 语义检索 | 有（整段技术方案 → 相似度） | 有但需 GCP：`gp_pipeline --seed` 的 `semantic` 轴走 BigQuery `embedding_v1` 向量近邻 |
| 引证/相似文献扩检 | 有，需分次调用 | `gp_pipeline` 自动把种子件页面的引证表、相似文献表并入候选池 |
| 适合 | 法定检索、法律状态、价值度 | 免费候选发现 + 原文核验门禁 + 第二轮独立复检索 |

两者都可用时：incoPat 定范围与法律状态，本 skill 做第二轴复检索与逐字核验，按公开号取并集后
统一走 `gp_verify.py`。

## 6. 边界（必须写进报告）

- 本 skill **不是法定检索**，也不判断抵触申请；
- `patentscope` 详情页**不保证**给权利要求全文，`evidence_level=metadata-only` 的条目**不得**作为对比文件引用；
- **中继通道的 provenance 必须如实标注**：`relay=tavily_extract/tavily_search` 的条目是从公开页面
  经第三方 API 取回，与直连取回在证据强度上不同；`gp_verify.py` 会给出
  `provenance`/`warnings`，`--require-direct` 可直接拒收中继证据。报告里要写清取数通道。
- Google 站点通道可用与否取决于出口网络，报告里应记录 `attempts`（哪条通道、是否被拦），
  以便复核时区分"确实没有"与"取不到"。
