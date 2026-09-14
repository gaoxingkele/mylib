---
name: patent-pipeline
description: "中国发明专利撰写流程入口（薄路由）——把各阶段派发到 paa/ 族真实资产，不自行实现检索、撰写或审查逻辑。支持发明专利与实用新型（CN 单管辖）。Use when user says \"写专利\", \"patent pipeline\", \"专利申请\", \"draft patent\", \"写权利要求书\", or wants to draft a CN patent application."
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Skill
metadata:
  argument-hint: "[invention-description — CN]"
  version: "2.0.0"
  scope: CN-only
---

# Patent Pipeline: CN 专利撰写入口（薄路由）

Draft a CN patent application based on: **$ARGUMENTS**

> **v2.0 改道说明（2026-09-14）** — 本 skill 原版（v1）串联 9 个 slash command，实测其中 **7 个在任何端都从未实现**：`/prior-art-search`、`/patent-novelty-check`、`/invention-structuring`、`/figure-description`、`/embodiment-description`、`/patent-review`、`/jurisdiction-format`。溯源确认它们并非搬运丢失（ARIS 上游 `42-wanshuiyin-ARIS` 是论文套件，本身无这些 skill），而是改编时从未写出。
>
> 已重写为**薄路由**：不新增平行流水线、不重复实现逻辑，只把各阶段派发到 `mylib/paa/` 族与 `mylib/skills/` 的既有资产。只有 `claims-drafting` 与 `specification-writing` 是真实可用的原 v1 资产，予以保留。

## 管辖与范围

- **JURISDICTION = `CN`**（固定，CNIPA）。原版的 US/EP 分支**超出本项目范围**（项目范围：发明专利——软件方法+装置+介质+电子设备；外观不做）。`../shared-references/patent-format-us.md` 与 `patent-format-ep.md` 仅作格式参考保留，本流水线**不产出** US/EP 文本。
- **PATENT_TYPE = `invention`** | `utility_model`
  - `utility_model`（实用新型）：CN 限，**仅装置/结构权项，无方法权项**；可复用本流程但省略深度检索。
- **AUTO_PROCEED = `false`** —— 每阶段必须等用户明确确认。专利申请需要发明人判断，不得自动推进。仅当用户显式要求自主模式时才置 `true`。
- **OUTPUT_DIR** —— 遵循宿主项目产物约定。本项目（zhuanlishenqing）为 `output/<案件名>/`，采用 `00`–`07` 编号；无约定时退回 `patent/`。

## 阶段 → 资产映射

全部路径相对本 skill 目录，均已核验可达。**执行时 `Read` 对应 SKILL.md，不要凭本表臆测其内容。**

| 阶段 | 派发到 | 要点 |
|---|---|---|
| **0 输入解析** | 本文 §Phase 0 + `templates/INVENTION_BRIEF_TEMPLATE.md` | 结构化/对话式输入 → 统一 brief |
| **1 现有技术检索** | `../../paa/skills/incopat-search/SKILL.md`（专利腿）<br>`../../paa/skills/npl-prior-art-search/SKILL.md`（NPL 腿） | **两条腿都跑**；禁编造 pn，每条留真实证据 JSON；NPL 查询须"拆短" |
| **1b 新颖性/创造性门禁** | `../../paa/skills/patent-grant-scorer/SKILL.md` | **先门禁后评分**；客体、单篇 X 文件、充分公开/支持单列，FAIL 不得被均分抵消 |
| **2 发明结构** | `../../paa/skills/patent-disclosure-skill/SKILL.md`（模式 A）<br>`../../paa/skills/cnipa-drafting-workflow/SKILL.md` Step 1–3 | 产出要素表、检索报告、撰写大纲（PGTree）；信息缺口集中列出 |
| **2b 权利要求** | `../claims-drafting/SKILL.md` + `templates/PATENT_CLAIMS_TEMPLATE.md` | CN 两部式（**其特征在于**）；编号连续**不分组**；禁 empirical content |
| **3 说明书** | `../specification-writing/SKILL.md` + `templates/PATENT_SPECIFICATION_TEMPLATE.md` | 五要素；权利要求支持逐条映射；术语与标号全文一致 |
| **3b 附图** | `../../paa/skills/cnipa-drafting-workflow/SKILL.md` Step 4 | 附图清单 + 附图标号体系；选定摘要附图 |
| **4 审查** | `../../paa/skills/cnipa-drafting-workflow/SKILL.md` Step 5–6<br>`../../paa/skills/patent-grant-scorer/SKILL.md` | 26.3/26.4、22.2/22.3 三步法、25 条客体、术语一致性、摘要字数、文献号真实性 |
| **5 输出** | CNIPA 直出 | 按宿主项目产物约定落盘；**终稿必须代理人复核** |

> **宿主项目自带专利 agent 团队时优先委派**：若项目存在 `.claude/agents/` 专利团队（如 zhuanlishenqing 的 patent-orchestrator / disclosure-analyst / prior-art-researcher / claim-drafter / specification-drafter / drawings-planner / abstract-drafter / quality-reviewer / patentability-examiner / terminology-keeper），把阶段派发给该团队，本路由退为流程骨架。该项目的生产入口是 `/patent`（见其 `CLAUDE.md`）。
>
> **PAA 打包**：需要四层结构化工件 + 四门禁时，改用 `../../paa/SKILL.md`（PAA compiler），产物落 `paa/`。

## 常量

- `MAX_REVIEW_ROUNDS = 2` —— 审查-修改循环上限
- `MIN_INDEPENDENT_CLAIMS = 2` —— 通常方法 + 系统；实用新型为 1（仅装置）
- `MAX_TOTAL_CLAIMS = 20`
- `CLAIM_STYLE = CN` —— 两部式，`其特征在于`

## State Persistence（压缩恢复）

专利撰写是长任务，可能触发上下文压缩。**每阶段结束**写一次状态文件（位置随 `OUTPUT_DIR`）：

```json
{
  "phase": 3,
  "jurisdiction": "CN",
  "patent_type": "invention",
  "invention_title": "...",
  "claims_count": 15,
  "claim_hash": "<当前独权哈希>",
  "search_claim_hash": "<检索所用独权哈希>",
  "status": "in_progress",
  "timestamp": "2026-09-14T15:00:00"
}
```

调用时检查该文件：缺失或 `status: "completed"` → 全新开始；`in_progress` 且 24h 内 → **从保存阶段恢复**（读产物文件重建上下文）；超过 24h → 视为陈旧，重新开始。

> `claim_hash` / `search_claim_hash` 是 `patent-grant-scorer` 的版本绑定要求：独权实质修改后，旧检索与旧评分自动过期（`STALE_REVIEW_RESEARCH_REQUIRED`）。

## Workflow

### Phase 0: 输入解析

从 `$ARGUMENTS` 提取：发明描述（结构化 brief / 对话式 / 图纸）、专利类型（"实用新型" → `utility_model`，默认 `invention`）、覆盖项（语言、输出格式、审查轮数）。

再收集上下文：读 `INVENTION_BRIEF.md`（若有）、项目内既有交底书与图纸、既有产物目录、状态文件（恢复用）。

输入不足时：完全没有描述 → 请用户描述或填 `templates/INVENTION_BRIEF_TEMPLATE.md`；有图纸 → 在 brief 中引用；无图纸 → 记下待补并规划所需视图。

**对话式输入**须先转成 brief 结构写入 `INVENTION_BRIEF.md`，供下游阶段消费。

### Phase 1: 现有技术检索与新颖性门禁

**1.1 检索** —— 按映射表派发到 `incopat-search`（专利腿）与 `npl-prior-art-search`（NPL 腿）。

**1.2 门禁** —— 派发到 `patent-grant-scorer`：先跑硬门禁，再做风险排序。

**🚦 Checkpoint** —— 呈现检索全景与门禁结论：

```
检索完成：
- 专利对比文件 X 件；NPL 对比文件 Y 件
- 最接近现有技术：[pn] —— [为何最接近]
- 硬门禁：[全通过 / 阻断项列表]
- 新颖性/创造性：[可专利 / 修改后可专利 / 不可专利]
- 主要风险：[列表]
```

**⛔ 停在此处等用户回复。** `go` → Phase 2；给调整意见 → 收窄范围后重跑；`stop` → 存进度。

**State**：写 `phase: 1`。

### Phase 2: 发明结构与权利要求

**2.1 结构** —— 派发到 `patent-disclosure-skill`（模式 A）+ `cnipa-drafting-workflow` Step 1–3，分解出发明核心构思、支撑特征、可选特征，建 PGTree 撰写大纲。

**2.2 权利要求** —— 派发到 `claims-drafting`（CN 两部式）。

**🚦 Checkpoint**：

```
发明已结构化：
- 核心构思：[摘要]
- 权项类别：[方法/系统/介质/设备]
- 权项数量：[X] 独权 + [Y] 从权 = [Z] 总数
- 独权 1（最宽）：[前 50 字]
- 审查结论：[通过项 / 待修项]
```

**⛔ 停在此处等用户回复。** `go` → Phase 3；调整意见（如"放宽独权 1"、"补从权"）→ 改权项；`stop` → 存进度。

**State**：写 `phase: 2` + `claim_hash`。

### Phase 3: 说明书

派发到 `specification-writing`（五要素、逐条支持映射），附图部分派发到 `cnipa-drafting-workflow` Step 4。

**🚦 Checkpoint**：

```
说明书完成：
- 名称：[标题]
- 章节：技术领域 / 背景技术 / 发明内容 / 附图说明 / 具体实施方式 / 摘要
- 实施例：[X] 个
- 附图标号：[Y] 个部件已映射
- 摘要字数：[Z]（上限 300 字）
- 权项支持：[全覆盖 / X 个要素缺支持]
```

**⛔ 停在此处等用户回复。**

**State**：写 `phase: 3`。

### Phase 4: 审查

派发到 `cnipa-drafting-workflow` Step 5–6，跑 26 条与 22 条自评与术语一致性扫描；必要时 `patent-grant-scorer` 复评。

**State**：写 `phase: 4` 与审查结论。

### Phase 5: 输出

按 `OUTPUT_DIR` 约定编译最终四件套（权利要求书 / 说明书 / 摘要 / 附图清单）落盘。

| 产物 | 位置 | 说明 |
|---|---|---|
| 权利要求书 | `OUTPUT_DIR` | CNIPA 格式 |
| 说明书 | `OUTPUT_DIR` | CNIPA 格式 |
| 说明书摘要 | `OUTPUT_DIR` | ≤300 字，含摘要附图指定 |
| 附图清单与描述 | `OUTPUT_DIR` | 标号体系一致 |

**State**：写 `phase: 5, status: "completed"`。

## Key Rules

- **禁止编造**专利号、文献号、法规条款、检索结果。对比文件一律来自 `incopat-search` / `npl-prior-art-search` 的真实返回并留证据。
- **不得把 AI 列为发明人**；申请人/发明人数据只能来自用户。
- 权利要求必须被说明书支持（26.3/26.4）；每个权项要素都要有说明书落点。
- 权利要求**禁**用"约/大概/左右"等模糊词、商标、竞品名、宣传词；**禁**写结果而非特征（"检测精度高" ✗ / "所述开口处形成间隙传感区域" ✓）。
- 效果表述用实测口径，**禁**"100%/大幅/领先"等绝对化词。
- 术语与附图标号全文一致。
- 实用新型**仅** CN、**仅**装置权项。
- `AUTO_PROCEED = false`：每阶段呈现结果并等待确认。子 skill 继承该约定，在各自的检查点同样暂停。
- 不得在未做**人工代理人复核**前标注为可提交；本流水线产出为**草稿**。
- 跨模型审查（`claims-drafting` / `specification-writing` 内的 `mcp__codex__codex`）：该 MCP 不可用时**跳过并在输出中注明**，不得因缺 reviewer 而失败。

## 与其他流程的组合

```
用户直接描述发明 ──────────────→ /patent-pipeline

项目已有交底书 ────────────────→ 直接进 Phase 1
/idea-discovery 产出 IDEA_REPORT → 提取可专利点后进入
/paper-* 产出强结果 ───────────→ 就该方法申请专利（注意先申请后公开）

需要四层 PAA 工件 + 四门禁 ────→ 改用 paa/SKILL.md（PAA compiler）
项目有专利 agent 团队 ─────────→ 优先委派，本路由退为骨架（如 /patent）
```

## 参考（按需读取）

- `templates/INVENTION_BRIEF_TEMPLATE.md` —— 输入结构化模板
- `templates/PATENT_CLAIMS_TEMPLATE.md` —— 权利要求起草工作表
- `templates/PATENT_SPECIFICATION_TEMPLATE.md` —— 说明书骨架
- `../shared-references/patent-writing-principles.md` —— 权项与说明书撰写原则、先行基础规则、常见陷阱
- `../shared-references/patent-format-cn.md` —— CN 格式（其特征在于）；`patent-format-us.md` / `patent-format-ep.md` 仅作参考
- `../shared-references/prior-art-databases.md` —— 现有技术数据库

## 致谢

格式规范的部分内容改编自 MPEP（US）、CN Patent Examination Guidelines（CN）、EPO Guidelines for Examination（EP）。v1 的流水线骨架参考 ARIS（Auto-claude-code-research-in-sleep）的 skill 编排架构。
