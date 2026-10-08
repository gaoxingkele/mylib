---
type: Review
title: LightGMEM review-method distillation
status: active
updated: 2026-10-01
owner: llm
tags: [peer-review, aaai, calibration, case-study]
source_paths:
  - D:/BaiduSyncdisk/paperreview/aaai2026 chen/陈​励凡投稿 aaai 2026 LightGMEM-0729.pdf
  - D:/BaiduSyncdisk/paperreview/aaai2026 chen/陈励凡 aaai 的审稿意见.pdf
  - D:/BaiduSyncdisk/paperreview/aaai2026 chen/aaai2026 陈励凡 paperreview.ai Get detailed AI feedback on your re.txt
  - D:/BaiduSyncdisk/paperreview/aaai2026 chen/output/pdf/LightGMEM_Paper_CCF_independent_review.pdf
  - D:/aicoding/mylib/Paper_CCF/tests/replays/review-calibration-20261001.md
source_urls:
  - https://arxiv.org/abs/2609.27279
confidence: medium
---

# LightGMEM：从评审中学习审查方法，而非继承结论

论文用轻量实体提取、冲突 lane 并行消歧、延迟画像与重叠社区降低记忆构建成本。
该例只用于训练核查动作；既有评分、拒稿决定和文字长度不是方法有效性的标签。
原始文件保持不变，以上 `source_paths` 指向本机证据，不保证其他机器可访问。
方法入口：[evidence-calibrated-review.md](../evidence-calibrated-review.md)。

## 可吸收的技巧

| 来源与定位 | 学到的审查动作 | 限制与迁移方式 |
|---|---|---|
| AAAI N7E5，评审 PDF 第 4-5 页，B1/B2/B4 | 跨表比较默认配置；把串并行质量与宣称控制条件对应；追问重排序混杂 | 先确认实验切片、随机性及检索协议；不能凭分数差异宣布全部消融无效。 |
| AAAI AI Review，评审 PDF 第 6-8 页 | 对公式与动态状态建立机制链；用实际领先幅度校准强结论；区分成本比与运行协议 | “键不交不能建立语义独立”是证据不足判断，不是直接宣布静态公式错误。 |
| paperreview.ai，正文 Detailed Comments / Questions for Authors | 从阈值敏感性、flush 前查询、lane 关键路径和弱共现噪声生成可验证问题 | 在线查询与额外领域能力仅在核心主张涉及它们时成为必要验证，不扩大成万能实验清单。 |
| 本次 Paper CCF 报告，第 2-6 页 | 对每个问题分开写证据、推论与核查动作；区分已确认算术问题与待澄清口径 | 这是复核产物而非严格盲审标签；也须核对其建议是否重复已有实验。 |

## 不应继承的断言

**并行机制。** 投稿第 4 页式（7）规定静态键集合不交，式（8）允许动态创建/更新实体。
Inference: 这些描述不足以证明语义解析独立；需核查实际过滤、快照和合并规则。
N7E5 的“式（7）不成立”过强。paperreview.ai 在仍提出跨 lane 重复风险时，提前把机制
称为 technically sound 的依赖过近似，也没有给出完备性依据。

**跨表与覆盖子集。** 投稿表 5 的 0.888 与表 6 的 0.830 需要解释，前者明确使用 conv26，
后者范围不清；不能先假定是完全相同的评测。表 5 的 260 是总实体数，第 5.5 节的 242 是
社区覆盖实体数，可能为子集。Overall 也未必是分类分数的简单均值。
这些事实支持“口径待澄清”，不支持“数据必然矛盾”。来源：投稿第 6-7 页、原评审第 4-5 页。

**确定的算术与可能的取整。** 投稿第 6 页表 4 中 MemoryOS 的 1,889k + 939k = 2,828k，
但 total 是 2,868k，差 40k；需要原始记录或定义解释。Mem0 与 LightGMEM 的对应差值均为
1k，可能来自独立取整。不能因为发现一个错就否定正确的 Zep 成本比：调用比约 58.0、
token 比约 12.4、时间比约 151.6。

**重复实验要求。** 投稿第 7 页第 5.5 节与表 6 已有去除社区检索的变体，LLM-J=0.822。
本次报告 R6 再要求“去除社区检索”不够精确；应先承认该控制，再追问未隔离的
cross-encoder 和图评分，以及两表的共同评测口径。这条来自对自身输出的复核。

**文献时间边界。** paperreview.ai 列出大量新系统；EnSIMem 的首次公开日期为 2026-09-23，
来源为上述 arXiv 原始记录。原评审 PDF 第 1 页显示该投稿于 2026-07-20 提交。
Inference: 后续公开工作可用于当前修订定位，但不能据此判原投稿当时遗漏它；还须确认
被评估的稿件版本。不能以文件名“0729”替代实际版本/投稿时间。

## 回放与验证边界

使用 [review-calibration.md](../../tests/fixtures/review-calibration.md) 的已供片段进行
fresh-session 回放；不要同时提供本页答案。核验是否发现重要数字问题、区别覆盖子集与总量、
对齐表格口径、保留随机性解释、识别已做实验、控制文献时间边界及补充材料未知项。
允许不同的有条件推荐；不以同意某位审稿人的接受/拒稿结论作为通过标准。

2026-10-01 回放记录见 [原始输出摘录与验证记录](../../tests/replays/review-calibration-20261001.md)。
观察：旧画像的回放能识别机制风险、统计与资源协议问题，但未呈现数值复算；仅增加方法说明的
两次回放仍遗漏该动作。接入执行型数值助手后，一次 fresh-session 回放实际运行核查并指出
40k 加总不一致，同时将 1k 差值与 58.0 倍显示值分别处理。
Inference: 可执行核查比单纯扩充检查清单更能支持此例的数值审计；这些次数不足以量化泛化提升。

这是一个稿件的目的性案例。未复现实验、未审阅其技术补充材料，也没有多稿盲测证据；
不能据此声称通用审稿能力已得到统计验证。
