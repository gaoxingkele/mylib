# LLM Wiki (Graph)

这是当前本机论文智能体能力的图结构 Wiki，面向「电网/AI 论文写作与投稿」。

## 入口

- 总图：`graph.md`
- 节点说明：`nodes.md`
- 路由手册：`playbooks.md`

## 设计原则

- 只保留可执行能力（已有脚本/skill/产物路径）。
- 优先复用现有主干：`ResearchStudio-Idea` + `RepLLM(CPA)` + `Paper_CCF`。
- 大型外部库（AERS）只做选择性桥接，不整包加载。

## 快速导航

1. 要做选题/构思蒸馏：从 `ResearchStudio-Idea` 节点出发。
2. 要做结构化证据审计：走 `RepLLM-CPA` 节点。
3. 要做期刊路由与写作规范：走 `Paper_CCF` 节点。
4. 要做投稿前质量闸门：走 `AERS-Bridge` 节点（引文/图表/降AIGC）。

