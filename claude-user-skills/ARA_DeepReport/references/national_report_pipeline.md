# 国别境外阵地报告 · 自动化管线（从美国报告全过程蒸馏）

本管线把"美国分册"从首版到 v1.3.1 的全过程优化为可复用流程。框架统一为
**选址 · 搭建 · 运营 · 保障**；记忆基座为 `ledger.json`；产出 RAND 研究报告制作规格 + 可审计证据账本。

## 阶段

1. **SCOPE/拆解**：读底稿该国章节（`美西方等国境外工作阵地构建研究 (1).md`），按旗舰机构分 ~4 集群；建 `reports/<国>/_research/`。
2. **RESEARCH 扇出**（并行）：每集群一 agent 多源核验——逐条标 `确认/修正/存疑/否证`、挂可点击出处、补 2025–2026 进展、严格区分**确证事实 vs 外界指称**；写 `_research/cluster_<key>.md`。
3. **SYNTHESIZE**：1 agent 读全部 cluster 文件，合成 RAND 式叙事 MD（封面 `::: cover` / `[[TOC]]` / 执行摘要含 `::: keyfindings` `::: recommendations` / 缩略语 / 选址搭建运营保障分章 / 综合研判 / 研究方法附录），并产出 `claims.json`（账本种子，字段见 ledger.py）。
4. **LEDGER+PRODUCE**：`ledger.py init+bulk` 建账本；复用框架图 `_assets/fig_framework.png`；`md_to_docx.py --title --version` 出 DOCX；`verify_report_generic.py` 验证门；`report_version.py changelog` 写 CHANGELOG → 出 **v1.0.0**。
5. **EXPERT REVIEW**（按需）：3 领域专家对抗式评审 → 意见清单 → patch 修订 → 第二轮闭环复核（v1.0.1/1.0.2）。
6. **LITERATURE**（按需）：近五年学术/智库文献匹配 → 附录 B + 切入点移植 + 数据更新（minor）。
7. **VERSION/EXPORT**：语义化版本（major 新国别 / minor 新维度 / patch 勘误时效），ledger + CHANGELOG 全程留痕。

## 不变量（持续学习铁律）
- 不臆造，每条事实挂出处；区分确证 vs 指称。
- 升级累积式、不灾难性遗忘：replay 旧断言、保护高置信项、新维度隔离挂载、翻案 `refuted` 留痕。
- 交付文档不写 AI/搜索厂商名。

## 复用资产
- 转换器 `autodeepreport/scripts/md_to_docx.py`（RAND 要素，向后兼容）
- 账本/版本 `ledger.py` / `report_version.py`
- 验证门 `news-monitor/scripts/ralph/verify_report_generic.py`（任意国别）
- 框架图 `fig_framework.png`（选址搭建运营保障，country-agnostic，可复制到各国 `_assets/`）
- 编排 `Workflow`（Research→Synthesize→Produce 三阶段 pipeline，6 国并行）
