# powergrid_skills — 电网论文技能包

从 10 个开源 GitHub skills 仓库（`D:/aicoding/lib/skills_external/`，完整克隆）中精选合并的高价值组件集合，面向电网/电力系统方向论文（C2GES、MA-SQLGrid 等）的写作、核查与投稿流程。

## 合并原则

1. **只补缺口**：审稿模拟与期刊画像环节本地已有更强系统 `D:/aicoding/paper_reviews/`（9 期刊画像 + 多智能体审稿），本包**不重复合并**相关组件；只合并其不覆盖的能力。
2. **精选拷贝**：`skills_external/` 保留完整上游克隆，本包是精选文件的拷贝。组件升级需重新对照上游仓库。
3. **保留原文件名**：同名文件（如多个 `SKILL.md`）以子目录区分来源 skill 单元。
4. **可溯源**：每个目录的 `MANIFEST.md` 记录每个文件的来源仓库 / 原路径 / 用途 / 用法。

## 目录结构

```
powergrid_skills/
├── README.md                  # 本文件
├── router.yaml                # 路由表（任务 → 组件，人读）
├── router.py                  # 路由 CLI（纯 stdlib）
├── citation_verification/     # 引用真实性与元数据核验
├── consistency_lint/          # 全文一致性与 LaTeX 静态检查
├── claim_evidence/            # claim-证据绑定与数字核查
├── writing_quality/           # 去 AI 腔与写作质量
├── paper_templates/           # 论文骨架 / 审稿自查 / 返修模板
└── statistics/                # 统计报告规范
```

### citation_verification（11 文件 + MANIFEST）

投稿前引用核查。亮点组件：

- `verify.py`（AutoResearchClaw）：三层引用核验引擎，检出幻觉参考文献，纯 stdlib 零依赖。
- claude-scholar 三脚本（`verify-citations.py` / `format-checker.py` / `api-clients.py`）：在线比对 Crossref / Semantic Scholar 等 API。
- `SKILL.md` + `common-patterns.md`（nature-skills）：逐字段交叉验证协议（作者/标题/年份/卷期/页码）。
- 4 份学术 API 协议文档（Semantic Scholar / Crossref / OpenAlex / arXiv）。

### consistency_lint（5 文件 + MANIFEST）

全文一致性与 LaTeX 静态检查。亮点：`check_consistency.py`（nature-skills）机械扫描一致性风险；`latex_guard.py`（PaperSpine）LaTeX 守卫检查；Supervisor-Skills 的 latex/grammar 规则清单。

### claim_evidence（19 文件 + MANIFEST）

claim-证据绑定与数字核查——本包最厚的一块。亮点：

- `scientific-writing/` 完整 skill 单元（scientific-agent-skills）：`audit_claims.py` 审计 claim→证据映射，`claim_evidence_template.csv` 逐条登记"正文 claim ↔ 结果文件"。
- `paper-claim-audit/SKILL.md`（Auto-claude-code-research-in-sleep）：零上下文数字核对协议，fresh reviewer 防确认偏误。
- `claim_verification_protocol.md` + `ai_research_failure_modes.md`：核查流程规范与失败模式清单。

### writing_quality（6 文件 + MANIFEST）

去 AI 味 / 降 AIGC。亮点：`phrases-to-cut.md` + `patterns-english.md`（claude-scholar）AI 高频短语与句法模式库；`humanize_check.py`（PaperSpine）扫描残留 AI 模式；`ai-tone-guardrails.md` 润色约束。

### paper_templates（19 文件 + MANIFEST）

论文骨架 / 审稿自查 / 返修模板。亮点：

- `benchmark-paper-template/` 完整 skill（Supervisor-Skills）：基准论文五支柱框架（Gap → Pipeline → Evaluation → Findings → Companion Method），**MA-SQLGrid 直接对口**。
- `kill-argument/SKILL.md`：双线程对抗评审，模拟最强拒稿意见。
- `rigor-reviewer/`（AI-Research-SKILLs）：ARA Seal Level 2 六维度语义评审。
- nature-skills 返修模板 `cover-letter.tex` / `response-to-reviewers.tex` + PaperSpine `structured_review.py` / `respond_check.py`。

### statistics（6 文件 + MANIFEST）

统计报告规范。亮点：`assumption_checks.py` 假设前提检查；`test_selection_guide.md` 检验选择；Nature 系 `statistical-reporting.md` + `reviewer-checklist.md` 双对照。

## 路由使用

```bash
# 按任务描述路由，输出匹配类别 + 应加载文件绝对路径 + note
python router.py "给 references.bib 做引用核查"
python router.py "帮我去 AI 味，降低 AIGC 痕迹"

# 列出全部 10 个任务类别
python router.py --list

# 机器可读输出（供 agent 消费）
python router.py --json "核对正文数字与表格是否一致"
```

打分规则：任务描述每命中一个关键词计 1 分，命中越多排名越前；无命中时打印全部类别。

路由表覆盖的 10 个任务类：投稿前引用核查、全文一致性/LaTeX 检查、claim/数字/证据核查、去 AI 味/降 AIGC/润色、写基准论文、写实验章节/表格规范、审稿前自查/模拟拒稿、返修回复、统计显著性报告、ARA/论文语义审稿。

**默认提示**：期刊适配与多智能体审稿模拟走 `D:/aicoding/paper_reviews/`（9 期刊画像），不在本包。

## 来源与许可

| 仓库 | LICENSE | 本包引用目录 |
|---|---|---|
| AI-Research-SKILLs | MIT | citation_verification, paper_templates |
| Auto-claude-code-research-in-sleep | MIT | claim_evidence, paper_templates |
| AutoResearchClaw | MIT | citation_verification |
| PaperSpine | MIT | consistency_lint, claim_evidence, writing_quality, paper_templates |
| Research-Paper-Writing-Skills | MIT | paper_templates |
| Supervisor-Skills | CC BY-NC-SA 4.0 | consistency_lint, writing_quality, paper_templates |
| academic-research-skills | CC BY-NC 4.0 | citation_verification, claim_evidence, writing_quality, statistics |
| claude-scholar | MIT | citation_verification, writing_quality |
| nature-skills | Apache 2.0 | citation_verification, consistency_lint, paper_templates, statistics |
| scientific-agent-skills | MIT | claim_evidence, statistics |

注意：Supervisor-Skills（CC BY-NC-SA 4.0）与 academic-research-skills（CC BY-NC 4.0）为**非商业**许可，仅限学术研究用途；Supervisor-Skills 衍生分发需保持同许可（SA）。

## 维护提醒

- `D:/aicoding/lib/skills_external/` 是 10 个仓库的完整克隆，本包是**精选拷贝**，不随上游自动更新。
- 组件升级流程：对照上游仓库对应路径 diff → 重新拷贝 → 更新本目录 `MANIFEST.md`（若有增删）→ 同步 `router.yaml` 的 components 清单。
- 本包内文件不要就地魔改；需要定制时复制到项目内再改，保持与上游 diff 可读。
