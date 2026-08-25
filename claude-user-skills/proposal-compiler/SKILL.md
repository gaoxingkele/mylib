---
name: proposal-compiler
description: |
  Grant Proposal Compiler for 科技部国际合作项目 (MOST international S&T cooperation;
  国家重点研发计划 政府间/港澳台 国际科技创新合作重点专项). Converts ANY proposal-related input —
  an old/draft 申报书 (PDF/Word), prior-round 函评意见 (reviewer comments), the 指南/call text,
  preliminary-experiment data/figures/code, PI & foreign-partner CVs/representative works,
  cooperation agreements/LOIs, or raw notes — into a structured, machine-navigable Grant Proposal
  Artifact (GPA): a cognitive layer (significance, key problems, innovation, INTERNATIONAL
  COOPERATION), a plan layer (technical route, task breakdown, KPIs, budget, risk), an exploration
  graph (drafting DAG incl. rejected framings and prior reviewer critiques), and grounded evidence
  (preliminary data, track record, agreements, references).

  TRIGGERS: compile proposal, 编译申请书, 编译本子, build GPA, create proposal artifact, 结构化申请书,
  convert 申报书, ARA from proposal, 把本子结构化, grant from PDF, 国际合作申报书, 重点研发计划申报书,
  整理函评, structure grant, 指南对接, 拟解决的关键科学问题
argument-hint: "<inputs...> [--output ./proposal/]"
---

# Proposal Compiler (GPA · 科技部国际合作)

Convert any grant-related input into a complete **Grant Proposal Artifact** under `--output`
(default `./proposal/`). The artifact spec is the GPA layout (logic / plan / trace / evidence; see
the bundled `README.md`). Specialized for 科技部国际合作项目: 指南对接 and 实质性国际合作 are
first-class, gated steps — not optional polish.

## Inputs (any combination)
- 旧/草稿申报书 (PDF / Word / Markdown) — the primary source if present.
- 往年函评意见 / 评审反馈 — mined into the exploration graph as dead-ends and required fixes.
- 指南 / 申报通知 / call text — becomes the **constitution**; every claim/KPI must map to it.
- 预实验数据、图表、代码、日志 — extracted into `evidence/preliminary/` (digitize plots to data points).
- 申请人 & 外方简历、代表作、在研项目 — into `evidence/track_record/`.
- 合作协议 / 意向书(LOI) / 对等支持函 — into `evidence/agreements/`; terms parsed into `intl_cooperation.md`.
- 散乱笔记 / 邮件 / 会议纪要 — atoms routed by content.

## 4-Stage protocol

### 1. 语义解构 (Semantic Deconstruction)
Read every input and extract atomic items, each tagged with a type and provenance:
- claim(意义/创新/必要性), key-problem(关键科学/技术问题), objective, content-item(研究内容),
  method/route, KPI(考核指标), budget-item, partner-fact(外方信息), agreement-term, evidence-datum,
  citation, guideline-clause(指南条款), reviewer-critique(往年函评), risk, decision/dead-end.
- Provenance: `user` (taken verbatim from a human-authored source) / `ai-suggested` (you propose to
  fill a gap) / `ai-executed` (you derived/computed) / `user-revised`. NEVER silently invent
  preliminary data, partner commitments, or funding figures — stub with `ai-suggested:NEEDS-INPUT`.

### 2. 认知映射 (Cognitive Mapping) → `logic/`
Map atoms into the cognitive layer, preserving cross-layer references:
- `significance.md` — 意义与必要性, explicitly tied to 国家需求 + the specific 指南方向 + 政府间协议背景.
- `state_of_the_art.md` — 国内外现状 as a typed citation graph (supports / contradicts / extends).
- `key_problems.md` — 拟解决的关键科学/技术问题: each falsifiable, scoped, and bound to ≥1 objective.
- `objectives.md` / `content.md` — 目标可考核; 内容按课题/任务划分; each content-item → a KPI and a task.
- `innovation.md` — 创新点: each MUST bind to evidence (`evidence/preliminary/` or `track_record/` or a
  citation). An innovation with no evidence binding is marked `UNSUPPORTED`.
- `intl_cooperation.md` — ★ structured fields: 合作必要性 / 外方互补优势 / 对等分工矩阵(中方·外方·共担) /
  对等投入(外方经费或所在国资助) / 协议或 LOI 引用 / IP 与数据安排 / 保密. Any missing field →
  `NEEDS-INPUT` and surfaced in the gap report.

### 3. 物理桩 (Physical Stubbing) → `plan/`
- `technical_route.md` — 技术路线闭环 + 可行性分析, each step bound to a key-problem and an objective.
- `task_breakdown.md` — 课题/任务分解 + 中外分工 + 时间节点 (Gantt-style list).
- `milestones_kpi.md` — 年度计划 + **量化考核指标** (number + unit + verification method) + 预期成果;
  flag any non-quantified KPI.
- `budget.md` — 科目预算 + 中外分摊 + 配套/对等说明 (stub figures as `NEEDS-INPUT` if absent).
- `risks.md` — 风险与应对, including the international-cooperation compliance set (数据出境 / IP / 伦理 /
  出口管制·制裁 / 协议时效).

### 4. 探索图提取 (Exploration Graph) → `trace/exploration_tree.yaml`
Reconstruct the drafting DAG with typed nodes and **dead ends**:
- node types: `framing`(立论框架), `aim`(研究内容/课题), `route`(技术路线), `partner`(合作方案),
  `budget`, `kpi`, `decision`, `dead-end`, `reviewer-critique`.
- From 往年函评: each critique becomes a `reviewer-critique` node linked to the `dead-end` it caused and
  the current node that addresses it ("上轮被批 X → 本轮改为 Y").
- Cut aims / rejected framings / abandoned partners are first-class `dead-end` nodes with a reason.

## 指南对接 gate (run after stage 3)
For every objective, content-item, and KPI, attach the matching 指南条款 (quote + locus). Produce a
**对接表** in `PROPOSAL.md`. Any item with no match → `脱靶风险` in the gap report. This is a hard gate:
the compile is "incomplete" until every KPI maps to the call or is explicitly waived by the user.

## 实质性国际合作 gate
Verify `intl_cooperation.md` has: (a) 互补且对等的分工, (b) 外方对等投入证据, (c) 实质协议/LOI,
(d) IP+数据安排. Missing any → list under `合作要素缺口` in the gap report (this maps to reviewer D4,
a desk-reject dimension).

## Output
- Write the full `proposal/` tree (create dirs as needed).
- `PROPOSAL.md` root manifest (~200 tokens): 一句话定位 + 专项/指南方向 + 合作国别 + 层级索引 +
  指南对接表 + 缺口清单(NEEDS-INPUT / 脱靶风险 / 合作要素缺口).
- End with a concise **缺口报告**: what is missing, what was AI-stubbed vs user-confirmed, and the
  top 5 things the PI must supply before this is review-ready.

## Hard rules
- Never fabricate preliminary results, partner commitments, funding amounts, or signed-agreement
  terms — stub as `NEEDS-INPUT`. A fabricated 对等经费 or 预实验 is a fatal integrity failure.
- Preserve the source language (Chinese 申报书 → Chinese artifact; bilingual partner content kept as-is).
- Keep human-confirmed (`user`) facts distinct from AI inferences in every file.
- Small, faithful extraction over creative rewriting; this is compilation, not ghostwriting.
