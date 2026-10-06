---
name: jev-help-decide
description: 以“jev帮我决策”为每轮问答提供自动 JEV 辅助判断，支持股票研究、专利项目和一般方案讨论。用户已授权每轮一次精简 API 调用；检查方案、证据及回答与目标的一致性。
---

# jev帮我决策

用户要求每轮问答自动使用。每个用户回合在最终回答前调用一次，不在每条进度消息、工具结果或后台通知上重复调用。用户明确暂停、取消或要求不外发时立即遵从。不要为了 JEV 无关建议扩展任务。

## 执行

1. 理解请求并完成必要查证，形成暂定回答；不把 JEV 当搜索引擎。
2. 将必要上下文写入临时 UTF-8 JSON：`domain` 为 `stock`、`patent` 或 `general`，`user_request`、`goal`、`facts`（带来源）、`unknowns`、`options`（可空）、`draft_answer`（精简要点）。`disclosure` 必须为 `sanitized` 或 `public`。如有多个领域，按本轮实际任务选择，不混入另一个项目的资料。
3. 执行 `python C:/aicoding/mylib/skills/jev-help-decide/scripts/decide.py --input <JSON路径> --project <当前项目路径>`。依赖 Python 标准库。合并独立问题，一轮一次请求；服务临时限流最多重试一次。
4. 阅读真实返回的 `answers`。回到原始证据检查重要分歧，必要时修正回答。JEV 不返回解释文本，不能替它编造理由、引用、诊断或证据。Noul 是“是”的概率，Choice confidence 是分布集中度，不是正确率。保持主模型独立判断，不用固定阈值自动执行动作。
5. 回答主体保持自然简洁。确实改变决策或有重要分歧时说明 JEV 的原始判断与核查依据；否则仅在结尾用一句“JEV 辅助检查已完成”。失败时说明“JEV 本轮不可用，按已核查证据回答”，不得声称调用成功。

## 自动调用边界

- 调用授权覆盖必要的精简问答上下文，不包含密钥、账号、凭据、整段会话、自动读取全文或其它项目内容。脚本不读取项目业务文件，只读取明确给出的输入包及凭据文件。
- 专利：保留本项目“未公开技术仅本机处理”的约定；自动调用只发送去除发明机制、参数、商业信息的流程级摘要。不能去除敏感信息且保持问题有效时，不发送该技术内容，说明本轮外部判断范围受限。外部全文评审必须有针对该内容的明确授权；本工具不触发浏览器多端评审。
- 本技能只提供意见，不启用 S20 合约、切换主对话模型、提交专利或替代人工最终决定。
- 不递归调用本技能，不自动启动子代理。正常问答也使用精简通用审查，不能擅自改成仅关键决策时调用。

## 项目侧重点

- 股票：分开上涨比例、先触发止损比例、期望收益；区分建仓与持有。读取本轮最新合约/实验，不把历史状态写死在 Skill 中。判断模型意见不等于回测证据。
- 专利：分别看技术问题—机制—效果、文本支持和真实对比文件；只用已提供且核验的资料。JEV 不能证明新颖性、创造性或授权率。对一篇已公开文献做要素判别时改用 `patent-jev-screen`，不要把未公开说明书放进本技能的自动调用。
- 一般讨论：审查拟议回答是否满足用户目标，是否遗漏决定所必需的事实；无须人为制造候选方案。

## 凭据与记录

优先环境变量 `TYPESAFE_API_KEY` / `JEV_API_KEY`，再取当前项目 `.env`，最后兼容本机 `C:/aicoding/jev.env.txt`。凭据不复制、不输出。`--dry-run` 仅检查输入和构造请求；`--self-test` 使用本地模拟服务检查接口与失败处理。每次只记 UTC 时间、输入哈希、模型、回答、usage、耗时/错误类别到本 Skill 的 `runtime/calls.jsonl`，不存会话原文。若本地写记录失败，返回 `audit_error`，不丢失已获得的 API 结果。

## 官方依据

封装基于 [TypeSafe 官方 Agent Skill](https://docs.typesafe.ai/agent-skill)，上游原件及 MIT 许可保留在 [references/typesafe-ai/SKILL.md](references/typesafe-ai/SKILL.md)。首次使用读该参考；修改 API 时按其要求核对 [HTTP API](https://docs.typesafe.ai/api)、[Choice](https://docs.typesafe.ai/primitives/choice)、[coding agents](https://docs.typesafe.ai/introduction/coding-agents)。问题和候选集中定义在 `scripts/decide.py`，便于审查。此 Skill 是代理工作流指令，不是宿主强制消息拦截器；新会话必须加载持久指令，实际工具仍由代理执行。
