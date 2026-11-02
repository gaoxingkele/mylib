---
type: Review
title: AGMS and PV-BEV AAAI review distillation
status: active
updated: 2026-10-27
owner: llm
tags: [peer-review, aaai, calibration, case-study]
source_paths:
  - D:/BaiduSyncdisk/paperreview/aaai2026 时/aaai2027_37027 (anonymous).pdf
  - D:/BaiduSyncdisk/paperreview/aaai2026 时/AGMS.pdf
  - D:/BaiduSyncdisk/paperreview/aaai2026 时/AGMS审稿意见.docx
  - D:/BaiduSyncdisk/paperreview/aaai2026 时/6cabd873ce605ddf47b9c1d228b2c341.jpg
  - D:/BaiduSyncdisk/paperreview/aaai2026 时/aaai2027_47175 (anonymous).pdf
  - D:/BaiduSyncdisk/paperreview/aaai2026 时/PV-BEV AAAI 第一轮审稿意见.docx
  - D:/BaiduSyncdisk/paperreview/tmp/pdfs/shi_20261001/AGMS-report.md
  - D:/BaiduSyncdisk/paperreview/tmp/pdfs/shi_20261001/PVBEV-report.md
source_urls: []
confidence: medium
---

# AGMS 与 PV-BEV：从 AAAI 评审中学习审查动作

两篇都是给时的 BEV 感知稿。AGMS 用的是 AAAI-27 匿名稿
`aaai2027_37027`（与同目录 `AGMS.pdf` 同文）。PV-BEV 用的是
AAAI-27 匿名稿 `aaai2027_47175`，标题为 Geometry-Preserving BEV
Representation Learning via Point-Voxel Collaboration。同目录较晚的
`PVBEV.pdf` 是另一份 CVPR 投稿，不作为这轮拒稿意见的对照稿。

这里只吸收可复核的审查动作。官方评分、均分和拒稿态度不是方法有效性的
标签，也不写成 AAAI 的数值门槛。2026-10-01 的 Paper_CCF 独立评审已经读过
稿件；本页是对照后的蒸馏，不是盲审。方法入口：
[evidence-calibrated-review.md](../evidence-calibrated-review.md)。

## 材料里实际有什么

AGMS 意见文档含五份 Program Committee 评审，外加一份不计入这五份的 AI Review，
以及 2026-09-25 的 Program Chairs 说明：稿件仍在 AAAI-27 流程中，Phase 2
结束、rebuttal 打开前才给齐评审。五份评分是 VUjG 5、dTce 6、6mLV 5、Sbx6 7、
5Hin 5，置信度 4、4、3、4、4。截图上的平均分 5.60、平均置信度 3.8 与这五份
一致。截图右侧状态只露出 “No Re”，不能当成完整决定。

PV-BEV 文档是两份第一轮文字意见，没有贴出分数或元决定。用户将它们标为
第一轮拒稿意见。两份 Justification 都认为核心主张未被证立。下面不把这个
态度改写成一个分数。

## AGMS：可吸收的动作

| 来源 | 学到的审查动作 | 在本稿上的核对 |
|---|---|---|
| VUjG、AI Review；稿第 4 页式 (13)–(15) | 同一射线上的矩协方差秩至多为 1，却写进二维逆。把“公式未闭合”和“实现必然失败”分开，并允许正文漏写 footprint 或正则 | 式 (14) 只对射线上的深度点求协方差，式 (15) 直接使用投影协方差的逆。代码是否加了横向尺度，本地看不到 |
| VUjG、AI Review；式 (17) 前 | 多相机 alpha 合成要写共同排序标量。相机深度不能直接互比 | 正文写按 “their depths” 做 front-to-back，没有定义该深度属于哪一个坐标系 |
| dTce | 若偏离该表示的常规合成方向，同时写明偏离了什么、为什么 | 3DGS 常见是 back-to-front。本稿写 front-to-back。这是惯例差，不是单凭方向就能判渲染错误 |
| VUjG、6mLV、Sbx6、5Hin；表 6 | 累积消融不能把 mixture、opacity、过滤和 diversity 算成同一个机制。优先要已有的 K=1、去掉 diversity、或分量可视化；rebuttal 不必新开实验 | 表 6 为 42.8 → 43.2 → 43.5 → 43.9。OGMS 一步是 0.4。没有分量深度或 opacity 图 |
| VUjG；图 3、图 4 | 只有预测和真值的定性图不能证明相对基线的遮挡改进。距离曲线若不拆遮挡、重叠或天气，就不能支撑这些解释 | 图 3、图 4 的这一限制来自评审描述；本页没有逐像素重读原图 |
| 5Hin；表 4 | 效率主张同时给绝对差和相对差 | 80.2 到 72.6 FPS，绝对少 7.6 FPS，相对约 9.5%。对应 IoU 是 38.3 到 39.0，不要和摘要里的 1.4 点混用 |
| dTce | 改编来的标准构件要引用原工作。缺引用是署名和清晰性问题 | 稿中检索不到 Swin。窗口注意力是否就是 Swin，本页不另下结论 |
| 摘要与表 1、表 6 | 家族级 SOTA 先核对同族方法，再核协议是否同一过滤和分辨率。别人评审里的外部数字，在打开原文前保持未验证 | 摘要把 +1.4 限定为 unprojection-based，对应可见性过滤、448×800 下 GaussianLSS 46.1 到 47.5。稿中没有 GaussianBeV。AI Review 给出的 43.9 / 50.3 未在本轮打开原文核对 |

## AGMS：不要继承的断言

**均分不是门槛。** 5.60 只描述这五份评分。Sbx6 给 7 并认为结果足以接收，
同时仍要求 OGMS-only、K 的代价曲线和分量可视化。7 分没有证明多峰深度
已经被隔离。VUjG 给 5，重点是协方差和排序。dTce 给 6，重点是符号、
warping 和引用。不能把这些理由折成一条“增量工作一律拒”的规则。

**表 6 的 0.5% 不是已经坐实的四舍五入。** 表内 43.2−42.8=0.4 个 IoU 点。
正文写 “0.5% IoU gain”，下一步又写 “0.3%”，而 43.5−43.2=0.3 个点。
0.4/42.8 也不是 0.5%。单位笔误和未展示的原始值都仍可能。AI Review 把
它说成 “0.5 points” 改写了稿子里的百分号。

**224×448 与 EN-64 是配置不一致，不是结果作废。** 实现和表 1 使用
224×480 或 448×800，骨干写 EfficientNet-B4 / EN-b4。表 6 标题写
224×448，但 42.8 和 43.9 与表 1 里 224×480、可见性过滤那一列相同。
表 5 把三行都标成 EN-64。先要求逐表配置，不要直接宣布数字不可用。

**GaussianBeV 的数字不能直接拿来否定摘要。** 它不在本稿参考文献里。
在核对原文的分辨率、过滤阈值和是否同属 unprojection 之前，它只是一条
必须去核的同族文献假设。表 1 里 PointBeV 在高分辨率过滤设定下是 47.6，
AGMS 是 47.5；这足以阻止“所有列都第一”，但不能在 Type 列读不清时
把 PointBeV 改判进 unprojection。

**全因子消融、另一个相机阵列、标定噪声扫描不是录用条件。** VUjG 写明
rebuttal 不要求新实验，只要已有证据。Sbx6 的愿望清单即使出现在一份
接收意见里，也仍然是扩展项。

## PV-BEV：可吸收的动作

| 来源 | 学到的审查动作 | 在本稿上的核对 |
|---|---|---|
| 两份评审；式 (2)–(4) 与实现段 | 批评量化时保留稿子自己的限定语，并算出格子边长 | 范围 [−54, 54] 米、180 格，格子约 0.6 米，同格特征平均。正文把“不额外量化”限制在 feature extraction stage。标题级 geometry-preserving 比这句宽 |
| Review 2；第 6 页 | 预训练要记下任务，并看比较系统有没有同一初始化。稿子自己的归因句算直接证据；公开 checkpoint 的数据集是另一层推断 | 实现段写 PTV3 用 official pretrained checkpoint，VoxelNet 用 BEVFusion 权重。后文把 mAVE/mAAE 部分归因于 PTV3 的 semantic segmentation pre-trained weights。稿子没有写该 checkpoint 就是 nuScenes 语义标签 |
| 两份评审；表 1、表 3、表 4 标题 | 设计选择标在 test 上时，追问提交次数和是否先在 val 冻结。标题不是泄漏证明 | 三张表标题都写 nuScenes test set。表 2 分割写 validation。本地没有 evaluation-server 记录 |
| Review 1；表 4 与式 (19) | 同一查询、同一距离下，精确 KNN 的半径内命中不应少于其候选子集。覆盖率高于精确行，说明查询或度量可能不同 | direct KNN 的 RCR/VNR 为 0.435/0.426，Hilbert 为 0.441/0.437。各行是否同一 checkpoint，稿子没写 |
| Review 2；式 (19) | 若模块承载核心主张，报告空返回比例。低于一半是机制事实 | 表 4 每一行 RCR 都低于 0.5。Hilbert 0.441 表示大约 56% 的参考点没有半径内邻居 |
| 两份评审；实现段与表 4 段 | 正文窗口和实验预算冲突时，问最终模型用哪一个 | 实现段 2L=6，表 4 公平比较写总预算 2L=8，Hilbert 行复现主结果 70.1 mAP |
| Review 1；表 2 与第 6 页 | “全部类别最高”必须带模态限定 | 该句没有模态限定。LiDAR 各行里 PV-BEV 六类都高于所列表内 LiDAR 方法。对整张表不成立：X-Align 的 mIoU 为 0.580，PV-BEV 为 0.537；X-Align 在 Drivable、Ped.Cross、Stop Line、Carpark 四类更高 |
| Review 2；参考文献与表 1 | 先对参考文献标题、稿子自己的描述和表内 Modality 单元格 | 参考文献标题是 “LiDAR-Centric Multi-Modal Fusion”。相关工作也写 multi-modal。表 1 把 BEVDilation 标成 LiDAR，并当作 LiDAR 组 mAP 的前最佳。被引论文的真实设定本轮没有打开 |
| Review 1 | 清单若在材料里，逐条对稿子；没有清单文本就不要写成已观察到的冲突 | 这份 9 页 PDF 没有 reproducibility checklist 正文。Review 1 所说的 yes/N/A 冲突在本地稿里不可核 |

## PV-BEV：不要继承的断言

**“X-Align 只领先两类”是数错的。** 按表 2 显示值，X-Align 高于 PV-BEV 的是
四类，不是两类；两类上 PV-BEV 更高，即 Walkway 与 Divider。相机 BEVFusion
的 mIoU 0.566 也高于 0.537。正确动作是重数每一列，而不是沿用审稿人的胜负计数。

**“大约十五次 test 提交”是由表行数推断的。** 本地没有服务器日志。标题可以
要求作者解释选择协议，不能写成已经发生的测试集调参。

**“比 VoxelNet 更粗”还缺体素边长。** 0.6 米是 BEV 格子，不是已与体素分支
比较过的结果。稿子没有给出 VoxelNet 的 voxel size。

**“official checkpoint = nuScenes 语义分割标签”是审稿人的识别。** 稿子明确
写出的是 semantic segmentation pre-trained weights，以及它被用来解释
mAVE/mAAE。数据集名称要单独标注来源。

**点云分支崩溃和薄结构增益是有用证据。** Review 2 把 point-only 明显低于
voxel、以及 divider / crossing / stop line 上的增益当作几何假设的正面证据。
不要因为归因不干净就抹掉这些已经报告的结果。混合不同曲线族会变差，也是
稿子已经写出的负结果，不应再要求一份“曲线组合实验”。

**拒稿态度不是清单。** 两份意见把验证集选择、同查询检索、预训练对齐和
收窄表述放在一起。系统级 FPS、全超参扫描和另一数据集是扩展。几何主张
缺少直接几何指标，这是证据缺口，不是“检测数字本身不成立”。

## 相对 2026-10-01 独立评审

当时的 AGMS 报告已经分开写了秩亏协方差、跨相机排序、累积消融、
224×448 / EN-64，以及 0.4 与正文 0.5 的差异。这轮补上的是：效率用相对降幅、
定性图没有基线、front-to-back 相对常规 3DGS 的方向差、改编模块的引用，
以及同族遗漏文献必须先当假设。不要把当时对 0.5 的取整解释说成已证实。

当时的 PV-BEV 报告已经写了窗口不是精确近邻、Hilbert 覆盖高于 direct KNN
的替代解释、2L 冲突、test 标题不等于泄漏、0.6 米格子仍会聚合，以及
“全表最高”不成立。这轮补上的是：RCR<0.5 表示核心采样大多空返回；
预训练任务要随稿子自己的归因句一起读；参考文献标题和 Modality 列冲突；
清单不在 PDF 里就不能复述成已核冲突。当时写 X-Align 四类更高，比
Review 2 的“两类”准确，应保留重算结果。

## 边界

没有重跑实验，没有打开 GaussianBeV 或 BEVDilation 原文，也没有把这两篇
做成 fresh-session 回放。两篇同领域稿件不能证明 AAAI 的通用接收线。
Phase 1 的早期意见可以被修改日期更新；修改日期本身不表示分数已经改变。
