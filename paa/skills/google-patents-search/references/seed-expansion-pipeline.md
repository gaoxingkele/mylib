# 种子件扩检流水线（`gp_pipeline.py`）

一次调用完成：**多轴召回 → 去重排序 → 取原文 → 核验骨架**。
目标是消除"只跑一条关键词腿就下结论"的漏检风险，同时把每一条腿的可用性如实记录下来。

## 1. 四条召回轴

| axis | 来源 | 免 key？ | 实测（2026-09-26，本机出口被 Google 503） |
| --- | --- | --- | --- |
| `seed_citation` | 种子件页面**引证表**（该件引用的在先公开） | 需能取到种子页（中继即可） | `CN103399241B` → 5 条，含 CN102087321A、CN102662113A 等高相关件 |
| `seed_similar` | 种子件页面**相似文献表** | 同上 | 同件 → 25 条 |
| `semantic` | BigQuery `google_patents_research.publications.embedding_v1` 向量近邻 | ❌ 需 GCP | 本机 `bigquery_sdk_missing`，如实记为 `unavailable` 并给出 remedy |
| `keyword` | `--query` 显式检索式，或由种子件题名自动派生 | ✅ | `配电变压器 故障诊断` → patentscope 5 + 中继腿 6 |

> 种子页面的引证表/相似文献表来自 Google Patents 页面本身（直连或中继），
> 不是第三方推测——它们是 Google 自己标注的引用关系与相似文献。

## 2. 题名派生检索式（`keyword` 轴的兜底）

只给 `--seed` 不给 `--query` 时，脚本用种子件题名派生检索式：

1. 按结构性词（`一种/基于/的/与/系统/方法/装置/…`、`and/of/for/system/method/…`）切题名，取 ≥2 字片段；
2. 生成候选：`EN_ALLTXT:(最长片段)` → `EN_ALLTXT:(最长两片段)`（后者的 AND 只在第一个候选 0 命中时才试）；
3. 有 `--country` 时拼 `AND CTR:(XX)`。

实测依据：PATENTSCOPE 对中文查询会自行分词，`EN_ALLTXT:(配电变压器故障诊断)` 能召回，
而四个词空格相连做 AND 会掉到 0 命中。**派生检索式只是兜底**——正式检索仍建议显式 `--query`。

## 3. 去重、排序与截断

- 去重主键：规范化公开号；保留 provenance（`axes[]` 记录哪些轴发现了它）；
- 启发式分 `score`（只决定"先看哪件"，**不是相关性结论**）：

  | 分项 | 权重 |
  | --- | --- |
  | 轴权重 | `seed_citation` 3.0 / `seed_similar` 2.0 / `semantic` 2.0 / `keyword` 1.0（多轴命中累加） |
  | 截止日资格 | 有 `--cutoff` 时：公开日 ≤ 截止 +1.0，> 截止 −1.0，未知 0 |
  | 题名词重合 | 命中词占比 × 2.0（词来自显式检索式与种子题名片段） |
  | 同国别 | +0.5（与种子件同国别） |
  | 公开日未知 | −0.25（无法做"申请日前公开"判断） |

- **截断时按轴保底**：`--limit` 生效时先给每条轴留 `--per-axis`（默认 3）个名额，再按总分补足。
  否则高分轴会把整条轴挤空（实测曾出现 12 条关键词轴候选全被挤出前 30）。

## 4. 取原文与核验

取件链 `google → tavily → bigquery`（`--no-relay` 去掉中继），逐件落盘：

```
<out>/docs/<PN>.json        结构化文档（claims/description/摘要/日期/引证/相似文献）
<out>/docs/<PN>.md          人读版
<out>/docs/<PN>.relay.md    中继取件的原始 Markdown（sha256 的计算对象）
<out>/docs/<PN>.pdf         --save-pdf 时的同页 PDF 字节留痕
<out>/citations.draft.json  引用骨架（quote=权利要求1原文，role 留空，auto=true）
<out>/verify.json           核验门禁结果（含 provenance/relay warnings）
<out>/screening.md          筛查报告（轴覆盖 / 候选池 / 已取原文 / 限制）
<out>/pipeline.json         全量 JSON（与 stdout 的 GP_PIPELINE_JSON 同构）
```

**骨架不是结论**：`citations.draft.json` 只证明"已取到原文且可逐字定位"，
真正的 X/Y/A 片段与角色必须人工替换后重跑 `gp_verify.py`。

## 5. 退出码

| 码 | 含义 | 处理 |
| --- | --- | --- |
| 0 | 有候选且至少一件取到原文（或显式 `--fetch-top 0` 只筛查） | 正常，进入人工判读 |
| 4 | 有候选但一件原文都没取到（如候选都只在美国库、或都被拦截） | 看 `limitations[]`：多为 `doc_not_on_google_patents` 或通道受限 |
| 3 | 无候选且存在被拦/不可用的轴 | 按 `remedy` 配 `TAVILY_API_KEY`（中继）或 GCP |
| 2 | 参数错误（例如既没 `--seed` 也没 `--query`） | 修参数 |
| 5 | 运行时错误 | 看 stderr `GP_NOTE:` |

## 6. 典型调用

```bash
# 种子件扩检（四轴全开），排除某日之后公开的文献，取前 8 件原文并留 PDF
python gp_pipeline.py --seed CN103399241B --country CN --cutoff 2026-09-25 \
  --fetch-top 8 --out runs/p06 --audit runs/p06/audit.jsonl --save-pdf

# 已有明确检索式：显式给 --query（推荐），同时保留种子轴
python gp_pipeline.py --seed CN103399241B --query "配电变压器 故障诊断" --country CN

# 保守模式：不碰第三方中继、不碰 BigQuery（只用直连 + PATENTSCOPE）
python gp_pipeline.py --seed CN103399241B --no-relay --no-semantic
```

## 7. 边界

- 候选池**不是**检索结论；`未发现` 只能表述为"本轮检索未发现"；
- 中继通道（`tavily`）取回的文本 provenance 为 `relay`，与直连证据强度不同，
  引用前建议用同页 PDF（`--save-pdf`）复核；
- `semantic` 轴缺失时，报告必须如实写"本轮无语义轴覆盖"，不能用关键词轴的结果冒充语义覆盖。
