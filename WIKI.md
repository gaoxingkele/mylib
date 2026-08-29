# mylib 技能库 Wiki

> 单一事实源：`D:/aicoding/mylib`。三端（Claude Code / Codex / Kimi）以 junction 引用，不做第二份副本。
> 本 wiki 记录每个技能的来源、用处、实测效果与路由关系。更新技能时同步更新本文件。
> 最后更新：2026-08-29

---

## 0. 架构总览

```
事实源 mylib/                        端点（junction）
├── paa/           专利族            → 项目 .claude/skills/、三端 ~/.{claude,codex,kimi-code}/skills/
├── skills/        论文族+检索族       → 三端 skills 目录
├── Paper_CCF/     投稿画像          → 三端
├── RepLLM/  ARA/  HarnessBank/ …    → 三端
└── 三路由：paa（专利）/ paper-writing（论文）/ npl-prior-art-search（检索）
```

路由原则：说人话触发 → 族内按状态二次派发 → 出口确定性门禁兜底（validate.py / claim_formal_check / 禁编造口径）。

---

## 1. 专利族（`paa/`，路由入口 `paa`）

### 1.1 paa — PAA（Patent Application Artifact）框架
- **来源**：本项目（zhuanlishenqing）方法论沉淀；架构移植自 ARA（论文）→ GPA（基金）→ PAA（专利）的领域可移植性三连证。上游思想同 ARA（arXiv:2604.24658）
- **用处**：把一案产物编译为四层机器可执行工件（`logic/ application/ trace/ evidence/`）+ MANIFEST；四道硬门禁：①客体适格（法25/2.2）②新颖性/创造性证据绑定 ③充分公开（法26.3）④禁编造对比文件
- **效果**：`validate.py` 24 项 Seal Level 1 检查 + 四门禁程序化；example（P05-1）24 PASS 0 WARN 0 FAIL；历史教训：P03/P07 死在客体适格、P06-2 充分公开风险——均已成门禁条款
- **配套**：`engine/patent_ara/`（纯 stdlib Python 引擎：解析→claim 分解→incopat 集成→三步法→四门禁→AHP-SEM→export_paa，7 项测试全过）

### 1.2 incopat-search
- **来源**：incoPat 开放数据平台真实 API，厦门大学平潭研究院测试账号（授权至 2026-08-31，测试域 apitest.incopat.com）
- **用处**：真实专利查新——17 子命令：search/count/semantic/info/family/citation/claim/spec/legal/value/assign/licence/reexam/oned1/oned2/twod/batch
- **效果**：三步漏斗（semantic 语义召回→search 关键词补充→claim/spec 精读比对）为查新基线；2026-08-26 联调扩展 ipc/ipcm/status-lite/lgd 字段；凭证存 `paa/skills/incopat-search/scripts/credentials.json`（gitignore）

### 1.3 patent-grant-scorer
- **来源**：项目 AHP（四专家群决策）+ SEM（结构方程）方法论
- **用处**：授权成功率预测——客体适格/新颖性/创造性/充分公开/撰写质量五潜变量 16 指标；多专家仲裁版（拜占庭-马尔可夫异常评分处理、跨轮版本漂移、同批案件相对公平）
- **效果**：P05-1 修改后评估概率 0.461（入 PAA example scoring.json）；外部端点持续演进中（references/ 三篇 + tests/ 已入库）

### 1.4 cnipa-drafting-workflow / patent-disclosure-skill / cn-patent-application-cluster / paa-patent-toolkit
- **来源**：项目工作流 + Codex 原生集群
- **用处**：cnipa-drafting=四件套起草+RRAG 审查环；disclosure=项目文档挖专利点出交底书；cluster（Codex）=挖掘/检索/撰写/评审/打包编排；toolkit=Codex 侧模块路由（mylib-first）
- **效果**：闽投申报 10 篇（P01-P06×2）全套产物即此流水线输出；确定性检查 `claim_formal_check.py` + `patent_static_check.py` 对真实案件跑通

### 1.5 通用专利技能（skills/）
- **claims-drafting / specification-writing / patent-pipeline / shared-references**：来源=外部 patent skill 套件；用处=权利要求/说明书撰写、CN/US/EP 三管辖流水线、共享格式规范（patent-format-cn/ep/us、prior-art-databases）；三端原已装，统一时收敛为 mylib 单一副本

---

## 2. 论文写作族（`skills/paper-writing` 路由）

### 2.1 ARA — Agent-Native Research Artifact
- **来源**：论文《The Last Human-Written Paper: Agent-Native Research Artifacts》（arXiv:2604.24658）+ 仓库 AmberLJC/Agent-Native-Research-Artifact（MIT，同步 commit e52a925 / 2026-08-29）
- **用处**：把 autoresearch 变成结构化可验证产物。8 子技能：research-manager（过程记录）/ compiler（编译，Seal L1 结构校验）/ rigor-reviewer（认知审查，Seal L2）/ research-visualizer（轨迹 HTML）/ research-foresight（grounded 提问）/ context-drop（单 URL 分享）/ research-fuzzer（fuzzer 式调查）/ submit-ara（发布）
- **效果**：论文实测 PaperBench 问答 72.4%→93.7%、RE-Bench 复现 57.4%→64.4%（"保留失败轨迹"是关键）；本地 24 个 ARA artifacts（Stock_benchmark 6 + geo-benchmark 18）Seal Level 1 全 PASS
- **四层结构**：PAPER.md（~200 token 渐进披露）+ logic/（认知层）+ src/（物理层）+ trace/exploration_tree.yaml（探索图，死路一等节点）+ evidence/（原始证据）；跨层绑定、溯源标签

### 2.2 博导推荐表达三件套（2026-08-29 接入）
| 工具 | 来源 | 用处 | 融合决策 |
|---|---|---|---|
| **Supervisor-Skills** | HKUSTDial/Supervisor-Skills（**CC-BY-NC-SA-4.0 非商用**） | 导师式方法+专项 Skill | **融合 6 模块**进路由：paper-polish（忠于原意润色，"需作者确认"机制）/ paper-writer（证据门控正文）/ intro-drafter（六段式引言）/ pre-submission-reviewer（五维投稿前审查）/ idea-evaluator（五维选题评估）/ figure-designer（核心三图审计）。deep-research 重名冲突不融合 |
| **research-writing-skill** | Norman-bury/research-writing-skill | 长项目工程系统（术语表/证据图/进度回写，工社医法分流） | **保持独立**：整包三端 junction；短摘要润色场景"流程比正文重"，按需启用 |
| **academic-paper-skills** | lishix520/academic-paper-skills | 哲学/跨学科：strategist 分析平台→composer 逐章写作（28/35 大纲门槛） | **融合为理论型支线**：academic-paper-strategist → composer 成链；需 8-10 篇样例风格校准 |

### 2.3 其他写作/评估执行器
- **academic-research-suite**（Academic-Research-Skills-Codex）：ARS 学术全流程（outline→draft→revision+审稿模拟）
- **academic-humanizer**（v0.3.3）：学术化改写降 AI 痕迹，保事实/引用/数字
- **idea_spark / scoop_check**（微软 ResearchStudio-Idea）：可证伪想法生成 / 查重先防
- **Paper_CCF**（paper-ccf）：投稿路由——186 件期刊/会议画像（fit/证据门槛/APC/审稿模式/desk-reject 风险/备选）
- **逆向复现族**：repllm-content-parse（PDF→paper.json）→ paper-to-code（Paper2Code 三阶段：规划 UML+依赖图→逐文件逻辑→依赖序生成）→ experiment-code / experiment-design / paper-compilation（LaTeX 编译）
- **harnessbank-gated-evolution**：研究自动化 agent 栈进化（非论文写作本体）

---

## 3. 检索族（`paa/skills/npl-prior-art-search` 路由）

### 3.1 执行器（9+1）
| 工具 | 来源 | 覆盖 | 实测效果 |
|---|---|---|---|
| paper_search | 微软 ResearchStudio-Idea | 六源并发（arXiv/DBLP/OpenAlex/OpenReview/S2/Crossref），自动年份 | NPL 初扫基线 |
| academic-search | ustc-ai4science（570★，MIT） | arXiv/S2/OpenAlex/Crossref/Unpaywall/PubMed/GS/知网；两段式检索；CCF 分级；OA PDF 级联 | 中文/CCF 线首选 |
| paper-search-pro | O0000-code（147★，Apache-2.0） | 七源四档（Quick→Audit）+ PRISMA-S + 中科院/JCR 分区 + NSSD/yiigle 中文 | 系统综述深度扫描 |
| papers-skill | sickn33/agentic-awesome-skills | S2 2 亿篇 + arXiv PDF（自带 CLI） | 无 key 通道 |
| scholar-search | mrshu/agent-skills | uvx 四 CLI：s2cli/openalexcli/arxivy/dblpcli | 引用追溯主力 |
| literature-search / deep-research / literature-review / citation-management | lingzhi227/agent-research-skills | S2/arXiv/OpenAlex→JSONL+BibTeX；六阶段系统综述；多视角对话综述；BibTeX 管理 | deep-research 系脚本默认读 S2_API_KEY |
| anysearch | AnySearch Team（claude-user-skills） | 通用实时搜索（web/学术/专利垂直域） | 兜底层 |

### 3.2 关键经验（实测 2026-08-29）
- **查询拆短**：arXiv/DBLP 是关键词匹配，长句 0 命中（"knowledge graph retrieval augmented generation hallucination"→arxiv=0；"graph RAG hallucination"→5733 条）
- **中文线降级**：OpenAlex 中文语义对工科技语召回差（返回教学/法医噪声）；知网/GS 需 Chrome CDP（未开时如实标注"未检索"）；工科以英文检索为主
- **限流**：S2/OpenAlex 已配 key（环境变量 S2_API_KEY + ~/.paper-search-pro/config.yaml）；突发连发仍会瞬时 429，重试前等 ≥10s
- **合规**：每条 NPL 带真实 DOI/arXiv ID+检索日期；WebSearch 摘要=source-degraded 线索；不绕付费墙

---

## 4. 领域专项与工具

- **mw-\*（管理世界，11 件）**：事实源 mylib/skills/（自 Claude 插件缓存拷贝）；Claude 走插件机制，Codex/Kimi 走 junction；选题/综述/机制/政策/复现/投稿/回复全套
- **aers-powergrid-bridge / codex-ars-powergrid**：电网/AI 论文域路由（AERS/ARS 最小必要子技能）
- **skill-runtime/**（新）：三端 skill 路径审计/修复运行时 + ara/paa/paper-ccf 路由器（外部端搭建）
- **素材库**（未进活跃层，按需启用）：Auto-Empirical-Research-Skills（顶层 22 件，统计/计量/降AIGC）、Research-Paper-Writing-Skills（彭思达方法论）、cnki-skills、gs-skills、thesis-writing-skill 等

---

## 5. 凭证与合规清单

| 项 | 位置 | 状态 |
|---|---|---|
| incoPat 凭证 | `paa/skills/incopat-search/scripts/credentials.json`（gitignore） | ✓ 授权至 2026-08-31 |
| OpenAlex key | `~/.paper-search-pro/config.yaml`（0600） | ✓ 已配（2026-02 起强制） |
| S2 key | 环境变量 `S2_API_KEY` + psp config | ✓ 已配并实测（2026-08-29） |
| NCBI/CrossRef | psp config 可选位 | 未配（医疗线增强用） |
| 禁编造 | 对比文件号必须真实 API 返回 | 硬约定 |
| 许可注意 | Supervisor-Skills=CC-BY-NC-SA-4.0（非商用）；research-writing-skill/academic-paper-skills 待核 | 商用前核 |

---

## 6. 效果时间线（2026-08）

- 08-21：专利四件套流水线 + incopat API 接入（授权账号实测）
- 08-22：PAA 上线（ARA→GPA→PAA 三连证）
- 08-25：mylib 建档，PAA/五技能同步
- 08-26：incopat 联调扩展字段（ipc/status-lite）
- 08-27：P05-1 v3（封箱+元适配），CN121659916A 退出语义 top5
- 08-28：学术检索组安装（8 件）+ NPL 路由 + OpenAlex key
- 08-29：单一事实源重构（三端 99+ junction）→ S2 key → ARA 对齐上游 e52a925（8 子技能）→ 逆向复现族 → 博导三件套融合 → 本 wiki
