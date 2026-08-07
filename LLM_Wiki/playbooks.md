# Playbooks (Graph Traversal)

## 1) 从“想法”到“目标期刊”

1. `ResearchStudio-Idea`：生成 idea pattern 与 bottleneck。
2. `Paper_CCF`：按期刊 slug 做 fit 路由。
3. 产物落盘：`ideaspark_fullcorpus_*` + `journals/<slug>/SKILL.md`。

## 2) 从“初稿”到“投稿前 QA”

1. `RepLLM-CPA`：抽取章节结构与证据几何（baseline/ablation/dataset/DAS/code）。
2. `AERS-Bridge -> citation-checker`：核验参考文献真伪与元数据。
3. `AERS-Bridge -> figure-table-audit`：校验图表与正文 claim 对齐。
4. `AERS-Bridge -> de-AIGC`：处理中英文本 AI 痕迹（不改事实数字）。

## 3) 全流程“一条龙”

1. `ResearchStudio-Idea`（方法蒸馏）
2. `RepLLM-CPA`（证据蒸馏）
3. `Paper_CCF`（期刊约束）
4. `AERS-Bridge`（投稿前闸门）

## 规则

- 任何改写不得改变系数、样本量、显著性结论与引用指向。
- 当不同体系冲突时：以目标期刊 `Paper_CCF/journals/<slug>/SKILL.md` 为准。
- AERS 仅按需调用，不做整包递归加载。

