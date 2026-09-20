# 已踩坑（按类，不要再写成一次性补丁）

1. **扩展模式文件选择器失败** → 粘贴 Markdown；Perplexity 可 `drop`。不要假称已上传。
2. **系统剪贴板进不了 composer** → `keyboard.insertText`；生成 insert JS 时把全文 JSON 嵌进脚本。
3. **`require is not defined`** → `run_code_unsafe` 不是 Node 页面脚本，禁止 `fs`。
4. **串案** → 每案每端新 URL。混线程会把两案评在一起。
5. **Gemini 法律拒答** → 技术文档 framing。标题「对话终止」必须新开，同线程 reframe 无效。RAG/LLM 主题可能连续拒答（P05-1 两次）。
6. **ChatGPT「复制消息」** → 那是用户提示。必须「复制回复」。无该按钮则 continue。
7. **Grok Submit 被 Bot 对话框挡住** → Dismiss 后再 Submit。
8. **Perplexity 提交 disabled /「0 个模型」** → 委员会在 `/` 菜单；三模型未齐不要点提交。
9. **wiki_log 追加到 EOF** → 行必须插入含 `--section` 标记的标题下、下一 `##` 之前。
10. **网页模型专利号** → 非指定对比文件；不得写入申请对比文件表，不得当 incoPat 命中。
11. **Python 3.14 + PIL** → Word/AHP 用 3.12。本 pack 的 prepare/wiki_log/wrap_eval 用 3.14 即可。
