---
description: 外循环：从跨案缺陷与真实 OA 进化专利撰写系统的基因组（agents/knowledge/scripts）
argument-hint: [--since N | --from-oa <OA文件路径> | 案件简称...]
---

# /evolve-patent-system

本项目的**进化外循环**入口。内循环（`/draft-patent`）用当前基因组产出专利；本命令让**系统自身**随时间变强——不改 LLM 权重，只进化可编辑工件（提示词 / 知识库 / 工具 / 拓扑）。

## 参数
- 无参 / `--since N`：扫描最近 N 个案件（默认全部）的 `06/07 自评` 与门禁报告。
- `--from-oa <路径>`：以一份**真实审查意见通知书(OA)** 为最高权重信号驱动进化。
- `案件简称...`：只针对指定案件的缺陷进化。

## 执行流程（编排 patent-evolver）

1. **采信号**：收集
   - `output/*/06_审查自评_26条.md`、`output/*/07_审查自评_22条.md`
   - `output/*/_oa_amendment_playbook.md` 与 `--from-oa` 指定的 OA（**外部真值,最高权重**）
   - `output/*/_consistency_report.md`、`cluster_v5_*/review/集群审查门禁报告.md`
2. **静态门禁**：运行 `scripts/patent_static_check.py`（若存在）产出**不可作弊**的 `R_static`（禁词/术语标号一致/权项引用合法性/公式体例/字数）。
3. **变异**：调用 `patent-evolver`，聚类复现缺陷 → 产出定位到具体文件/行的修改提案（优先级 知识库② > 提示词① > 工具③ > 拓扑④）。
4. **沙箱回归**：把 `evolution/golden_cases/`（冻结黄金案）用"打了 patch 的基因组"重跑 `quality-reviewer` + `patentability-examiner` + 静态检查；目标缺陷须消解且 `R_static` 不退化，否则驳回该提案。
5. **人工审核（阶段一默认）**：把 `evolution/proposals/<时间戳>_proposal.md` 呈现给用户；用户确认后：
   - 逐条 `Edit` 应用到 `agents/*.md` / `knowledge/*.md` / `scripts/`；
   - 若项目已 `git init`：`git commit`（英文 message，基因组版本 +1），便于**一键回滚**（`v5 差就 checkout v4`）；
   - 在 `omx_wiki/` 追加进化账本条目（为什么改、证据出处 OA/指南、`[[]]` 互链）。

## 奖励函数（务必遵守优先级）
```
R = 0.2·R_self + 0.3·R_static + 0.5·R_external
    (26/27自评   (确定性脚本    (真实OA/授权驳回,延迟真值)
     仅早停信号)   不可作弊)
```
**进化决策只认 R_static 与 R_external；R_self 永不当奖励**（防目标漂移/reward hacking）。

## 触发纪律
仅在 (a) 收到新 OA、(b) 同类缺陷 ≥3 案复现、(c) 手动 时运行；有进化冷却期；不自动合并（阶段一）。

## 输出
- `evolution/proposals/<时间戳>_proposal.md`（提案 + 沙箱验证 + 建议 commit）
- 人工确认后：基因组文件被编辑 + （git 仓库下）一个进化 commit + `omx_wiki/` 进化账本条目

## 受保护条款
`knowledge/常见问题与避坑.md` 第一节 AI 合规底线为**不可进化削弱**的受保护条款。
