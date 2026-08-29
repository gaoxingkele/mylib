# -*- coding: utf-8 -*-
"""Request IEEE DataPort AWS S3 URIs from student collaborator (Ding Wei)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xmu_send import send_utf8_mail  # noqa: E402


def main() -> None:
    to_addr = "dingwei@stu.xmu.edu.cn"
    subject = (
        "【powergrid_benchmark 协作】请协助提供 IEEE DataPort 缺口数据集的 AWS S3 URI"
        "（约 36 GB）"
    )

    body = """丁威你好：

我们是厦大 powergrid_benchmark 项目组（电网 Benchmark 数据跟踪）。此前你方已协助开通 IEEE DataPort 订阅并完成 DPSYOR / DPSYFOR / IEEE9 TSA 等大批量 S3 下载（约 354 GiB，已校验入库）。感谢。

现对照国网重大专项与仓库跟踪目标（PG-T07 宽频/强迫振荡、PG-T13 构网 IBR 等），仍有若干 DataPort 数据集无法从公开页面自动解析 S3 路径，需你在已订阅账号下从「AWS S3」页签复制完整 URI，回传给我们用于本机 aria2 续传下载。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
一、需要你提供的 S3 URI 清单（按优先级）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

请登录 https://ieee-dataport.org/（需 Individual Subscription），进入各数据集页面 → 右侧或上方「AWS S3 URI」页签 → 点击「Copy All URIs to Clipboard」，将全文粘贴回复本邮件（或附 .txt）。

【P0 — 宽频 EMT / 强迫振荡 / PoW 测试库，合计约 36 GB】

1) IRTSD — IBR 富集输电网 EMT 事件数据（Open Access，但大文件仍走 S3）
   页面：https://ieee-dataport.org/open-access/irtsd-open-source-data-and-toolset-electromagnetic-transient-analysis-disturbances-and
   DOI：10.21227/mp6d-j677
   至少需要：
   - Event_Data.zip（约 29.56 GB）
   可选一并提供：
   - PSCAD.zip（约 15 MB）
   说明：脚本包 SENT_*.zip 我们已从 open-access 路径拉取；缺主数据 Event_Data。

2) Power system forced oscillation datasets（IBR 高频 FO 等，与已下 DPSYFOR 不同包）
   页面：https://ieee-dataport.org/documents/power-system-forced-oscillation-datasets
   DOI：10.21227/ksv8-sp77
   至少需要：
   - FO_datasets.zip（约 5.32 GB）

3) Test Cases Library — 强迫/持续振荡（含 14-bus PoW、GFL/GFM 次同步等）
   页面：https://ieee-dataport.org/documents/test-cases-library-forcedsustained-power-system-oscillations
   DOI：10.21227/a6hg-n822
   建议全部提供（合计约 0.8 GB）：
   - WECC179_model_and_data.zip（约 163 MB）
   - WECC240_model_and_data.zip（约 50 MB）
   - ISO-NE_data.zip（约 17 MB）
   - 14bus_data_PoW.zip（约 313 MB）
   - IEEE14_data_PoW.zip（约 313 MB，若与 14bus 重复可只给其一并注明）

【P1 — 非 DataPort S3，本邮件可不处理】
- OPFData（Google Cloud gs://gridopt-dataset/）— 项目组自行用 gcloud
- ACTIVSg（TAMU 填表）— 另行申请

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
二、期望回传格式
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

每条一行，标准 S3 URI 即可，例如：
  s3://ieee-dataport/data/xxxxxx/yyyyyy/Event_Data.zip

若页面提供的是带签名的 https://ieee-dataport.s3.amazonaws.com/... 长链接，也可原样粘贴（我们可转换或直接用 aria2 下载）。

请同时注明：
1) 你登录 DataPort 的 IEEE 账号是否仍为有效订阅；
2) 各文件在页面上显示的 Size（便于我们核对磁盘）；
3) 是否遇到「LOGIN TO ACCESS」仍无法看到 AWS S3 页签（如有请截图）。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
三、本地落盘目录（供你知悉，无需你上传文件）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

我们收到 URI 后将下载至：
  D:\\aicoding\\powergrid_benchmark\\data\\public_datasets\\grid_tracking\\datasets\\gap_dataport\\
    irtsd_event_data\\
    fo_ksv8\\
    oscillation_testcases_dataport\\

脚本：scripts/data_acquisition/download_dataport_gap_s3.py

当前 D 盘剩余空间约 93 GB，上述 P0 合计约 36 GB，空间足够。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
四、背景说明（为何需要这批数据）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- 已覆盖：机电频段 DPSYOR/DPSYFOR、IEEE9 图 TSA、SIIB-Time、EnEnv、OGE、PGLearn 14_ieee 等。
- 缺口：宽频 EMT（IRTSD）、IBR 强迫振荡 benchmark（ksv8-sp77）、含 GFM/GFL PoW 的振荡溯源测试库（a6hg-n822），对应国网指南中宽频振荡 / 构网型 IBR 研究方向。
- 详见仓库：data/public_datasets/grid_tracking/README.md

如有疑问可直接回复本邮件或联系 iamafan@xmu.edu.cn。

谢谢支持。

——
powergrid_benchmark 项目组
发件：iamafan@xmu.edu.cn
仓库：D:\\aicoding\\powergrid_benchmark
"""

    status = send_utf8_mail(
        to_addr,
        subject,
        body,
        from_display="powergrid_benchmark项目组",
    )
    print(status, flush=True)


if __name__ == "__main__":
    main()
