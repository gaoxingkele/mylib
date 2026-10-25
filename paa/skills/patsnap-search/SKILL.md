---
name: patsnap-search
description: >
  智慧芽（PatSnap）开放平台专利与论文检索、原文取件（纯 REST API）。用于查新、对比文件发现、
  按公开号取著录项/权利要求/说明书/法律状态并留证据 JSON，以及相似专利群的可专利性与技术创新统计。
  只用检索与数据接口，不外发技术方案（不调用 AI 查新、Pat GPT、撰写类接口）。
  TRIGGERS: 智慧芽, PatSnap, patsnap, zhihuiya, 查新, 现有技术检索, 对比文件, 相似专利, 语义检索,
  权利要求原文, 说明书原文, 法律状态, 论文检索, 可专利性指标
---

# 智慧芽检索与取件（方案一：只检索、不外发方案）

脚本：`scripts/patsnap.py`（仅标准库）。接口来源：`https://open.zhihuiya.com/openapi.json`（375 个接口），
2026-10-21 实测可用：P001/P002/P007/P008/P011–P019/P041/P050/P051/P081。L001 旧文献检索返回服务端错误，论文改用 P081。

## 用法

```powershell
python scripts/patsnap.py count  --query "TACD:(锂电池 AND 负极)"
python scripts/patsnap.py search --query "TACD:(锂电池 AND 硅碳负极) AND IPC:(H01M)" --limit 100 --out <case>/raw_inputs/patsnap
python scripts/patsnap.py semantic --text "硅碳负极 预锂化 循环寿命" --country CN --limit 50 --out ...
python scripts/patsnap.py similar --pn <公开号> --limit 50 --out ...
python scripts/patsnap.py paper  --keywords silicon anode prelithiation --semantic "prelithiation of silicon-carbon anode" --out ...
python scripts/patsnap.py fetch  --pn <公开号> --parts biblio,claims,desc,legal --out ...
python scripts/patsnap.py indicators --pns <公开号1>:80% <公开号2>:79%
```

- 检索式语法：`TACD:`（标题/摘要/权利要求/说明书）、`TTL:`、`ABST:`、`CLMS:`、`IPC:`、`AND/OR/NOT`、括号；`collapse` 默认按申请号合并。
- `--out` 每次调用写一个证据 JSON（端点、请求、HTTP 状态、UTC 取回时间、原始响应 sha256、原始响应）。
- 密钥：`PATSNAP_API_KEY` / `ZHIHUIYA_API_KEY` 环境变量，或当前目录向上的 `.env`；不回显、不入证据。

## 红线

1. **不外发技术方案**：语义检索与论文语义查询限 80 字，只放公开层级主题词（对象、工序名、产品类别），
   不放机制、参数、判据。AI35/M002/AI29/AI30/Pat GPT/AI37 等需要提交方案全文的接口不在本脚本内；
   确需使用，须用户针对具体内容本轮明确授权，改用 `scripts/patsnap_ai.py`（方案二，见下）。
2. **对比文件入 `01_现有技术检索报告.md` 前必须 `fetch` 取回原文**并保留证据 JSON；检索列表只是候选。
3. `indicators` 是相似专利群的统计（授权比例、复审数、高相似件数），**不是本申请的授权概率**，
   只可作为 patent-grant-scorer 的输入特征。
4. 估值类接口（P035–P040）只对已公开专利有数据，不用于未申请文本。

## 方案二：AI 查新（`scripts/patsnap_ai.py`，外发方案全文）

- 子命令：`ai30`（同步相似比对）、`ai29`（技术构思验证）、`m002`（查新智能体）、`ai35`（12 步查新，
  自动原样确认方案摘要/特征/检索要素，最后取报告链接）、`poll`（续轮询已有 task）。
- 每次必须带 `--authorized`，输入只从 `--input-file` 读；证据 JSON 存 `--out`（建议案件 `raw_inputs/patsnap_ai/`）。
- 与 `patsnap.py` 共用余额；余额不足返回 `error_code 67200005`，不是"未检出"。
- 结果属模型意见（R_self 同级）：文献号须 `patsnap.py fetch` 取原文核验后才可进 01；
  其新颖性/创造性判断不等于授权概率，进 patent-grant-scorer 时只作证据条目。

## MCP 通道（`scripts/patsnap_mcp.py`，"专利&文献融合检索" MCP）

- 服务端 `https://connect.zhihuiya.com/2b0355/logic-mcp`；与 REST 授权/计费分开：REST 报 67200004（应用未开通）
  或 67200005（余额不足）时，MCP 可能仍可用，先 `tools` 再 `search` 实测。
- 密钥优先 `PATSNAP_MCP_KEY`，只经环境变量传。2026-10-23 实测：`Authorization: Bearer <key>` 与 URL 参数
  `?apikey=<key>` 两种认证等价（同 9 个工具、同检索结果）；脚本用 Bearer，避免密钥进 URL/日志。
- 子命令：`search`（semantic_query 上限 8000 字，可放独权全文；`--keywords` 中英日短语；`--family` 同族折叠）、
  `fetch --md`（著录＋权利要求＋说明书全文）、`life`（法律事件）、`lit`（期刊论文）、`call`（任意工具）。
- 只有检索与取件，没有 AI 特征比对；比对在本机做。语义查询含未公开方案全文时，同方案二须用户明确授权。

## 与其它检索 skill 的关系

incopat-search（真实 API，账号可用时首选）、google-patents-search（免费复检索与中继取件）、本 skill（智慧芽，
覆盖全球专利＋论文、带相似度）。同一结论建议至少两个库交叉；不同库的命中差异如实记录，不把"未检出"写成"不存在"。
