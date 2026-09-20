---
name: browser-multi-model-review
description: >
  Playwright MCP 浏览器控制包：在已登录 Chrome 扩展会话里操作 Gemini、ChatGPT、Grok、Perplexity，
  每案独立会话、最高档模型审核中国发明专利申请文件。上传失败则 insertText 粘贴；回复写入入口标识 md；
  wiki 日志必须含标识词+版本号。TRIGGERS: 浏览器四端审核, Playwright MCP, Gemini 扩展思考,
  GPT-6 Astra 极高, Grok Expert, Perplexity 模型委员会, 独立会话评专利, /browser-multi-model-review
---

# 浏览器四端控制（Playwright MCP）

父会话亲自操作浏览器。不要再 spawn 会抢同一 Chrome 的子代理。
不调用 incoPat。不编造专利号。网页模型点名的文献一律标「非指定对比文件」。

解释器：`D:/Python/Python314/python.exe`。python-docx / AHP 用 `C:\WINDOWS\py.exe -V:3.12`。

## MCP 用法

1. 先 `search_tool` 取 Playwright 工具 schema，再 `use_tool`。不要猜参数名。
2. 会话须是 Playwright **扩展模式**（已登录的 Chrome）。`setFiles` 常返回 `Not allowed`。
3. 长脚本用 `playwright__browser_run_code_unsafe` 的 `filename=` 指向本 skill 的 `scripts/js/*.js`。页面里没有 Node `fs`。
4. 点击一律 `{ force: true }`。复制走站点按钮 + `scripts/save_clipboard.py`，不要指望 Playwright `Control+V` 进输入框。

常用工具：`browser_tabs`（list/new/select）、`browser_snapshot`、`browser_find`、`browser_click`、`browser_run_code_unsafe`。

站点选择器、失败模式见 `references/`。

## 硬约束

- 每专利独立会话，禁止串案。
- 模型：Gemini 账号最高档（禁止 Flash-Lite）；ChatGPT **GPT-6 Astra 极高**；Grok **Expert**；Perplexity **模型委员会 Max**（`/` 搜索菜单，点满三模型后「提交」才可用）。
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
3. 等生成结束（ChatGPT「停止回答」消失且出现「复制回复」）。
4. 点复制按钮，然后：

```
D:/Python/Python314/python.exe .../scripts/save_clipboard.py <raw.txt>
D:/Python/Python314/python.exe .../scripts/wrap_eval.py --case P0x-x --gate GEMINI --url <会话URL> --raw <raw.txt> --note "扩展思考" --out-dir <案目录>
D:/Python/Python314/python.exe .../scripts/wiki_log.py --case P0x-x --gate GEMINI --version 20260918 --url <会话URL> --log <项目>/wiki/log.md --section 八案四端审核
```

5. 四门齐后按 `prompts/adoption-rules.md` 改 02/03/05，升版本，再 `wiki_log` 新版本号行。

Gate 标识词只能是：`GEMINI` `GROK-EXPERT` `GPT-ASTRA-HIGH` `PPLX-COMMITTEE`。

## 四端要点（摘要）

| 端 | 输入框 | 发送 | 复制 | 拒答/中断 |
|---|---|---|---|---|
| Gemini | `为 Gemini 输入提示` | `gemini_submit.js` | `gemini_copy_footer.js`（点「风险清单」后最后一个「复制」） | 标题「对话终止」须新开；否则 `gemini_reframe.js` |
| ChatGPT | `与 ChatGPT 聊天` | `chatgpt_submit.js` | **复制回复** last()，不要「复制消息」 | 只有用户气泡则 `chatgpt_continue.js` |
| Grok | `Ask Grok anything` | 先 Dismiss「Meet Grok Bot」，再 `grok_submit.js` | `Copy response` | Expert 检索可 >3 min；md 如实记录 |
| Perplexity | contenteditable last | `/` → 模型委员会 → 三模型 Max → `pplx_click_submit.js` | 最后一个「复制」 | 「提交」在 0 个模型时禁用 |

Gemini 新会话把专利当法律咨询时，改称「中国发明专利申请技术文件质量评估，不是法律意见」。标题已是「对话终止」时同线程追问无效。
