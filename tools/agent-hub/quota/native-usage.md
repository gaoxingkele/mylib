# Claude Code 与 Grok 的本地试点额度来源

两种来源均通过现有 quota worker 回写标准化百分比和重置时间。配置必须显式选择来源并启用 native_enabled。账号、项目、worker、额度池和 origin_source 都取自试点登记，Hook 任务的来源与工具必须匹配。定时任务可没有 Hook 来源，但仍核对账号三元组及本地数据来源。两种适配器都要求观测时间达到领取任务对应的入库时间，且距离采集时不超过 15 分钟。过期重置窗口会从本次结果中移除。无可用结果时沿用既有失败状态和最近有效记录。

## Claude Code statusLine

使用 Claude Code 官方 statusLine 输入的 rate_limits.seven_day 和 five_hour。两者的 used_percentage 是使用比例，余量以 100 减去使用比例计算。resets_at 为 Unix 秒，转换为 UTC。API/gateway 账单、上下文剩余及文本信息不进入输出。该来源由已登录的试点 Claude Code 会话主动送出本地数据。 [Claude Code 官方 statusLine 文档](https://code.claude.com/docs/en/statusline#rate-limit-usage)

在本地 worker 配置加入下列字段。配置及状态数据库放在单独的限权目录，且只能由运行该账号的本地用户访问。示例中的账号、会话和版本需换成获授权的试点值。

    {
      "native_enabled": true,
      "project": "pilot",
      "account": "claude-seat-a",
      "pool": "included",
      "worker": "quota-pilot-usa",
      "origin_source": "pilot-claude-origin",
      "provider": "claude",
      "source": "claude_statusline",
      "claude_config_dir": "C:/AgentHub/claude-pilot-profile",
      "claude_session_id": "replace-with-pilot-session-id",
      "claude_version": "replace-with-exact-statusline-version",
      "observer_db": "C:/AgentHub/private/claude-observer.sqlite"
    }

将以下命令接入专用试点的 statusLine 脚本，stdin 由 Claude Code 提供。使用隔离环境的 Python，并确保能导入 agent_hub。已经使用 statusLine 的试点可在本地包装脚本中保留原命令和输出。配置目录由宿主明确设置 CLAUDE_CONFIG_DIR；操作者通过官方界面核对该目录的订阅账号。组件不会读取登录文件。

    python -m agent_hub.native_usage claude-statusline --profile C:/AgentHub/private/claude-quota.json

每个周期的首次值只建立对照。后续重绘、重复值和同一重置窗口内倒退的用量不会刷新时间。满足条件的变化记录本地接收时间。周额度与短周期分别核对观测时间，周额度没有入库后的变化时显示暂不可用。Claude statusLine 没有提供厂商采样时间，因此本地时间只能证明观察到一次变化。配置会话、版本或账号变更时，先重新核对登录并为新绑定使用新状态文件。完整 stdin、会话路径和账号登录数据均不进入数据库。 [Claude Code 更新时机](https://code.claude.com/docs/en/statusline#when-the-status-line-updates)

## Grok CLI

本机安装版本为 Grok 1.0.92（b06756fd6256）。其 usage --help 说明：省略会话 ID 时，usage --json 向后台读取套餐限额，可通过 --leader-socket 选择隔离 leader。公开参考资料未给出这条命令的响应结构。试点需先由操作员在授权环境核对一份数据，含官方账号标识、实际观测时间、百分比和周重置时间。未知格式、仅提供会话成本、或者缺少可核对账号/观测时间的响应不会生成成功快照。可用人工核对的官方用量导出作回退。 [Grok CLI 参考](https://docs.x.ai/build/cli/reference) · [Grok 用量说明](https://docs.x.ai/grok/faq#usage-and-limits)

配置常规项目、账号、池、worker 和 origin_source，设 provider 为 grok、source 为 grok_cli、native_enabled 为 true，并加入：

| 字段 | 填写方法 |
| --- | --- |
| grok_executable | 试点 Grok 可执行文件的绝对路径 |
| grok_version_line | 使用 grok --version 获得的完整文本 |
| grok_leader_socket | 已运行且已绑定试点账号的本地套接字绝对路径，文件名为 leader-试点名.sock |
| grok_account_id | 预期官方响应账号标识，留在本地配置 |
| grok_schema.shape_sha256 | 确认载荷的 JSON 结构摘要 |
| grok_schema.account_path | 官方账号标识所在字段路径，以 JSON 键数组表示 |
| grok_schema.observed_at_path 与 observed_at_format | 观测时间字段路径和格式，支持 unix_seconds 或带时区的 utc_iso |
| grok_schema.windows | 1 或 2 个周期。每个配置 period、window_minutes、used_percent_path、reset_path、reset_format。weekly 需 10080 分钟，short 小于 1440 分钟 |

仅对授权、脱敏且保留结构的样例计算结构摘要。

    python -m agent_hub.native_usage grok-shape --fixture C:/AgentHub/private/reviewed-shape.json

适配器确认 CLI 版本及本地试点套接字已经存在，然后使用固定 argv 与隔离工作目录调用。不会启动、替换或登录 leader。检测不到实际套接字的平台返回暂不可用，可在支持 Unix 套接字且运行试点 leader 的 WSL/Linux 环境中核对。响应内容只在本地内存解析；只回写批准的归一化字段。当前核验使用合成样例，没有进行真实账号查询或改动本机 CLI 配置。
