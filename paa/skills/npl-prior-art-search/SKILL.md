---
name: npl-prior-art-search
description: >
  非专利文献（NPL）现有技术检索统一路由。专利流程中论文/学术文献类对比文件的检索入口，
  按需求自动选择已安装的学术检索 skill：快速多源并发→paper_search；中文文献/知网/CSSCI/CCF→
  academic-search；系统综述式深度扫描→paper-search-pro；Semantic Scholar 引用网络/单篇追溯→
  scholar-search 或 papers-skill；BibTeX 管理→citation-management。
  TRIGGERS: NPL检索, 论文对比文件, 学术文献检索, 非专利文献, 文献综述扫描, prior art NPL,
  论文查新, 领域是否已被论文公开
allowed-tools: Read, Write, Bash(D:/Python314/python.exe *|node *|uvx *|git *), Glob, Grep
---

# NPL 现有技术检索路由

专利查新分两条腿：**专利腿**用 `incopat-search`（真实 API），**NPL 腿**用本路由。本 skill 不实现检索本身，而是按需求把任务派发给已装入 `~/.codex/skills/` 的学术检索 skill，并统一证据口径与落稿位置。

## 路由表（按需求自动选择，禁止同时盲目全跑）

| 需求 | 路由到 | 何时用 |
|---|---|---|
| **快速多源并发初扫**（arXiv/DBLP/OpenAlex/OpenReview/S2/Crossref，自动推断年份） | `paper_search`（ResearchStudio 版） | 查新第一步的默认动作；输入是发明要素表核心词 |
| **中文文献**（知网 CNKI、CSSCI/C刊、CCF 分级、近 6 月置顶） | `academic-search` | 中文场景的发明（如电网、行业软件），或审查员视角需要国内期刊/学位论文 |
| **系统综述式深度扫描**（四档 Quick→Audit，PRISMA-S 记录，中科院/JCR 分区过滤） | `paper-search-pro` | "该领域是否已被论文公开"的全面性检查；交底书查新收紧时；需要分区证据时 |
| **引用网络追溯/单篇核查**（S2 引用与被引、按 DOI/arXiv 取详情） | `scholar-search`（uvx s2cli/openalexcli/arxivy）或 `papers-skill`（自带 CLI） | 对某篇候选论文做前向/后向引证；核验一篇文献真实性 |
| **检索结果 BibTeX 管理** | `citation-management` | LaTeX 向（.tex/.bib 校验），专利流程仅在需 .bib 校验时用；日常用 s2cli/openalexcli 自带 BibTeX 导出即可 |
| 兜底（上述失败/限流） | `anysearch`（通用实时搜索，web/学术/专利等垂直域，已装三端）→ 仍不可用再 WebSearch + WebFetch（限定 scholar.google.com / arxiv.org / doi.org） | 仅在 skill 不可用时，且须标注来源降级 |

选择优先级：算法/软件类发明 → arXiv+S2 优先；涉及医疗/生物 → paper-search-pro（PubMed）；中文审查语境 → academic-search 优先。**两条腿都跑**：`semantic` 专利召回 + `paper_search` NPL 初扫是查新基线。

### 查询构建规则（派发前必做，实测 2026-08-29）

- **拆短**：arXiv/DBLP 是关键词匹配，长句查询会 0 命中（实测 `knowledge graph retrieval augmented generation hallucination` → arxiv=0；拆成 `graph RAG hallucination` 才能召回）。派发前把要素表核心词拆成 2-4 个 ≤5 词的短查询，`paper_search` 用 `--queries q1 q2 q3` 一次并发提交。
- 中文主题词先转译成英文检索式（学术 API 英文覆盖远大于中文）；中文查询仅当明确要中文文献时用。

### 中文线降级阶梯（OpenAlex 中文语义对工科技语召回差，实测 2026-08-29）

1. 首选 `academic-search` 知网线（CDP 模式）：Chrome 未开远程调试（chrome://inspect）时**如实标注"CNKI 未检索（CDP 未开）"**，不得假装检索过。
2. 社科/经管主题 → `paper-search-pro` NSSD 通道（中文原生，社科向）。
3. 工科主题且无 CDP：以英文检索为主（arXiv/OpenAlex 转译查询），中文期刊用 OpenAlex 中文标题筛选补充，报告中注明中文库覆盖受限。

## 执行口径（与项目合规底线一致）

1. **禁编造**：每个 NPL 对比文件必须带真实 DOI / arXiv ID / URL + 来源渠道 + 检索日期；WebSearch 摘要不是核验过的正文，只能算发现线索（`source-degraded`），须二次核验。
2. **不绕付费墙**：只用开放获取渠道取全文；没有 OA 就把摘要+元数据写进报告并标注"未取全文"。
3. **限流**：S2 已配置 API key（2026-08-29，存于用户环境变量 `S2_API_KEY` + psp config），突发连发仍会瞬时 429——重试前等 10 秒以上，不要重试轰炸。
4. **S2 key 约定**（已配置，全组生效）：环境变量 `S2_API_KEY`（scholar-search/s2cli、deep-research 系脚本默认读取）+ `~/.paper-search-pro/config.yaml` 的 `semantic_scholar_api_key:`（paper-search-pro）+ academic-search 的 curl 头 `-H "x-api-key: $S2_API_KEY"`。papers-skill 与 paper_search 无 key 通道（设计如此，限流时换渠道）。
5. Python 一律 `D:/Python314/python.exe`；`uvx` 已装（0.12.7）；`node` v24 可用（academic-search 的 .mjs 脚本、CDP 模式可跑）。

## 输出落点（专利流程内）

1. **`01_现有技术检索报告.md` 的"NPL 对比文件"节**：每条含 DOI/arXiv ID、题名、作者、年份、来源渠道、检索式、与发明的区别特征比对结论（X/Y/A 分类）。
2. **`_evidence_pack.md`**：NPL 证据锚点与专利证据同表维护，供 claim-drafter 引用。
3. **PAA 打包时**：NPL 文献写入 `paa/logic/related_work.md`，原文转写/元数据存 `paa/evidence/prior_art_npl/`，MANIFEST 记录 NPL 数量。

## 已安装清单（事实源 `D:/aicoding/mylib/skills/`，各工具端 junction 引用）

- `academic-search`（ustc-ai4science，570★）— arXiv/S2/OpenAlex/Crossref/Unpaywall/PubMed/GS/知网；两段式检索；CCF 分级
- `paper-search-pro`（147★，mylib 仓库根 `paper-search-pro/`）— 七源四档；Shadcn HTML 报告；PRISMA-S；NSSD/yiigle 中文
- `paper_search`（Microsoft ResearchStudio）— 六源并发快查
- `papers-skill` — 自带 Python CLI（S2 2 亿篇 + arXiv PDF）
- `scholar-search` — uvx 四 CLI（s2cli/openalexcli/arxivy/dblpcli）
- `literature-search` / `literature-review` / `citation-management` / `deep-research`（lingzhi227）
- `anysearch`（通用实时搜索兜底，源在 mylib/claude-user-skills/anysearch）

技能事实源统一在 `D:/aicoding/mylib`：专利组在 `paa/skills/`，学术组在 `skills/`。Codex 运行时通过 `~/.codex/skills/` 的 junction 引用 mylib，不做第二份副本。
