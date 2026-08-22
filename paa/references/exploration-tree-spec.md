# Exploration Tree YAML Spec (PAA)

The exploration tree captures the drafting history: how claims evolved, what was tried, what was rejected, what the OA said, and how we responded. It is **the connective tissue across drafting rounds** — currently this "why was it changed" information is scattered across git commits; PAA structures it.

## Schema (YAML)

```yaml
artifact: <case_id>
schema_version: "1.0"
root_questions:
  - id: R01
    text: <central question this PAA addresses>
    support_level: explicit | inferred
    source_ref: <file or §>

nodes:
  - id: CV-01                          # claim-version node
    type: claim-version
    text: <short description of the version>
    claim_file: application/claims.md
    claim_no: 1                         # which 独立权利要求 this version is
    preamble: <verbatim preamble text>
    characterizing: <verbatim 特征部分 text>
    mechanism_summary: <one-line summary of the invention's mechanism in this version>
    support_level: explicit | inferred
    source_ref: <git commit / file / §>
    parents: []
    children: [CV-02, ...]
    evidence: [EC-01, ...]              # binding to inventive concepts

  - id: CV-02
    type: claim-version
    text: <description of v2>
    claim_file: application/claims.md
    claim_no: 1
    preamble: ...
    characterizing: ...
    mechanism_summary: ...
    support_level: explicit | inferred
    source_ref: ...
    parents: [CV-01]                    # the previous version
    children: [CV-03, ...]
    evidence: [EC-01, EC-02]
    diff_from_parent: |                  # what changed from the previous version
      - swapped_injection_for_sealing
      - added_meta_policy_gating

  - id: PA-01                           # prior-art node
    type: prior-art
    pn: <real patent number>
    relationship: conflicts | contrasts | background
    discovered_in_round: <CV-id>
    source: <incopat-search / manual>
    relevance: <X | Y | A>
    evidence_file: evidence/prior_art_claims/<pn>.md
    contested_features: [D-01, D-02]     # difference_features this prior art negates
    notes: <free-form analysis>

  - id: DA-01                           # design-around node
    type: design-around
    text: <short description of the workaround decision>
    target_prior_art: PA-01              # the prior art being worked around
    from_version: CV-01                 # the version being changed
    to_version: CV-02                   # the new version
    mechanism_before: <verb and target, e.g., "事实注入 to 提示模板">
    mechanism_after: <substituted mechanism, e.g., "封箱隔离 + 元门控, no injection">
    rationale: <why this is a verb-level (mechanism-level) avoidance, not just content-level>
    evidence: [EC-XX]                   # binding to inventive concept + scoring

  - id: DE-01                           # dead-end node
    type: dead-end
    text: <short description of what was tried and rejected>
    support_level: explicit | inferred
    rejected_at: <CV-id>
    reason: <why it was abandoned>

  - id: OA-01                           # office action response
    type: oa-response
    text: <OA summary + response strategy>
    related_claim_version: CV-XX
    triggered_changes: [CV-YY, CV-ZZ]   # new claim-versions introduced to address
    source: <OA document>

edges: ...
```

## Node type summary

| type | meaning | required fields | optional fields |
|---|---|---|---|
| `claim-version` | one round of independent-claim rewrite | id, text, claim_no, preamble, characterizing, support_level, source_ref, evidence | mechanism_summary, parents, children, diff_from_parent |
| `prior-art` | a conflict/contrast document | id, pn, relationship, source, evidence_file | relevance, contested_features, discovered_in_round |
| `design-around` | a workaround decision (mostly 1-1 with claim-version transitions) | id, text, target_prior_art, from_version, to_version, mechanism_before, mechanism_after, rationale | evidence |
| `dead-end` | a rejected direction (NOT a real prior art / claim) | id, text, support_level, rejected_at, reason | — |
| `oa-response` | review-opinion response | id, text, related_claim_version, triggered_changes, source | — |

## Support levels

- `explicit` — from a real source (commit hash, OA doc, draft file). Must carry `source_ref`.
- `inferred` — reconstructed by the agent from circumstantial evidence. Must carry `source_ref` describing the inference basis.

Never set support_level: `explicit` on something you don't actually have a real source for.

## Hard rules

1. **Never invent `dead-end` / `design-around` / `claim-version` nodes** to hit a quota. If the source has fewer, write what is real. An honest 3-node tree beats an inflated 30-node tree.
2. **Every `claim-version` must carry `evidence:` refs** to inventive concepts in `logic/inventive_concepts.md` (EC-ids).
3. **`prior-art` nodes must carry a real pn** and a path to `evidence/prior_art_claims/<pn>.md`. No placeholder pns.
4. **`design-around` `mechanism_before` and `mechanism_after` are the mechanism-level substitution** — see README § "Four patent-specific gates" / `gates-checklist.md` § "Mechanism-level avoidance principle".
5. **`oa-response` nodes chain to `claim-version` nodes via `triggered_changes`** — the response introduces a new claim version.

## Worked example: P05-1 three rounds

Three claim-versions tied together by design-arounds against two prior-arts. The full tree is in
`./example/trace/exploration_tree.yaml`. Summary view:

```
R01: 防幻觉 RAG 的图谱校验-约束闭环可行吗？
    ├─ PA-01 (CN121636664A, conflicts) — three-engine fusion, pre-round-1 prior art
    ├─ PA-02 (CN121659916A, conflicts) — fact injection into prompt, post-round-2 prior art
    │
    ├─ CV-01 (事实注入版本)
    │   └─ DA-01 design-around target=PA-01 → CV-02
    │
    ├─ CV-02 (冲突标记注入版本)
    │   └─ DA-02 design-around target=PA-02 → CV-03 (BUT injection mechanism itself is owned)
    │
    └─ CV-03 (封箱+元适配版本)
        └─ mechanism-level avoidance: replaced "injection" verb with "structural isolation + meta gating"
        └─ evidence: EC-03 (C03 inventive concept), scored I1/I2 ≥ 5
```

The lesson: when the prior art monopolizes the **verb** (the action: injection), content-level swaps
(injecting different content) don't constitute avoidance. Mechanism-level avoidance requires
replacing the verb itself.

This lesson is recorded as a `design-around` rationale and surfaced in `logic/solution/constraints.md`
so future rounds of any case can reference it.