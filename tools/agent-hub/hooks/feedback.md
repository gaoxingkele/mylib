# 窗口回馈与版本确认的隔离接入

桌面驾驶舱的「反馈到此执行」在用户已获得项目只读权限后可见。要从驾驶舱直接确认托管消息，中央 Hub 还需打开 `--enable-feedback`，并在私有授权文件为操作者配置 `tasks:read`、`feedback:confirm`、允许的 `accounts` 和 `feedback_hosts`（真实主机安装 ID）。桌面与第二设备可以使用相同 `subject` 的独立授权。凭据由用户在确认弹窗输入，仅在该弹窗存活期间使用。

源主机使用独立 `feedback:source` 凭据、允许的 `feedback_hosts` 及对应账号，连接 HTTPS/WSS 中转入口。浏览器的 Origin 和源主机指定的 Origin 均需列入已允许的来源。中央库只存确认的 sha256、目标、nonce 和核对状态。真正的文本由已登录源主机的 OP24 接受；源主机负责签收回执，仅它能标记中央记录的受理状态。

源主机管理员可在 SuperMonoAgent 状态目录创建 `cockpit-feedback.json`。在 Windows 使用仅当前用户可访问的目录；在 POSIX 上将文件权限设为 0600。仅向已经过源端核验的执行增加映射，交接、关闭或撤权时移除对应映射。配置文件应原子写入。各端使用一致的宿主安装 ID、托管窗口和会话 ID、进程代次及日志 ID。项目 Hook 配置的 `terminal_session_id` 指 SuperMonoAgent 会话；原生工具产生的 `session_id` 单独记录。

```json
{
  "authority": {
    "endpoint": "wss://relay.example.invalid/hub/feedback",
    "origin": "https://host.example.invalid",
    "token": "<source credential>"
  },
  "bindings": [{
    "owner_scope": "<source journal owner scope>",
    "project": "pilot", "task_id": "task-1", "attempt_id": "attempt-1",
    "host_installation_id": "<journal store host installation>",
    "window_id": "<source window>", "session_id": "<source terminal session>",
    "process_generation": "<process generation>", "journal_id": "<source journal>",
    "tool": "codex", "role": "primary", "account": "pilot-account"
  }]
}
```

在 `report_step` 里提交对应的 `host_installation_id`、`terminal_session_id`、`generation`、`journal_id` 和 `window_id`。操作员打开目标后再从任务详情选择此执行。普通终端支持「准备草稿」，最终发送由终端自己的输入界面处理。托管终端的确认绑定完整正文、当前执行、一次请求和 120 秒有效期。另一设备可以用同一用户身份查询原 nonce，并通过已授权源端核对是否收妥。接手或撤权后，原确认无法切换投递目标。

「此执行的 mylib 版本」使用独立 `evolution:confirm` 和 `evolution_hosts` 权限。先预览固定工件 SHA 与版本，再逐次确认。是否已加载以原执行的宿主证据为准。Android 试点先开放只读查看，手机确认流程须独立验收。
