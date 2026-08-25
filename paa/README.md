# PAA — Patent Application Artifact

> Universal four-layer machine-executable knowledge package for patent drafting. Adapts the ARA / GPA architecture (cognitive layer / artifact layer / exploration graph / grounded evidence) into the patent domain, with four patent-specific gates.

This README is the **tool-agnostic core**. It is intentionally written so that any LLM-based tool (Claude Code, Kimi, Codex CLI, generic Agent SDKs, Grok, Pi, etc.) can ingest it directly as instructions. Tool-specific adapters live in `./adapters/`.

---

## What is a PAA

A **P**atent **A**pplication **A**rtifact (PAA) packages a patent application as a structured, machine-executable knowledge package. The same architecture is shared with the universal ARA (`paper_compiler`) and grant-proposal variant (`proposal-compiler` / GPA); PAA is the patent-domain instance.

```
PAA/
├── MANIFEST.md                  # root: title, claims, gates, gaps
├── logic/                       # cognitive layer (knowledge)
│   ├── invention.md             # 技术领域/技术方案/技术效果
│   ├── subject_matter.md        # 客体适格分析 (Article 25 / 2.2)
│   ├── claims_analysis.md       # 独立权利要求拆解 (preamble + characterizing portion)
│   ├── inventive_concepts.md    # 创造性点 (each falsifiable, evidence-bound)
│   ├── prior_art.md             # 对比文件图 (X/Y/A 分类)
│   ├── related_work.md          # related patent/non-patent literature
│   └── solution/                # 实施方案 (drafting plan, strategy)
├── application/                 # artifact layer (formal outputs)
│   ├── claims.md                # 权利要求书 (独立 + 从属 + 多主题)
│   ├── specification.md         # 说明书 (五要素)
│   ├── drawings.md              # 附图清单与描述
│   └── abstract.md              # 说明书摘要
├── trace/                       # exploration graph
│   └── exploration_tree.yaml    # 权利要求改版史 + 绕行决策 + 被否方向
└── evidence/                    # grounded evidence (all real, no fabrication)
    ├── prior_art_search/        # 真实 pn + 检索式 + 相似度
    ├── prior_art_claims/         # 对比文件权利要求全文 (Markdown transcription + screenshot .png)
    ├── scoring/                  # AHP-SEM 评分数据 + 权重一致性
    └── design_around/            # 逐特征对照表 + 机制级绕行决策
```

## Inputs (any combination, like ARA/GPA)

- 技术交底书 (PDF / Word / Markdown / docx)
- 检索报告 / 对比文件列表
- 现有申请文件草稿 (权利要求 / 说明书 / 附图 / 摘要)
- 审查意见通知书 (OA) — fed into `trace/exploration_tree.yaml` as `oa-response`
- 代理人会议纪要 / 发明人访谈笔记
- 评分数据 (e.g., `patent-grant-scorer` 输出)

## Four-stage protocol (paralleling ARA's epistemic chain-of-thought)

### Stage 1 — Semantic Deconstruction
Strip narrative framing. Extract atoms with type + provenance:
- 发明要素 (technical problem/solution/effect), 权利要求特征 (preamble vs characterizing), 创造性点, 对比文件, 实施例, 参数, 公式, 设计绕行决策, OA 反馈
- Provenance: `user` / `ai-suggested` / `ai-executed` / `user-revised`
- Build **evidence ledger first**: enumerate every 权利要求, 实施例, 附图, 对比文件 (in order). Save `claims.md` with full text + screenshot of the 原文 if source is PDF/Word.

### Stage 2 — Cognitive Mapping → `logic/`
Map atoms into the cognitive layer with cross-layer references:
- `invention.md` — 技术问题 → 技术手段 → 技术效果 闭环
- `subject_matter.md` — patent Article 25 / 2.2 analysis (技术方案 vs 智力活动规则/商业方法)
- `claims_analysis.md` — for each 独立权利要求, mark **preamble (前序)** vs **characterizing portion (特征部分)**, list every **difference feature (区别特征)** with a binding to 实施例 and 对比文件
- `inventive_concepts.md` — each 创造性点: Statement / Proof (→ 实施例 ID / 对比文件 ID) / Status
- `prior_art.md` — typed citation graph (X/Y/A classification, closest prior art, differences)
- `solution/` — drafting strategy: 机制级绕行 decisions, claimed scope analysis

### Stage 3 — Artifact Layer → `application/`
The formal patent application files. Each file mirrors the corresponding CNIPA requirement:
- `claims.md` — 独立权利要求 (with preamble/特征部分 structure) + 从属 + 多主题 (装置/介质/电子设备)
- `specification.md` — 五要素 (技术领域/背景技术/发明内容/附图说明/具体实施方式)
- `drawings.md` — 附图清单 + 每幅 Mermaid 描述 + 统一标号体系
- `abstract.md` — ≤300 字 + 摘要附图指定

### Stage 4 — Exploration Graph → `trace/exploration_tree.yaml`
Patent-specific node types:
- `claim-version` — each round of independent-claim rewrite (e.g., v1 事实注入 → v2 冲突标记注入 → v3 封箱+元适配)
- `prior-art` — each discovered conflict/contrast document, with `relationship: conflicts | contrasts | background`
- `design-around` — workaround decision: which verb was changed, what mechanism was substituted
- `dead-end` — rejected claim directions (with reason)
- `oa-response` — Office Action response (each review opinion + how it was addressed)

Support levels: `explicit` (from source) / `inferred` (reconstructed).

## Four patent-specific gates (硬性门禁)

Run after Stage 3, before MANIFEST.md finalization. Each gate produces PASS/FAIL with concrete fix instructions.

1. **客体适格门禁 (Article 25 / 2.2)** — 一票否决: any pure business rule / mental activity rule → FAIL. 检查 `claims.md` 与 `invention.md` 是否绑定到具体技术手段与内部结构。
2. **新颖性/创造性证据绑定门禁** — every 独立权利要求 difference feature must bind to ≥1 prior_art node in `evidence/prior_art_search/` with a real `pn` (no fabricated numbers). 一个无证据绑定的区别特征 = 未完成。
3. **充分公开门禁 (Article 26.3)** — every 权利要求 feature has ≥1 实施例 paragraph supporting it; parameters / formulas / thresholds are concrete (not black-box). 特别检查算法类与LLM类申请。
4. **禁止编造对比文件** — integrity hard rule: every cited pn appears in `evidence/prior_art_claims/` with real claim text (or in `evidence/prior_art_search/` with search receipt). No fabrication, no "近似的"、"类似" placeholder.

If any gate FAILs: artifact is **incomplete** until fixed. The MANIFEST.md lists gate status + concrete fix list.

## Validation — Seal Level 1 (mandatory-core checks)

Run `./scripts/validate.py <paa-dir>`. It checks:
- All mandatory-core dirs and files exist and non-empty
- `MANIFEST.md` has valid frontmatter + Layer Index
- `claims_analysis.md` lists all 独立权利要求 with preamble/特征部分 split
- `inventive_concepts.md` has C01+ blocks with Statement / Proof / Status
- `prior_art.md` has typed citation graph with conflict/contrast edges
- `evidence/prior_art_search/` has at least one real pn
- `evidence/prior_art_claims/` has transcription (not just citation)
- `trace/exploration_tree.yaml` parses; explicit nodes carry source refs; design-around / dead-end / claim-version are not invented
- Cross-layer bindings resolve: 区别特征 → 实施例 ID → 对比文件 pn → score data
- All four gates pass
- No fabricated prior art (cited pn ⊆ evidence/prior_art_search)

## Cross-layer binding example

```
difference_feature: "对违背图谱关系路径的候选结果施加惩罚因子"
  ├─ inventive_concept.md C03.Proof → application/specification.md §embodiment_1
  │   └─ evidence/scoring/scoring.json → I1=5.15
  ├─ prior_art.md §D1 (CN121636664A) — relationship: contrasts (对方图谱只做加法召回, 无减法)
  └─ evidence/prior_art_claims/CN121636664A.md — claimed claim 1 excerpt
```

## Hard rules (carry-over from ARA + patent-specific)

1. **禁编造专利号 / 文献号** — every cited pn must come from real prior-art search (`incopat-search` or equivalent real source)
2. **禁 AI 列发明人** — applicant/inventor data must be `user`-provenance
3. **效果表述实测口径** — 禁"100%/大幅/领先"等绝对化用语
4. **权利要求禁模糊词** — 禁"约/大概/左右/如权利要求"
5. **术语全文一致** — terminology-keeper pass on `claims.md` vs `specification.md`
6. **No silent omissions** — files whose absence is intentional must appear in `MANIFEST.md` with reason
7. **Source-bounded minimums** — claim / evidence counts are targets, not quotas; under-claim is honest, over-claim is fraud

## Integration with existing tools

- `cn-patent-application-cluster` skill → orchestrates intake, patent-point tree, prior-art preparation, drafting, examiner review, and packaging; companion role prompts live in `./agents/`
- `incopat-search` skill → feeds `evidence/prior_art_search/` (real pn + search expressions + semantics scores)
- `patent-grant-scorer` skill → feeds `evidence/scoring/` (AHP weights, SEM scores, indicator scores)
- `cnipa-drafting-workflow` skill → produces `application/` layer content
- `patent-disclosure-skill` → produces `logic/invention.md` from project docs
- 探索图(`trace/`)is) is the connective tissue across drafting rounds that current scattered git commits lose

Portable copies are under `./skills/`; Codex role prompts are under
`./agents/`. See `./PATENT_TOOLKIT.md` for installation and provenance.

## Tool adapters

This README is the tool-agnostic core. Per-tool wrappers live in `./adapters/`:

- `claude.md` — Claude Code `SKILL.md` format (frontmatter + tools)
- `codex.md` — Codex CLI plugin format reference
- `kimi.md` — Kimi skill/agent format reference
- `agent.md` — Generic AI Agent SDK instructions format
- `grok.md` — Grok plugin format reference
- `pi.md` — Pi assistant format reference

Each adapter is a thin wrapper that ingests this README and translates it into the tool-specific format.

## Example

A fully-built PAA example based on the P05-1 case lives in `./example/`. It includes:
- All mandatory core files
- Real prior art evidence (CN121636664A, CN121659916A)
- Three-round exploration graph (claim-version history: 事实注入 → 冲突标记 → 封箱+元适配)
- Pass-through of all four gates

## Scripts

- `./scripts/scaffold.py` — creates empty PAA directory structure
- `./scripts/validate.py` — runs Seal Level 1 + four gates on an existing PAA

## Engine

`./engine/patent_ara/` — PatentARA, the Python implementation of this spec:
parse patent text → claim decomposition → Incopat search → LLM element
evaluation → CNIPA three-step evaluation → four gates → AHP-SEM scoring →
`export_paa()` emits the PAA directory defined above. Pure stdlib;
see `./engine/patent_ara/README.md`.

## License

MIT — make it yours, please cite upstream (ARA / GPA / PAA) when redistributing.
