# AgentPanelX 研究报告：能否提炼为论文写作 Harness

**日期：** 2026-08-07
**对象：** https://aowo-1345.github.io/AgentPanelX/ ，源码已克隆至 `D:/aicoding/Lib/AgentPanelX/`（91 个 Python 文件 + React 前端，8.8 MB，MIT 系许可证见 LICENSE）
**结论先行：** **可以，且映射度异常高。** AgentPanelX 的七个核心原语几乎是论文写作治理流程的同构物——我们 2026-08-05～07 在两篇 Applied Sciences 稿件上手工执行的协议冻结、作者授权、账本、事件记录、协议演化，正是它产品化的东西。建议采用"轻量提炼"而非整体引入。

---

## 1. AgentPanelX 是什么

本地优先的**长周期交付运行时**（不是又一个 Coding Agent）：Project Owner 作为用户代理维护长期意图，把需求滚动拆成 Plan → Milestone → Stage；每个 Stage 在独立 Git worktree 里由 Codex CLI 执行；所有状态进 SQLite + EventBus Timeline；React 看板只是投影。三个 agent-native skills（Observe / Control / Attribution）让外部 Codex/Claude 在终端里只读观察、有边界介入、事后归因。

## 2. 七个可复用原语（与论文写作的直接映射）

| AgentPanelX 原语 | 机制 | 论文写作中的同构物（本项目实例） |
|---|---|---|
| **Plan Hard Gate + subject digest** | 批准对象、审查对象、提交对象绑定同一哈希，任一不匹配 fail-closed | 我们的协议冻结 SHA-256 + 授权绑定（BIRD `c7769959…`、标注协议 v1.0–v1.2）。AgentPanelX 把它做成了系统级关卡 |
| **Durable Activation / Stage** | 状态机 PENDING→RUNNING→terminal 持久化，进程重启可恢复；无法证明在跑的 RUNNING 重启后判失败 | 我们的后台 BIRD 运行、attempt 崩溃后的 incident 处理——目前是手工纪律，它是自动的 |
| **隔离 worktree + Candidate 决策** | 每个 Stage 独立 worktree，产出 commit 形成 candidate，Owner 决定 accept/reject 后才并入 | 论文场景：每轮修改/每个实验在独立分支，作者接受才并入主稿 |
| **BLOCKED 证据检查点** | 失败时固定 Runtime/Plan/Git/Timeline 现场 | 我们的 INCIDENT_*.md（目前是手工写） |
| **Timeline / EventBus** | 同步事件溯源，所有状态转换可查询 | 我们的 raw_ledger.jsonl / sample_manifest（ad-hoc 版） |
| **Attribution → Harness Evolution** | fork 只读 Historical Owner 质询复盘，阻塞归因沉淀为改进提案 | 我们标注协议 v1.0→v1.1→v1.2 的演化（裁决率 0.76→0.33→0.17）就是手工 harness evolution |
| **三权限 Skills** | Observe/Control/Attribution 是同一 Runtime 的三种权限面，非三套状态 | 论文 harness 里对应：审稿代理只读审阅、作者代理批准计划、复盘代理归因退稿/大修 |

## 3. 需要改造的部分（coding 专用，不能直接用于论文）

1. **Stage Executor 的完成判据**：代码场景是 build/test 通过；论文场景要换成——LaTeX 编译链通过（我们已验证 pdflatex×3+bibtex）、undefined citation/reference 扫描、声明完整性检查、数字与账本一致性核查（类似我们的晋级门禁）。
2. **Agent 传输层**：`CodexTurnTransport` 绑定 openai-codex SDK；论文角色（Writer/Reviewer/Experimenter）应走我们的 Cloubic 多模型路由，且 Reviewer 要与 Writer 不同家族（沿用标注管线的 A/B/C 经验）。
3. **Plan 文档集**：`requirements.md/architecture.md/roadmap.md` → 论文版应为 `claims.md`（主张清单）/ `evidence_map.md`（主张→证据工件映射）/ `journal_fit.md`（目标期刊画像引用，可接 D:/aicoding/paper_reviews/config/journals/ 的 9 份 YAML）。
4. **Candidate 验收**：代码合并 → 论文的"作者确认 diff + 重编译 + 合规复扫"。
5. 前端看板、Bubblewrap 沙箱等对论文场景价值低，可裁。

## 4. 提炼路线评估

**路线 A：直接用 AgentPanelX 跑论文项目。** 可行（Runtime 本身是领域无关的 Feature/Plan/Milestone/Stage），但代价是引入 Codex CLI 依赖、Node 前端和整套 web 运行时，且 Stage Executor 的编码语义仍需改造。重。

**路线 B：轻量提炼（推荐）。** 抽取其模式为 `D:/aicoding/Lib/paper_harness/`（约几百行）：
- `PaperOwner`：维护目标期刊、主张清单、证据边界、滚动待办（接 PROJECT_MEMORY 模式）
- **Hard Gate**：任何实验/修改提案先冻结 digest，作者批准绑定哈希后才执行（直接复用我们已验证的授权 JSON 模式）
- **Stage Runner**：durable 状态机 + 每 Stage 独立分支 + 完成后跑"论文验收脚本"（编译/引用/声明/数字一致性）
- **Evidence Timeline**：统一 SQLite 或 append-only JSONL 事件流，替代目前分散的 ledger 文件
- **Review Contract**：Reviewer 代理在隔离副本上按期刊 YAML 画像评审，输出结构化 issue matrix（我们 round1–3 已在手工做）
- **Attribution 复盘**：BLOCKED/拒稿时回放证据链，产出 harness 改进提案（协议版本化）
- 三权限 skill 写成 Kimi/Codex/Claude 通用 SKILL.md（沿用其 .codex/skills 格式，与我们 AGENTS.md 约定兼容）

**不建议**：整体依赖 AgentPanelX 运行时。其价值在设计模式而非代码复用——且项目较新（自举展示为主），绑定它会引入维护风险。

## 5. 风险与限制

- AgentPanelX 执行层强绑 Codex CLI（openai-codex 0.144.x），换模型路由需改 transport
- 其 Owner 基于 mini-swe-agent 的 ReAct loop，论文场景的长上下文（整篇稿件 + 账本）需要额外的上下文管理设计
- 官网自举展示（用它改造自己的前端）证明基本可用，但暂无第三方成熟度证据
- 论文 harness 的"验收脚本"覆盖率决定上限——编译通过 ≠ 主张有证据，evidence_map 核查需要领域规则（可从我们 round1–3 评审矩阵沉淀）

## 6. 建议的下一步

1. 在 `D:/aicoding/Lib/paper_harness/` 建最小骨架：Hard Gate + Stage Runner + Evidence Timeline 三件（最能解决我们当前的痛点：授权-执行-账本的一致性）
2. 以两篇 Applied Sciences 稿件的"三轮评审 + 投稿前清单"为第一个驱动用例
3. Reviewer 角色接 `paper_reviews/config/journals/` 的 9 份期刊 YAML
4. 验证后再决定是否引入看板前端

**参考实现位置**：`D:/aicoding/Lib/AgentPanelX/`（docs/architecture.md 是最佳入口；skills 在 .codex/skills/；Owner 工具在 src/agentplanex/project_owner_agent/tools/）
