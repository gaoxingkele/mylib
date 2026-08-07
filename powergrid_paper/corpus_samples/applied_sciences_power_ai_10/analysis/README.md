# MDPI Applied Sciences 电力系统 × AI 论文结构统计（10 篇）

## 结论先行

Applied Sciences 官方不设论文最大篇幅，强调完整、可复现的实验细节。因此，下面数字是同主题已录用 Article 的经验分布，不是编辑部硬性配额。

本样本包含 2023–2026 年 10 篇 Applied Sciences 正式 Article，覆盖电网 NLP、负荷/风电预测、电压控制、机组组合、输配电规划与应急调度。样本中位数为：**24 页、正文 7098 个英文词、5 个一级正文节、73.5 个正文段落、每段中位数 73.5 词、26 个编号显示公式、1 个独立实验数据集/算例、9 幅图、5 张表、2 幅方法框图、8.5 个实验结果图表**。

适合把两篇 CMC 稿件迁移到 Applied Sciences 的稳健目标是：**18–26 页、正文 7000–9000 词、5–6 个一级正文节、20–35 个有效公式、1–3 个数据集/算例、2–4 幅框图、8–15 个实验结果图表**。公式数量应服从方法需要；纯深度学习预测稿不应为了接近中位数而堆公式。

## 统计摘要

| 指标 | 平均数 | 中位数 | 四分位区间 | 最小–最大 |
|---|---:|---:|---:|---:|
| PDF 页数 | 22.7 | 24 | 17–26.2 | 14–34 |
| 摘要词数 | 200.2 | 193 | 170.8–238.2 | 113–279 |
| 正文净词数 | 7278.5 | 7098 | 5237.5–9022.5 | 4488–11174 |
| 一级正文节 | 5.5 | 5 | 5–5.8 | 4–8 |
| 正文段落 | 76.9 | 73.5 | 64.5–85.5 | 36–128 |
| 单段词数（逐篇中位数） | 86.5 | 73.5 | 53.5–100.8 | 36–212 |
| 编号显示公式 | 28.8 | 26 | 20.8–33.2 | 4–73 |
| 独立实验数据集/算例 | 1.6 | 1 | 1–2.5 | 1–3 |
| 全部 Figure | 10.9 | 9 | 6.2–16.8 | 3–19 |
| 全部 Table | 5.2 | 5 | 3.2–7 | 1–9 |
| 方法/架构框图 | 2.4 | 2 | 2–3.5 | 1–4 |
| 实验结果 Figure | 7.4 | 5 | 3.2–11.8 | 0–17 |
| 实验结果 Table | 2.8 | 2.5 | 1.2–4.5 | 0–6 |
| 实验结果图表合计 | 10.2 | 8.5 | 5.5–14 | 2–22 |

“正文净词数”统计 JATS `<body>` 段落中的英文词，不含摘要、参考文献、图注、表内文字和文末声明；页数是正式 PDF 的全部页数。因 MDPI JATS 有时把列表或连续说明合并为一个 `<p>`，段落词数宜看中位数，不宜只看均值。

## 典型章节蒸馏

| 章节角色 | 覆盖论文 | 观察到的中位段落数/篇 | 中位词数/篇 | 单段中位词数 | 迁移稿建议 |
|---|---:|---:|---:|---:|---|
| Introduction | 10/10 | 8.5 | 1117 | 133.5 | 7–10 段，900–1400 词 |
| Related Work（独立成节） | 2/10 | 3 | 797 | 304.8* | 通常并入引言；若独立，5–8 段、800–1200 词 |
| Method/Model（同篇相关一级节合计） | 10/10 | 36 | 3106 | 76.3 | 25–40 段，2600–3600 词，分 3–6 个小节 |
| Data/Simulation Setup（独立成节） | 2/10 | 24.5 | 2007 | 77.7 | 可并入实验；独立时 8–15 段、700–1400 词 |
| Experiments/Results | 9/10 | 17 | 2360 | 90.9 | 15–25 段，2000–3000 词，必须形成证据链 |
| Discussion（独立成节） | 1/10 | 4 | 498 | 124.5 | 可与结果合并；独立时 4–7 段、500–900 词 |
| Conclusions | 10/10 | 4.5 | 318.5 | 90.2 | 3–5 段，250–450 词 |

\* Related Work 只有两篇独立成节，且 XML 把长枚举合并进少量段落，因此 304.8 词/段不应作为写作目标。

最常见的五节骨架是：`1. Introduction` → `2. Materials and Methods / Problem Formulation` → `3. Proposed Method / Framework` → `4. Case Study / Experiments and Results` → `5. Conclusions`。Related Work 多数并入 Introduction，Discussion 多数并入 Results；若目标是增强 Applied Sciences 的应用解释和可复现性，建议将 `Experimental Setup` 与 `Discussion` 明确拆成小节，但不必机械增加一级标题。

## 10 篇逐篇统计

“图+表”是论文全部图表；“实验证据”仅含结果、对比、消融、鲁棒性、敏感性等图表；“框图”仅含流程、架构和网络结构图。

| ID | 主题简称 | 页 | 正文词 | 一级节 | 公式 | 数据集/算例 | 图+表 | 框图 | 实验证据 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 13-11074 | Grid RoBERTa 关系抽取 | 14 | 4893 | 5 | 24 | 1 | 10 | 2 | 2 |
| 13-12690 | DNN 配电网电压控制 | 17 | 4488 | 8 | 4 | 1 | 19 | 2 | 15 |
| 14-06486 | 输电与储能协同规划 | 24 | 9182 | 5 | 34 | 1 | 16 | 2 | 9 |
| 14-10368 | 台风下电网应急调度 | 17 | 7014 | 5 | 37 | 1 | 12 | 1 | 5 |
| 14-11797 | 含 SOP 的主动配网优化 | 27 | 9132 | 6 | 73 | 1 | 18 | 1 | 11 |
| 15-02435 | 多注意力 CNN-LSTM 负荷预测 | 24 | 8694 | 5 | 20 | 3 | 13 | 4 | 8 |
| 15-04498 | GNN+LP 加速机组组合 | 15 | 4962 | 5 | 23 | 3 | 10 | 4 | 3 |
| 15-07003 | GCN-Transformer 负荷预测 | 34 | 6064 | 5 | 14 | 3 | 26 | 2 | 22 |
| 16-00466 | Graph-Mamba 风电预测 | 24 | 7182 | 4 | 28 | 1 | 12 | 4 | 7 |
| 16-04476 | 疲劳预测辅助风场调频 | 31 | 11174 | 7 | 31 | 1 | 25 | 2 | 20 |

## 数据集与实验设计蒸馏

样本的“1 个数据集”通常不是简单切一次训练/测试集，而是一个完整应用案例：真实量测或公开数据 + 物理系统/仿真平台 + 多种运行场景。三个数据集的论文主要是通用预测模型或跨规模算法验证。

1. **最低可接受证据层**：一个真实或公认 benchmark 数据集/算例；严格按时间或场景切分；6–10 个有竞争力的基线；主结果表；误差/运行曲线；至少一组消融。
2. **稳健录用层**：两个独立数据来源、区域或系统规模，或三个公开预测数据集；多预测时域/负荷水平/渗透率；统计显著性或多随机种子；复杂度与运行时间；敏感性和鲁棒性。
3. **电网应用增强层**：加入物理约束检查、潮流/调度可行性回放、极端工况、工程阈值、失败案例与部署成本。Applied Sciences 的应用价值通常由这一层拉开差距。
4. **避免数据泄漏**：时间序列按时间分割；归一化只用训练集拟合；滑窗不得跨 train/validation/test 边界；同一母场景扰动生成的样本不得分散到不同集合。
5. **图表证据链建议**：2–4 幅方法框图；1–2 张数据/参数表；1 张总性能表；1 张消融表；4–8 幅预测/调度/潮流结果图；1–3 幅敏感性、鲁棒性或复杂度图。合计约 10–16 个高信息密度图表即可，不追求数量本身。

## 公式、图表与篇幅的正确理解

- 公式不是录用指标。样本从 4 到 73 个，差异来自任务类型：端到端 DNN 控制可只有 4 个，而优化建模论文常有 30–70 个。建议保留定义、目标函数、关键约束、损失函数和复杂度推导，删除教科书式重复公式。
- 数据集不是越多越好。优化/控制论文用一个权威网络加多场景完全常见；通用预测模型若只用一个数据集，则应补跨时段、跨站点或跨预测步长验证。
- 页数也不是目标函数。24 页是正式排版中位数，不等于 Word/LaTeX 投稿稿件 24 页。更可控的目标是正文 7000–9000 词与完整证据链。
- 框图要回答不同问题：总体工作流、模型内部结构、物理系统/数据流。三张内容重复的“大框图”不如两张层次清晰的图。

## 样本清单与数据来源

1. [A Combined Semantic Dependency and Lexical Embedding RoBERTa Model for Grid Field Relational Extraction](https://doi.org/10.3390/app131911074)
2. [Deep Neural Network-Based Autonomous Voltage Control for Power Distribution Networks with DGs and EVs](https://doi.org/10.3390/app132312690)
3. [Multi-Stage Coordinated Planning for Transmission and Energy Storage Considering Large-Scale Renewable Energy Integration](https://doi.org/10.3390/app14156486)
4. [Emergency Dispatch Strategy Considering Spatiotemporal Evolution of Power Grid Failures Under Typhoon Conditions](https://doi.org/10.3390/app142210368)
5. [Optimization of Active Distribution Network Operation with SOP Considering Reverse Power Flow](https://doi.org/10.3390/app142411797)
6. [Power Grid Load Forecasting Using a CNN-LSTM Network Based on a Multi-Modal Attention Mechanism](https://doi.org/10.3390/app15052435)
7. [Stable Variable Fixation for Accelerated Unit Commitment via Graph Neural Network and Linear Programming Hybrid Learning](https://doi.org/10.3390/app15084498)
8. [Short-Term Power Load Forecasting Using an Improved Model Integrating GCN and Transformer](https://doi.org/10.3390/app15137003)
9. [A Dual-Decomposition Graph-Mamba-Transformer Framework for Ultra-Short-Term Wind Power Forecasting](https://doi.org/10.3390/app16010466)
10. [Coordinated Optimization of Wind Farm Control Parameters for Primary Frequency Regulation Based on Fatigue Load Prediction](https://doi.org/10.3390/app16094476)

PDF 和 JATS XML 均来自 MDPI 官方资源服务器。每篇 DOI、官方 PDF URL、本地 PDF/XML 路径均保存在 `paper_stats_raw.csv`。

## 可复现文件

- `../pdf/`：10 篇正式 PDF。
- `../xml/`：10 篇官方 JATS XML。
- `paper_stats_raw.csv` / `paper_stats_raw.json`：逐篇统计与人工数据集标注。
- `section_stats.csv`：55 个一级节的段落与词数统计。
- `section_role_summary.csv`：按章节角色合并后的统计。
- `figure_inventory.csv`：109 幅 Figure 的标题和自动候选标签。
- `corpus_summary.json`：可机器读取的汇总分布。
- `../../../../scripts/literature/analyze_applsci_corpus.py`：复算脚本。

人工标注用于区分框图和实验结果图表；自动字段 `auto_framework_figures`、`auto_result_figures` 仅供审计，不作为最终结论。
