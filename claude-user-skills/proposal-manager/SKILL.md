---
name: proposal-manager
description: |
  End-of-turn grant-drafting recorder for 科技部国际合作项目, with progressive crystallization.
  Invoked at the END of EVERY turn (after the user's request is fully addressed, before yielding
  control). Reviews what happened in the turn, extracts proposal-significant events, and writes them
  into the proposal/ artifact via three stages: Context Harvester → Event Router → Maturity Tracker.
  TRACE events (起草决策, 被否的立论框架, 合作谈判进展, 函评意见的处理, 砍掉的研究内容, 经费调整,
  指南对接修订) are recorded IMMEDIATELY as journey facts. KNOWLEDGE events (定稿的创新点, 关键科学问题,
  研究目标, 中外分工, 考核指标, 合作协议条款) are STAGED first and crystallize into typed layers ONLY
  on closure signals — topic abandonment, PI verbal affirmation, empirical resolution (预实验结果),
  or artifact commitment (写入定稿/提交). NEVER mid-turn. All entries carry provenance tags
  (user / ai-suggested / ai-executed / user-revised).

  TRIGGERS: research-manager for grants, 记录起草, capture drafting, 申请书过程记录, log proposal decision,
  记录函评处理, 记录合作谈判, proposal journey, end-of-turn proposal
argument-hint: ""
---

# Proposal Manager (Live Capture · 科技部国际合作)

Run at the end of a turn to accrue drafting knowledge as a side-effect of ordinary work. Target the
GPA artifact (default `./proposal/`; if none exists, write to `./proposal/trace/` and note that a
full compile via `/proposal-compiler` is recommended).

## Stage 1 — Context Harvester
Scan the just-completed turn for proposal-significant signals:
- decisions made (chose framing A over B; merged 课题 2 into 1; raised KPI target).
- dead ends (a 立论 the PI rejected; a partner that fell through; an aim cut for scope/budget).
- 合作进展 (外方确认承担 X; 对等经费口头答应待函; LOI 拟签).
- 函评处理 (上轮函评第 N 条 → 本轮如何回应/修改).
- evidence changes (新预实验结果; 代表作更新; 协议文本到位).
- 指南对接修订 (对接条款变化; 发现脱靶并修正).
For each, capture: what, why, who originated it (provenance), and any locus in the artifact.

## Stage 2 — Event Router
Route each signal to TRACE or KNOWLEDGE:
- **TRACE (write now)** → `trace/exploration_tree.yaml` as a typed node
  (`decision` / `dead-end` / `partner` / `reviewer-critique` / `pivot` / `budget` / `kpi`), linked to
  the nodes it supersedes or addresses. Trace is append-only; never delete a dead end — that is the
  point (prevents re-litigating settled rejections on resubmission).
- **KNOWLEDGE (stage, don't commit yet)** → a staging note. Knowledge = durable claims that belong in
  `logic/` or `plan/` (a finalized 创新点, 关键问题, 分工矩阵 row, 考核指标, 协议条款). Hold until a
  closure signal fires.

## Stage 3 — Maturity Tracker
Crystallize staged knowledge into the typed layer ONLY on a closure signal:
- **topic abandonment** — the thread moved on without reopening → demote to a `dead-end` if dropped, or
  crystallize if settled.
- **PI verbal affirmation** — "就这么定 / 用这个 / 对" → crystallize with provenance `user`.
- **empirical resolution** — a 预实验/数据 settled the question → crystallize with `ai-executed` +
  evidence binding.
- **artifact commitment** — text was written into a 定稿 section or the 申报书 → crystallize as `user`.
Until a closure signal, leave it staged. NEVER crystallize mid-turn or on speculation.

## Provenance (mandatory on every entry)
`user` (PI stated/confirmed) · `ai-suggested` (you proposed) · `ai-executed` (you derived/computed) ·
`user-revised` (AI draft the PI edited). 合作承诺与经费数字默认 `ai-suggested:NEEDS-INPUT` until the
PI or a document confirms them — never upgrade a partner's commitment to `user` without a source.

## Output discipline
- Idempotent: do not duplicate a node already recorded; link/refine instead.
- Quiet: emit a one-line summary of what was recorded (counts by type), not a wall of text.
- If nothing proposal-significant happened, record nothing and say so.
- Special care for the two gated dimensions: any change to 实质性国际合作 (D4) or 指南对接 (D1) is always
  trace-worthy and flagged in the summary, because they decide desk-reject outcomes.
