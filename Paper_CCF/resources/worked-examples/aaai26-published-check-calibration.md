---
type: Review
title: AAAI-26 published-paper calibration of added review checks
status: active
updated: 2026-10-28
owner: llm
tags: [peer-review, aaai, calibration, published]
source_paths:
  - D:/aicoding/mylib/Paper_CCF/tests/fixtures/aaai26-published-ledger.json
source_urls:
  - https://ojs.aaai.org/index.php/AAAI/article/view/42441
  - https://ojs.aaai.org/index.php/AAAI/article/view/37238
  - https://ojs.aaai.org/index.php/AAAI/article/view/42484
  - https://ojs.aaai.org/index.php/AAAI/article/view/37580
  - https://ojs.aaai.org/index.php/AAAI/article/view/38238
confidence: medium
---

# AAAI-26 已发表论文对新增审查动作的校准

对象是 AAAI-26 主会已发表论文，不是投稿中的稿。目的是看新增检查在录用论文上
会成立、会空转，还是会误伤。五篇都来自 proceedings volume 40，下载日期
2026-10-28。数值用 `scripts/audit_review_numbers.py` 对
[aaai26-published-ledger.json](../../tests/fixtures/aaai26-published-ledger.json)
复算，18 项均为 `consistent` 或 `display_consistent`。这五篇不能代表全部
AAAI-26。

| 论文 | 用到的检查 |
|---|---|
| SPSC，view/42441 | 百分号是相对提升，还是 IoU 点数；模态分列 |
| Seeing in Double，view/37238 | 百分号是点数；同族基线；分辨率错字；效率；预训练；窗口注意力引用 |
| GUIDE，view/42484 | 50% 相对提升；同族方法；协方差是否秩亏 |
| HAT，*Rethinking the Spatio-Temporal Alignment of End-to-End 3D Perception*，view/37580 | 均值四舍五入；摘要必须对上具体阶段；碰撞率的相对百分号；预训练声明 |
| BEVDilation，view/38238 | 模态列与标题；SOTA 幅度的表格范围；体素与 BEV 格子；FPS 取舍；预训练数据集 |

## 百分号先对上两种算法，再决定有没有问题

SPSC 摘要写 mIoU 提升 12.0%、11.0%、4.8%，顺序是 multi-modal、LiDAR、camera。
表 1 注明 mIoU 以百分数显示。单帧最强对照分别是 OccMamba 25.1、L-OccMamba 22.7、
C-OccGen 14.5，SPSC 为 28.1、25.2、15.2。点数差是 3.0、2.5、0.7。相对变化
3.0/25.1、2.5/22.7、0.7/14.5 按三位小数四舍五入为 0.120、0.110、0.048。
摘要的百分号是相对变化。把它读成 +12.0 个 IoU 点会造出一篇录用论文里并不存在的错误。

Seeing in Double 写低分辨率下相对 GaussianLSS 为 +4.1% 和 +3.3%。表 1 的
224×480 两列是 42.4−38.3=4.1 和 46.1−42.8=3.3。这里的百分号等于点数差。
相对变化约 10.7% 和 7.7%，论文没有这么写。

GUIDE 写 instance occupancy mAP 21.61，比 SparseOcc 高 50%。表中 SparseOcc 为
14.40。点数差 7.21，7.21/14.40 按两位小数为 0.50。

HAT 摘要的平均 +0.7% NDS 和 +0.6% mAP，是表 3 三个检测器增益的均值：
NDS (0.7+0.9+0.4)/3=0.666…，mAP (0.5+0.5+0.9)/3=0.633…，一位小数分别是 0.7 和 0.6。
摘要的 +1.3% mAP 与 +3.1% AMOTA 对的是表 1 第二阶段 SparseDrive，不是第一阶段的
+0.2 mAP。碰撞率从 0.123 到 0.084，相对下降 0.039/0.123，按两位小数为 0.32，
与 “32%” 一致。

因此百分号有两种已经出现在录用论文里的合法读法。检查先同时算出点数差和相对变化，
再把句子绑到具体的行、阶段、模态和分辨率。对上其中一种，就不是单位错误。
两种都对不上，才保持未解决，像 AGMS 正文的 0.5% 那样。不要先改写单位。

## 录用论文里的严重度

**分辨率错一个数。** Seeing in Double 的表 1 和 Lyft 比较写 224×480，实现段、
消融和效率段写 224×448。消融最终 IoU 46.1 与表 1 里 224×480、可见性过滤那一列相同。
这是配置问题。消融数字仍然对得上另一张表的列，不能据此把表作废。

**效率取舍。** BEVDilation 表 1 相对 DAL 是 7.08 对 7.39 FPS，绝对少 0.31 FPS，
相对约 4.2%，同时 NDS/mAP 为 +1.0/+1.5。Seeing in Double 表 7 是 14 对 15 FPS，
IoU 为 42.4/46.1 对 38.7/44.0。两篇都把这写成有竞争力的效率。检查要报出绝对差、
相对差和同一行的精度。这个幅度本身不是拒稿条件。

**预训练。** BEVDilation 写明 ResNet-50 用 nuImage 预训练，并写 “following current
approaches”。Seeing in Double 写两个分支都用 ImageNet 预训练。HAT 写明 HAT 本身
没有预训练，并给使用了轨迹预训练的对照打了标记。写明初始化数据集，且没有把独有
初始化说成方法增益时，这项检查算完成。录用论文常常没有逐个基线的初始化列。
只有稿子把对照系统没拿到的初始化当成自己的贡献时，缺对照才进入主要问题。

**模态。** BEVDilation 的标题是 LiDAR-Centric Multi-Modal Fusion，表 1 的模态格是
L+C。论文自己的标题和表是一致的。后续稿若把这些数字标成 LiDAR-only，冲突的是
引用稿的单元格和这篇已发表来源，不是审稿人的猜测。

**SOTA 句子的附着范围。** 表 1 上 75.0/73.0 相对 DAL 的 74.0/71.5 确实是 +1.0 NDS
和 +1.5 mAP。表 2 更强骨干下，相对 MambaFusion 的 75.0/72.7 只有 +0.3 NDS 和
+0.7 mAP。正文把 “at least +1.0 and +1.5” 延伸到 “including those with more
powerful backbones”，超出了表 2。这是句子范围问题。两张表里该方法仍是所列最高行。

**不该启动的检查。** GUIDE 的协方差是 Σ=R S Sᵀ Rᵀ，尺度来自对角矩阵，不是由
同一条射线上的点生成的秩至多为一的协方差。秩亏求逆检查在这里不启动。五篇都没有
报告采样命中率，也没有改写多相机 front-to-back 顺序。空返回比例和合成方向检查
保持关闭。录用论文不需要为了通过审查而包含这些量。

**引用可以满足。** Seeing in Double 在使用 window cross-attention 时引用了
Liu et al. 2021。缺引用仍是署名和清晰性问题。同一领域的录用论文会在使用该构件时
给出出处。

**格子边长以论文所写为准。** BEVDilation 写出体素 (0.075 m, 0.075 m, 0.2 m)，
以及 XY 范围 [−54 m, 54 m] 上的 180×180 BEV 图。108/180=0.6 m 可以由正文算出。
SPSC 写出体素 0.2 m。Seeing in Double 写出 100 m×100 m、50 cm、200×200。
论文没写的边长仍然不能补。

## 边界

没有重做实验，没有核对补充材料里的图。图 3 的距离分箱增益只出现在图和正文句子里，
没有进入这次账本。表 4 的勾选列在文本抽取里换行，1.4% 那句因此没有放进审计。
五篇都是感知方向，用来校准这批新增检查，不能外推成 AAAI-26 的接收率或分数线。
