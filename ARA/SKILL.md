---
name: ara
description: >
  Route Agent-Native Research Artifact work to maintained modules for research capture, compilation,
  rigor review, visualization, grounded foresight, context sharing, research fuzzing, and publication.
  Use when creating or verifying an ARA, recording decisions and experiments, visualizing an
  exploration graph, asking artifact-grounded questions, or publishing an ARA.
---

# ARA — Agent-Native Research Artifact（统一 skill）

复刻自论文 **《The Last Human-Written Paper: Agent-Native Research Artifacts》**(arXiv:2604.24658，本地 PDF：`D:/aicoding/mylib/ARA/ARA_paper_2604.24658.pdf`) 的开源工具箱
(`AmberLJC/Agent-Native-Research-Artifact`, MIT，同步 commit e52a925 / 2026-08-29)。把 AI 科研过程中"被覆盖的代码、散落的日志、无人记录的死路"强制变成
**结构化、可验证、可追溯**的研究产物(ARA),让人类无需逆向数千行终端输出就能信任 AI 产出的科学。

本文件是**统一入口**:按意图路由到 `skills/<name>/SKILL.md` 里的 8 个专用子技能(原库逐字保留)。参考代码在 `packages/`（ara-skills CLI + ara-viewer）。

## 三条核心设计原则

- **🛡️ 护栏与验证 (Guardrailing & Verification)** —— 作为"认知锚",把每条科学主张直接接到 ground-truth 执行与可证伪结果上,防幻觉结论。
- **🧠 结晶洞见 (Crystallizing Insights)** —— 强制 AI 科学家系统记录其"充满转折与死路的图状轨迹",把易逝的非结构化日志结晶成可靠知识。
- **👁️ 完全可观测 (Total Observability)** —— 把复杂的 agent 行为与探索图翻译成极简界面,人类做高层监督、随时介入纠偏。

## 使用方法（按意图路由）

先判断用户想做什么,再打开对应子技能的 `SKILL.md` 执行(每个子技能自带 `references/` 规范,相对路径已就绪):

| 你想… | 子技能 | 打开 |
|---|---|---|
| **记录** 研究过程(决策/实验/消融/死路/配置),边做边写进 `ara/` | **research-manager** | `skills/research-manager/SKILL.md` |
| **编译** 已有论文/仓库/代码/笔记 → 完整 ARA | **compiler** | `skills/compiler/SKILL.md` |
| **验证** 一个 artifact 的认知严谨性(信任/发表前；即 Seal Level 2) | **rigor-reviewer** | `skills/rigor-reviewer/SKILL.md` |
| **可视化** 整个研究轨迹为交互式 HTML 过程图 | **research-visualizer** | `skills/research-visualizer/SKILL.md` |
| **提问** 对某个 ARA 给出有根据、可证伪的回答("下一步试什么/为何有效/若改 X 会怎样") | **research-foresight** | `skills/research-foresight/SKILL.md` |
| **分享** 文件/文件夹给另一个 agent(一个 URL,免仓库免压缩包) | **context-drop** | `skills/context-drop/SKILL.md` |
| **驾驭** 开放式调查(像 fuzzer 一样:每次行动前预测、跟踪未尝试线索、防原地打转、结论先自驳) | **research-fuzzer** | `skills/research-fuzzer/SKILL.md` |
| **提交/发布** 一个 ARA(校验/编译→可视化→发到 GitHub→上架 ARA Hub) | **submit-ara** | `skills/submit-ara/SKILL.md` |

路由步骤:①确定意图 → ②打开对应 `skills/<name>/SKILL.md` → ③严格按其规范执行,按需加载它的 `references/`。
子技能之间会互相引用(如 submit-ara 会调用 compiler / research-visualizer)——它们都在本 skill 的 `skills/` 下同级并存。

**让"记录"自动化**:把下面这段加到你的 agent 系统提示文件(`CLAUDE.md` / `AGENTS.md` / `.cursorrules`)里,记录就会每轮自动填充:
```markdown
## ARA: end-of-session research capture
At the END of every coding session, invoke the research-manager skill (skills/research-manager/SKILL.md)
to record decisions, experiments, dead ends, and claims into the ara/ artifact.
```

## ARA 产物结构（四层，所有子技能读写同一结构）

```
example_artifact/
  PAPER.md                    # 根清单 + 层索引 (~200 tokens，渐进披露入口)
  logic/                      # 认知层 — What & Why
    claims.md                 #   可证伪断言 + 证据引用
    experiments.md            #   声明式实验计划
    solution/{architecture,algorithm,constraints}.md
    related_work.md           #   带类型的依赖图
  src/                        # 物理层 — How
    configs/                  #   带 rationale 的超参
    environment.md            #   依赖/硬件/种子
  trace/                      # 探索图 — Journey
    exploration_tree.yaml     #   研究 DAG，含带类型节点 + 死路(×)
  evidence/                   # 原始证据
    tables/  figures/         #   精确结果表 + 抽取的数据点
```

关键结构原则:**渐进披露**(PAPER.md ~200 tokens 决定是否深入)· **跨层绑定**(claim↔experiment↔evidence↔code 全部可解析)·
**保留死路**(失败方案是探索图的一等节点,不丢弃)· **溯源标签**(每条目标注 `user`/`ai-suggested`/`ai-executed`/`user-revised`)。

## 示例（可直接参考的真实 ARA）

- `examples/minimal-artifact/` —— 最小 ARA(PAPER.md + logic/ + trace/)。
- `examples/resnet-ara-example/` —— 完整 ARA(四层齐全),配 `examples/resnet-walkthrough.md`。

## 全局使用 & 说明

- Codex 使用轻量入口 `~/.codex/skills/ara/`；完整模块保留在 `D:/aicoding/mylib/ARA/skills/`，由入口按需读取。
- 官方也提供 npx 安装器把技能**分别**装成独立 skill(`npx @ara-commons/ara-skills`,自动识别 Claude Code/Cursor/Gemini/Codex,可选全局/本地)。本统一 skill 是把它们**收敛成一个 `/ARA` 入口**的等价封装,内容逐字保留。
- 遵循 [Agent Skills 开放标准](https://agentskills.io/specification),跨 Claude Code / Codex / Cursor 等通用。

## 归属与许可

来源:`AmberLJC/Agent-Native-Research-Artifact`(MIT © 2026 Orchestra Research);论文 arXiv:2604.24658。
8 个子技能与其 `references/`、`packages/` 参考代码、示例、`LICENSE` 均逐字保留于本目录(见 `UPSTREAM_README.md`,内含 provenance 与同步清单)。工具本身以官方仓库为准,规范更新时以上游为准。
