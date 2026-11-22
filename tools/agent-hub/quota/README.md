# Agent Hub 账号额度采集

每个已入库的步骤对应一个额度任务。worker 按本地配置的项目和计费账号领取租约，查询一次，使用同一 `job_id` 和 `lease_token` 回写标准化结果。每个账号的成功观测、自报时间、计量单位与重置时间均独立留存。失败分类包括登录待恢复、限流、暂不可用和来源不支持，限流与暂时故障由服务重排。

## 运行

在 `tools/agent-hub` 中，用包含本项目 MCP 客户端依赖的 Python 运行。受限的采集凭据由操作系统环境变量 `AGENT_HUB_QUOTA_TOKEN` 提供，`worker` 填写该授权在服务端登记的主体别名。项目、账号和额度池取自已登记的绑定。以下命令中的配置文件由操作员创建、保存在 Git 之外。

```powershell
python -m agent_hub.quota --profile C:\AgentHub\config\quota-codex.json --endpoint https://hub.example/hub/mcp --watch
```

省略 `--watch` 可执行单次检查；空队列返回 `idle`。测试通过隔离应用进程、合成用量快照和临时 SQLite 库运行。

如需无人使用时也更新账号用量，在 profile 中设置 `idle_after_seconds`（60 至 604800 秒）。中央端优先领取现有任务，在账号空闲超过配置间隔时创建独立定时查询。显示为周期刷新，不计作开发步骤。选择可满足厂商限流和预算的间隔。

### Codex 订阅

```json
{
  "project": "pilot",
  "account": "codex-seat-a",
  "pool": "included",
  "worker": "quota-usa",
  "provider": "codex",
  "source": "codex_app_server",
  "codex_home": "C:\\AgentHub\\codex-pilot-profile",
  "codex_account_id": "<official accountId>"
}
```

授权配置指向专用的本地 Codex profile，`codex_account_id` 为操作员核对的官方账号标识。worker 经 stdio 初始化 app-server，调用 `account/rateLimits/read`，校验响应的 `accountId`，再读取所配置的额度池。默认使用 `rateLimits`；配置 `limit_id` 后按 `rateLimitsByLimitId` 精确读取。按返回的窗口时长识别周和短周期，使用来源原有的百分比单位，并将官方 Unix 重置时间保存为 UTC。没有可验证账号标识时报告登录待核对。可选的 `codex_executable` 指向操作员安装的兼容 CLI。 [Codex 官方协议](https://github.com/openai/codex/blob/main/codex-rs/app-server-protocol/src/protocol/v2/account.rs)

### Claude Code、Grok 及其他明确提供的官方用量

对已在官方用量页核对的记录，配置 `source` 为 `operator_usage_export`，并将 `provider` 设为对应提供商。配置 `snapshot_file` 为受信本地文件路径。由操作员或已获授权的适配器写入格式如下的最新观测；应先写临时文件、持久化再原子替换。worker 只读取列出的字段。 [Claude 官方用量说明](https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work) · [Grok 官方用量说明](https://docs.x.ai/grok/faq)

```json
{
  "provider": "claude",
  "account": "claude-seat-a",
  "pool": "included",
  "observed_at": "2026-11-22T10:28:00Z",
  "windows": [
    {"period": "weekly", "unit": "percent", "remaining": 42, "reset_at": "2026-11-24T09:00:00Z"},
    {"period": "short", "unit": "percent", "remaining": 80, "reset_at": "2026-11-22T13:00:00Z"}
  ]
}
```

示例为合成数值。导出观测必须属于绑定的提供商、账号和额度池，采集时间须在本次事件入库后。过期导出记为暂不可用并保留最后有效观测。周期支持 weekly、short、daily、monthly、balance 和 other；单位支持 percent、tokens、credits、requests、CNY 和 USD；未知的精确余量或重置时间可为 null。新的官方查询来源可用与 `exported_snapshot(profile, job, now)` 相同的接口接入。浏览器登录页自动化、真实账号比对和多机部署仍需各自验收。

## DeepSeek API 余额

`source=deepseek_balance`、`provider=deepseek` 使用固定的官方 HTTPS 地址。按计费账号设置独立采集进程，私有环境变量 `MYLIB_HUB_DEEPSEEK_KEY` 提供凭据，配置 `key_sha256` 固定其摘要。结果按 CNY/USD 余额展示，周重置字段为空。 [官方接口](https://api-docs.deepseek.com/api/get-user-balance/)
