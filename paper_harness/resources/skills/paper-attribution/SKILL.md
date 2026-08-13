---
name: paper-attribution
description: 对 BLOCKED/FAILED 的 stage 做归因复盘——读取固定现场（日志、timeline 节选、plan），产出归因与 harness 改进提案。当 stage 进入 BLOCKED 需要分析原因时使用。
---

# paper-attribution（BLOCKED 复盘）

## 触发条件

`status` 显示某 stage 为 `BLOCKED`（executor 失败、验收未通过、merge 冲突）或 `FAILED`（harness 重启时发现遗留 RUNNING）。

## 步骤

1. 先观察现场（等价于 paper-observe）：`status`、`timeline.jsonl`、`runs/v<plan>_<stage_id>/` 下的 `executor.log` 与 `acceptance.json`。
2. 生成归因报告：
   ```bash
   python -m paper_harness attribute <paper_dir> <stage_id> [--model M]
   ```
   输出到 `<paper_dir>/.paper_harness/attributions/attribution_<stage_id>_<ts>.md`，并写 `attribution_created` 事件。
3. 归因至少区分：论文/证据问题、executor 问题、harness 机制问题、环境问题、必须由作者提供的人类输入。报告含处置建议与 harness 改进提案。

## 现场保留原则

- BLOCKED 时 harness 固定现场：worktree 分支、日志、timeline 游标都保留，不要清理。
- merge 冲突导致的 BLOCKED：主工作区处于合并中状态，由人工解决后再决定重新 `accept` 或放弃。
- 复盘结论如果是"计划本身有问题"：正确路径是重新 `plan`（新版本）→ `approve` → `run`，而不是修改旧 plan。
- 不得把缺少专家评价、作者身份、基金或新实验结果归因成“文字问题”并用生成内容绕过。
