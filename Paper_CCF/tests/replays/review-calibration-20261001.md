# Review calibration replay record — 2026-10-01

This is evaluation evidence, not input for a fresh replay. The fixture is
[review-calibration.md](../fixtures/review-calibration.md); the numeric ledger is
[construction-cost-ledger.json](../fixtures/construction-cost-ledger.json).
No manuscript verdict is used as a pass/fail answer. These are purpose-built,
non-statistical observations, not a controlled comparison of models or a blind
review of an unseen paper. The final replay was also asked to list executed checks.

## Baseline: old router/profile, no shared review method

The independent evaluator returned the following finding text (verbatim excerpt):

> 最主要问题是证据强度不足。多个关键结果只报告单次运行，缺少方差、显著性或跨会话复现，尤其多跳任务中LLM-J仅0.748对0.747、F1仅0.419对0.412，差距很小，难以支撑强结论。Table 4没有说明硬件、并行度、基线模型、成本是总量还是均值，导致效率优势不可审计。并行NED的正确性也需更严格论证：lane键集合互斥不等于真实实体不会跨lane共指，chunk间合并顺序可能影响实体创建与更新。社区实验的问题集来源、与组件消融的关系、relation density定义均不清楚。相关工作方面，2025年已有延迟整合系统应纳入严肃比较；2026-09-23的新系统晚于稿件cutoff，可在作者回应或最终版本中说明时间线，但不应被当作原稿必然遗漏。

Observation: the review recognized important method/statistical/protocol concerns,
but its complete response did not present the supplied token-total inconsistency
or any completed headline ratio calculation. Absence from output alone does not
prove that the evaluator never calculated internally.

## Instruction-only revisions

Two fresh-session reviews with the shared method still omitted the numerical audit
from their delivered reviews. The first evaluator was asked to identify actual
reading/check coverage and returned this verbatim item among unperformed checks:

> 表格原始数值复算与单位追踪

This motivated an execution helper, not a claim that adding more prose had already
improved the numerical review behavior.

## Final replay: method plus executed numeric helper

The independent evaluator returned this verbatim finding excerpt:

> 第一，并行 NED 的正确性论证不完整：预计算 key set 跨 lane 不相交，并不必然保证 resolver 创建或更新 canonical entity 后不会产生跨 lane 状态冲突。当前只报告 conversation 26 的单次 ablation，260 个实体相同但 Hit@5/LLM-J 有差异，无法区分并行策略、随机性和下游评测波动。第二，成本表存在可复现性和数字问题：MemoryOS 的 input+output 为 2828，不是报告的 2868；LightGMEM 的 2441+36 与 2478 可由舍入解释；Zep 调用数约为 LightGMEM 的 58.0 倍。基线硬件、并行度、总量/均值定义缺失，削弱了效率结论。

It separately reported (verbatim):

> 运行本地数值审计脚本；未联网核查 AAAI 当前官方政策，因为用户明确禁止联网。

Observation: this replay executed the audit and included the token-total finding,
rounding distinction and valid headline ratio in the review. The original report
still needs ordinary author-facing calibration: "可由舍入解释" means a possible
explanation under the supplied nearest-rounding assumption, not a known rounding
procedure. The review did not request the already-present no-community ablation.

## Reproduce the deterministic part

From `D:/aicoding/mylib`:

```text
python -X utf8 -m unittest discover -s Paper_CCF/tests -p test_audit_review_numbers.py
python -X utf8 Paper_CCF/scripts/audit_review_numbers.py Paper_CCF/tests/fixtures/construction-cost-ledger.json
```

The expected input-consistency categories are `mismatch`, `rounding_possible`,
and `display_consistent`, respectively. They are not scientific truth judgments
or an acceptance recommendation. The helper's unit tests also cover malformed
inputs, unknown rounding, finite-number boundaries and precision handling.
