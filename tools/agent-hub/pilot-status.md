# 0.2.81 隔离试点交付记录

本轮为本地试点实施。Windows、Android 及 mylib 服务按同一任务契约联调。生产更新频道和现役安装独立于该次构建。

| 总目标 | 本轮证据 | 现场放行还需验证 |
| --- | --- | --- |
| 跨机任务接手、并行复验 | 两项目隔离；真实 MCP 客户端提交 Codex→Claude 接手和 Grok 验证的合成事件；离线旧执行补传不改变现任；宿主安装、会话、代次与执行绑定 | 选定两台测试机和真实项目，验证实际工件访问、工具版本和源宿主注册 |
| 本地 wiki 与中央正文一致 | Hook 持久队列、SQLite 原子事件与回执、文档修订或撤回、备份轮换和恢复测试。已安装的 Codex 0.166.0、Claude Code 2.1.310、Grok 1.0.92 在各自隔离配置和本机模拟提供商下完成一轮，均实际触发 Hook 并写入对应 wiki 与待办 | 中转服务器独立业务实例、两台机器离线补传，以及独立存储上的恢复演练 |
| 全局额度及总管 | Codex app-server、Claude 用量窗口观察、Grok CLI 适配、手动官方快照；授权项目聚合、已绑定共享池去重及历史失效判断。中转与独立总管的两套真实回环 MCP、模拟模型和证据撤回验证通过 | 逐个账号与官方用量核对，确认绑定、原单位、下一次重置和新鲜度；真实美国主机与已选模型端点验收 |
| 桌面、安卓与目标窗口反馈 | 双端真实文档在 Edge 接收 SQLite 数据。普通终端准备草稿；桌面合成受控宿主确认、受理、回执丢失与第二客户端查证通过。安卓只读入口及独立包名 APK 已构建 | Android 手机/平板真机返回、软键盘、旋转和挂起恢复；真实试点用户确认及宿主接收。安卓写入放行需另过真机与宿主门槛 |
| mylib 与 RSI | 桌面本机目录可配置；固定版本查询、离线比较、保留集、影子观测、人工确认、工件哈希和加载回执在隔离场景验证 | 用授权的真实反例、独立验证和真实宿主加载回执证明一项改动的效用，再决定推广范围 |

## 已验证的本地交付物

SuperMonoAgent 的本地试点分支 `codex/agent-hub-pilot` 指向 `1c88cb4`。冻结的 0.2.80 公共 ZIP、可执行文件及 0.2.78 APK 的 SHA-256 均再次与原清单核对。

- Windows ZIP SHA-256 `7cd74773ae3e147148759adf2780e478c0982f705f4a07f23eb3337c4e17457c`；冻结 EXE 连接测试后台并以 WebView2 完成启动。[便携包](/D:/aicoding/supermonoagent/.omx/artifacts/agent-hub-0.2.81-pilot-20261122-052838-r2/products/windows/SuperMonoAgent-0.2.81-Pilot-Portable.zip) · [原生启动证据](/D:/aicoding/supermonoagent/.omx/artifacts/agent-hub-0.2.81-pilot-20261122-052838-r2/native-smoke.json)
- Android `dev.supermonoagent.mobile.pilot` 使用测试签名和独立包名，版本码 83，SHA-256 `ea905240fcdddf08235efe4c114cd294fbc4f9d27d9b2983b371b85467714598`。[APK](/D:/aicoding/supermonoagent/.omx/artifacts/agent-hub-0.2.81-pilot-20261122-052838-r2/products/android/0.2.81/SuperMonoAgent.apk) · [包校验清单](/D:/aicoding/supermonoagent/.omx/artifacts/agent-hub-0.2.81-pilot-20261122-052838-r2/verification.json)
- 两台模拟上报端、20 个会话。本地 MCP 回执至打开的驾驶舱显示 p95 为 1.395 秒，最大 1.411 秒，PTY 输入与 resize 帧为零。[测量记录](/D:/aicoding/supermonoagent/.omx/worktrees/agent-hub-pilot/.omx/artifacts/cockpit-pilot/20-session-latency.json)
- 默认关闭新功能时，账号、中继回放、剪贴板、文件传输、通知、编辑器、客户端更新等 130 项专项回归通过。另有 59 项会话与多主机专项通过。旧基线中两个安卓用例未展开辅助工具栏，桌面窄窗用例在弹窗遮挡期间断言底栏可见；测试现按真实入口交互并检验原行为。[兼容性报告](/D:/aicoding/supermonoagent/.omx/worktrees/agent-hub-pilot/.omx/artifacts/cockpit-pilot/legacy-regression.xml)
- [mylib 服务启动与权限配置](service.md) · [开发机 Hook](hooks/README.md) · [真实账号接入前的采集契约](quota/native-usage.md) · [RSI 版本管理](evolution-operator.md) · [时间与容量轮换](maintenance.md)
- [中央 MCP、Hook、额度与 RSI 服务源码包](/D:/aicoding/supermonoagent/.omx/artifacts/agent-hub-0.2.81-pilot-20261122-052838-r2/products/server/mylib-agent-hub-0.2.81-pilot.zip) · [本地交付清单及校验值](/D:/aicoding/supermonoagent/.omx/artifacts/agent-hub-0.2.81-pilot-20261122-052838-r2/delivery.json)

RSI 试点支持已有告警规则评测，以及对固定 skill/harness 工件的配对任务评测。合成工件验证了连续两次版本演进、受控宿主回调和回退。项目私有证据撤回时，关联试验会重新核对依赖。真实技能发布须有授权验证人、独立评测工件和实际窗口加载证明。

## 外部验收前提

登记两台允许启用试点的主机、项目和计费账号别名，通过私有配置给相应进程提供凭据，确认 Android 测试设备可用，并约定可接受的数据损失窗口和恢复时长。只在试点项目上逐个启用，回退时保持正在运行的原有 Agent 与草稿。真实模型、额度、跨国链路、生产推广和技能收益分别记录结果。

本机检查时未设置试点绑定及模型/用量服务的专用环境变量。现有公网技能 MCP 对匿名请求返回 401。ADB 因本机客户端与服务端版本不同自动重启了本机 ADB 服务，随后两次设备检查均未列出连接设备。
