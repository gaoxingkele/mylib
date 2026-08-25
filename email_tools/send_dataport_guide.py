# -*- coding: utf-8 -*-
"""Send DataPort student-account guide email via XMU SMTP."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xmu_send import send_utf8_mail  # noqa: E402


def main() -> None:
    to_addr = "dingwei@stu.xmu.edu.cn"
    subject = (
        "【操作指南】用学生 IEEE 账号开通 DataPort 并下载电网缺口数据集"
        "（DPSYOR / DPSYFOR / IEEE9 TSA）"
    )

    body = """丁伟你好：

我们在 powergrid_benchmark 仓库做电网 Benchmark 跟踪时，公开直链数据集已基本下完；仍缺 3 个挂在 IEEE DataPort 上的电力数据集（Standard，非 Open Access）。免费 DataPort 账号下不了。下面写清：如何用「学生 + IEEE」路径低成本开通权限，并把文件下到仓库统一目录。

一、需要下载的数据集
1) DPSYOR（振荡响应）
   https://ieee-dataport.org/documents/dpsyor-dataset-power-system-oscillation-responses
   DOI: 10.21227/ebwk-j667
   体量：多个 zip/7z，单包约 0.1–34 GB

2) DPSYFOR（强迫振荡）
   https://ieee-dataport.org/documents/dataset-power-system-forced-oscillation-responses
   DOI: 10.21227/q65f-zt55
   体量：更大，单包约 22–78 GB

3) IEEE9 TSA 2 万场景图数据集
   https://ieee-dataport.org/documents/20000-scenario-graph-dataset-full-generator-trajectories-transient-stability-assessment
   对应论文 arXiv:2608.18318
   体量：约 2.7–2.85 GB（单个 .mat / HDF5）

建议本地目录（下载后放到）：
  D:\\aicoding\\powergrid_benchmark\\data\\public_datasets\\grid_tracking\\datasets\\dataport\\
    dpsyor\\
    dpsyfor\\
    ieee9_tsa\\

二、关键结论（付费/免费怎么选）
- DataPort 分两类：Open Access（免费可下）与 Standard（需订阅）。
- 上述 3 个都是 Standard。
- 个人订阅约 USD 40/月。
- 更划算：任意 IEEE Society 会员登录 DataPort 后，通常自动获得个人订阅（约合 480 美元/年）。
- IEEE Senior Member 等级本身不送 DataPort；关键是「有没有 Society」。
- 学生路径：先 IEEE 学生会员，再加 PES（或其它 Society），再登录 DataPort。

三、推荐路径 A：学生 IEEE + PES → DataPort 免费订阅（优先）

步骤 1：确认/注册 IEEE 账号
- 打开：https://www.ieee.org/
- 用个人邮箱注册或登录 IEEE Account（可与 XMU 学号邮箱关联，但不是必须）。
- 学生会员：https://www.ieee.org/membership/join/index.html
  选择 Student / Graduate Student，按地区交 IEEE 学生年费。

步骤 2：加 IEEE Power & Energy Society（PES）
- 已是 IEEE 学生会员后，在会员资料中 Add Society。
- PES 学生 Essential 加购官方宣传约 USD 1/年（以结账页为准）。
- PES 入口：https://ieee-pes.org/
- PES 会员权益宣传中包含 Free IEEE DataPort。

步骤 3：激活 DataPort
1. 打开 https://ieee-dataport.org/
2. 用与 Society 绑定的同一 IEEE 账号登录（Login / SAML IEEE）。
3. 登录后应自动开通 Individual Subscription。
4. 打开上面三个数据集页面，确认出现 Download / LOGIN TO ACCESS 变为可下载。

步骤 4：下载
- 浏览器直接下（适合 IEEE9 ~3GB）。
- 大包（DPSYOR/DPSYFOR）：订阅用户可在 DataPort 个人资料中查看 AWS S3 访问说明；复制带签名的下载链接后，可用本机 aria2 续传。
- 本仓库默认下载方式（有签名 URL 时）：
    python -m download_tools <URL> <输出路径>
  或：
    aria2c --all-proxy=http://127.0.0.1:17890 --split=16 --max-connection-per-server=16 --continue=true -d <目录> -o <文件名> <URL>

四、备选路径 B：不办 Society，直接个人付费
1. 打开 https://ieee-dataport.org/subscribe
2. Individual Subscription，约 USD 40/月，信用卡/IEEE 结账。
3. 付款后返回 DataPort，再下上述数据集。
4. 下完可发邮件 contactcenter@ieee.org 取消续订（以官网 FAQ 为准）。

适合：只想短期下完、不想办 Society。

五、备选路径 C：学校机构订阅
1. 问厦大图书馆是否已订 IEEE DataPort Institutional。
2. 若已订：校园网/VPN + 学校认证后登录 DataPort。
3. 若未订：由图书馆联系 IEEE 销售，或邮件 dataport@ieee.org。

六、操作自检清单
[ ] IEEE 账号能登录
[ ] Memberships 里能看到 Student（或 Graduate Student）
[ ] 已添加至少一个 Society（建议 PES）
[ ] 登录 ieee-dataport.org 后，DPSYOR 页面可 Download
[ ] 文件落到 dataport\\dpsyor|dpsyfor|ieee9_tsa
[ ] 告知仓库维护者更新 manifest / CACHE_STATUS

七、找不到完整镜像时的说明
- DPSYOR / DPSYFOR：目前未见 Zenodo/HF/GitHub 全量镜像，基本只能 DataPort。
- IEEE9：DataPort 有现成 .mat；也可参考 GitHub 自再生（需 MATLAB + MATPOWER + Simscape）：
  https://github.com/drsupreme/ieee9-transient-stability-assessment-graph-dataset
- 临时代理（任务不同，不能替代）：仓库已有 SMIB PINN、GridSTAGE、LBNL PMU 等。

八、联系与回传
下载完成后请回复本邮件，说明：
1) 用的是路径 A / B / C；
2) 三个数据集各自是否成功、实际占用磁盘；
3) 本地最终路径。

如登录报错、Society 未自动开通 DataPort，把页面截图或报错原文发我，我再帮你排查。

相关仓库文档：
- docs/benchmark_design/grid_tracking_targets.md
- data/public_datasets/grid_tracking/README.md

谢谢。

——
发件人：iamafan@xmu.edu.cn
（电网 Benchmark 数据协作）
"""

    status = send_utf8_mail(
        to_addr,
        subject,
        body,
        from_display="电网Benchmark协作",
    )
    print(status, flush=True)


if __name__ == "__main__":
    main()
