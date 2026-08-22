# MANIFEST — P05-1

> 案例编号 P05-1 · 基于知识图谱校验-约束闭环的检索增强生成防幻觉方法

## Gate Status

| Gate | Status | Evidence |
|---|---|---|
| 1. 客体适格 | **PASS** | logic/subject_matter.md（无 Article 25 / 2.2 风险） |
| 2. 新颖性/创造性证据绑定 | **PASS** | logic/prior_art.md：12 区别特征全部绑定真实对比文件 pn |
| 3. 充分公开 | **PASS** | application/specification.md 含 2 实施例 + 数值实例 |
| 4. 禁编造对比文件 | **PASS** | evidence/prior_art_search/ 含 2 真实 pn，evidence/prior_art_claims/ 含 claim 全文转写 |

## Layer Index

- `logic/` — 认知层（发明要素 / 客体 / 独权拆解 / 创造性点 / 对比文件 / 方案）
- `application/` — 工件层（权利要求 / 说明书 / 附图 / 摘要）
- `trace/exploration_tree.yaml` — 探索图（v1 事实注入 → v2 冲突标记 → v3 封箱+元适配）
- `evidence/` — 证据（CN121636664A, CN121659916A 真实查新 + claim 全文 + 评分）

## Summary

- 独立权利要求：1
- 从属权利要求：14（含装置 / 介质 / 电子设备主题）
- 对比文件：2（CN121636664A 冲突 / CN121659916A 冲突）
- 探索图节点：5（2 prior-art + 3 claim-version）
- 创造性点：4
- 评估概率（修改后）：0.461

## Gap Report

None. All four gates PASS, all cross-layer bindings resolve, no NEEDS-INPUT items.