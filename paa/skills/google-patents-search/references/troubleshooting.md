# 取数路线与故障排查（2026-09-26 实测）

## 1. 实测结论：为什么必须走"真实浏览器"

同一天、同一台机器、同一网络下逐条实测：

| 取数方式 | 结果 |
| --- | --- |
| `python requests` → `/xhr/query`（站点检索用的内部接口） | **503**，返回 Google "Sorry… automated queries" 页 |
| `python requests` → `/patent/<PN>/<lang>`（单件说明书页） | **503**，同上 |
| Playwright 自带 chromium **无头** | **503**，同上 |
| Playwright 自带 chromium **有头** | 仍可能被拦（视网络信誉） |
| **用户真实 Chrome（Playwright MCP / 扩展会话）** | ✅ 正常：结果页 10 条/页，单件页可取 `#claims`（实测 22 项）与 `#description`（实测 51k 字符） |
| Playwright `connect_over_cdp` 挂到带调试端口的 Chrome | ✅ 管路已验证（复用真实 profile 即可复用会话） |

**结论**：Google 的拦截是**会话/信誉级**的，不是 UA 级。绕过方式不是伪造请求头，而是**用真实浏览器会话**。
因此本 skill 的默认路线是 `--route auto`：先试 CDP，失败才降级无头，且降级后被拦时**明确报错**
（退出码 3 + `GP_BLOCKED: google_anti_bot`），绝不静默返回 0 条。

## 2. 三条路线怎么选

```bash
# 路线 A（推荐，可脚本化）：让 Chrome 带调试端口启动一次
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
python gp_search.py --query '石墨烯 眼罩 country=CN' --cdp 9222
python gp_fetch.py CN103399241B --cdp 9222 --out evidence/gp

# 路线 B（推荐，人工在场时最稳）：MCP 浏览器工具
python gp_search.py --query '石墨烯 眼罩 country=CN' --print-url     # 取 URL
#   → browser_navigate 到该 URL
#   → browser_run_code_unsafe filename=scripts/gp_parse_current_search.js
#
# 路线 C：离线复算（把上一次的 HTML 拿来解析，可回归测试）
python gp_search.py --html tmp/gp/result.html
```

## 3. 症状 → 处置

| 症状 | 判定 | 处置 |
| --- | --- | --- |
| 屏幕/HTML 出现 "Sorry… automated queries" | `GP_BLOCKED: google_anti_bot` | 换路线 A/B；不要在无头下反复重试（会加重拦截） |
| 结果页 0 条但页面正常 | 检索式问题 | 按 `query_syntax.md` 逐项放宽：去 `CL=`/`CPC=` 限定、改 `country=`、减词 |
| 单件页无 `#claims` | 该公开号只有著录项或尚未公开全文 | 试同族其他成员、试 `zh`/`en` 另一语言路径，或改用 incoPat/官方渠道 |
| `--html` 解析出 0 条 | HTML 是重定向页/被拦页 | 用 `--save-html`（实时路线）保存原始 HTML 再离线复算 |
| CDP 连不上 | Chrome 未开调试端口/端口占用 | 确认 `--remote-debugging-port=9222` 且该实例未崩溃；`curl http://127.0.0.1:9222/json/version` 自检 |

## 4. 频率与礼貌抓取

- 结果页与单件页之间**留 2–3 秒**间隔；批量取件时建议每 10 件停 20–30 秒；
- 本 skill 不做并发抓取（`gp_fetch.py` 逐个顺序执行）；
- 只要出现一次 `GP_BLOCKED`，本轮就应停止抓取并切换路线，不要循环重试。

## 5. 与 incoPat 的关系（互补，不替代）

| 维度 | incoPat（本仓首选） | google-patents-search（本 skill） |
| --- | --- | --- |
| 凭证 | 需要账号（测试账号授权 2026-08-31 已到期） | **无需 key** |
| 中文库覆盖 | 中国库完整，支持语义检索/法律状态/同族/引证 | 覆盖广但**无法律状态**，中文全文以公开文本为准 |
| 语义检索 | 有（整段技术方案 → 相似度） | 无（只有布尔/字段检索） |
| 适合 | 法定检索、法律状态、价值度 | 免费候选发现 + 原文核验 + 与检索式互补的第二轮复检索 |

两者条件都具备时：先用 incoPat 拿范围与法律状态，再用本 skill 做**第二轮独立复检索**（换轴检索），
两边结果按公开号取并集后统一走 `gp_verify.py` 的核验门禁。
