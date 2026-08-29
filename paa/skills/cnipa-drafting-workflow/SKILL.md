---
name: cnipa-drafting-workflow
description: 中国发明专利申请文件起草与审查工作流。用于从技术交底书生成 CNIPA 草稿、改写权利要求、补强说明书充分公开、做 26/22 条审查、生成 OA 修改预案或提交前质量门禁。
---

# CNIPA Drafting Workflow

本 skill 是本仓库 `.claude/agents/` 专利团队的本地工作流入口。它吸收三类外部可借鉴做法：

- CNIPA 专利 skill 的 checklist/template-first 思路：先加载合规清单，再写稿，再自检。
- AutoPatent 的 planner / writer / examiner 分工：先规划 Patent Guideline Tree，再由写作 agent 分块生成，最后由审查 agent 回灌修改。
- Pap2Pat 的 outline-guided chunk generation：长说明书按大纲分块撰写，每块都绑定来源证据，避免长文重复和遗漏。

## 适用场景

当用户要求：

- 起草中国发明专利、实用新型草稿或完整申请包；
- 修改/扩写权利要求书、说明书、摘要、附图说明；
- 做 CNIPA 合规体检、充分公开检查、客体合规检查；
- 基于检索报告更新背景技术、区别特征、OA 修改预案；
- 将项目源码、论文、技术交底书转成专利申请文件；

必须先读取本 skill，再读取 `checklists/cnipa-2026.md`。

## 标准工作流

1. **Intake**
   - 读取技术交底书、补充材料、已有申请书和输出目录。
   - 生成或更新 `00_发明要素表.md`。
   - 不编造技术细节；缺少关键参数时集中列出信息缺口。

2. **Evidence Pack**
   - 生成或更新 `01_现有技术检索报告.md`。
   - 若已配置 `.env.incopat`，优先执行 incoPat 专业中文专利检索；若未配置，生成 `incopat_query_plan.json` 并把状态标记为待执行。
   - **NPL 腿**：论文类对比文件按 `.claude/skills/npl-prior-art-search/SKILL.md` 路由检索（默认 `paper_search` 多源并发初扫，中文/深度/引用追溯按需切换），结果入报告的"NPL 对比文件"节，每条带真实 DOI/arXiv ID/URL。
   - 对每个对比文件记录：文献号、来源 URL、公开日、共有特征、区别特征、风险等级。
   - 未核验的文献号不得进入权利要求或说明书正文。

3. **PGTree / Drafting Outline**
   - 在 `output/<案件名>/_drafting_outline.md` 建立树状撰写大纲：
     - 保护主题树：方法 / 系统 / 装置 / 介质 / 设备；
     - 区别特征树：每个区别特征对应技术问题、技术手段、技术效果；
     - 说明书分块树：技术领域、背景技术、发明内容、附图说明、实施例；
     - 证据锚点：每个关键特征指向交底书、源码、图纸、检索报告或用户确认。

4. **Chunked Drafting**
   - 权利要求先写独权，再围绕区别特征树布置从权。
   - 说明书按大纲分块撰写，每块完成后核对术语、标号、参数和权利要求支持关系。
   - 长说明书禁止一次性自由生成；每一块必须说明来源证据。

5. **RRAG Review Loop**
   - reviewer 先列问题，再让对应 writer 修改。
   - 每轮审查记录：问题、依据、修改对象、是否关闭。
   - 对高风险对比文件建立 A/B/C 三套修改预案：宽版、合入关键从权版、应急窄版。

6. **Final Gate**
   - 运行术语一致性、26.3/26.4、25 条客体、22.2/22.3、摘要字数、附图标号和文献号真实性检查。
   - 未通过时不得声称可提交，只能标记为草稿或待代理人复核。

## 产物约定

每个案件目录建议包含：

```text
output/<案件名>/
├── 00_发明要素表.md
├── 01_现有技术检索报告.md
├── _drafting_outline.md
├── _evidence_pack.md
├── 02_权利要求书.md
├── 03_说明书.md
├── 04_附图清单与描述.md
├── 05_说明书摘要.md
├── _terminology.md
├── _consistency_report.md
├── 06_审查自评_26条.md
├── 07_审查自评_22条.md
└── _oa_amendment_playbook.md
```

## 硬性禁止

- 不得把 AI 列为发明人。
- 不得虚构专利号、论文号、法规条款、检索结果。
- 不得把未经核验的公开材料直接写入背景技术。
- 不得把未实际调用的 incoPat / 专业库检索写成已完成。
- 不得只写功能效果而不给技术手段。
- 不得在权利要求中使用商标、竞品名、宣传词或模糊词。
- 不得在未做人工代理人复核前标注为正式提交稿。

## 必读清单

- `checklists/cnipa-2026.md`
- `knowledge/说明书五要素.md`
- `knowledge/权利要求书规范.md`
- `knowledge/摘要规范.md`
- `knowledge/创造性三步法.md`
- `knowledge/充分公开与支持.md`
- `knowledge/常见问题与避坑.md`
