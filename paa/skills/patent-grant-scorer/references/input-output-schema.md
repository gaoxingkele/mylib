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
| `ahp_index` | 由1—9分AHP综合值线性映射得到的0—100内部风险/准备度指数，不是授权概率 |
| `decision` | 门禁、版本和证据约束后的工作流决策 |
| `score_layers.structural_readiness` | D/Q主导的文本结构成熟度 |
| `score_layers.ahp_substantive_index` | 与`ahp_index`相同的AHP实质风险层 |
| `score_layers.evidence_confidence` | 当前证据完整性，不是模型自信 |
| `hard_gates` | 不能被平均分覆盖的PASS/FAIL/CONDITIONAL |
| `consensus.<indicator>` | 中位数、MAD、证据加权均值、异常抑制和高质量少数意见 |
| `version_binding.stale` | 当前评审或检索是否绑定旧独权 |
| `round_transition` | 本轮是文本变化、证据变化还是混合变化 |
| `relative_position` | 当前输入同批案件百分位 |
| `action_queue` | P0/P1/P2整改任务 |
| `score_layers.residual_distinction` | 2.3.0，可选；残余区别特征层，不入指数（见第 6 节） |
| `score_layers.retrieval_coverage` | 2.3.0，可选；检索覆盖层，不入指数（见第 6 节） |
| `expert_independence` | 2.3.0，可选；角色独立性声明与角色偏移诊断 |
| `audit_warnings` | 2.3.0；新层、防提分漏洞与独立性的警告汇总，只在非空时出现，不改分 |
| `audit_details` | 2.3.0；如`evidence_removed`（相对上一轮被删的证据文件） |

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
# 默认稳健仲裁；--root 为 search_path 的相对路径基准（通常是案件目录）
python paa/skills/patent-grant-scorer/scripts/ahp_only_scorer.py input.json -o output.json --root <案件目录>

# 仅用于复现旧AHP/SEM历史报告；grant_probability不得解释为真实概率
python paa/skills/patent-grant-scorer/scripts/ahp_sem_scorer.py input.json --aggregation legacy-mean
```

## 6. 2.3.0 可选字段（AHP-only 评分器）

以下字段全部可选。都不提供时，输出与 2.2.x 逐字段一致，只有两处差别：`protocol_version` 变为 `2.3.0-ahp-only`；有 `history` 而缺 `review_context.anchor_sha256` 时多出 `audit_warnings: ["anchor_not_frozen"]`。AHP 指数公式、组权重、16 项指标和档位阈值都没有改，新层不入指数。

### 6.1 输入

```json
{
  "expert_meta": {
    "examiner": {"calibration": 1.0, "domain_fit": 1.0, "independent": false, "author_id": "same-model-same-session"}
  },
  "review_context": {
    "feature_matrix": {
      "features": {"F1": "特征描述", "F2": "..."},
      "independent_claim_features": ["F1", "F2"],
      "docs": {"D1 CNxxxxxxA": {"F1": "●", "F2": "◐"}, "D2 USyyyyyyA": {"F1": "○", "F2": "●"}},
      "frozen_at": "可省，等同 feature_matrix_frozen_at"
    },
    "feature_matrix_frozen_at": "v2.8 拆分（某报告 §1）",

    "retrieval": {
      "databases": ["patsnap", "google_patents"],
      "claim_fulltext_semantic": true,
      "fulltext_fetched_n": 38,
      "incopat_done": false,
      "npl_fulltext": false,
      "legal_status_verified": false,
      "conflict_blindspot": true,
      "features_searched": ["F1", "F2"]
    },

    "search_binding": {
      "relation": "same_claim_text",
      "search_path": "raw_inputs/xxx_mcp_search.json",
      "input_jsonpath": "request.semantic_query",
      "normalization": "strip_ws_sha256"
    },

    "independent_claim_hashes": {"1": "sha256:...", "22": "sha256:..."},
    "text_bundle_hash": "sha256:...",
    "evidence_hash_facts": "sha256:(检索报告、对比文件 JSON)",
    "argument_hash": "sha256:(playbook、06/07 自评)",

    "anchor_sha256": "sha256:(冻结的评分锚点文件)",
    "data_artifact_hashes": {"sim/result.csv": "sha256:..."},
    "evidence_files": {"01_现有技术检索报告.md": "<sha256>"},
    "evidence_removal_waiver": "删除某证据文件的理由（可省）",

    "gates": {"background_prior_art_alignment": "PASS | WARN | FAIL"}
  },
  "history": [
    {
      "claim_hash": "sha256:...", "evidence_hash": "sha256:...", "ahp_index": 57.1,
      "independent_claim_hashes": {}, "text_bundle_hash": "sha256:...",
      "evidence_hash_facts": "sha256:...", "argument_hash": "sha256:...",
      "anchor_sha256": "sha256:...", "data_artifact_hashes": {},
      "evidence_files": {}, "indicator_scores": {"I4": 4.95, "D3": 3.95},
      "feature_matrix_frozen_at": "...", "independent_claim_features": ["F1", "F2"]
    }
  ]
}
```

`evidence_files` 接受 `{路径: sha256}`、`["路径"]`、`["sha256␣␣路径"]` 或 `["路径\tsha256"]`。`indicator_scores` 也可以用上一轮输出里的嵌套 `indicators`。

### 6.2 计算规则

| 特性 | 规则 |
|---|---|
| 残余区别特征 `score_layers.residual_distinction` | 对 `independent_claim_features` 逐个判断：任一文献为 ● 记为 `disclosed`；没有 ●、只有 ◐ 记为 `partial_only`；全为 ○ 记为 `undisclosed`。输出 `not_fully_disclosed`（非 ● 特征）、`untouched_by_any_document`（全 ○）、两种覆盖率和 ● 最多的单篇文献。非 ● 特征 ≤1 时警告 `single_pivot_independent_claim`。未登记拆分基线时警告 `feature_matrix_not_frozen`；与上一轮的 `feature_matrix_frozen_at` 或特征清单不一致时警告 `feature_matrix_split_changed` |
| 检索覆盖 `score_layers.retrieval_coverage` | 7 个分项：全文语义检索、取全文 ≥10、incoPat、≥2 个数据库、法律状态已核、NPL 全文、抵触盲区已关闭。`search_status == "degraded"` 时，证据置信度封顶 = 45 + 5×（前 5 项满足数），上限 65，并加 `degraded_cap_graded_to_<n>`；failed/empty/quota-exhausted 仍封顶 45。不提供 `retrieval` 时仍是二值 45。独权特征不在 `features_searched` 中时警告 `feature_not_searched:<Fi>` |
| 检索绑定 | `input_jsonpath` 从证据 JSON 读查询文本（支持 `a.b`、`a[0].b`）；`normalization: "strip_ws_sha256"` 去全部空白后取 sha256；读不到字段时警告 `search_evidence_missing_jsonpath_field` |
| 收窄关系 | `relation: "narrowed_from_searched_claim"` 只有在同时给出 `new_features_searched`（bool）时才生效：true 时不判 STALE，`version_binding.narrowed_status = "narrowed_rechecked"`，并给 `narrowed_search_reused_with_added_features_searched` 警告；false 时维持 STALE，并加原因 `narrowed_new_features_not_searched`。不给该布尔值时与 2.2.x 相同 |
| 版本与证据分层 | 当前轮或上一轮出现 `independent_claim_hashes`、`text_bundle_hash`、`evidence_hash_facts`、`argument_hash` 任一字段时启用。两轮都有 `evidence_hash_facts` 时按事实层判断证据是否变化，否则用 `evidence_hash`。transition 新增 `non_claim1_text_revision_fixed_evidence`（权 1 未变，其他独权或文本束变化，证据不变）、`mixed_text_and_evidence_shift`、`argument_revision_fixed_evidence`（只有论证层变化，计为申请人侧改进）。启用后，`same_state_recheck` 只在文本束哈希两轮都有且相同时成立，否则为 `unknown`。另外输出 `applicant_side_changes` |
| 防提分漏洞（只警告） | 有 history 但缺 `anchor_sha256`：`anchor_not_frozen`；锚点哈希与上一轮不同：`anchor_changed_since_previous_round`。I4 或 D3 共识分比上一轮 `indicator_scores` 高，而 `data_artifact_hashes` 缺失或与上一轮相同：`effect_score_raised_without_new_data:<I4/D3>`。上一轮给了 `evidence_files`，本轮不是其超集且没有 `evidence_removal_waiver`：`evidence_set_shrunk` |
| 角色独立性 `expert_independence` | 任一角色声明了 `independent` 时输出。全部为 false 时 `flags = ["disagreement_not_informative"]`。同时输出每个角色相对各指标中位数的平均偏移与平均绝对偏移。只作诊断，不改聚合 |
| 门禁 `background_prior_art_alignment` | 由输入提供（别名 `background_alignment`）。WARN 计入 `conditional`，FAIL 计入 `blocking`；不提供时不出现在 `hard_gates.statuses` 中 |
