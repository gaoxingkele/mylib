# Playbooks — 电网论文 × Codex × ARS

## A. 新开一篇电网/AI 稿

1. 工作区：打开 `D:/aicoding/powergrid_benchmark`（或具体 `paper_projects/<name>`）。
2. 读规则：项目 `AGENTS.md` + 目标刊 `Paper_CCF/journals/<slug>/SKILL.md`。
3. 收敛问题：
   ```text
   Use $academic-research-suite.
   主题：……；先苏格拉底式收敛研究问题与方法，不要写正文。
   ```
4. 本地证据：先看 `powergrid_paper/metadata/` 与 IdeaSpark / RepLLM-CPA 蒸馏，再写 related work。

## B. 文献综述（有本地语料）

1. Context：`papers/literature/`、`powergrid_paper/metadata/ideaspark_*`、`repllm_cpa_*`。
2. Constraints：优先本地 PDF / 蒸馏笔记；新增网搜引用必须可核验。
3. Call：`ars-lit-review` 或 `$academic-research-suite` + 主题。
4. Done when：空白点 / 争议点 / 已被充分研究者分栏，且每条能指回文件。

## C. 初稿 → 目标刊打磨

1. `Paper_CCF` 定期刊 fit（APC / soundness / section）。
2. `$academic-research-suite` → `academic-paper` revision / outline。
3. 闸门：`AERS-powergrid-bridge` → citation-checker + figure-table-audit + de-AIGC。
4. 可选：`ars-citation-check` 再跑一轮。

## D. 投稿前审稿模拟

```text
Use $academic-research-suite.
请以期刊审稿人审阅 drafts/...（或 paper_projects/.../paper.tex）。
重点：问题是否清楚、方法能否回答、证据是否支撑、引用是否错配、desk-reject 风险。
直接说问题，不要夸。目标刊：Applied Sciences / CMC / Energies（选一）。
```

## E. 不该用 ARS 的时候

- 只下数据集 / 跑 aria2 → 用现有 `AGENTS.md` 下载规则与 `download_tools`。
- 只改期刊模板字体 → `Paper_CCF` / CMC style。
- 只做本地语料蒸馏 → IdeaSpark / RepLLM 脚本。
