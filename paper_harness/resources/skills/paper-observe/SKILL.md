---
name: paper-observe
description: 只读恢复论文 Harness 现场——查看 stage 看板、timeline 事件链、plan 与 approval 状态。当需要了解"论文项目现在进行到哪一步、上次发生了什么"时使用，不做任何修改。
---

# paper-observe（只读观察）

用于在不改变任何状态的前提下恢复论文 Harness 的现场。

## 步骤

1. 查看看板：
   ```bash
   python -m paper_harness status <paper_dir>
   ```
   输出当前 plan 版本与审批状态、各 stage 状态（PENDING/RUNNING/CANDIDATE/ACCEPTED/REJECTED/BLOCKED/FAILED）、最近 10 条事件。

2. 需要更早的历史时，直接读 append-only 事件日志：
   ```
   <paper_dir>/.paper_harness/timeline.jsonl
   ```
   每行一个 JSON：`{"ts", "type", "data"}`。关键事件：`plan_created` → `approved` → `stage_started` → `candidate_ready` → `accepted`/`rejected`；异常为 `stage_blocked` / `stage_failed` / `run_refused`。

3. 读当前计划与批准记录：
   ```
   <paper_dir>/.paper_harness/plans/plan_vN.md
   <paper_dir>/.paper_harness/approvals/approval_vN.json
   ```
   approval 中的 `plan_sha256` 是 plan 全文的 SHA-256（小写 hex），可手工复核 plan 是否在批准后被改动。

4. stage 的执行细节在 `<paper_dir>/.paper_harness/runs/v<plan>_<stage_id>/`：`executor.log`（执行日志）、`acceptance.json`（验收检查结果）。
5. reviewer 输出应包含 `manuscript_sha256` 与 `coverage.complete`；缺少这些字段时不能证明评审覆盖了当前完整稿件。

## 边界

- 只读：不运行 `approve` / `run` / `accept` / `reject`，不编辑 plans、approvals、timeline。
- 如需介入，改用 `paper-control` skill。
