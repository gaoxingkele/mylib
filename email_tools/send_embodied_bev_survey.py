# -*- coding: utf-8 -*-
"""Send embodied-AI + BEV/point-cloud dataset survey email (UTF-8)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xmu_send import send_utf8_mail  # noqa: E402


BODY = """师友通你好：

现将「具身智能（Embodied AI）数据集」与「点云 / BEV 感知数据集」的基本情况，以及近五年（约 2021–2026）采用这些数据的代表性文献，整理如下，供选题与数据选型参考。

说明：
1）具身智能与自动驾驶 BEV 是两条相对独立的数据生态；IEEE DataPort 上仅有零散机器人条目，主流不在 DataPort。
2）下列文献均为领域内高频引用的公开工作（含 arXiv / 会议正式版）；规模数字以各项目官网/论文为准，会随版本更新。
3）本稿侧重「常用哪些数据、近五年谁在用」，不是穷尽式文献计量；若需某子集的完整引用列表，可再针对性检索。

════════════════════════════════════
第一部分：具身智能数据集概况
════════════════════════════════════

一、真机操作 / 跨本体（当前主战场）

1）Open X-Embodiment（OXE）
   - 性质：把全球多实验室真机数据统一到 RLDS 格式的「总库」。
   - 规模（论文/官网口径）：约 60+ 既有数据集汇总；100 万+ 轨迹；约 22 种机器人本体；数十个机构贡献。
   - 入口：https://robotics-transformer-x.github.io/
   - 子数据集完整表：
     https://docs.google.com/spreadsheets/d/1rPBD77tk60AEIGZrGSODwyyzs5FgCU9Uz3h-3_t2A9g
   - 代码/说明：https://github.com/google-deepmind/open_x_embodiment

2）BridgeData / BridgeData V2
   - 侧重：桌面/厨房类操作，语言标注与成功标签较友好；WidowX 等平台常见。
   - 常作为 OXE 混合物中的重要组成部分。

3）DROID（Distributed Robot Interaction Dataset）
   - 规模口径：约 7.6 万轨迹、约 564 场景、多机构统一硬件（Franka + 固定相机配置）。
   - 特点：场景「野外」多样性强，近年常被用于微调 OpenVLA / π0 等通用策略。
   - 论文：arXiv:2403.12945（2024）

4）RT-1 训练数据、RoboNet、Language Table、BC-Z、RoboTurk、RH20T、FurnitureBench、TACO 等
   - 多数已（或部分）并入 OXE；单独使用时请按 OXE spreadsheet 核对许可与引用。

二、第一人称 / 人类演示（给 VLA 视觉–语言先验）

1）Ego4D：大规模自我中心视频（Meta 等，CVPR 2022 起广泛使用）
2）EPIC-KITCHENS：厨房第一人称活动
3）Something-Something 等：动作识别（偏视频理解，非直接机器人控制）

说明：这类数据通常没有机器人关节动作；训练策略时常配合手部跟踪或逆动力学模型（IDM）。

三、仿真环境与基准（可交互、可大规模采样）

| 名称 | 侧重 |
|------|------|
| Habitat / HM3D / Gibson / Matterport3D | 室内导航、具身感知 |
| AI2-THOR / ProcTHOR / ALFRED | 交互式家居、语言指令 |
| BEHAVIOR / BEHAVIOR-1K | 长程家务活动基准 |
| ManiSkill / ManiSkill2/3 | 可泛化操作 + 大量演示 |
| Meta-World / RLBench / RoboSuite / Isaac Lab | 桌面操作、仿真 RL |
| CALVIN / LIBERO | 语言条件操作、终身/多任务学习 |

四、人形 / 移动操作（近年增长快，开放程度不一）

- AMASS 等人体动作库（常做人形运动先验）
- 各厂商/联盟人形与移动操作数据集（Agibot World、Unitree 相关发布等）：许可与下载渠道变化快，使用前务必核对官网条款（此处不展开具体版本号，以免过时）

五、IEEE DataPort 上的相关条目（零散，非主库）

可检索到例如：DARP（双臂 RGB-D 感知）、CREATE（移动机器人多模态）、双臂布料操作等。
入口：https://ieee-dataport.org/ （关键词 robot / manipulation）
覆盖面远小于 OXE，一般作补充而非主训练集。

════════════════════════════════════
第二部分：近五年具身智能——「采用该数据的文献」代表作
════════════════════════════════════

（按「数据集 → 代表工作」组织；年份约 2021–2026）

【OXE / 跨本体】
- Open X-Embodiment: Robotic Learning Datasets and RT-X Models
  arXiv:2310.08864（2023）；项目页同上
  贡献：发布 OXE 总库；在混合数据上训练 RT-1-X / RT-2-X，验证跨本体正向迁移。
  评测/训练数据：OXE 混合物（含 Bridge 等子集）。

【BridgeData V2】
- Walke et al., BridgeData V2: A Dataset for Robot Learning at Scale, 2023
  被 OXE、后续 RT-X / VLA 工作大量引用与混训。

【DROID】
- Khazatsky et al., DROID: A Large-Scale In-the-Wild Robot Manipulation Dataset, arXiv:2403.12945, 2024
  数据本身 + 配套策略实验；后续 OpenVLA / π 系列等常作微调数据（以各论文实验设置为准）。

【通用机器人策略（多在 OXE±DROID/Bridge 上训或微调）】
- Octo Model Team, Octo: An Open-Source Generalist Robot Policy, 2024（多在 OXE 风格数据上预训练，待结合原文确认具体混合物）
- OpenVLA 等工作（2024）：开源视觉–语言–动作模型，预训练数据以大规模机器人轨迹混合物为主（通常声明基于 OXE 等；细节以原文数据章节为准）

【自我中心 / 导航仿真】
- Ego4D 数据集论文及后续挑战赛相关工作（CVPR 2022 起）：自我中心理解、手–物交互等
- Habitat 系列环境论文及后续导航/重排工作：仿真具身智能主流平台之一
- ALFRED、BEHAVIOR、ManiSkill 各自基准论文 + 大量跟进方法（2021 后持续有工作）

选型建议（具身）：
- 要做「通用操作策略 / VLA」→ 以 OXE 为预训练底座，再用 DROID / 自采数据微调。
- 要做「导航 / 语言家务」→ Habitat + ALFRED/BEHAVIOR。
- 要做「可复现仿真操作」→ ManiSkill / LIBERO / CALVIN。

════════════════════════════════════
第三部分：点云 / BEV 相关数据集概况
════════════════════════════════════

BEV（Bird’s-Eye-View）感知是自动驾驶 3D 检测、分割、占据预测的主流表示之一；「点云相关」涵盖：纯 LiDAR、相机–LiDAR 融合、以及用 LiDAR/地图监督的相机 BEV。

一、主赛道数据集

1）nuScenes（Motional）
   - 传感器：1×LiDAR + 5×Radar + 6 路相机（约 360°）+ IMU/GPS
   - 规模口径：1000 个约 20s 场景；大量 3D 框；另有 lidarseg、地图等扩展
   - 任务：3D 检测/跟踪、BEV 地图分割、点云语义等
   - 官网：https://www.nuscenes.org/
   - 地位：环视相机 BEV 与多传感器融合论文的**默认主榜**

2）Waymo Open Dataset（Perception）
   - 多 LiDAR，深度质量好；相机覆盖约前/侧（约 ~240°，非严格 360° 环视）
   - 规模大、标注密；另有 3D 语义、occupancy、scene flow 等扩展
   - 官网：https://waymo.com/open/
   - 地位：点云检测与融合的另一主榜；严格 360° 环视相机 BEV 时需注意 FOV 差异

3）Argoverse 1 / 2
   - LiDAR + 环视/立体相机 + HD map
   - 场景规模通常小于 nuScenes/Waymo；部分 BEV/预测工作作辅榜

4）KITTI / KITTI-360
   - 经典前视 + Velodyne 点云；规模相对小
   - 现代环视 BEV 主文较少单用；适合方法原型或历史对比

二、偏点云 / 大规模 / 占据

| 数据集 | 用途要点 |
|--------|----------|
| ONCE | 大规模城市场景 LiDAR 3D 检测 |
| Lyft Level 5 | 多传感器，格式接近 nuScenes 生态 |
| SemanticKITTI | 逐点语义分割 |
| nuScenes-lidarseg | nuScenes 点云语义 |
| Occ3D / OpenOccupancy 等 | 占据栅格基准（多基于 nuScenes/Waymo 衍生） |
| Waymo Occupancy / 3D 语义 | 占据与点云语义 |

三、地图 / 车道 BEV

- nuScenes map、Argoverse HD map、OpenLane 等：BEV 车道与地图元素分割/矢量建图
- 常与检测任务共享同一驾驶数据集（尤其 nuScenes）

选型建议（BEV/点云）：
- 环视相机 BEV 或相机–LiDAR 融合（BEVFusion 一类）→ 优先 nuScenes
- 纯点云或强调多 LiDAR → Waymo / ONCE / KITTI
- Occupancy → Occ3D 等衍生基准 + Waymo/nuScenes 相关标注

════════════════════════════════════
第四部分：近五年 BEV / 点云——「采用该数据的文献」代表作
════════════════════════════════════

下列均为近五年高频基线；主实验数据集以论文声明为准。

【相机 BEV 检测（主用 nuScenes，部分报 Waymo）】
1）BEVDet: High-performance Multi-camera 3D Object Detection in Bird-Eye-View
   Huang et al., arXiv:2112.11790, 2021
   数据：nuScenes（典型）

2）BEVFormer: Learning Bird's-Eye-View Representation from Multi-Camera Images via Spatiotemporal Transformers
   Li et al., arXiv:2203.17270；ECCV 2022
   数据：nuScenes、Waymo
   后续扩展版讨论 LiDAR–Camera 融合 BEV（如 TPAMI 相关更新，见 IEEE Xplore / 作者主页）

3）PETR / PETRv2 等（2022–）：query 式多相机 3D 检测，nuScenes 主榜常见

【相机–LiDAR 融合（统一到 BEV）】
4）BEVFusion: Multi-Task Multi-Sensor Fusion with Unified Bird's-Eye View Representation
   Liu et al. (MIT-HAN Lab), arXiv:2205.13542；ICRA 2023
   数据：nuScenes、Waymo
   任务：3D 检测 + BEV map segmentation

5）另有同名/相近的 BEVFusion 融合框架工作（Liang et al., arXiv:2205.13790, 2022）
   引用时请区分作者与代码仓库，避免混淆。

【纯点云检测（常与 BEV 柱体/体素表示相关）】
6）CenterPoint 等中心点检测器：nuScenes / Waymo 上长期作为强 LiDAR 基线（原作略早，但近五年对比表仍高频出现）
7）PointPillars、SECOND、VoxelNet 一脉：KITTI / nuScenes / Waymo 延续使用

【占据 / 多任务 BEV】
8）SurroundOcc、OccFormer、Occ3D 相关工作（约 2023–2024）：多在 nuScenes（及衍生占据标签）上报告
9）端到端自动驾驶（如 UniAD 等，2023 前后）：感知–预测–规划一体化，底层感知常基于 nuScenes 生态

【数据集本身（近五年仍被大量引用）】
- Caesar et al., nuScenes: A multimodal dataset for autonomous driving, CVPR 2020（略早于五年边界，但近五年几乎所有 BEV 文必引）
- Sun et al., Scalability in Perception for Autonomous Driving: Waymo Open Dataset, CVPR 2020（同上）

════════════════════════════════════
第五部分：对照小结（方便选题）
════════════════════════════════════

| 方向 | 首选数据 | 近五年代表方法线 |
|------|----------|------------------|
| 跨本体操作 / VLA | OXE → DROID/Bridge 微调 | RT-X、Octo、OpenVLA 等 |
| 仿真导航/家务 | Habitat、ALFRED、BEHAVIOR | Habitat 挑战赛跟进工作 |
| 仿真操作技能 | ManiSkill、LIBERO、CALVIN | 各基准官方 baseline + 跟进 |
| 环视 BEV 检测 | nuScenes | BEVDet、BEVFormer、PETR… |
| 多传感器融合 BEV | nuScenes (+ Waymo) | BEVFusion（MIT）等 |
| 纯点云检测 | Waymo / ONCE / KITTI | CenterPoint 及后续改进 |
| 占据预测 | Occ3D 等 / Waymo occ | SurroundOcc、OccFormer 等 |

════════════════════════════════════
获取与许可提示
════════════════════════════════════

- OXE / DROID / Bridge：多为 CC-BY 或各子集自有许可，按 spreadsheet 引用对应论文。
- nuScenes：非商业研究条款需阅读官网；商业用途需另行联系。
- Waymo Open：需注册并遵守使用协议。
- IEEE DataPort Standard 数据集需订阅或 Society 权益（与电网 DataPort 缺口同一机制，但具身/BEV 主流不依赖它）。

若你需要下一步，我可以再补一版：
A）仅「可公开下载直链 + 体量估算」清单；或
B）按你指定子方向（如只做 VLA，或只做 BEVFusion 复现）缩成 5–8 篇精读列表。

此致
iamafan@xmu.edu.cn
（自动整理发送，UTF-8）
"""


def main() -> None:
    to_addr = "shiyoutong@stu.xmu.edu.cn"
    subject = (
        "【数据集调研】具身智能数据 + 点云/BEV 数据集概况"
        "及近五年代表性文献（UTF-8）"
    )
    status = send_utf8_mail(
        to_addr,
        subject,
        BODY,
        from_display="厦大邮箱-数据集调研",
    )
    print(status)
    print(f"Chars: {len(BODY)}")


if __name__ == "__main__":
    main()
