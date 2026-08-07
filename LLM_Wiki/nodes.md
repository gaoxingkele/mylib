# Nodes

## Core Layer

### `ResearchStudio-Idea`
- 位置：`D:/aicoding/lib/ResearchStudio/ResearchStudio-Idea`
- 作用：IdeaSpark 模式词表、pattern cards、创新招数归纳
- 本地集成：`~/.claude/skills/{idea_spark,paper_search,scoop_check}`
- 关键脚本：
  - `scripts/literature/ideaspark_journal_pattern_distill.py`
  - `scripts/literature/ideaspark_fullcorpus_journal_distill.py`

### `RepLLM-CPA`
- 位置：`D:/aicoding/lib/RepLLM`
- 作用：借鉴 RepLLM 的 Content Parsing，把 PDF 解析为 `paper.json`
- 本地集成：`~/.claude/skills/repllm-content-parse`
- 关键脚本：`scripts/literature/repllm_cpa_journal_distill.py`
- 关键产物：
  - `papers/literature/target_journal_related/metadata/repllm_cpa_paper_json/`
  - `.../repllm_cpa_journal_distill.json`

### `Paper_CCF`
- 位置：`D:/aicoding/lib/Paper_CCF`（镜像自 `~/.claude/skills/Paper_CCF`）
- 作用：期刊路由、写作规范、投稿策略
- 关键入口：
  - `resources/ideaspark-fullcorpus-journal-distill.md`
  - `resources/repllm-cpa-journal-distill.md`
  - `journals/<slug>/SKILL.md`

## Bridge Layer

### `AERS-powergrid-bridge`
- 位置：`D:/aicoding/lib/skills/AERS-powergrid-bridge`
- 本地集成：`~/.claude/skills/aers-powergrid-bridge`
- 作用：从 AERS 选择性路由高 ROI 模块
- 路由模块：
  - `71` 文献工具编排
  - `62` 引文核验
  - `54` 图表审计
  - `48` 降 AIGC
  - `67` 终稿流水线（可选）

## Project mirror Layer

### `powergrid_paper`
- 位置：`D:/aicoding/lib/powergrid_paper`
- 内容：`scripts/literature`、蒸馏 `metadata`、期刊模板、CMC 文风、Appl. Sci. 样本分析
- 说明：`powergrid_paper/README.md`（不含全文 PDF）

## Data/Artifact Layer

### Applied Sciences 扩充语料
- 原项目：`D:/aicoding/powergrid_benchmark/papers/literature/applied_sciences_power_grid_recent/pdf`
- lib 镜像：仅 metadata → `powergrid_paper/corpus_samples/...`

### Full-corpus Distill
- lib 镜像：`powergrid_paper/metadata/ideaspark_fullcorpus_*`、`repllm_cpa_*`
