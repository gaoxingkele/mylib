# 四端选择器（2026-09-20 实测）

模型名单会变。以页面当前按钮文案为准；下表是当时可用的最高档。

## Gemini `gemini.google.com/app`

- 输入：role `textbox` name `为 Gemini 输入提示`
- 发送：role `button` name `发送`（不要在 click 后再 `getAttribute`，会超时）
- 复制：先点 heading `/风险清单/`，再最后一个 exact name `复制`。`复制` last() 有时会拿到 16 字符失败剪贴板，改走页脚复制。
- 新聊天法律拒答：同线程 `gemini_reframe.js`。标题为 `对话终止` / `拒绝回答` 时重开。

## ChatGPT `chatgpt.com`

- 输入：role `textbox` name `与 ChatGPT 聊天`
- 模型按钮须为 `GPT-6 Astra 极高`
- 发送：`发送提示|发送`
- 复制：`复制回复` last()。仅有 `复制消息` 时复制的是用户提问。
- 未完成：存在 `停止回答`。回复只有「评」等残句时发 `chatgpt_continue.js`。

## Grok `grok.com`

- 输入：role `textbox` name `Ask Grok anything`
- 模型：`Model select` 显示 `Expert`。home 上可能没有 name=Expert 的独立按钮。
- 发送：role `button` name `Submit`。若弹出 Meet Grok Bot，先 Dismiss。
- 复制：`Copy response`
- 提交后 URL 变成 `/c/<uuid>`，记下该 URL。

## Perplexity `perplexity.ai`

- Composer：`locator('[contenteditable="true"]').last()`
- **模型委员会不在「模型」按钮里**（那是 最佳 / GPT-5.6 Sol Max 等单模型列表）。在搜索框键入 `/`，选 **模型委员会**。
- 点满三个模型后「提交」才启用。2026-09-20 组合：模型1 GPT-5.6 Sol Max（正在思考）、模型2 Claude Opus 5 Max（正在思考）、模型3 Gemini 3.8 Flash。名单漂移时仍选各槽 Max + 思考。
- 提交：role `button` name `提交`
- 复制：exact name `复制` last()
- 重命名：会话操作 → `Pxx-x 简写`。标签仍可能显示提问摘要。
