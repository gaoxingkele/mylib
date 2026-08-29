---
name: paper-writing
description: >
  论文写作与评估统一路由。覆盖论文全生命周期：选题与新颖性核查、文献检索与综述、
  结构化写作、严谨性评估与审稿模拟、降 AIGC 与润色、投稿路由、PDF 结构化、
  论文逆向与复现工程（paper-to-code 生成代码仓）。
  按需求自动派发到已安装的论文族 skill，统一证据与质量口径。
  TRIGGERS: 写论文, 论文写作, 评估论文, 审稿模拟, 论文润色, 降AIGC, 论文投稿, CCF会议,
  论文选题, 新颖性核查, 论文复现, 逆向工程, 复现代码, paper writing, peer review,
  rebuttal, 论文修改, paper to code
allowed-tools: Read, Write, Bash(D:/Python314/python.exe *|node *|uvx *|git *), Glob, Grep
---

# 论文写作路由（写论文 + 评估论文）

论文族统一入口。本 skill 不实现写作/评估本身，而是按论文生命周期把任务派发给已装入的论文族 skill，并统一质量口径。检索类需求由 `npl-prior-art-search` 路由（本族交叉引用），专利类需求由 `paa` 族负责。

## 路由表（按阶段自动选择，禁止同时盲目全跑）

| 阶段 | 路由到 | 何时用 |
|---|---|---|
| **选题与新颖性** | `idea_spark`（生成可证伪的研究想法）、`scoop_check`（查重先防：核查是否已被发表） | 动笔前；新 idea 必须过 scoop_check |
| **文献检索与综述** | `npl-prior-art-search` 路由（paper_search 初扫 / academic-search 中文 / paper-search-pro 深度 / literature-review 多视角综述） | 所有检索需求走它，不自建检索流程 |
| **结构化写作** | `ARA`（paper_compiler：研究过程结构化编译为可验证工件）或 `academic-research-suite`（outline→draft→revision 流程） | 已有研究素材 → 结构化成文 |
| **严谨性评估 / 审稿模拟** | `ARA` 内 `rigor-reviewer`（认知严谨性逐条审查）、`academic-research-suite` 的 review/revision 流程、`literature-review`（综述视角） | 投稿前、R&R 前；**评估论文是写作的一部分，不是可选项** |
| **降 AIGC / 润色** | `academic-humanizer`（学术化改写降 AI 痕迹）、Auto-Empirical-Research-Skills 的 de-AIGC 组 | 终稿前；保留事实，只改文风 |
| **投稿路由** | `Paper_CCF`（CCF 会议分区与匹配） | 选 venue、对照 deadline |
| **论文逆向 / 复现工程** | `repllm-content-parse`（PDF → 分层 paper.json）→ `paper-to-code`（Paper2Code 三阶段：规划 UML+依赖图 → 逐文件逻辑 → 按依赖序生成代码仓）→ `experiment-code` / `experiment-design` / `paper-compilation`（实验与成稿辅助） | 把论文复现为可运行工程 |
| **电力/电网论文专项** | `aers-powergrid-bridge`、`codex-ars-powergrid` | powergrid 领域论文 |
| **研究自动化 agent 进化** | `harnessbank-gated-evolution` | 非论文写作——改进支撑研究的 agent 栈 |

## 质量口径（与项目合规底线一致）

1. **引用真实**：每个引用带真实 DOI/arXiv ID/URL，禁编造文献号；检索走 `npl-prior-art-search` 的真实数据。
2. **评估从严**：审稿模拟/rigor 审查输出逐条可定位（段落级），不接受"整体不错"式结论；R&R 回复先改正文再写回复信。
3. **降 AIGC 合规**：只改表述不改成事实；不伪造引用、不洗稿；最终文责由作者承担。
4. **投稿前门禁**：rigor 审查 + 引用核验 + 降 AIGC 三关全过才进入投稿路由。

## 已装清单（事实源 `D:/aicoding/mylib`，各工具端 junction 引用）

- 写作族：`ARA`（mylib/ARA，8 子技能：manager/compiler/rigor-reviewer/visualizer/foresight/context-drop/research-fuzzer/submit）、`academic-research-suite`（Academic-Research-Skills-Codex）、`academic-humanizer`、`thesis-writing-skill`（素材库，按需启用）
- 评估族：`rigor-reviewer`（在 ARA 内）、`scoop_check`、`idea_spark`、`literature-review`
- 逆向/复现族：`repllm-content-parse`（PDF→paper.json）、`paper-to-code`（Paper2Code 三阶段）、`experiment-code`、`experiment-design`、`paper-compilation`（LaTeX 编译）
- 投稿族：`Paper_CCF`；领域专项：`aers-powergrid-bridge`、`codex-ars-powergrid`、管理世界 `mw-*` 套件
- 检索族（交叉引用）：见 `npl-prior-art-search` 的已装清单
