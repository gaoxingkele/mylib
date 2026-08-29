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

论文族统一入口（ARA 式收敛：本目录为三端唯一注册入口，子技能在 `skills/` 下按需加载，不独立注册）。本 skill 不实现写作/评估本身，而是按论文生命周期把任务派发给子技能与兄弟族 skill，并统一质量口径。检索类需求由 `npl-prior-art-search` 路由（本族交叉引用），专利类需求由 `paa` 族负责。

**使用方法**：① 确定阶段 → ② 打开 `skills/<name>/SKILL.md` 执行（子技能自带 references/）→ ③ 按质量口径收口。

## 路由表（按阶段自动选择，禁止同时盲目全跑）

| 阶段 | 路由到 | 打开 | 何时用 |
|---|---|---|---|
| **选题与新颖性** | `idea_spark`（生成可证伪的想法）、`scoop_check`（查重先防）、`idea-evaluator`（五维评审式打分+致命缺陷审计） | spark/check 为兄弟族独立 skill；evaluator 在 `skills/idea-evaluator/SKILL.md` | 动笔前；新 idea 过 scoop_check，待选方向过 idea-evaluator |
| **文献检索与综述** | `npl-prior-art-search` 路由（paper_search 初扫 / academic-search 中文 / paper-search-pro 深度 / literature-review 多视角综述） | 兄弟族 | 所有检索需求走它，不自建检索流程 |
| **结构化写作** | `ARA`（paper_compiler）、`academic-research-suite`（outline→draft→revision）、`paper-writer`（证据门控正文）、`intro-drafter`（引言六段式） | writer/intro 在 `skills/paper-writer/SKILL.md`、`skills/intro-drafter/SKILL.md` | 已有研究素材 → 结构化成文；引言单列走 intro-drafter |
| **哲学/理论型跨学科** | `academic-paper-strategist`（平台/框架/空白分析→审稿维度优化大纲）→ `academic-paper-composer`（学风格→逐章→终评；28/35 门槛） | `skills/academic-paper-strategist/SKILL.md` → `skills/academic-paper-composer/SKILL.md` | 概念推进与长链条论证型论文；需 8-10 篇样例做风格校准 |
| **严谨性评估 / 审稿模拟** | `ARA` 内 `rigor-reviewer`（认知严谨性，Seal L2）、`academic-research-suite` review 流程、`pre-submission-reviewer`（五维投稿前审查，CRITICAL/MAJOR/MINOR）、`literature-review`（综述视角） | reviewer 在 `skills/pre-submission-reviewer/SKILL.md` | 投稿前、R&R 前；顺序：先 rigor（claim↔evidence）后 pre-submission（五维面检）；**评估论文是写作的一部分，不是可选项** |
| **降 AIGC / 润色** | `academic-humanizer`（文风+证据对齐）或 `paper-polish`（忠于原意：中→英改写、证据强度对腔、AI 腔去除；可能动到含义的改动先列"需作者确认"） | polish 在 `skills/paper-polish/SKILL.md` | 终稿前；保留事实只改文风；语义敏感/中译英场景用 paper-polish 的确认机制，泛润色用 humanizer |
| **图表设计** | `figure-designer`（核心三图范式+质量审计） | `skills/figure-designer/SKILL.md` | 三图定生死，投稿前单独过一遍 |
| **长项目系统** | `research-writing-skill`（术语表/证据图/进度回写的工程化长稿系统） | `skills/research-writing-skill/SKILL.md` | 多章节跨会话长项目；短文润色用它会"流程比正文重" |
| **投稿路由** | `Paper_CCF`（186 件期刊/会议画像） | 兄弟族 | 选 venue、对照 deadline |
| **论文逆向 / 复现工程** | `repllm-content-parse`（PDF→paper.json）→ `paper-to-code`（Paper2Code 三阶段）→ `experiment-code` / `experiment-design` / `paper-compilation` | 兄弟族 | 把论文复现为可运行工程 |
| **电力/电网论文专项** | `aers-powergrid-bridge`、`codex-ars-powergrid` | 兄弟族 | powergrid 领域论文 |
| **研究自动化 agent 进化** | `harnessbank-gated-evolution` | 兄弟族 | 非论文写作——改进支撑研究的 agent 栈 |

## 质量口径（与项目合规底线一致）

1. **引用真实**：每个引用带真实 DOI/arXiv ID/URL，禁编造文献号；检索走 `npl-prior-art-search` 的真实数据。
2. **评估从严**：审稿模拟/rigor 审查输出逐条可定位（段落级），不接受"整体不错"式结论；R&R 回复先改正文再写回复信。
3. **降 AIGC 合规**：只改表述不改成事实；不伪造引用、不洗稿；最终文责由作者承担。
4. **投稿前门禁**：rigor 审查 + 引用核验 + 降 AIGC 三关全过才进入投稿路由。

## 已装清单（事实源 `D:/aicoding/mylib`，各工具端 junction 引用）

- 写作族：`ARA`（mylib/ARA，8 子技能：manager/compiler/rigor-reviewer/visualizer/foresight/context-drop/research-fuzzer/submit）、`academic-research-suite`（Academic-Research-Skills-Codex）、`academic-humanizer`、`thesis-writing-skill`（素材库，按需启用）
- 表达校准族（博导推荐三件套，2026-08-29 接入，**ARA 式收敛为本目录子技能 `skills/`，junction 指向上游源**）：`paper-polish`/`paper-writer`/`intro-drafter`/`pre-submission-reviewer`/`idea-evaluator`/`figure-designer`（Supervisor-Skills，**CC-BY-NC-SA-4.0 非商用许可**，商用场景慎用）、`research-writing-skill`（长项目系统）、`academic-paper-strategist`/`academic-paper-composer`（哲学/理论型）
- 评估族：`rigor-reviewer`（在 ARA 内）、`scoop_check`、`idea_spark`、`literature-review`
- 逆向/复现族：`repllm-content-parse`（PDF→paper.json）、`paper-to-code`（Paper2Code 三阶段）、`experiment-code`、`experiment-design`、`paper-compilation`（LaTeX 编译）
- 投稿族：`Paper_CCF`；领域专项：`aers-powergrid-bridge`、`codex-ars-powergrid`、管理世界 `mw-*` 套件
- 检索族（交叉引用）：见 `npl-prior-art-search` 的已装清单
