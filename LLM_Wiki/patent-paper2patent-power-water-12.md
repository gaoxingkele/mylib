# 论文→专利迁移批次：电力/水利 12 案（PAPER2PATENT-12，2026-10-01）

> 面向任何 LLM 端（Claude Code / Codex / Grok / Kimi）的接续手册。读完本页即可在不翻对话记录的情况下接手该批次。
> 项目根：`C:/aicoding/zhuanlishenqing`（下文 `$P`）；技能事实源：`D:/aicoding/mylib`（下文 `$M`）。
> 批次目录：`$P/output/论文迁移电力水利12案_20261001/`（下文 `$B`）。

## 0. 一句话状态

12 案（电力 P1–P5、水利 W1–W7）交底书 + 完整申请书 + paa 证据包 + 两轮无浏览器查新 + NPL 核验 + 申请书 Word + 证据约束评分 **全部完成**；12/12 四门禁 PASS；**incoPat 未执行**（无凭证），所有分数与门禁均为"中继证据"口径；终稿须代理资质人员复核后才可递交。

## 1. 来源与案件映射

10 篇团队自有论文（`$P/docs/论文专利/papers/*_patent_zh.md` 6 篇 + `$P/docs/论文专利/aaai2026 */` 4 篇）。
**注意**：papers/ 下文件名里的 `peer-review` / `_reviewer` / `Proof` 是存档误命名，用户已确认均为自有论文；不要据文件名判为审稿件。

| 案 | 子目录 | 来源论文 | 独权押的"场景约束→机制改造" |
|---|---|---|---|
| P1 | P1_新能源负荷电价联合情景生成 | ScenarioFlow（数值核心） | 太阳高度角夜间掩码冻结 + 仅有效步算尺度且全程固定 + 自回归流匹配（电价可负） |
| P2 | P2_调度叙事极端保供情景推演 | ScenarioFlow（NL 接口） | 叙事→冻结编码器记忆空间检索先例 + NWP 可核验量剔除方向冲突 + 按天气过程去重 |
| P3 | P3_变压器因果图异常根因 | CSLGA | 通道级禁止关系经编码器敏感度换算为潜空间边违背度 Φ=RFRᵀ + 多工况邻接矩阵门控混合（并集无环为辅助） |
| P4 | P4_输电通道无源域自适应隐患检测 | GRSM 综述空白点 | GIS+相机位姿构造图像距离场（无需点云）+ 类别×距离分级伪标签阈值 |
| P5 | P5_倒闸操作票生成与仿真反向验证 | L2M2V | 候选票文本为已知条件构造反问 + 仿真轨迹为参考答案 + 前提类反问与两级权重（R2 后合入） |
| W1 | W1_流域雨洪水位联合情景生成 | ScenarioFlow | 同步内降雨两段式 + 死水位~坝顶有界映射 + 汇流时滞内实测/外生成 |
| W2 | W2_大坝安全监测因果图诊断 | CSLGA | 环境量根节点、无环只约束测点子阵 + 时滞分箱按物理许可表 + 水压/温度/时效分量归因 |
| W3 | W3_光学SAR跨传感器洪水淹没检测 | GRSM 空白点 | 子流域内教师高置信种子估计本次事件淹没高差 → 先验中心 → 与教师概率融合生成伪标签 |
| W4 | W4_多水源调配因果强化学习 | CausalTrader + TMA | 水务可行域投影（许可余量/死水位库容/混合水质）+ 学习与物理双世界模型 + 前瞻否决回退调度图 |
| W5 | W5_水厂管网因果图异常根因 | CSLGA | 方向掩码+回流白名单 + 按有效容积与实时流量逐时刻时延对齐 + 根因按行程时间分摊 |
| W6 | W6_供水工单管段消歧画像 | LightGMEM | 缓冲区∧关阀后拓扑可达限定候选 + 候选 GIS 属性构造冲突键 + 加权衰减证据阈值触发画像 |
| W7 | W7_水面倒影双峰深度监测 | AGMS | 水位计读数构造水面平面，深度分量分水上/水面/水下三层 + 镜像判别倒影 + 剔除倒影后定位 |

放弃：AHECSA（红海、仅仿真）；TMA 单独申请（并入 W4 从权）；PV-BEV→水利（场景太小众）。
同族已完成案（本批之前）：E1 `$P/output/电力运维图谱记忆构建`、E2 `储能多市场因果强化学习`、E3 `多相机混合高斯安全距离`、E4 `输电通道点体素净空检测`。

## 2. 每案目录里有什么

```
<案>/
  技术交底书_<名称>_<时间戳>.md / .docx     # 多版本并存，最新时间戳为准；旧版不删
  交底书自检记录.md                           # 自检单独成文，交底书正文不含自检清单（skill 要求）
  00_发明要素表.md  01_现有技术检索报告.md  _drafting_outline.md
  02_权利要求书.md  03_说明书.md  04_附图清单与描述.md  05_说明书摘要.md
  06_质量审查报告.md  07_可专利性自评.md
  evidence/prior_art/        # Tavily 中继取回的全文（relay 口径）
  evidence/search/ search_r2/ npl/   # 两轮检索记录、arXiv/Crossref 核验原始响应
  evidence/citations*.json  verify*.json      # gp_verify 逐字核验结果
  evidence/scoring/{scoring_input,search_input,scoring_result}.json + scoring_notes.md
  paa/                        # 四层工件 + MANIFEST；validate.py 23 PASS
  申请书交付_20261001/<编号>_完整申请文件.docx + 附图/ + 交付记录.json
  sim/                        # W2/W5/W7 合成数据仿真（已标注"非实测"）
```

批次公共文件：`$B/00_计划清单.md`、`00_子代理执行规范.md`、`00_第二轮执行规范_复检与NPL核验.md`、`00_评分执行规范.md`、`00_查询通道评估_20261001.md`、`00_汇总报告_20261001.md`、`00_汇总报告_20261001_R2.md`、`00_评分报告_20261001.md`、`_search/`（初检原始命中）、`_scoring/`（cohort 评分）。

## 3. 用到的技能与命令（可直接复用）

| 环节 | 技能 / 脚本 | 备注 |
|---|---|---|
| 交底书 | `$M/paa/skills/patent-disclosure-skill`（prompts/disclosure_builder.md → template_reference.md → disclosure_self_check.md） | 章节结构照 E1 样板 |
| 申请书 | `$M/paa/skills/cnipa-drafting-workflow` + `checklists/cnipa-2026.md` | PGTree 大纲 → 分块撰写 → RRAG 审查 |
| 证据包/门禁 | `$M/paa/scripts/scaffold.py`、`validate.py <案>/paa` | 四门禁；脚本只计 CN 号段，EP/US 件在 07 与 MANIFEST 注明 |
| 专利查新（无浏览器） | `$M/paa/skills/google-patents-search/scripts/gp_search.py --backend tavily "<通用词>"`；Brave API `site:patents.google.com`（key 在 `$P/.env` 的 `BRAVEAPI`） | 检索词只用通用技术词，不写完整方案 |
| 取全文 / 核验 | `gp_fetch.py --backend tavily <PN> --out evidence/prior_art`；`gp_verify.py --citations ... --docs ...` | 只有核验通过的公开号才能进 01/03 |
| NPL | arXiv API `export.arxiv.org/api/query`、Crossref `api.crossref.org/works` | 拆短查询（≤5 词）；S2/OpenAlex 当日限流 |
| Word 交付 | `$P/scripts/build_paper12_word.py [P1 W3 ...]` | 复用 `build_mintou_email_packages.build_docx`；mermaid-cli 12 不传 -w/-H |
| 评分 | `$M/paa/skills/patent-grant-scorer/scripts/ahp_only_scorer.py`；cohort 合并 `$B/_scoring/merge_cohort.py` | ahp_index 是内部指数，**不是授权率** |

### 已知坑（本批踩过，已修或已绕）
- `mermaid_render.py`（已修，mylib `763f694`）：Windows 引号、mmdc 12 的 `-w/-H`、多余 `mmdc` 子命令。本机 `npx -y @mermaid-js/mermaid-cli -i x.mmd -o x.png -b white -s 2`（**不加** `mmdc`）。含括号的行内公式要改写否则渲染失败。
- Python：`D:/Python314` 跑 validate/评分/BigQuery（已装 matplotlib）；`md_to_docx.py` 用 Python313（已装 pyyaml）。
- **BigQuery 禁用于取件**：`patents-public-data` lookup≈390 GB/次、search≈242 GB、similar≈111 GB，月免费 1 TiB；已加前置预算门（默认 50 GB 拒绝）。取件一律走 Tavily。
- Google Patents 直连 503 封 IP 后等 12 小时；恢复后每次间隔 30 秒。PATENTSCOPE 后端 0 命中（解析失效，待修）。
- 浏览器通道（CNIPA 公告站、Perplexity patents、多端网页评审）只在用户本轮点名时才可运行。

## 4. 查新与评分结论（两轮后）

- 12 案均无 X 类文件；创造性风险：W3 中低，其余 11 案中（P3 两个单项中高）。
- 评分（AHP-only robust，四角色×16 指标）：ahp_index 55.3–63.6；11 案 `CONDITIONAL_EVIDENCE_OR_GATE_REVIEW`，P5 `STALE_REVIEW_RESEARCH_REQUIRED`（R2 后改独权未重检）。evidence_confidence 被 `search_status=degraded` 封顶 45。
- 四角色分歧全在 I1–I3（创造性），根因是同族互为组合启示与 E 案抵触，不是检索能解决的。
- 排名（高→低）：P2=W2 63.6 > P3 63.5 > W5 62.7 > W7 62.2 > W1 62.1 > P1 61.9 > W3 60.9 > W4 60.3 > W6 59.1 > P4 58.3 > P5 55.3。

## 5. 待决与待办（接手者先看）

**需用户/代理师拍板**
1. 同日递交：P1/P2/W1 同族；P3/W2/W5 同族；P4/W3 同范式。
2. 抵触申请：E2 实施例三提到多水源（↔W4）、E3 实施例三提到水面倒影（↔W7）、E1↔W6——删段或同日递交。
3. P2 的 D1 CN121642918A（公开 2026-03-10）、P3 的 CN120067948B（2026-05-05）、P1 的 D8（2026-03-27）：申请日定后判现有技术/抵触申请。
4. W2 独权侧重：根节点约束 vs 分量偏离归因。
5. 10 篇来源论文公开时间必须晚于对应申请日。

**可直接执行**
- P0：P5 以当前权 1 重检（Tavily 两轴）并重跑 `ahp_only_scorer.py`。
- P1：补 incoPat 凭证（`$M/paa/skills/incopat-search/scripts/credentials.json` 或 `INCOPAT_*` 环境变量）后，按各案 `01` 第 5 节检索式复检，取 D1/D2 claim/spec 原文，重跑 `merge_cohort.py`；每案按 `03` "预期验证方案"做一组回测/仿真，否则 I4/D3 ≤4。
- P1：各案 07 补写"范式识别→跨领域失败模式→限定锚点"三段式算法原理审查（内容多数已有，缺标题化）。
- P2：附图改绘黑白线条图；申请人/发明人信息（现为 `[待填写]`）。

## 6. 硬性约定（本批沿用项目红线）

禁止编造专利号/文献号；对比文件只用真实 API/中继返回并留证据 JSON；AI 不列发明人；效果用"预期/示例"口径，禁"100%/大幅/领先/显著优于"；权利要求禁"约/大概/左右"；每案只改本案目录；不打开浏览器；不用 BigQuery 取件。

## 7. 相关记录

- 项目 wiki：`$P/wiki/log.md`（2026-10-01 `PAPER2PATENT-12*` 条目）、`$P/wiki/2026-10-01_papers-to-power-water-patent-migration.md`（迁移方法论：同构问题/场景约束/机制改造三列）
- 方法论依据：`$P/wiki/2026-08-22_two-round-novelty-search.md`（双轮复检索）、`2026-08-03_search-informed-differentiation.md`、`2026-09-25_patent-papers-grant-rate-techniques.md`
- git：zhuanlishenqing `3b5a2016`；mylib `763f694`
