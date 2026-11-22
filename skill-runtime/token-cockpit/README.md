# token-cockpit：多模型周额度快照 + quota-mcp

每次 Claude Code / Codex / Grok 一轮结束（Stop hook），后台刷新一次各模型的“周额度已用/剩余百分比 + 重置时间”，写入 `~/.agent-quota/state.json`；本地 MCP 服务 `quota-mcp` 把快照提供给三个 CLI 里的 agent。设计与决策见 `PLAN.md`。

## 文件

| 文件 | 作用 |
|---|---|
| `quota_probe.py` | 采集器。各模型适配器，离线优先，网络兜底受 TTL 限频，文件锁，原子写 |
| `quota_hook.py` | hook 入口。只读掉 stdin、启动后台采集、立即退出（实测约 130–180 ms），不输出任何内容 |
| `quota_mcp.py` | stdio MCP 服务（纯标准库 JSON-RPC）。工具 `list_quotas` / `get_quota` / `pick_model` / `refresh`，资源 `quota://snapshot` |
| `install.py` | 安装 / 卸载 / 状态。改任何配置前先备份 |

只依赖 Python 标准库（3.10+）。

## 数据来源

| 模型 | 首选（离线） | 兜底（网络，≤1 次 / TTL） | 说明 |
|---|---|---|---|
| Codex | `~/.codex/sessions/**/rollout-*.jsonl` 最后一条 `rate_limits` | `chatgpt.com/backend-api/wham/usage`（凭据 `~/.codex/auth.json`） | 离线数据只在 Codex 会话里刷新；超过 2×TTL 才走网络 |
| Claude | `~/.agent-quota/claude-statusline.json`（若有 statusline 副本） | `api.anthropic.com/api/oauth/usage`（凭据 `~/.claude/.credentials.json`） | 不改 Orca 的 statusLine，所以通常走网络兜底；令牌过期时跳过，等 Claude Code 自己刷新 |
| Grok | `~/.grok/logs/unified.jsonl` 中最后一条 `billing: fetched credits config` | 无 | `creditUsagePercent` 缺省按 0（protobuf 零值省略）；只在 Grok 拉取计费配置时更新 |
| Kimi / Gemini / OpenCode | — | — | `unsupported`，原因写在快照 `note` 字段 |

快照只含：`plan`、`windows[]`（`name`、`minutes`、`used_percent`、`remaining_percent`、`resets_at`）、`source`、`observed_at`、`fetched_at`、`stale`、`error`。不存令牌、提示词和余额。

`stale = now − observed_at > 2 × TTL`（TTL 默认 300 s，环境变量 `AGENT_QUOTA_TTL` 可改）。`resets_at` 已过的窗口按“已重置”显示 0% 已用并标 `estimated`。

## 安装

```
D:\Python314\python.exe C:\aicoding\mylib\skill-runtime\token-cockpit\install.py install
```

它会：
1. 备份到 `~/.agent-quota/backups/<文件名>.<时间戳>`；
2. 在 `~/.claude/settings.json`、`~/.codex/hooks.json` 的 `Stop` 事件**末尾追加**一个独立分组（不改 Orca 的条目）；
3. 写 `~/.grok/hooks/agent-quota.json`（Grok 也会读 Claude 的 settings.json，相同命令会去重）；
4. `claude mcp add --scope user quota-mcp ...`（写入 `~/.claude.json`；Grok 通过 Claude 兼容层同样加载）；
5. 在 `~/.codex/config.toml` 末尾追加带标记的 `[mcp_servers.quota]` 块。

**Codex 需要人工信任新 hook**：Codex 对每个 hook 记录 `trusted_hash`，新增的 Stop 分组在你于 Codex 里审核（`/hooks`）之前不会执行。本脚本不伪造信任记录。

手动跑一次：`python quota_probe.py --print`（`--force` 忽略 TTL）。

## 卸载 / 回滚

```
D:\Python314\python.exe C:\aicoding\mylib\skill-runtime\token-cockpit\install.py uninstall
```

只删除带 `token-cockpit/quota_hook.py` 标记的 hook 分组、`agent-quota.json`、`quota-mcp` 注册和 `config.toml` 中的标记块。也可以直接把 `~/.agent-quota/backups/` 里的备份拷回原位。数据目录 `~/.agent-quota/` 可整个删除。

## 驾驶舱（Orca）

Orca 原生面板继续负责 Claude / Codex（仅限 Orca 窗格内启动的会话）。Orca 没有第三方额度写入接口，所以 Grok 等模型的数值目前通过 quota-mcp 查询，不在 Orca 右侧面板显示；要进面板需要 Orca 提供插件面板或写入接口。
