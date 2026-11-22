# 业务 MCP 隔离试点

业务 MCP 监听回环地址 `/hub/mcp`，驾驶舱使用同一进程的只读 WebSocket `/hub/view`。已有 `/mylib/mcp` 仍提供技能检索。服务代码在本目录的 `agent_hub/`，数据库、授权文件和备份放在管理员设置的私有目录中。

## 启动

解压服务源码包后，在 `agent-hub` 目录创建独立环境。例如，Windows 可运行以下两行，再使用该环境的 Python 执行后续命令。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

1. 在单独的 Python 3.11+ 环境中使用[依赖清单](requirements.txt)，确认实际 SQLite 版本及日志模式。已有中央 mylib MCP 使用自己的解释器。Windows 联调复用了本机 Python 3.14 的 MCP SDK 和桌面中继 WebSocket 依赖。先只用回环监听器与测试凭据验证。
2. 为每个身份生成独立随机凭据。服务端 JSON 仅保存 UTF-8 token 的 SHA-256 十六进制摘要。POSIX 授权文件使用 `0600`，Windows 使用限服务账号访问的目录 ACL。按下面的结构替换各自的摘要。`subject` 是稳定的来源或 worker ID。`project` 由管理员登记。Hook 的 `host`、`tools` 和 `accounts` 要与本机绑定一致。多个项目可为同一查看凭据分别建立授权行。

```json
{"grants":[
  {"sha256":"<hook-digest>","subject":"pilot-a","project":"demo","scopes":["events:append","wiki:write"],"host":"pilot-a","tools":["codex"],"accounts":["dev-plan"]},
  {"sha256":"<viewer-digest>","subject":"viewer","project":"demo","scopes":["tasks:read","usage:read"],"accounts":["dev-plan"]},
  {"sha256":"<worker-digest>","subject":"quota-worker","project":"demo","scopes":["usage:collect"],"accounts":["dev-plan"]}
]}
```

3. 在 `tools/agent-hub` 下启动服务。对每个经过登记的桌面或 Android 文档源分别设置 `--allowed-origin`。示例的源和端口为隔离试点值。

```powershell
python -m agent_hub.server --database D:/AgentHub/data/pilot.db --auth-file D:/AgentHub/private/grants.json --port 8822 --allowed-origin http://127.0.0.1:6771
```

4. Hook 连接 `http://127.0.0.1:8822/hub/mcp`，本机测试驾驶舱连接 `ws://127.0.0.1:8822/hub/view`。其他设备接入时用具备受信证书的 TLS 反向代理，配置业务入口专属路径和 `--allowed-host`（与实际转发的 Host 完全一致）。首个 WebSocket 消息为 `{"op":"hello","token":"…","project":"demo"}`，也可选择 `*` 查看该身份获准的项目。后续请求仅包含项目范围、工具名和参数。凭据通过 MCP 的 Bearer Header 或 WebSocket 初始消息传递。

## 数据流和角色

**Linux 中转服务器试点。** [systemd 示例](deploy/agent-hub-pilot.service)使用独立账号、解释器、数据目录和进程。安装位置 `/opt/agent-hub-pilot` 应含 `agent_hub/` 和试点 venv。`/etc/agent-hub-pilot/grants.json` 由服务账号只读、权限 `0600`，`pilot.env` 由管理员维护，在其中设置 `HUB_PUBLIC_HOST`、`HUB_DESKTOP_ORIGIN` 和 `HUB_ANDROID_ORIGIN` 为试点实际发出的 Host 和 Origin。先在机器本地核对授权拒绝与合法查询，再在试点 TLS 虚拟主机逐条引入[精确代理路径](deploy/hub-locations.nginx.conf)并验证配置。观察原中继及原技能 MCP 的健康情况，保留原配置副本。回退只移除本次试点路由并停止试点服务，保留已确认数据库与待办供核对。当前验证证据来自 Windows 回环环境，实际 Linux 上的解释器、权限、代理和 TLS 需要另行验收。

| 权限 | 主要操作 |
| --- | --- |
| `events:append` | `report_step` 在一步事务内持久化 Hook 事件、对应 wiki 版本和额度待办。返回 `event_id`、`task_id`、`attempt_id`、`seq` 与 `usage_job_id`。异机同名窗口由主机、执行、会话代次区分。 |
| `wiki:write`、`wiki:withdraw` | 版本修订与项目授权的撤回。既有步骤的文档修订独立于用量触发。 |
| `tasks:read` | `list_tasks`、`get_task_status`、`search_task_events`、`get_wiki_entry`、`chat` 以及只读 mylib、RSI 工具。全局列表带来源项目；详情绑定单一项目。无模型配置时聊天界面展示最近事件。 |
| `usage:collect` | `claim_usage_job` 领取对应账号的待办，`record_usage_snapshot` 写回有来源、时效和单位的观测；重试须携带原租约。 |
| `usage:read` | `get_usage_overview` 只返回授权账号。最近观测与最近一次成功值分别返回。 |
| `chat:model` | 为相应项目开启配置模型的证据查询。接入前明确项目允许送往该提供商的摘要范围。 |

中央库查询需 `--catalog-endpoint` 及服务专用的 `MYLIB_HUB_CATALOG_TOKEN`。桌面本机设置优先采用用户保存的 mylib 目录，默认 `D:\aicoding\mylib`。中央 MCP 的 `--evolution-database` 指向独立 RSI 账本。可在专用模型实例本地配置 `--model-endpoint`、`--model` 及 `MYLIB_HUB_MODEL_KEY`；中转服务通过 `--supervisor-mcp`、`--supervisor-project` 及 `MYLIB_HUB_SUPERVISOR_TOKEN` 转发单项目授权查询。上游引用使用单向配置，避免同一服务循环调用。各实例 HTTPS 证书和允许来源在运行前核对。

## 试点验收入口

**多项目只读看板。** 授权文件按项目填写每个读取身份的 `accounts`。若两个项目的不同别名已核实属于同一真实订阅，在相应授权行写 `"shared_pools":{"本项目账号别名":{"本项目额度池":"管理员分配的同一订阅池ID"}}`。全局页合并这些已授权行，同时保留最近状态、最近成功值和项目列表。相同的显示名字不会触发推断合并。

**跨项目模型。** 中转服务器可重复传入 `--supervisor-project` 限定委托范围。在美国模型实例上可使用 `--model-project-token-env PROJECT=ENV_VAR` 为每个项目指定独立中央只读凭据。用于跨项目模型查询的服务身份还须在每个项目具备 `chat:delegate`、`chat:model` 和 `tasks:read`。查询前后复核项目授权与证据撤回版本。 [总管配置](supervisor/README.md)

**受理与采用。** `--enable-feedback` 打开独立的逐次确认通道；只读看板工具不具备确认权限。启用精确宿主绑定时，Hook grant 的 `host_installation_id` 应与已登记的本机安装 ID 匹配。用 `--asset-manifest`、`--asset-manifest-sha256`、`--asset-root` 和独立的 `--evolution-database` 选择版本资产。正式发布与真实窗口采用须有单独的人工确认和宿主证据。

- [开发端 Hook 的捕获、入队、上报及按工具安装](hooks/README.md)
- [账号额度采集、周期和重置时间](quota/README.md)
- [SQLite 备份、轮换和恢复](maintenance.md)
- [RSI 本地操作与生效证据](evolution-operator.md)
- [跨仓库目标、真机与发布门槛](rollout-design.md)

在含测试依赖的隔离环境中，从本目录运行 `python -m pytest -q tests`。在管理员选定测试机和账号之后，再进行跨机授权、真实厂商用量、Android 真机和恢复到独立存储的验收。
