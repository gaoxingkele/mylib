# 开发机 Hook 客户端

在每次执行启动时设置进程级环境变量 `AGENT_HUB_BINDING`，指向操作者控制的 JSON 文件；各窗口有各自的绑定。以下为合成示例。把目录和柜台登记的名称换成实际值，配置文件、状态目录和写入凭据均放在项目库外的个人数据目录，使用仅当前用户可访问的目录权限。

```json
{
  "project": "pilot-a",
  "project_root": "D:/projects/pilot-a",
  "wiki_dir": "omx_wiki/agent-results",
  "state_dir": "D:/private/agent-hub/state",
  "endpoint": "http://127.0.0.1:8822/hub/mcp",
  "host": "pilot-host-a",
  "window": "pilot-terminal-1",
  "generation": "1",
  "task_id": "task-1",
  "attempt_id": "attempt-1",
  "account": "pilot-account",
  "tool": "codex"
}
```

可设置 `session_id` 锁定原生会话；若展示名称与制度内的稳定窗口 ID 不同，另填 `window_id`。显式接手用新的 `attempt_id` 和 `previous_attempt_id`。验证者使用 `role: "verify"` 和被测工件的 `artifact`，手工验证报告可附 `verdict`（pass、fail、unknown）。同一份绑定同时供原生 Hook 和投递进程读取。迁移绑定前先处理待同步记录，队列按绑定隔离。

## 试点调用

**跨机接手与并行验证。** 可用 `python -m agent_hub.attempts start --profile <本机配置> --binding <新的私有绑定文件> --artifact <工件版本>` 登记第一台机器上的执行。命令返回项目、任务和执行 ID，以及本地排队状态。接手方使用自己的本机配置，执行 `handoff` 并传 `--task-id`、`--previous-attempt` 和目标工件。验证者执行 `verify` 并传相同的 `--task-id` 和 `--artifact`。各自用结果绑定启动该会话的 Hook 和投递进程。中央回执确认接手成功；两人同时接手时保留冲突供核对。若绑定写入后进程异常退出，`resume-registration --binding <路径>` 可重放同一注册步骤。

1. 在用户选择的测试项目的既有 Hook 列表中追加下方 command 记录。将命令中的 Python 和 `run.py` 替换为实际安装的绝对路径；保留已有 Hook、执行顺序和其他设置。以 `-I` 启动可从固定安装位置加载模块。未绑定的窗口将返回空 JSON。由用户启动的单个会话也可通过支持的临时设置加载合并后的片段。
2. 原生 `capture` 只负责本地持久入队和 wiki 新增页面，返回 `{}`。上报网络由后台工作进程处理。用同一私有绑定运行 `python -I D:/aicoding/mylib/tools/agent-hub/hooks/run.py watch --interval 5`。该进程从自己的 `AGENT_HUB_TOKEN` 环境变量读取试点写入凭据。也可执行一次 `flush` 或查询 `status` 的待办/回执数量。遇网络错误逐步退避，最长默认五分钟。超过 14 天的未确认记录在本地标为待核对；已确认的本地回执保留 35 天。
3. 项目 wiki 中每份记录独立保存为一页，MCP 提交同一正文及 SHA-256。传输失败保留原始事件和序号；启动投递进程时恢复尚未写入 wiki 的记录。现有页面被手动改动时保留冲突现场。使用生成式 wiki 的项目应通过原生账本集成；本目录的普通 Markdown 发布器以独立目录保存记录。

```json
{
  "hooks": {
    "Stop": [
      {"hooks": [{"type": "command", "command": "python -I D:/aicoding/mylib/tools/agent-hub/hooks/run.py capture"}]}
    ],
    "PostToolUse": [
      {"matcher": "Edit|Write|apply_patch|ApplyPatch", "hooks": [{"type": "command", "command": "python -I D:/aicoding/mylib/tools/agent-hub/hooks/run.py capture"}]}
    ]
  }
}
```

| 宿主 | 可选项目配置与采集范围 |
| --- | --- |
| Codex | 受信项目的 `.codex/hooks.json`。使用 `hook_event_name`、`session_id`、可用的 `turn_id` 和结论字段；本机 0.166.0 的 `codex features list` 显示 hooks 已启用。 [官方 Hook 规范](https://developers.openai.com/codex/hooks) |
| Claude Code | 选择当前项目的本机设置层或通过 `--settings` 加载已合并配置。本机探测版本 2.1.310。使用 `Stop` 的 `last_assistant_message` 和 `PostToolUse` 工具名。 [官方 Hook 规范](https://code.claude.com/docs/en/hooks) |
| Grok Build | 受信项目的 `.grok/hooks/*.json` 或明确配置的 `GROK_HOME/hooks/*.json`。实测 1.0.92 b06756fd6256 的 `hookEventName` 使用 `stop` 等小写事件，`promptId` 区分轮次。采集 `end_turn`，忽略额外的会话收尾 Stop。Grok 也可发现项目中的 Claude hooks，应只注册一次。 [官方 Hook 规范](https://github.com/xai-org/grok-build/blob/main/crates/codegen/xai-grok-pager/docs/user-guide/10-hooks.md) |
| 其他工具 | 可用显式 `report` 接口桥接一个受信步骤。支持情况按实际安装环境登记。 |

原生编辑事件仅提交工具名与状态。Stop 默认提交简短状态。已验证的 Codex、Claude 与 Grok 宿主的最终可见回答中，以 `HUB-REPORT:` 开头的一行可作为可分享摘要。手动 `report` 从标准输入接受 `{"step_id":"case-44","summary":"回归通过，等待设备验收","status":"reported","evidence":["test/run-44"],"skills":["example@v2"]}`。显式摘要与证据应由项目授权共享。客户端过滤常见密钥模式，并限制输入大小；不会读取工具参数、完整输出、环境变量表或会话正文。对于宿主没有提供稳定轮次或事件 ID 的回调，每次原生调用生成一个新 ID；网络重投始终复用已持久保存的 ID。

Windows 原生生命周期验收使用 `AGENT_HUB_RUN_NATIVE_HOOKS=1` 和 `pytest -q tests/test_native_cli_hook.py`。每个测试以临时项目、独立配置和回环响应源运行实际 CLI，核对同一条 wiki 正文、事件 ID 与 SQLite 待发送项。版本门槛为 Codex 0.166.0、Claude Code 2.1.310、Grok Build 1.0.92 b06756fd6256。三种 CLI 的隔离验收覆盖本机单轮 Stop；真实远程主机、真实模型推理和订阅额度按各自的试点条件验收。
