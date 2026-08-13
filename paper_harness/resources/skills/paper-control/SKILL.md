---
name: paper-control
description: 对论文 Harness 做有边界的介入——批准计划、执行 stage、裁决 candidate。当用户明确要求推进论文项目流程（approve/run/accept/reject）时使用。Hard Gate：plan 批准后被篡改则 run 必定拒绝。
---

# paper-control（有边界介入）

## Hard Gate 工作流（不可绕过）

```
plan →（人工审阅 digest）→ approve → run →（验收检查）→ CANDIDATE → accept / reject
```

- `approve` 记录 plan 全文 SHA-256；`run` 前重新计算并精确比对，不一致即拒绝。
- 计划变更 = 生成新 plan 版本 + 重新批准，不允许"改了接着跑"。

## 命令

```bash
python -m paper_harness plan    <paper_dir> --goal "..." [--from-file f.md] [--model M]
python -m paper_harness approve <paper_dir> --by "姓名"
python -m paper_harness run     <paper_dir> [--stage <id>] [--model M]
python -m paper_harness accept  <paper_dir> <stage_id>
python -m paper_harness reject  <paper_dir> <stage_id>
```

## 边界

- `approve` 前必须实际读过 plan 全文并向用户确认 digest；不得替用户盲目批准。
- `run` 每次只执行首个 PENDING stage；该 stage 未被人工 `accept/reject` 前，后续 stage 必须保持 PENDING。
- 正文和配置必须已纳入 Git 且论文子树干净；否则预检拒绝运行，不能用缺少真实稿件的 worktree 制造假阳性。
- git 仓库或 monorepo 子目录下，每个 stage 在独立 worktree（分支 `paper-harness/<project>/v<plan>-<stage>`）中执行；验收通过后先提交候选，再进入 CANDIDATE。
- `accept` 会把 stage 分支 `--no-ff` 合并回主分支；merge 冲突时 stage 转 BLOCKED 并保留现场，此时停止并报告用户，改用 `paper-attribution`。
- `reject` 会删除该 stage 的 worktree 与分支（仅 `paper-harness/*` 命名空间），执行前向用户确认。
- 不直接编辑论文正文——内容改动走 executor（`run`）。不得虚构作者、基金、引用、专家标注、实验或数据；负结果和证据边界必须保留。
