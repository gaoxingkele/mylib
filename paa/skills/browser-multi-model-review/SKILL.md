---
name: browser-multi-model-review
description: >
  Playwright MCP 浏览器控制包：在已登录 Chrome 扩展会话里操作 Gemini、ChatGPT、Grok、Perplexity（/patents 专利入口）
  与 Kimi（K3 + 学术数据库插件），每案独立会话、最高档模型审核中国发明专利申请文件。**仅限用户手动点名触发，
  不属于 /patent、patent-orchestrator、/evolve-patent-system 任何自动化环节。**上传失败则 insertText 粘贴；回复写入
  入口标识 md；wiki 日志必须含标识词+版本号。TRIGGERS（须用户明确说出）: 浏览器多端审核, 浏览器四端/五端审核,
  Playwright MCP, Gemini Pro, GPT-6 Pro, Grok Expert, Perplexity 专利搜索, Kimi K3 学术数据库,
  独立会话评专利, /browser-multi-model-review
---

# 浏览器多端控制（Playwright MCP）

## 触发方式：仅手动（2026-09-27 规则）

- **只在用户本轮明确要求时运行**（如"跑一下浏览器五端""用 Kimi 查一下 P05-4"）。可以只跑其中一端或几端。
- **任何自动化流程不得调用本 skill**：`/patent` 四阶段、`patent-orchestrator` 调度、`cnipa-drafting-workflow`、
  `patent-grant-scorer`、`/evolve-patent-system`、`patent-evolver`、Workflow 脚本、定时任务（/loop、/schedule）一律不得
  自动触发浏览器会话。原因：需要已登录的个人浏览器会话、会占用同一 Chrome、网页模型档位与界面随时漂移、
  且产出需人工判断采纳。
- 自动化流程可以**读取**本 skill 以往的产出文件（`<GATE>_*.md`）作为参考输入，但不得因"缺少这些文件"而自动发起浏览器会话，
  只能在报告里提示"可手动触发浏览器多端评审"。
- **证据层级**：网页模型（含 Perplexity /patents、Kimi 学术数据库）的结论属于 `R_self` 同级的**模型意见**，
  不是 `R_professional`（持证代理机构意见）也不是 `R_external`（OA）。它们给出的专利号/论文一律标「非指定对比文件」，
  须经 Google Patents 原文或 DOI/arXiv 页面核验后才能写入 `01_现有技术检索报告.md`。


父会话亲自操作浏览器。不要再 spawn 会抢同一 Chrome 的子代理。
不调用 incoPat。不编造专利号。网页模型点名的文献一律标「非指定对比文件」。

解释器：`D:/Python/Python314/python.exe`。python-docx / AHP 用 `C:\WINDOWS\py.exe -V:3.12`。

## Token 纪律（硬约束，2026-09-27）

浏览器控制的 token 主要花在"页面内容进模型上下文"上。以下规则不得违反：

1. **禁止用 `browser_snapshot` 轮询等待生成结束。** 等待一律用 `browser_run_code_unsafe` 的 `filename=` 执行 `scripts/js/wait_done.js`：它在 Playwright 进程内每 30 秒测一次正文长度和"停止"按钮，连续 30 秒无变化才返回 `done:true`（检查本身不耗 token，token 只花在调用次数上），只回传 `{site, done, reason, elapsedSec, len}` 这样的小对象。返回 `done:false` 就原样再调一次，不要改用快照查看进度。
2. **`browser_snapshot` 只用于定位失败时**（`getByRole` 找不到元素、首次适配新站点如 Kimi），且先用 `browser_find`，再用 `browser_snapshot(target=ref)` 看局部，不做整页快照。
3. **申请全文不进上下文。** 用 `mk_site_insert.py` 生成 `insert_<site>.js`，经 `filename=` 执行；不要先 Read 全文再手动输入。
4. **回复不整篇读回。** 复制 → `save_clipboard.py` → `wrap_eval.py` 直接落文件；需要采纳时只读结论与 P0/P1 段。
5. **按需单端。** 只查专利跑 Perplexity `/patents`，只查学术文献跑 Kimi，不必每次五端齐跑。

## MCP 用法

1. 先 `search_tool` 取 Playwright 工具 schema，再 `use_tool`。不要猜参数名。
2. 会话须是 Playwright **扩展模式**（已登录的 Chrome）。`setFiles` 常返回 `Not allowed`。
3. 长脚本用 `playwright__browser_run_code_unsafe` 的 `filename=` 指向本 skill 的 `scripts/js/*.js`。页面里没有 Node `fs`。
4. 点击一律 `{ force: true }`。复制走站点按钮 + `scripts/save_clipboard.py`，不要指望 Playwright `Control+V` 进输入框。

常用工具：`browser_tabs`（list/new/select）、`browser_snapshot`、`browser_find`、`browser_click`、`browser_run_code_unsafe`。

站点选择器、失败模式见 `references/`。

## 硬约束

- 每专利独立会话，禁止串案。
- 模型（2026-09-27 用户指定）：Gemini **Pro**（账号最高档，禁止 Flash-Lite）；ChatGPT 对话选 **GPT-6 Pro**（此前轮次为 GPT-6 Astra 极高）；Grok **Expert**；Perplexity 从 **`https://www.perplexity.ai/patents`** 进入，能选模型委员会就选 **Max**（`/` 搜索菜单，点满三模型后「提交」才可用），该入口下不能选则用页面可用最高档并在 md 中如实记录；Kimi 选 **K3** 模型并启用 **学术数据库** 插件。
- 粘贴用 `page.keyboard.insertText`。Perplexity 可对 composer `drop({files})`。
- 只改合理项：锁耦合、消 26.4 冲突、补说明书支持。数值/未实测公式不进独权。
- 每轮：`当前版本_YYYYMMDD` + wiki 一行 `` `GATE` `CASE` 版本 `YYYYMMDD` ``。

## 一案步骤

1. 准备全文：

```
D:/Python/Python314/python.exe D:/aicoding/mylib/paa/skills/browser-multi-model-review/scripts/prepare_case.py --case P0x-x --title "发明名称" --short "简写" --version 20260918 --src <含02/03/04/05的目录> --out <batch-dir>
```

或 `--cases-json` + `--case` + `--src`。再：

```
D:/Python/Python314/python.exe .../scripts/mk_site_insert.py --batch-dir <batch-dir> --case P0x-x --site gemini|chatgpt|grok|pplx
```

2. 新标签打开对应站点 → 选最高档 → 粘贴/拖放 → 发送。JS 在 `scripts/js/`。
3. 等生成结束：`browser_run_code_unsafe` `filename=scripts/js/wait_done.js`，`done:false` 就再调一次；ChatGPT 返回 `no_reply_button` 时执行 `chatgpt_continue.js` 后再等。**不要用快照轮询。**
4. 点复制按钮，然后单次调用 `post_copy.py`（合并 save_clipboard + wrap_eval + wiki_log，3 步 → 1 步）：

```
D:/Python/Python314/python.exe .../scripts/post_copy.py \
  --case P0x-x --gate GEMINI --version 20260918 \
  --url <会话URL> \
  --out-dir <案目录>/paa/evidence/browser_review \
  --log <项目>/wiki/log.md \
  --note "扩展思考" --section 八案四端审核
```

stdout 返回单行 JSON，含 `summary`（400 字结论摘要）、`out_md`（全文路径）、`wiki`（wiki 行）、`raw_len`（字符数）。
**Claude 只读 `summary` 字段**，不 Read 全文 md，全文留作存档。

5. 四门齐后按 `prompts/adoption-rules.md` 改 02/03/05，升版本，再 `wiki_log` 新版本号行。

Gate 标识词只能是：`GEMINI` `GROK-EXPERT` `GPT-6-PRO` `PPLX-PATENTS` `KIMI-K3-ACADEMIC`。
历史记录中的 `GPT-ASTRA-HIGH`（GPT-6 Astra 极高轮次）与 `PPLX-COMMITTEE`（普通 `/search` 入口的委员会轮次）保留原名，不回改。

## 各端要点（摘要）

| 端 | 输入框 | 发送 | 复制 | 拒答/中断 |
|---|---|---|---|---|
| Gemini | `为 Gemini 输入提示` | `gemini_submit.js` | `gemini_copy_footer.js`（点「风险清单」后最后一个「复制」） | 标题「对话终止」须新开；否则 `gemini_reframe.js` |
| ChatGPT | `与 ChatGPT 聊天` | `chatgpt_submit.js` | **复制回复** last()，不要「复制消息」 | 只有用户气泡则 `chatgpt_continue.js` |
| Grok | `Ask Grok anything` | 先 Dismiss「Meet Grok Bot」，再 `grok_submit.js` | `Copy response` | Expert 检索可 >3 min；md 如实记录 |
| Perplexity（`/patents`） | contenteditable last | `/` → 模型委员会 → 三模型 Max → `pplx_click_submit.js`（`/patents` 下菜单若不同，按实际页面并记录） | 最后一个「复制」 | 「提交」在 0 个模型时禁用 |
| Kimi（`kimi.com`） | 待首次实跑补录（`mk_site_insert.py` 暂用 contenteditable last 兜底） | 选 **K3** → 启用 **学术数据库** 插件 → 发送 | 待首次实跑补录 | 插件未生效时不得把回答当学术检索结果 |

Perplexity 一律从**专利搜索入口** `https://www.perplexity.ai/patents` 进入（区别于普通 `/search`；本机命令行直连该地址被 Cloudflare 403，
只能走浏览器会话）。Kimi 的价值在学术文献（NPL）腿：提问时要求其列出 DOI/arXiv ID/期刊卷期，便于逐条核验。

Gemini 新会话把专利当法律咨询时，改称「中国发明专利申请技术文件质量评估，不是法律意见」。标题已是「对话终止」时同线程追问无效。
