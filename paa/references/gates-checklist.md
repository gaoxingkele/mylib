# PAA Four Gates Checklist (Hard Gates)

The four patent-specific gates that every PAA must pass before finalization. Run after Stage 3
(cognitive + artifact layer generated) and before `MANIFEST.md` is finalized. Each gate produces
**PASS / FAIL / WAIVED** with concrete evidence. Any FAIL → artifact is `incomplete`; the gap report
must list the concrete fix.

The gates parallel GPA's `指南对接 gate` and `实质性国际合作 gate`. Both ARE first-class, hard
desks (one-way), not optional polish.

---

## Gate 1 — 客体适格门禁 (Article 25 / 2.2)

**Threshold**: ONE-WAY. Pure business rules, mental activity rules, or non-technical 领域 are
**rejected at the gate**, regardless of how clever the solution is. This is the leading cause of
Chinese invention patent rejections in our project (cases P03 / P07 died here).

### Check

For each 独立权利要求 in `application/claims.md`:

```
[ ]  claim recites at least one technical feature bound to a concrete technical means
[ ]  claim binds to internal structure / data flow / signal / transformation (not pure
     business logic)
[ ]  algorithm parameters / thresholds / data structures are present
[ ]  the underlying technical problem problem in logic/invention.md is "technical"
     (not "how to organize workflow" / "how to do risk control" / etc.)
```

### Output

```yaml
gate_1_subject_matter:
  status: PASS | FAIL | WAIVED
  check_artifact: application/claims.md (each 独立) + logic/invention.md
  claims_at_risk: [C01, ...]                 # if any
  reason: <if FAIL, explain which claim fails and which Article (25 or 2.2)>
  fix: <if FAIL, concrete rewrite hint>
```

### Common failures + fixes

- **Pure business rule claim** (e.g., "基于流程引擎的不良资产管理方法" with no concrete technical means)
  → FAIL. Fix by introducing at least one concrete technical means: specific data structure (e.g., DAG, FSM),
  specific algorithm with parameter ranges, specific protocol/format, or specific hardware/software constraint.
- **Mental activity claim** (e.g., "基于人工判断的风险识别方法")
  → FAIL. Fix by binding to a concrete machine-readable criterion + automatic execution path.
- **领域 specification too broad** (e.g., "信息处理方法")
  → narrow the 领域 to a specific technical subsystem.

---

## Gate 2 — 新颖性/创造性证据绑定门禁

**Threshold**: every 独立权利要求 difference feature must bind to ≥1 prior-art node in
`evidence/prior_art_search/` with a real `pn`. Difference features without bound prior-art are
**unverified against prior art** — they might be novel, but we can't claim we checked.

### Check

```
For each difference_feature D01..DXX in logic/claims_analysis.md:
  [ ]  ≥1 prior_art node PA-YY in logic/prior_art.md with relationship ∈ {conflicts, contrasts}
  [ ]  PA-YY has a real pn field, not a placeholder
  [ ]  evidence/prior_art_search/<pn>.json exists (raw search response)
  [ ]  evidence/prior_art_claims/<pn>.md exists (claim text transcription)
  [ ]  the relationship is justified in 3-5 sentences (why this prior art conflicts/contrasts with our claim)
```

### Output

```yaml
gate_2_novelty_inventive:
  status: PASS | FAIL | WAIVED
  total_difference_features: N
  bound_to_prior_art: M
  unbound: [<D-XX>, ...]
  unbound_reason: NEEDS-SEARCH (run more search expressions)
```

---

## Gate 3 — 充分公开门禁 (Article 26.3)

**Threshold**: every 权利要求 feature has ≥1 supporting 实施例 paragraph with concrete implementation
detail. Black-box algorithms and prompt-only LLM claims are **rejected at the gate** — 案例 P06-2 originally
had this risk and was fixed via "补实施例 + 门禁判定规则" expansion.

### Check

```
For each 权利要求 feature (independent + dependent):
  [ ]  ≥1 实施例 paragraph in application/specification.md §具体实施方式
  [ ]  parameters / formulas / thresholds are concrete numbers or named ranges (not "about X")
  [ ]  no black-box terms: no "本发明采用X算法" without showing how the algorithm works
  [ ]  if LLM / model is involved:
       - prompt templates are given (full structure, not summary)
       - gating rules are explicit
       - input/output examples are given
```

### Output

```yaml
gate_3_sufficient_disclosure:
  status: PASS | FAIL | WAIVED
  claims: [C01, C02, ...]
  features_at_risk: [feature_X, ...]
  reason: <if FAIL, which feature has no concrete embodiment>
  fix: <e.g., "添加实施例N：给出从入库到第N次作答校准的完整数值实例">
```

### Common failures + fixes

- **LLM algorithm with prompt-only description** → FAIL. Fix by giving full prompt template structure + template text + grounding rules.
- **Threshold / weight left abstract** → FAIL. Fix by giving a concrete number or a named range with selection rule.
- **Single 实施例 only** → usually fine but weak. ≥2 implementations strongly recommended for software-method claims.

---

## Gate 4 — 禁编造对比文件 (Integrity Hard Rule)

**Threshold**: every cited patent number must come from real prior-art search. No fabricated pns.
No "类似的"、"近似的" placeholder references.

### Check

```
For every pn in logic/prior_art.md, logic/claims_analysis.md, application/specification.md:
  [ ]  pn appears in evidence/prior_art_search/<pn>.json (raw search response with source=incopat-search or equivalent)
  [ ]  pn appears in evidence/prior_art_claims/<pn>.md (transcription of claim text)
  [ ]  not on the fabricated-look-alike list (i.e., not a clearly invalid format)
```

### Output

```yaml
gate_4_no_fabrication:
  status: PASS | FAIL | WAIVED
  cited_pns: [...]
  unverified_pns: [<pn>, ...]  # any cited but not in evidence
  duplicate_pns: <count>
  fabricated_look_alike_warnings: [<pn>, ...]
```

### Notes

- This is the integrity hard rule. Any FAIL here is a credibility failure — the artifact is unreliable
  for filing. Re-run searches, transcribe claims, link real evidence. Do NOT lower the gate.

---

## Reading the gates

The four gates are not equally strict:
- Gate 1 (客体适格) is the most likely to FAIL outright — reframe the claim with technical means.
- Gate 2 (证据绑定) rarely fails by absence (search usually returns something); it can fail by
  fabrication (placeholder pns). Run real search.
- Gate 3 (充分公开) is the most likely to be partial — implementation-detail amplification.
- Gate 4 (禁编造) is the integrity check — any FAIL is fatal.

A PAA with all four gates PASS is ready for human review (代理人复核 → 提交 CNIPA). Any FAIL means
the artifact is incomplete and the compiler agent should surface the gap, NOT silently lower the gate.

---

## Companion files

- The four gates are run by `./scripts/validate.py` (programmatic, gives structured PASS/FAIL output).
- The gates' PASS/FAIL status is reflected in `MANIFEST.md` § "Gate Status" table.
- A dedicated "gap report" section in `MANIFEST.md` lists each gate's failures with concrete fixes.