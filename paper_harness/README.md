# paper_harness 0.2.5

## 0.2.5 preserved locked-worktree retry

`retry --preserve-locked-worktree` records and excludes a locked legacy
incident directory, rotates the retry to a nonce-derived target, and never
deletes or merges the preserved site. The full smoke suite contains 18 passing
tests.

## 0.2.4 isolated-source acceptance

Custom Python acceptance checks prepend the isolated worktree's `src`
directory to `PYTHONPATH`. Scientific gates therefore import the candidate
implementation instead of depending on the caller's checkout or global
environment. The full smoke suite contains 17 passing tests.

面向论文写作、实验补强和投稿核验的本地 Harness。流程是：

```text
只读评审 -> 计划 -> 人工核对 SHA-256 -> 批准 -> 单阶段隔离执行
         -> 自动验收 -> CANDIDATE -> 人工 accept/reject -> 下一阶段
```

## 0.2.3 timeout containment

Each real transport call starts in its own process group/session. If the
configured timeout is reached, the harness terminates that call's controlled
process tree before returning exit code 124. This prevents orphan descendants
from holding an isolated worktree open; pre-existing processes are never targeted.

## 0.2.2 的核心边界

- 计划全文由 SHA-256 绑定人工批准；计划在创建或批准后发生任何修改均拒绝执行。
- 每次只执行一个 stage。前一 stage 未 `ACCEPTED` 时，后续 stage 不能启动。
- Git monorepo 子目录使用正确的仓库根目录和相对前缀；分支为
  `paper-harness/<project>/v<plan>-<stage>`，不同论文不会冲突。
- 正文和配置文件必须已纳入 Git 且论文子树必须干净。未跟踪或有未提交修改时拒绝运行，
  防止 worktree 中缺少真实论文却产生假阳性。
- executor 改动通过验收后自动提交到 stage 分支；越出论文子树的改动会使 stage `BLOCKED`。
- reviewer 读取完整稿件（默认上限 240,000 字符），记录稿件 SHA、覆盖范围、claim map、
  issue taxonomy、证据边界和每项问题的可观察验收条件。
- 已蒸馏 MA-SQLGrid、C²GES 和闽投六篇的叙事经验，规则位于
  `resources/paper_experience_digest.json` 和 `resources/reviewer_protocol.md`。

## 启动

```powershell
$env:PYTHONPATH='D:\aicoding\Lib'
python -m paper_harness init <论文目录> --journal mdpi_applied_sciences --manuscript paper_applsci.tex
python -m paper_harness review <论文目录>
python -m paper_harness plan <论文目录> --goal "完成证据对齐的三轮修改与投稿核验"
python -m paper_harness approve <论文目录> --by "批准人"
python -m paper_harness run <论文目录>
python -m paper_harness accept <论文目录> <stage_id>
python -m paper_harness run <论文目录>
```

若 stage 因可证明的基础设施故障进入 `BLOCKED/FAILED`，修复后可在原批准计划下记录原因并重试：

```powershell
python -m paper_harness retry <论文目录> <stage_id> --reason "已修复的基础设施原因"
```

`retry` 不修改计划或批准，只清理该 stage 的失败 worktree/branch 并留下时间线事件。

`review` 是只读操作，不需要批准。`approve` 必须由实际审阅过计划和 digest 的人运行；
Harness 不代替作者批准自己的计划。

## Mock 模式

```powershell
$env:PAPER_HARNESS_TRANSPORT='mock'
```

长阶段可在不改变已批准计划的前提下显式延长 Codex CLI 执行上限：

```powershell
$env:PAPER_HARNESS_CODEX_TIMEOUT='3600'
```

配置中的 `read_only_paths` 会把共享测试或证据树加入 sparse worktree，但不会扩大
`allowed_write_paths` 或主工作区干净基线的检查范围。超时工作树应先导出并哈希
WIP patch，再通过 `retry` 从干净基线执行；WIP patch 不是候选或科学证据。

Mock 不调用 Codex CLI，但仍真实运行 Git、LaTeX 和验收检查。

## 验收检查

- `latex_build`：在正文所在目录执行 LaTeX/BibTeX/Biber 链，拒绝 fatal、未定义引用与缺失 PDF。
- `no_placeholders`：扫描配置正文及指定 glob，拒绝作者、通信邮箱、基金和 TODO 占位。
- `declarations`：按期刊检查声明组；MDPI 默认五项，IEEE Access 使用适配后的声明组。
- `narrative_structure`：检查 Abstract、Introduction、Method、Results、Discussion、Conclusion，
  并应用可配置摘要词数上限。
- `artifact_consistency`：检查插图路径和重复 LaTeX label。
- `pdf_integrity`：检查当前 PDF、文本可提取性和编译后占位符。
- `manuscript_hygiene`：检查乱码和已知投稿过程元叙事。
- `custom:<path>`：运行项目自定义确定性脚本，退出码 0 才通过。

## 计划格式

```markdown
---
stages:
  - id: s1
    title: 对齐题目、贡献与证据
    objective: 在不改变既有数字和方向的前提下，修复 title-to-evidence claim map 中的 major issues
    acceptance:
      - narrative_structure
      - manuscript_hygiene
  - id: s2
    title: 投稿级构建与核验
    objective: 更新正式 LaTeX/PDF、图表和声明；缺少作者确认的信息保持 blocker
    acceptance:
      - latex_build
      - no_placeholders
      - declarations
      - artifact_consistency
      - pdf_integrity
---
```

每个 stage 都必须单独 `run -> CANDIDATE -> accept/reject`。不能一次启动整份计划。

## Evidence Timeline

`.paper_harness/timeline.jsonl` 采用 append-only JSONL。候选的关键事件链为：

```text
plan_created -> approved -> stage_started -> worktree_created
-> candidate_committed -> candidate_ready -> accepted/rejected
```

异常会记录为 `run_refused`、`stage_blocked`、`accept_blocked` 或 `stage_failed`，现场保留供归因。

## 测试

```powershell
python D:\aicoding\Lib\paper_harness\tests\test_smoke.py
```

测试不需要 pytest，且强制使用 mock transport，保证零 API 调用。
