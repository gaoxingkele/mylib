# 申请 GCP 并用 BigQuery 深入使用 Google Patents

本文件回答两个问题：**怎么开通 GCP**、**开通后能比网页多做什么**。
事实依据：Google Cloud 官方文档（Free Trial / Free Tier / BigQuery sandbox，2026-09-26 抓取）
与官方示例仓库 `google/patents-public-data`（表名与字段来自其示例 SQL）。

## 1. 三条入门路径（先选一条）

| 路径 | 费用 | 要不要信用卡/账单账户 | 关键限制 |
| --- | --- | --- | --- |
| **BigQuery 沙盒**（最省事） | 免费 | **不需要**（官方原话：without providing a credit card or creating a billing account） | 每月 1 TiB 查询量；**你创建的表/视图/分区 60 天后自动过期**；不支持流式写入、DML、Data Transfer Service |
| **Google Cloud Free Trial** | 90 天内 $300 赠金 | **需要**信用卡或其它支付方式（用于身份验证与反欺诈） | 赠金用尽或 90 天到期后需升级为付费；同时享有 Free Tier |
| **Free Tier（长期免费额度）** | 每月免费额度 | 需要账单账户 | BigQuery：**每月 1 TiB 查询 + 10 GiB 存储** |

**建议**：只为查新/核验用，走**沙盒**就够，而且不必绑卡。注意沙盒里不要建自己的大表（会 60 天过期），
查询公共数据集不受这个过期限制。

## 2. 开通步骤

### 路径 A：BigQuery 沙盒（免卡）

1. 用 Google 账号登录 <https://console.cloud.google.com/bigquery>；
2. 首次进入时若提示"沙盒模式（Sandbox）"，直接继续——**不创建账单账户**；
3. 在查询编辑器里直接跑下面第 3 节的 SQL（公共数据集免授权即可读）。

### 路径 B：Free Trial（要卡）

1. 打开 <https://console.cloud.google.com/freetrial> 申请，填国家/地区与支付方式；
2. 创建项目（记下 **项目 ID**）；
3. 本地安装 gcloud 并登录：

```bash
# Windows: 下载 Google Cloud CLI 安装包；或用 winget
winget install --id Google.CloudSDK
gcloud auth login
gcloud auth application-default login     # 让 Python SDK 用你的身份
gcloud config set project <你的项目ID>
```

4. 装 Python SDK：

```bash
pip install google-cloud-bigquery db-dtypes
```

5. 自检：

```bash
python scripts/gp_bigquery.py probe
# 期望：{"installed": true, "credentials": "ok", "project": "<你的项目ID>"}
```

> 服务账号方式（无人值守/CI）：建服务账号 → 授予 BigQuery Job User + BigQuery Data Viewer →
> 下载 JSON → 设 `GOOGLE_APPLICATION_CREDENTIALS=<路径>`。

## 3. 数据集能给你什么（这是"更深入"的实质）

Google 把专利数据放在 BigQuery 公共数据集里，两个关键表（**字段依据官方示例 SQL 核实**）：

### `patents-public-data.patents.publications`（主表）

| 字段 | 用途 |
| --- | --- |
| `publication_number` | 公开号（如 `CN210644322U`），可与我们报告里的编号直接对上 |
| `country_code` | 国别过滤（`CN`/`US`…） |
| `title_localized` / `abstract_localized` | 标题与摘要（按语言数组） |
| **`claims_localized`** | **权利要求全文**（REPEATED RECORD，含 `language`、`text`） |
| `cpc`（REPEATED RECORD） | CPC 分类号数组，可按前缀过滤 |
| `priority_date` / `publication_date` | 申请优先权日 / 公开日（`yyyymmdd` 整数，便于区间比较） |
| `assignee` / `inventor` | 申请人 / 发明人 |
| `citation` 等 | 引证关系（用于引证网与 FTO 线索） |

官方示例（可直接跑）：

```sql
SELECT publication_number, priority_yr, cpc4, claims.text
FROM `patents-public-data.patents.publications` AS pubs,
     UNNEST(claims_localized) AS claims
WHERE claims.language = 'en'
LIMIT 10;
```

### `patents-public-data.google_patents_research.publications`（带向量）

| 字段 | 用途 |
| --- | --- |
| `publication_number` / `country` | 对应关系与国别 |
| `top_terms` | 该专利的主题词 |
| **`embedding_v1`** | **向量嵌入**，可用 `cosine_distance()` 做**语义近邻检索** |

官方示例形态：

```sql
SELECT gpr.publication_number,
       cosine_distance(gpr.embedding_v1, seed.embedding_v1) AS distance
FROM `patents-public-data.google_patents_research.publications` AS gpr,
     (SELECT embedding_v1 FROM `patents-public-data.google_patents_research.publications`
      WHERE publication_number = 'CN210644322U') AS seed
WHERE gpr.country = 'China'
ORDER BY distance LIMIT 20;
```

**这就是 incoPat 语义检索的免费等价物**：以一件专利（或你已有的最接近文献）为种子，
在整个语料里按语义找最近的公开。对"查新"特别有用：先用关键词/CPC 找到一件近似文献，
再用它做语义近邻扩检，能捞到关键词漏掉的同族思路。

## 4. 本 skill 怎么用（`scripts/gp_bigquery.py`）

```bash
B="D:/aicoding/mylib/paa/skills/google-patents-search/scripts"

python "$B/gp_bigquery.py" probe                      # 前置条件自检

# 取著录项 + 权利要求全文（扫描量极小，秒级）
python "$B/gp_bigquery.py" lookup CN210644322U --out evidence/bq/CN210644322U.json

# 结构化检索：关键词 + CPC + 国别 + 优先权日区间
python "$B/gp_bigquery.py" search --keyword 石墨烯 --keyword 眼罩 \
  --country CN --cpc A61F --after 2015-01-01 --limit 20 --max-gb 50

# 语义近邻（以种子件扩检）
python "$B/gp_bigquery.py" similar CN210644322U --country China --limit 20 --max-gb 20
```

三处都先**干跑估算**扫描量：`search`/`similar` 超过 `--max-gb` 会直接拒绝执行（退出码 3），
把"预计要扫多少 GB"写在 JSON 里，避免无意烧掉每月 1 TiB 免费额度。

## 5. 成本与安全要点

- **永远先干跑**：本 skill 已内置（`bigquery.QueryJobConfig(dry_run=True)`，干跑不计费）；
- **优先用可过滤字段**：`country_code`、`priority_date`、`cpc` 能大幅降低扫描量；
  纯关键词 `LIKE` 扫标题/摘要仍是全表扫，务必配 `--country`/`--after` 收窄；
- **避免裸跑全表余弦**：`cosine_distance` 近邻若不加国别/日期过滤会扫整个研究子集（可达数百 GB），
  本 skill 用 `--max-gb` 拦；
- 大结果集不要 `SELECT *`；只要公开号时只选 `publication_number`；
- 沙盒里别建大表（60 天过期）；需要持久化就落本地 JSON（本 skill 已这么做）。

## 6. 它做不到的（别指望）

- **没有法律状态**（是否有效、年费、专利权人变更）——这部分仍需 incoPat / 官方渠道；
- **不是法定检索**：语料有覆盖与更新延迟，不能替代代理师的检索报告；
- **description（说明书全文）能否取到，需在你的项目里用 INFORMATION_SCHEMA 确认**：
  ```sql
  SELECT column_name, data_type FROM `patents-public-data.patents.INFORMATION_SCHEMA.COLUMNS`
  WHERE table_name = 'publications' ORDER BY column_name;
  ```
  拿到的字段清单请回填到本文件，再决定是否把说明书全文纳入 `gp_fetch.py`。
- 沙盒不支持 DML/流式写入，所以"把结果写回 BigQuery 做后续分析"这条路在沙盒里走不通（改用本地文件）。
