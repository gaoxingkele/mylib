---
name: google-patents-search
description: >
  免费专利检索与原文核验（无需 API key，**不使用浏览器自动化**）。用于发明专利研究过程中的
  查新（现有技术检索 / 候选对比文件发现）与验证（按公开号取权利要求与说明书原文、
  逐字引用核验、公开日资格判断）。后端：Google Patents 站点 JSON 接口（curl_cffi 指纹）、
  WIPO PATENTSCOPE 官方库（免 key 兜底，覆盖 CN）、Google 官方 BigQuery 专利数据集。
  当 incoPat 不可用、授权过期、额度耗尽，或需要做第二轮独立复检索时使用本 skill。
  TRIGGERS: google patents, Google Patents 检索, 免费专利检索, 查新, 现有技术检索,
  prior art, 对比文件, 新颖性检索, 创造性检索, 公开号核验, 权利要求原文, 说明书原文,
  专利溯源, PATENTSCOPE, patentscope, patents-public-data, BigQuery 专利,
  incoPat 不可用时的检索, 第二轮复检索
---

# 免费专利检索与核验（纯 HTTP / API，无浏览器）

本 skill 解决两件事，**全部通过 HTTP 客户端完成，不驱动任何浏览器**：

1. **查新/检索**：找出候选对比文件（`gp_search.py`）；
2. **验证/核验**：把候选升级为**可引用的原文证据**，或明确判定"核验不通过"
   （`gp_fetch.py` + `gp_verify.py`）。

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
| **Google BigQuery `patents-public-data`** | ✅ 可达（401 只表示缺 GCP 凭据）——**这才是 Google 官方程序化入口** |
| `patentimages.storage.googleapis.com`（PDF 存储） | ✅ 200，可直接下 PDF（需带哈希的路径） |

所以本 skill 的做法是**多后端 + 如实上报**，而不是"必须靠浏览器"：

| backend | 说明 | 需要 key |
| --- | --- | --- |
| `google` | Google Patents 站点内部 JSON 接口（curl_cffi 指纹）。**不被拦的网络**上最直接 | 否 |
| `patentscope` | WIPO PATENTSCOPE 官方库，免 key，覆盖 CN；默认兜底 | 否 |
| `bigquery` | Google 官方专利数据集（著录项/摘要/可得权利要求） | GCP 项目凭据 |

**想"更深入"用 Google Patents，就得走 BigQuery**（Google 唯一的官方程序化入口）：
SQL 直查约 1 亿+ 公开文本、权利要求全文、CPC/日期/国别过滤，以及
`google_patents_research.publications.embedding_v1` 的**向量语义近邻检索**（incoPat 语义检索的免费等价物）。
开通方式（含**免信用卡的沙盒**）与成本控制见 `references/gcp_bigquery_setup.md`。

`--backend auto`（默认）先试 google；被拦则自动改走 patentscope，并在输出的 `attempts`
里记录两次尝试——**绝不把"被拦"写成"0 命中"**。

## 何时使用

- incoPat 走不通时（账号授权过期 / 接口未授权 / 429 配额）——本 skill **无需任何 key**；
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

# 1c) 走 Google 官方数据集（需 GCP 凭据；先 probe 自检）
python "$P/gp_bigquery.py" probe
python "$P/gp_bigquery.py" lookup CN210644322U --out evidence/bq/CN210644322U.json
python "$P/gp_bigquery.py" search --keyword 石墨烯 --keyword 眼罩 --country CN --cpc A61F --max-gb 50
python "$P/gp_bigquery.py" similar CN210644322U --country China --limit 20 --max-gb 20   # 语义近邻

# 2) 取候选原文（核验腿）
python "$P/gp_fetch.py" CN210644322U --backend google --out evidence/gp \
  --from-hits hits.json --save-html --audit audit.jsonl
python "$P/gp_fetch.py" --doc-id CN241725947 --backend patentscope --out evidence/ps   # doc_id 见 gp_search 输出
python "$P/gp_fetch.py" CN210644322U --backend bigquery --out evidence/bq              # 需 GCP 凭据

# 3) 核验门禁：只有全部 verified 才允许写进检索报告
python "$P/gp_verify.py" --citations citations.json --docs evidence/gp \
  --cutoff 2026-09-25 --strict-locator --out verify.json
echo "exit=$?"     # 0=全部通过；1=有未通过项（应阻断落稿）

# 4) 离线复算（把上次保存的 HTML 拿来解析，可回归测试）
python "$P/gp_search.py" --html saved_result.html
python "$P/gp_fetch.py" CN210644322U --html saved_patent_page.html --out tmp/gp
```

## 输出契约（与仓内 `cnipa_epub_search.py` 一致）

- **stdout 仅一行**：`GP_HITS_JSON:` / `GP_DOC_JSON:` / `GP_VERIFY_JSON:` + JSON（UTF-8，可含中文）；
- **stderr 只写 ASCII 诊断**：`GP_NOTE:` / `GP_HINT:` / `GP_BLOCKED:`（减轻 PowerShell 把中文 stderr 当错误流）；
- **退出码**：检索 `0` 有命中 / `3` 被拦 / `4` 无命中 / `2` 参数 / `5` 运行时；
  取件 `0` 有原文 / `3` 被拦 / `4` 只有元数据 / `2` / `5`；
  **核验 `0` 全部通过 / `1` 有未通过项（供流水线阻断）/ `2` 输入错误**。

## 工作流（融合 incoPat skill 的三步漏斗 + 本仓证据门禁）

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
- **摘要片段不能当证据**：`gp_verify.py` 会直接拒绝 `snippet-degraded` 条目，这是设计如此；
- **PATENTSCOPE 详情页只有著录项**：`evidence_level=metadata-only`，不能当对比文件原文；要权利要求全文请用 `google` 或 `bigquery` 后端；
- **公开号规范化**：`US:20230013787:A1` 与 `us20230013787a1` 都会规范为 `US20230013787A1`；
- **不要为取数引入浏览器自动化**：若两条后端都不通，请在报告里如实记录受限并升级到有凭据的通道（BigQuery/incoPat），
  而不是回退到浏览器操作。

## 与 incoPat 的分工

| 维度 | incoPat（本仓首选） | 本 skill |
| --- | --- | --- |
| 凭证 | 需要账号（测试账号授权 2026-08-31 已到期） | 无需 key |
| 语义检索 / 法律状态 / 价值度 | 有 | 无（本 skill 不抓法律状态） |
| 定位 | 法定检索、范围与法律状态 | 免费候选发现 + **原文核验** + 第二轮独立复检索 |

两者都可用时：incoPat 定范围，本 skill 做第二轴复检索与逐字核验，按公开号取并集后统一走 `gp_verify.py`。

## 边界（必须如实写进报告）

本 skill **不是法定检索**；`patentscope` 通道覆盖以著录项为主；Google 站点通道可用与否取决于出口网络；
本 skill **不判断**抵触申请、不做法律状态结论、不代替代理师的检索报告。
所有"未发现"只能表述为"本轮检索未发现"。
