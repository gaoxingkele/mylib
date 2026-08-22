# Evidence Index — P05-1

## 真实查新记录（incopat-search 真实返回）

| pn | 检索类型 | 检索日期 | 状态 |
|---|---|---|---|
| CN121636664A | semantic + claim | 2026-08-22 | 记录 |
| CN121659916A | semantic + claim | 2026-08-22 | 记录 |

源：`incopat-search` skill（apitest.incopat.com）。

## 对比文件权利要求全文转写

| pn | 文件 | 状态 |
|---|---|---|
| CN121636664A | evidence/prior_art_claims/CN121636664A.md | 已转写 |
| CN121659916A | evidence/prior_art_claims/CN121659916A.md | 已转写 |

## 评分数据

- `evidence/scoring/scoring.json` — AHP-SEM 三轮评分（before / after_correction_v1 / after_mechanism_avoidance_v3）

## 设计绕行记录

| 轮次 | 文件 | 目标 |
|---|---|---|
| Round 1 | `round_1_facts_to_contrast.md` | v1 → v2（仅换内容，未构成机制级绕行） |
| Round 3 | `round_3_injection_to_sealing.md` | v2 → v3（换机制，构成机制级绕行） |

## 所有 pn 均经过 incoPat 真实查询，无编造

→ gates-checklist.md Gate 4 PASS