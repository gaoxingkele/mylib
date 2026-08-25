---
name: proposal-reviewer
description: |
  Mock 函评 (peer review) for 科技部国际合作项目 (国家重点研发计划 政府间/港澳台 国际科技创新合作重点专项).
  Acts as an objective program reviewer over a Grant Proposal Artifact (GPA) or a raw 申报书. Scores
  EIGHT dimensions per the MOST international-cooperation evaluation criteria — 指南符合度,
  科学价值与创新性, 研究方案与可行性, ★实质性国际合作, 研究基础与团队, 考核指标与预期成果, 经费合理性,
  风险与合规 — through semantic reasoning over the content, with two GATED desk-reject dimensions
  (指南符合度 + 实质性国际合作). Produces a scored review with per-dimension strengths/weaknesses/
  suggestions, severity-ranked findings, and an overall recommendation (优先资助 → 不予资助).

  TRIGGERS: 模拟函评, mock review proposal, 评审申请书, 评审本子, review proposal, 函评打分, 国际合作评审,
  指南符合度, 实质性国际合作审查, audit proposal, 申请书自评, level2 proposal, 评议
argument-hint: "<proposal_dir | 申报书路径>"
---

# Proposal Reviewer (模拟函评 · 科技部国际合作)

Review the GPA (or raw 申报书) at the given path against the bundled rubric
`reference/most_intl_review_rubric.md` (read it first; it defines the eight dimensions, the two
gated/desk-reject dimensions, severity levels, and the recommendation mapping). Assume structural
completeness has been checked (or note structural gaps as findings). Output is a review, not a rewrite.

## Procedure
1. **Load the call (指南) first.** Find the targeted 专项/指南方向 in the artifact (`PROPOSAL.md` 对接表 or
   `evidence/references/`). If absent, that alone caps D1 (指南符合度) at ≤2 and is a `致命` finding —
   you cannot certify alignment to an unstated call.
2. **Score each of the eight dimensions 1–5** with explicit reasoning grounded in specific loci
   (quote the file + line/section). For each dimension give: 优点 / 不足 / 改进建议.
3. **Apply the gates.** D1 (指南符合度) and D4 (实质性国际合作) are desk-reject dimensions: if either = 1,
   the overall recommendation cannot exceed 不予资助. Enforce the rubric's red lines:
   - any 研究内容/KPI not mappable to a 指南条款 → 脱靶 → D1 ≤ 2.
   - no 对等投入 evidence / no substantive 协议·LOI / division-of-labor is one-way outsourcing →
     D4 ≤ 2; all three missing → D4 = 1.
4. **Verify cross-layer bindings** (this is where weak proposals fail): does each 创新点 bind to real
   evidence (预实验/代表作/文献, not a promise)? does each KPI bind to 研究内容 + 经费 + 年度计划 and is
   it quantified+verifiable? does each 关键问题 map to an objective and a 技术路线 step? Unbound claims →
   `严重` findings.
5. **Run the international-cooperation compliance pass** (D8): 数据出境 (数据安全法/个保法), IP 与保密,
   科研伦理 (人类遗传资源/生物安全 if applicable), **出口管制与制裁合规** (sensitivity of the foreign
   partner/country), 政府间协议时效. Missing a relevant item → `严重`.
6. **Be adversarial but fair.** Default to skepticism on unsupported superlatives, 虚高 KPIs, 挂名外方,
   and 配套经费 stated without a source. Reward concrete, evidence-bound, on-target proposals. Do not
   inflate scores to be encouraging — the value is an honest pre-submission read.

## Findings
Each finding: `{severity, dimension, locus, issue, fix}` where severity ∈ {致命, 严重, 一般}.
- 致命: gate triggered / desk-reject condition / major compliance gap.
- 严重: core argument or evidence binding missing; materially lowers a score.
- 一般: fixable wording, consistency, or completeness issue.
Rank findings by severity, then by the dimension's weight.

## Output (write both)
- `<dir>/trace/most_review_report.json` — machine-readable: per-dimension scores, findings array,
  gate states (D1/D4), overall recommendation, and a one-line rationale per dimension.
- `<dir>/trace/most_review_report.md` — human-readable: 逐维 优点/不足/建议, the severity-ranked
  findings list, the two gate verdicts called out explicitly, and the 总体建议 with reasoning.
Also print a short console summary: the eight scores, both gate states, and the overall recommendation.

## Overall recommendation
Map per the rubric: 优先资助 / 建议资助 / 可资助(需修改) / 不予资助. Gate rule: D1 or D4 = 1 → at most
不予资助; 优先资助 requires both gated dimensions ≥4 and zero `致命` findings. State the binding
constraint (which dimension or finding determined the ceiling) in one sentence.

## Hard rules
- Never raise a score to soften the message; an honest 不予资助 with precise fixes is the product.
- Ground every score in quoted loci; no vibes-based scoring.
- Treat `NEEDS-INPUT` stubs as missing (not as satisfied) — a stubbed 对等经费 is an unmet D4 requirement.
- Do not edit the proposal; review only. (Use /proposal-compiler or manual edits to fix.)
