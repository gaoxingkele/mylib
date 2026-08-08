# DIGEST — Codex 做研究的正确姿势 + ARS

来源浓缩自：
- OpenAI Codex Best Practices
- [academic-research-skills-codex](https://github.com/Imbad0202/academic-research-skills-codex)
- 用户提供的图文教程（Codex App 视角）

核心理念：**别把 Codex 当命令行 ChatGPT；给它研究现场 + 规则 + 完成标准。**

---

## 0. 四种形态（同一账号）

| 形态 | 适合 |
|---|---|
| Codex App | 新手 / 多数科研用户（教程默认） |
| IDE 插件（VS Code / Cursor） | 写代码的人 |
| CLI | 终端老手 |
| Codex Cloud | 远程挂任务 |

Skill / `AGENTS.md` 在四种形态间通用。本机已同时挂 Claude skills 与 Codex skills。

---

## 1. 六个核心动作

### 动作一：先给工作区，再聊天

研究现场目录（可让 AI 建）：

```text
my-research/
├── AGENTS.md
├── research-question.md
├── literature/
├── data/
├── drafts/
└── outputs/
```

本仓库等价现场：
- 文献 / 蒸馏：`papers/literature/`、`D:/aicoding/lib/powergrid_paper/`
- 手稿：`paper_projects/`
- 期刊规则：`Paper_CCF` / `~/.claude/skills/Paper_CCF`

### 动作二：规则写入 `AGENTS.md`

可执行条款，不是口号。模板见 `AGENTS.academic.template.md`。
分层：`~/.codex/AGENTS.md`（个人）→ 项目根 → 子目录更严。

### 动作三：每个任务讲清四件事

1. **Goal** — 要做成什么  
2. **Context** — 相关文件 / 材料  
3. **Constraints** — 红线（不编造引用、只用 literature/ 等）  
4. **Done when** — 完成标准  

简单任务低推理；审稿 / 方法收敛用高推理。

### 动作四：难题先 Plan

`/plan` 或先反问，再写大纲/正文。研究问题未收敛时禁止直接写三千字。

### 动作五：当审稿人，不当夸夸机

用 `/review`、diff、引用核查。输出要直接：desk-reject 风险、证据错配、虚构引用。

### 动作六：一个阶段一个线程

文献 / 草稿 / 数据分线程；过长用 `/compact`；分叉用 `/fork`。

---

## 2. ARS（academic-research-suite）

**装 Codex 版，不要装 Claude Code 四 skill 拆分布局。**

本机路径：`Academic-Research-Skills-Codex/skills/academic-research-suite/`（单入口 router）。

五个内部工作流（由 router 选，不单独注册）：

| 工作流 | 干什么 |
|---|---|
| `deep-research` | 文献、综述、苏格拉底收敛问题 |
| `academic-paper` | 大纲 / 摘要 / 改稿 / 引用格式 |
| `academic-paper-reviewer` | 多视角审稿、编辑决策 |
| `academic-pipeline` | 研究→成稿全流程 + 诚信闸门 |
| `experiment-agent` | 实验规划、统计解读、可复现清单（不替你跑实验） |

### 调用方式

```text
Use $academic-research-suite to help me plan a literature review on ...
```

常用别名（Codex 内模拟）：

| 别名 | 作用 |
|---|---|
| `ars-plan` | 引导式规划章节 |
| `ars-outline` | 只出大纲 |
| `ars-abstract` | 摘要 |
| `ars-lit-review` | 文献综述 |
| `ars-citation-check` | 查引用 |
| `ars-full` | 完整 pipeline |

### 验证

新对话列出 skills：**只应出现一个** `academic-research-suite`。

---

## 3. 红线

- AI 是副驾驶不是机长：署名与科学判断在你。  
- 不编造论文 / DOI / 系数；证据不足标「待核实」。  
- 第三方 skill 先读 `SKILL.md`；外部源优先只读。  
- 幻觉引用是真问题；ARS 诚信闸门辅助，终核仍是人。

---

## 4. 进阶（知道即可）

权限收紧 → 每次改动确认；MCP 接文献库优先只读；流程跑稳再固化成 Skill。
