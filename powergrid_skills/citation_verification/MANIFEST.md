# MANIFEST — citation_verification

引用真实性与元数据核验组件。用途：投稿前检查 references.bib / 参考文献列表是否存在幻觉引用、字段错误、格式不规范。

| 文件 | 来源仓库 | 原路径 | 用途 | 怎么用 |
|---|---|---|---|---|
| verify.py | AutoResearchClaw | researchclaw/literature/verify.py | 三层引用核验引擎（解析 → 在线比对 → 置信度分级），检出幻觉参考文献，纯 stdlib | `python verify.py <bib_or_refs>` 或作为库 import |
| verify-citations.py | claude-scholar | skills/citation-verification/scripts/verify-citations.py | 引用核验主脚本，调用 api-clients 查 Crossref/Semantic Scholar 等 | `python verify-citations.py <文件>` |
| format-checker.py | claude-scholar | skills/citation-verification/scripts/format-checker.py | 参考文献格式（著录字段、标点、大小写）检查 | `python format-checker.py <文件>` |
| api-clients.py | claude-scholar | skills/citation-verification/scripts/api-clients.py | 各学术 API（Crossref、Semantic Scholar 等）客户端，含速率限制 | 被 verify-citations.py 引用，不单独运行 |
| SKILL.md | nature-skills | skills/nature-ref-verifier/SKILL.md | nature-ref-verifier 协议：逐条多源交叉验证作者/标题/年份/卷期/页码，输出结构化验证报告 | 作为指令文档加载，指导 agent 逐条核验 |
| common-patterns.md | nature-skills | skills/nature-ref-verifier/references/common-patterns.md | 常见参考文献错误模式库（卷年/DOI 年冲突、作者顺序异常等） | 配合 SKILL.md 参考 |
| citation-workflow.md | AI-Research-SKILLs | 20-ml-paper-writing/ml-paper-writing/references/citation-workflow.md | ML 论文引用工作流：何时引、怎么引、如何整理 | 写作/整理参考文献时参考 |
| semantic_scholar_api_protocol.md | academic-research-skills | deep-research/references/semantic_scholar_api_protocol.md | Semantic Scholar API 调用协议（端点、限流、字段） | 手写核验脚本时查阅（注：原在 academic-paper，实际位于 deep-research/references/） |
| crossref_api_protocol.md | academic-research-skills | deep-research/references/crossref_api_protocol.md | Crossref API 调用协议 | 同上 |
| openalex_api_protocol.md | academic-research-skills | deep-research/references/openalex_api_protocol.md | OpenAlex API 调用协议 | 同上 |
| arxiv_api_protocol.md | academic-research-skills | deep-research/references/arxiv_api_protocol.md | arXiv API 调用协议 | 同上 |

备注：academic-research-skills 的 4 个 API 协议文档在任务预期路径 `academic-paper/references/` 下不存在，经仓库内搜索定位于 `deep-research/references/`，已按同名文件拷贝。
