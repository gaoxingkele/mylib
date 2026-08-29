# 评分输入输出格式

## 1. 兼容输入

旧版数字输入继续支持：

```json
{
  "case": "P01-1",
  "title": "...",
  "scores": {
    "examiner": {"S1": 7, "S2": 7, "S3": 6, "N1": 5, "N2": 5, "N3": 5, "I1": 4, "I2": 5, "I3": 4, "I4": 4, "D1": 7, "D2": 6, "D3": 5, "Q1": 7, "Q2": 7, "Q3": 8},
    "attorney": {"S1": 7, "S2": 7, "S3": 7, "N1": 6, "N2": 6, "N3": 6, "I1": 5, "I2": 6, "I3": 5, "I4": 5, "D1": 8, "D2": 7, "D3": 6, "Q1": 8, "Q2": 8, "Q3": 8},
    "invalidator": {"S1": 6, "S2": 6, "S3": 6, "N1": 4, "N2": 4, "N3": 5, "I1": 3, "I2": 4, "I3": 3, "I4": 3, "D1": 6, "D2": 6, "D3": 5, "Q1": 6, "Q2": 7, "Q3": 7},
    "analyst": {"S1": 7, "S2": 7, "S3": 6, "N1": 5, "N2": 5, "N3": 5, "I1": 4, "I2": 5, "I3": 4, "I4": 4, "D1": 7, "D2": 7, "D3": 5, "Q1": 7, "Q2": 7, "Q3": 8}
  }
}
```

纯数字输入会产生`legacy_numeric_scores_without_evidence_metadata`，证据置信度上限较低。

## 2. 推荐输入

顶层可为单案、案件数组，或：

```json
{
  "cohort": {"id": "software-method-2026Q3-pre-filing"},
  "cases": []
}
```

推荐单案结构：

```json
{
  "case": "P01-1",
  "title": "...",
  "review_context": {
    "claim_hash": "sha256:current-claim",
    "reviewed_claim_hash": "sha256:current-claim",
    "search_claim_hash": "sha256:current-claim",
    "evidence_hash": "sha256:verified-prior-art-set",
    "application_date": "2026-01-01",
    "search_status": "complete",
    "claim_text_verified": true,
    "engineering_evidence_status": "needs-confirmation",
    "patentara_score": 89.8,
    "gates": {
      "subject_matter": "PASS",
      "novelty_inventive_evidence": "PASS",
      "disclosure_support": "CONDITIONAL",
      "evidence_integrity": "PASS",
      "claim_formality": "PASS"
    }
  },
  "expert_meta": {
    "examiner": {"calibration": 1.0, "domain_fit": 1.0},
    "attorney": {"calibration": 0.95, "domain_fit": 1.0}
  },
  "scores": {
    "examiner": {
      "I3": {
        "score": 4.0,
        "confidence": 0.85,
        "evidence_quality": 0.95,
        "status": "confirmed",
        "evidence_refs": ["claim:CNxxxxxxA:1", "claim:CNyyyyyyA:3"]
      }
    }
  },
  "history": [
    {
      "round": 1,
      "claim_hash": "sha256:old-claim",
      "evidence_hash": "sha256:verified-prior-art-set",
      "grant_probability": 0.47,
      "latent": {"S": 7.0, "N": 5.0, "I": 4.2, "D": 5.8, "Q": 6.8}
    }
  ]
}
```

示例只展开`I3`；实际每个专家必须提交全部16项指标。

## 3. 状态词

评分证据状态：

```text
confirmed | supported | inferred | needs-confirmation | unverified | contradicted
```

门禁状态：

```text
PASS | FAIL | CONDITIONAL | WARN | WAIVED | UNKNOWN
```

搜索状态建议：

```text
complete | degraded | failed | empty | quota-exhausted
```

其中后四种都不能解释为负向检索结论。

## 4. 关键输出

| 字段 | 含义 |
|---|---|
| `grant_probability` | AHP/SEM内部风险点估计 |
| `decision` | 门禁、版本和证据约束后的工作流决策 |
| `score_layers.structural_readiness` | D/Q主导的文本结构成熟度 |
| `score_layers.risk_adjusted_patentability` | 风险点估计百分制表示 |
| `score_layers.evidence_confidence` | 当前证据完整性，不是模型自信 |
| `uncertainty_interval` | 证据不足/分歧导致的工作区间，非统计置信区间 |
| `hard_gates` | 不能被平均分覆盖的PASS/FAIL/CONDITIONAL |
| `consensus.<indicator>` | 中位数、MAD、证据加权均值、异常抑制和高质量少数意见 |
| `version_binding.stale` | 当前评审或检索是否绑定旧独权 |
| `round_transition` | 本轮是文本变化、证据变化还是混合变化 |
| `relative_position` | 当前输入同批案件百分位 |
| `action_queue` | P0/P1/P2整改任务 |

### 决策值

```text
STALE_REVIEW_RESEARCH_REQUIRED
BLOCKED_BY_HARD_GATE
CONDITIONAL_EVIDENCE_OR_GATE_REVIEW
READY_FOR_PATENT_ATTORNEY_REVIEW
REVISE_AND_REVIEW
REBUILD_INDEPENDENT_CLAIM_OR_RESELECT_POINT
```

不存在`DIRECT_FILE`或`GUARANTEED_GRANT`。

## 5. 命令

```powershell
# 默认稳健仲裁
python paa/skills/patent-grant-scorer/scripts/ahp_sem_scorer.py input.json -o output.json

# 仅用于复算旧历史均值口径
python paa/skills/patent-grant-scorer/scripts/ahp_sem_scorer.py input.json --aggregation legacy-mean
```

