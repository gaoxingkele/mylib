# 多模型额度驾驶舱方案（token-cockpit）

状态：方案稿（2026-11-21），未实施。
目标：Claude Code、Codex、Grok 及其他 CLI 模型每次 hook 触发后，刷新“本周剩余额度 + 下次重置时间”，汇总成一份统一快照，通过一个本地 MCP 服务提供给全局环境；右侧驾驶舱（Orca）和任意 agent 都能读到。

## 1. 现状调查（2026-11-21，本机）

| 项 | 发现 |
|---|---|
| 驾驶舱 | Orca 桌面应用（`%LOCALAPPDATA%\Programs\orca`），右侧统计面板有 Claude / Codex / OpenCode / Muse / Grok 标签 |
| Orca 自带额度轮询 | **Claude**：`https://api.anthropic.com/api/oauth/usage`，取 5 小时窗口、7 天窗口与 Fable 周额度（`weekly_scoped` / `seven_day`）及 `resets_at`。**Codex**：`https://chatgpt.com/backend-api/wham/usage`，取 primary / secondary 窗口 |
| Orca hook 通道 | 各 CLI 的 hook 调用 `~/.orca/agent-hooks/<agent>-hook.cmd`，POST 到 `127.0.0.1:$ORCA_AGENT_HOOK_PORT/hook/<agent>`；Claude 另有 statusline 通道 `/statusline/claude`，仅当 payload 含 `rate_limits` 时上报。没有面向第三方的“额度写入”接口 |
| 生效前提 | 只在 Orca 窗格里启动的会话才有 `ORCA_AGENT_HOOK_PORT/TOKEN/PANE_KEY`；在独立终端里启动的会话不上报 |
| Codex 离线数据 | `~/.codex/sessions/**/rollout-*.jsonl` 的 token_count 事件带 `rate_limits`：`primary.used_percent`、`window_minutes`（10080 = 周）、`resets_at`（epoch）、`plan_type`、credits 余额。**不联网即可读取** |
| Claude 离线数据 | Claude Code statusline 输入 JSON 带 `rate_limits`（five_hour / seven_day 的 used_percentage 与 resets_at） |
| Grok | `~/.grok` 有 hooks、sessions、settings_cache；本机缓存未发现额度字段，需调研 CLI 是否提供 `/usage` 类命令或接口 |
| 其他（Kimi、Gemini、OpenCode 等） | 多为 API key 计费，没有“周额度”概念；可显示余额或当期用量，没有就显示 N/A |

结论：Claude、Codex 两家 Orca 已经能显示（前提是在 Orca 里启动）。缺口有三：①Grok 和其他模型；②Orca 之外启动的会话；③没有一个全局可查询的统一快照（agent 自己无法知道“哪个模型还有余量”）。

## 2. 方案总览

```
各 CLI hook（Stop / SessionEnd / turn 完成）
   └─► quota-probe --agent <name> --detach     （立即返回，不阻塞 hook）
          ├─ 适配器：先读本地离线数据，没有再按 TTL 调用厂商接口
          └─► 写入 ~/.agent-quota/state.json（原子写入，仅含百分比和重置时间）
quota-mcp（本地 MCP 服务，stdio + 可选 HTTP 127.0.0.1）
   ├─ tools: list_quotas() / get_quota(agent) / pick_model(min_remaining)
   └─ resource: quota://snapshot
展示：Orca 原生面板（Claude/Codex）＋ quota-mcp 快照（全部模型）＋ 可选 statusline 一行汇总
```

设计原则：
- **hook 不等网络**：hook 只负责 spawn 后台进程并立即返回 `{}`，总耗时 < 200ms，不影响 Orca 现有 hook。
- **离线优先**：能从本地会话日志或 statusline payload 读到的，就不调用接口。
- **限频**：每个模型的接口调用 TTL 默认 300 秒，多个窗口同时触发时用文件锁去重。
- **最小数据**：快照只存 `used_percent`、`remaining_percent`、`window`、`resets_at`、`plan`、`source`、`fetched_at`；不存 token、不存提示词内容。
- **不改 Orca 安装文件**：Orca 的 hook 脚本保持原样，新 hook 作为同一事件下的第二个命令并列注册。

## 3. 统一数据结构

```json
{
  "updated_at": "2026-11-21T08:00:00Z",
  "agents": {
    "codex": {
      "plan": "pro",
      "windows": [
        {"name": "weekly", "minutes": 10080, "used_percent": 40.0, "remaining_percent": 60.0,
         "resets_at": "2026-11-26T03:18:32Z"}
      ],
      "credits": {"balance": "1234.56"},
      "source": "codex-rollout",
      "fetched_at": "2026-11-21T07:59:58Z",
      "stale": false
    },
    "claude": {"windows": [{"name": "5h"}, {"name": "weekly"}, {"name": "weekly-fable"}], "source": "statusline|oauth-usage"},
    "grok": {"windows": [], "source": "unsupported", "note": "待调研"}
  }
}
```

`stale = now - fetched_at > 2 × TTL`。驾驶舱和 agent 看到 `stale` 时应该显示“数据过期”，不能把旧数据当作当前值。

## 4. 各模型适配器

| 模型 | 首选来源 | 备选来源 | 触发 hook | 备注 |
|---|---|---|---|---|
| Claude Code | statusline payload 的 `rate_limits`（在现有 statusLine 命令里加一行 tee 给 probe） | `api/oauth/usage`，凭据读 `~/.claude/.credentials.json` | `Stop`、`SessionEnd` | oauth/usage 是未公开接口，可能变动；失败时退回 statusline 数据 |
| Codex | 最新 `rollout-*.jsonl` 中最后一个 `rate_limits` | `backend-api/wham/usage`，凭据读 `~/.codex/auth.json` | `~/.codex/hooks.json` 的 `Stop`（或 turn 完成事件） | 离线数据已验证可用 |
| Grok | 待调研：CLI 命令、`~/.grok/sessions` 日志、`cli-chat-proxy.grok.com` 响应头 | 无 | `~/.grok` hooks | 第一阶段只记录“最后使用时间” |
| Kimi / Gemini / OpenCode / 其他 | 厂商余额或用量接口（如有） | 无 | 各自 hook（Orca 已有 kimi-hook.sh 等） | 没有周额度的显示余额或 N/A |

适配器统一接口：`probe(agent) -> Snapshot | None`；每个适配器单独超时（3s），失败只记日志，不抛到 hook。

## 5. MCP 服务（quota-mcp）

- 实现：Python（`mcp` SDK）或 Node，单文件 + `state.json`。
- 注册：Claude Code `claude mcp add --scope user quota-mcp -- python <path>/quota_mcp.py`；Codex 写入 `~/.codex/config.toml` 的 `[mcp_servers.quota]`；Grok 按其 MCP 配置方式注册。
- 工具：
  - `list_quotas()` → 全部模型快照，按剩余百分比排序；
  - `get_quota(agent)` → 单个模型；
  - `pick_model(min_remaining=20)` → 返回剩余额度 ≥ 阈值且最早重置的模型，供编排类任务选择模型；
  - `refresh(agent?)` → 手动触发一次 probe（同样受 TTL 限频）。
- Orca 侧展示：Orca 没有第三方额度写入接口，第一阶段依靠 Orca 原生的 Claude/Codex 面板，加上 quota-mcp 快照。如需在 Orca 右侧面板显示全部模型，有两条路，需要确认 Orca 是否支持：①Orca 的插件或扩展面板；②向 Orca 提需求，新增 `/quota/<agent>` 写入接口。

## 6. 实施步骤与验收

| 阶段 | 内容 | 验收 |
|---|---|---|
| M1 | `quota_probe.py`：Codex 离线适配器 + Claude statusline 适配器 + state.json 原子写 | 在独立终端跑一次，state.json 出现 codex/claude 两项，数值与 Orca 面板一致（误差 ≤1%） |
| M2 | hook 接线：Claude `Stop`、Codex `Stop` 并列注册 `quota-probe --detach` | hook 总耗时 < 200ms；Orca 原有 hook 行为不变；连续 10 次 Stop 只触发 ≤2 次接口调用 |
| M3 | `quota_mcp.py` + 三个 CLI 注册 | 三个 CLI 内都能调用 `list_quotas` |
| M4 | Grok / Kimi / Gemini 适配器调研与实现 | 能拿到的显示数值，拿不到的显示 `unsupported` 和原因 |
| M5 | 可选：statusline 一行汇总（如 `Codex 60%·5d │ Claude 71%·3d │ Grok –`） | 不影响 Orca statusline 上报 |

## 7. 风险

- **未公开接口**：`api/oauth/usage`、`wham/usage` 可能随时变更或被限流 → 离线优先 + TTL + 失败降级。
- **凭据安全**：只在本机读取凭据，只发往对应厂商的自有域名；日志与快照不得包含 token；脚本不放进任何公开仓库的明文配置。
- **服务条款**：调用频率保持与官方客户端同级或更低；不用于绕过额度限制。
- **hook 叠加**：Codex、Claude 的 hook 数组里新增项必须追加，不能覆盖 Orca 的条目；修改前备份 `settings.json` / `hooks.json`。

## 8. 待决策

1. 是否接受“Claude/Codex 继续以 Orca 原生面板为主，quota-mcp 负责全局查询和其他模型”的分工；
2. Grok 及其他模型优先做哪几个；
3. 是否需要 `pick_model` 自动选模型（会影响编排类技能的行为）。
