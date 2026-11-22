# 独立总管与证据查询

总管通过 `EvidenceSupervisor(store, endpoint, model, api_key)` 接入 `chat`。调用者需要同一项目的任务读取和模型聊天授权。只有操作员配置的模型端点会收到文本；请求方只能选择获授权项目、问题及任务 ID。

## 独立美国主机

在中转服务器为目标项目创建仅有 `tasks:read` 的凭据。美国主机通过 OS 私有环境注入该凭据和经授权模型的 API key。美国服务面向驾驶舱的另一份 grant 绑定同一项目及 `tasks:read`、`chat:model` 两个 scope。各项目使用独立读取凭据。默认本机监听，受限入口通过固定 TLS 代理发布。

```powershell
# MYLIB_HUB_EVIDENCE_TOKEN 与 MYLIB_HUB_MODEL_KEY 由服务环境提供。
python -m agent_hub.server --database C:\AgentHub\state\supervisor.sqlite3 --auth-file C:\AgentHub\private\grants.json --port 8842 --model-evidence-endpoint https://relay.example/hub/mcp --model-project pilot --model-endpoint https://api.deepseek.com --model MODEL_ID
```

模型名称以已授权标准 API 账号实际可用值为准，示例主机和端口按部署配置替换。`--model-evidence-endpoint` 和 `--model-project` 将总管的证据读取绑定在中央 MCP，`--database` 是该服务实例的本地业务库。向美国实例发起授权的 `chat` 请求即可触发远程证据读取。其他业务写入仍走中央 MCP。

同进程部署可使用 `Store` 作为数据来源。远程集成使用 `RemoteReadStore(endpoint, {project: project_read_token})`，读取项目任务列表、任务状态、步骤及确定版本的 wiki 记录。美国实例在取证前、发给模型前和返回答案前，经中央 MCP 的 `get_evidence_epoch` 核对当前授权及撤回代次。其间失权或证据已撤回时，该次答复作废。部署方负责提供项目级模型数据处理授权。

### 中央驾驶舱委托美国实例完成全局聊天

驾驶舱连接中转服务器。用户在授权项目范围内进行全局提问时，中央 MCP 核实每个项目的 `tasks:read` 和 `chat:model` 权限，调用部署方指定的美国 MCP 上的 `infer_projects`。请求只携带问题、项目列表与对应的撤回代次。美国节点使用该项目自己的读取凭据从中央读取最新任务摘要，核对授权和撤回代次，将允许的摘要一次发给模型，并在返回前复核。中央按最初读取的项目、来源和事件 ID 核验答复中的每条引用，并再次检查用户授权和撤回状态。

两端的示例参数如下。变量名是配置指针，具体值由两台机器各自的凭据环境提供。

```powershell
# 中央节点。MYLIB_HUB_SUPERVISOR_TOKEN 属于中央至美国服务的专用身份。
python -m agent_hub.server --database C:\AgentHub\state\hub.sqlite3 --auth-file C:\AgentHub\private\central-grants.json --allowed-host relay.example --supervisor-mcp https://usa.example/hub/mcp --supervisor-project A --supervisor-project B

# 美国节点。A、B 分别使用中央授予对应项目的 tasks:read 凭据。
python -m agent_hub.server --database C:\AgentHub\state\supervisor.sqlite3 --auth-file C:\AgentHub\private\us-grants.json --port 8842 --allowed-host usa.example --model-evidence-endpoint https://relay.example/hub/mcp --model-project-token-env A=CENTRAL_READ_A --model-project-token-env B=CENTRAL_READ_B --model-endpoint https://api.deepseek.com --model MODEL_ID
```

美国节点的 grants 文件对每个允许项目为同一委托服务凭据登记 `tasks:read`、`chat:model`、`chat:delegate`。普通驾驶舱凭据仅按项目授予所需的查看或模型权限。部署时给反向代理配置与两个 MCP 入口一致的 TLS 域名及服务端允许的 Host。美国业务库可以为空；任务证据始终从中央节点读取。在模型处理期间撤回证据、移除项目授权、传入未知项目或返回不在原始可见记录中的引用，均使相应请求失效。在两套独立临时 MCP 服务与模拟模型上可运行 `python -m pytest -q tests/test_remote_global.py` 做验收。

## 上下文和失败语义

- 指定任务时读取该任务的当前执行和并行验证摘要。总览读取最多 20 个任务，命名任务及明确待处理项优先，最多展开 5 个任务的近期证据。提问明确涉及 wiki、原文或依据时，按记录引用读取最多两个固定版本的短摘录。
- 每次发送前计量包含问题、系统提示、JSON 转义和模型设置的完整请求。请求体上限为 7,000 个 UTF-8 字节，另预留 1,000 token 的供应商消息封装空间。实际厂商侧 token 计量及隐藏封装需独立实测。超预算时保留有界的数据库记录回答。
- 模型只接收筛选后的摘要。模型必须逐条返回短结论与输入记录引用，服务校验引用范围并填入真实事件 ID。未知引用、工具调用、模型超时、限流、非法响应和重定向将回退到已读取的记录，返回 `mode=recent_events`。这项校验验证引用身份；结论的语义正确性仍需抽样复核。来源鉴权失败则停止查询。
- 全局聊天在用户可读取的各项目均授予模型处理权限时，将已过滤的事实轮流取样，使用同一字节上限发一次模型请求。每条引用包含项目、来源及事件 ID。跨库同名事件可独立定位；返回结果前服务重新校验所有项目的授权和撤回状态。远程证据绑定仅覆盖部分项目时，全局答复展示可读记录。
- 实际运行所需依赖沿用中央 MCP 工具的 Python 环境。用隔离的本地 HTTP 模型夹具和临时 SQLite 运行 `python -m unittest discover -s tests -p test_supervisor.py`。
