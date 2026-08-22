# PAA Schema Reference

Field-level format for every file in a Patent Application Artifact. Loaded on demand by the compiler.

## File-level frontmatter (all .md files)

```yaml
---
title: <human title>
case_id: <e.g., P05-1>
paa_version: "1.0.0"
generated_by: <agent/tool>
generated_at: <YYYY-MM-DD>
provenance_tags: [user, ai-suggested, ai-executed, user-revised]
status: draft | under-review | filed | granted | rejected
---
```

---

## MANIFEST.md (root)

- **title** (required) — patent title
- **case_id** (required)
- **claims_summary** (required) — number of 独立 + 从属 per subject (方法
- **prior_art_count** (required) — total cited prior-art references
- **gate_status** (required) — table: {gate_name: PASS | FAIL | WAIVED, evidence}
- **Layer Index** (required) — links to all major files
- **Gap Report** (required) — top 5 missing items (e.g., NEEDS-INPUT for applicant data)
- **exploration_summary** (required) — node count by type in `trace/exploration_tree.yaml`

---

## logic/ — cognitive layer

### logic/invention.md
Three-part chain (技术问题 → 技术手段 → 技术效果):
- **技术领域**: Yaml frontmatter field `domain: <e.g., 软件方法+装置+介质>`
- **技术问题**: numbered list (T1, T2, ...) with binding to 实施例 + 对比文件
- **技术手段**: numbered (S1, S2, ...) — each binds to a 权利要求特征
- **技术效果**: numbered (E1, E2, ...) with measurement/observation evidence (real data only)

### logic/subject_matter.md
- **Article 25 check** — does any claim recite 智力活动规则 / 商业方法 without technical means? → 风险等级
- **Article 2.2 check** — does any claim recite non-技术 领域? → 风险等级
- **技术特征 vs 业务规则 占比 estimate**: per claim
- **Binding to gates/evidence**: ref to 客体适格门禁 result

### logic/claims_analysis.md
For each 独立权利要求 (C01, C02, ...):
- **preamble (前序)** — verbatim text
- **其特征在于 marker** — position
- **characterizing portion (特征部分)** — verbatim text, broken into D01, D02, ... (difference features)
- For each difference feature:
  - **Support binding**: `→ application/specification.md §embodiment_X`
  - **Prior-art contrast**: `→ logic/prior_art.md §D_anchor_X` (X files contradicted)
  - **Score binding**: `→ evidence/scoring/scoring.json → I_value`

### logic/inventive_concepts.md
Block per concept:
- `### C01: <concept title>`
- **Statement** (falsifiable)
- **Status**: CONFIRMED | UNSUPPORTED | NEEDS-EVIDENCE
- **Proof** — refs to 实施例 ID + 对比文件 pn + score
- **Non-obviousness rationale** (for 三步法预答辩)

### logic/prior_art.md
Typed citation graph:
- `### D01: <closest prior art title>`
- **pn**: real patent number
- **applicant / ad / pd**: real fields (provenance `user` if from filings, `ai-executed` if from search)
- **relationship**: `conflicts` | `contrasts` | `background`
- **preamble vs. our claims**: short mapping table
- **difference features it negates**: refs to `claims_analysis.md` D01..DXX
- **Source**: → `evidence/prior_art_search/<pn>.json` + `evidence/prior_art_claims/<pn>.md`

### logic/related_work.md
Non-conflicting literature (academic, technical specs, etc.) — keep concise.

### logic/solution/constraints.md
- Limitations/assumptions (technology maturity, deployment cost, regulatory, etc.)
- Drafting strategy notes (which mechanism was substituted in each round, why)

---

## application/ — artifact layer

### application/claims.md
- 权利要求书 preamble
- Each 权利要求 in markdown with **bold** claim number, structure preserved
- Each 从属权利要求 explicitly references the parent by number

### application/specification.md
Five elements in order:
1. 技术领域
2. 背景技术 — cites prior-art pn from `logic/prior_art.md`, describes their defects
3. 发明内容 — three-part chain (技术问题/技术方案/有益效果); 三步法预答辩 logic
4. 附图说明
5. 具体实施方式 — numbered embodiments, ≥2 with numerical examples

### application/drawings.md
- 附图清单 table
- Per figure: Mermaid description + uniform numbering system (e.g., 100-series)

### application/abstract.md
- ≤300 字
- Includes 技术领域, 技术问题, 方案要点, 主要用途/效果, 摘要附图指定
- No absolute expressions

---

## trace/exploration_tree.yaml

See `exploration-tree-spec.md` for the full schema. Required:
- root nodes: central questions
- typed nodes: `claim-version`, `prior-art`, `design-around`, `dead-end`, `oa-response`
- cross-edges: `evidence:` → claim-versions / prior-art ids
- support_level: `explicit` (from source) / `inferred` (reconstructed)
- No invented dead_ends or decisions

---

## evidence/ — grounded evidence

### evidence/README.md
- Index of all evidence files
- Anything not filed must appear here with `reason: omitted because ...`

### evidence/prior_art_search/
- Per file: `<pn>.json`
- fields: pn, search_expression, semantics_score (if applicable), search_date, source=`incopat-search`
- Original raw response preserved

### evidence/prior_art_claims/
- Per file: `<pn>.md` (transcription) + `<pn>.png` (screenshot if available)
- Transcription fields: claim_no, claim_or (verbatim original text), claim_en (if bilingual), claim_zh_clean (HTML-stripped)
- Source: cite `incopat-search claim API, YYYY-MM-DD`

### evidence/scoring/
- scoring.json: {case_id, scores: {expert_name: {indicator: value}}, group_weights: {N, I, D, Q}, group_CR, latent, grant_probability, grade}
- Matches the schema of `patent-grant-scorer` output

### evidence/design_around/
- per round: `round_<N>_<mechanism>.md`
- fields: round_no, prior_art_target, mechanism_before, mechanism_after, why_switched, regression_check (semantic_score trajectory)

---

## Cross-layer binding (mandatory)

For every `difference_feature` in `claims_analysis.md`, the following three refs must resolve:

```
difference_feature:
  → embodiment: application/specification.md §embodiment_X  (must)
  → prior_art: logic/prior_art.md §D_X (must, ≥1)
  → score: evidence/scoring/scoring.json → I_value (must)
```

`./scripts/validate.py` enforces this.

---

## File set decisions

Mandatory core is fixed. Additional files are your judgment based on case content:
- 说明书补强 (`logic/solution/disclosure_amplification.md`) — when 26.3 risk detected
- 答辩预案 (`logic/solution/oa_response_plan.md`) — when OA exists
- 附图核读 (`evidence/drawings/`) — when figures need visual extraction

Do not force template files onto cases that don't need them.