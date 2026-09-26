# Google Patents 检索式速查（免费站，无需 key）

Google Patents 的检索式写在 URL 的 `q=` 参数里，语法与网页检索框一致。
本 skill 的 `gp_search.py --query '<检索式>'` 会原样透传，只做 URL 编码。

## 1. 基本运算

| 写法 | 含义 | 示例 |
| --- | --- | --- |
| `词A 词B` | 空格 = **AND** | `石墨烯 眼罩` |
| `A OR B` | 或 | `眼罩 OR 眼贴` |
| `-词` 或 `词 NOT` | 排除 | `石墨烯 -电池` |
| `"短语"` | 精确短语 | `"采集电极"` |
| `(A B) OR C` | 分组 | `(眼罩 石墨烯) OR (眼贴 石墨烯)` |
| `词*` | 前缀通配（站内支持有限，慎用） | `光*电` |

## 2. 常用字段

| 字段 | 含义 | 示例 |
| --- | --- | --- |
| `TI=` | 标题 | `TI=(加热 眼罩)` |
| `AB=` | 摘要 | `AB=(脑电 采集)` |
| `CL=` | 权利要求 | `CL=("采集电极")` |
| `DESC=` | 说明书 | `DESC=(石墨烯 发热)` |
| `CPC=` / `IPC=` | 分类号 | `CPC=A61F7/02`、`IPC=A61B5/00` |
| `country=` | 国家/地区 | `country=CN`、`country=(CN OR US)` |
| `assignee=` | 申请人 | `assignee=("某某公司")` |
| `inventor=` | 发明人 | `inventor=(张三)` |
| `before=` / `after=` | 日期边界 | `before=priority:20200101`、`after=publication:20180101` |
| `status=` | 法律状态（GRANT/APPLICATION） | `status=GRANT` |
| `type=` | 文献类型（PATENT） | `type=PATENT` |

日期可指定基准：`before=priority:YYYYMMDD` / `after=filing:YYYYMMDD` / `before=publication:YYYYMMDD`。

## 3. 组合式范例（可直接复制）

```text
# 中国范围内、眼罩 + 石墨烯 + 采集电极
石墨烯 眼罩 采集电极 country=CN

# 分类号锁定 + 关键词（提高查准）
CPC=A61F7/02 (石墨烯 OR graphene) (眼罩 OR 眼贴 OR "eye mask")

# 申请日前公开的候选对比文件（把日期换成本案申请日的前一天）
after=publication:20150101 before=publication:20260925 (脑电 采集电极) country=CN

# 权利要求里明确写到"加热区独立驱动"的
CL=("独立驱动" 加热区) country=CN

# 同族/引证扩展的起点：已知最接近文献的公开号
US20230013787A1
```

## 4. 检索策略（三步漏斗，沿用 incoPat skill 的做法）

## 3.5 同一条 `--query` 在别的后端会怎样（归一化规则）

`gp_search.py` / `gp_pipeline.py` 的 `--query` 会被**按后端归一化**，实测口径（2026-09-26）：

| 后端 | 归一化 | 实测 |
| --- | --- | --- |
| `google` | 原样透传 URL `q=` | 本机 503（见 `troubleshooting.md`） |
| `patentscope` | 无字段算子时包成 `EN_ALLTXT:(…)`；抽出 `country=XX`/`ctr=XX` 拼进 `AND CTR:(XX)`；词数 >2 时再追加"最长两词""最长一词"两个收窄候选，逐个试、命中即停 | `配电变压器 故障诊断` → 5 命中；`温升 负荷关系 配电变压器 故障诊断`（4 词 AND 会 0 命中）→ 自动收窄到 `(配电变压器 负荷关系)` → 5 命中 |
| `tavily`（中继） | 原样交给 Tavily，限定 `include_domains=["patents.google.com"]`，只保留能解析出公开号的链接 | `配电变压器 故障诊断` → 6 条 Google Patents 中文条目 |

要点：

- **裸中文检索式可用**（PATENTSCOPE 侧会自动加字段算子），但**词越多越容易 0 命中**——
  该库对空格相连的词做 AND，而它对中文会自行分词，所以"概念词 2–3 个"通常比"整句 5 个词"更有效；
- 输出里保留 `query_used` 与 `variants`，报告应据此写清"最终生效的检索式"。

## 4. 检索策略（三步漏斗，沿用 incoPat skill 的做法）

1. **粗召回**：3–6 组不同角度的检索式（技术主题词、手段词、效果词、分类号），每组取前 10–20 条；
2. **并集去重**：以 `pub_number` 为主键合并，得到候选池；
3. **精读定位**：对候选池中标题/摘要高度相关的 top 5–8 件逐件 `gp_fetch.py` 取原文，读权利要求与说明书，
   再判定 X/Y/A 类（见 `verification_protocol.md`）。

已有"最接近的已知文献"时，**跳过 1–2 步直接扩检**更快：`gp_pipeline.py --seed <公开号>` 会以该件为种子，
用它的引证表、相似文献表（免 key）与向量近邻（需 GCP）自动铺开候选池，
详见 `seed-expansion-pipeline.md`。

## 5. 覆盖与限制（必须写进报告的限制说明）

- **不是法定检索**：Google Patents 是免费商业站点，数据有延迟与覆盖缺口（部分国家/早期文献无全文，只有著录项）；
- **中文全文**：`country=CN` 的多数公开文本可在 `zh` 路径读到全文；个别只有申请公布文本（A 文献）而检索不到授权文本（B 文献）；
- **分类号漂移**：同一技术在 CPC/IPC 上的归类可能不同，单靠分类号会漏检，务必与关键词结果取并集；
- **同族**：同一发明在多国的公开号不同，判断"是否已被公开"时应考虑同族；本 skill 只取单件原文，同族扩展需另行核对；
- **法律状态**：本 skill 不抓取法律状态（Google Patents 的 "Status" 有时滞后），涉及是否有效的判断请用 incoPat 或官方渠道复核。
