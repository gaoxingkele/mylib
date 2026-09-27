# browser-multi-model-review

Playwright MCP 浏览器控制包：Gemini / ChatGPT / Grok / Perplexity（`/patents`）/ Kimi（K3 + 学术数据库）独立会话、最高档模型审核中国发明专利申请文件。

**仅手动触发**：只在用户明确要求时运行，不属于任何自动化流程（见 `SKILL.md`「触发方式」）。

入口：`SKILL.md`。站点选择器与失败模式在 `references/`。可执行脚本在 `scripts/`，页面片段在 `scripts/js/`。

测试：

```
D:/Python/Python314/python.exe -m unittest discover -s tests -v
```
