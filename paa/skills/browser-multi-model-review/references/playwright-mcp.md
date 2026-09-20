# Playwright MCP 控制约定

扩展模式：已登录的用户 Chrome，不是无头空配置。文件选择器 `setFiles` 常报 `Not allowed`；不要把这当成「已上传」。

## 调用顺序

1. `search_tool` query 含 `playwright` 与动作名，读取 `input_schema`。
2. `use_tool` 的 `tool_name` 必须是 `playwright__<tool>`。
3. 长交互写成 `async (page) => { ... }`，用 `browser_run_code_unsafe` 的 `filename` 指向本 skill `scripts/js/` 或案件 `insert_<site>.js`。

`run_code_unsafe` 在 Playwright 服务进程里跑，**不是**浏览器页面 VM。不要 `require('fs')`，不要假设 Node 全局。把文本嵌进 JS 字符串（`mk_site_insert.py`），或用 `page.keyboard.insertText`。

## 标签

- `browser_tabs` `action=list` 看现有会话，避免把两案贴进同一 URL。
- `action=new` + `url` 开独立会话。
- `action=select` + `index` 切回生成中的标签。

## 定位

优先 `browser_find` 再 `browser_snapshot(target=ref)`。整页 snapshot 在长专利粘贴后会截断。点击用 snapshot `ref` 或 JS `getByRole`；`click` 超时则 `{force:true}`。

## 剪贴板

Playwright `Control+V` 经常到不了 ChatGPT/Gemini composer。粘贴只走 `insertText`。收获回复：点站点复制按钮 → Windows `Get-Clipboard`（`save_clipboard.py`）→ `wrap_eval.py`。
