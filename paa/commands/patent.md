---
description: 专利撰写统一入口——自动按"有没有交底书"路由到挖交底/起草/门禁阶段，一条命令跑全程
argument-hint: [案件简称或项目路径] [可选: disclosure|draft|review|finalize 指定只跑某阶段]
---

# /patent —— 专利撰写总入口

**一把钥匙走全程。** 你不用再判断该调 `patent-disclosure-skill` 还是 `cnipa-drafting-workflow`——本命令按输入状态自动路由。系统进化是另一把钥匙 `/evolve-patent-system`（收到 OA 才用），**不在本入口内**，避免误触基因组。

## 路由逻辑（自动判定，无需用户指定）

1. **定位案件目录**：`output/<案件简称>/`（不存在则新建）。
2. **判断处于哪一阶段**：
   - 目录内**无** `技术交底书.md` / `00_发明要素表.md`，输入是项目路径/代码/论文/PPT → **阶段 A：挖交底**
   - **有**交底书但**无** `02_权利要求书.md` 等四件套 → **阶段 B：起草**
   - 四件套已在、要审查或改某环 → **阶段 C：审查/门禁**
3. 用户用第 2 参数（`disclosure|draft|review|finalize`）可**强制**只跑某阶段。

## 阶段 A —— 挖交底书（无交底书时）
读取并执行 `.claude/skills/patent-disclosure-skill/SKILL.md` 的 8 步流程（intake→扫描→专利点融合→查新→预览→交底书生成→自检），产出 `技术交底书_{时间戳}.md`+`.docx`。完成后**自动衔接阶段 B**（除非用户 `disclosure` 限定只挖交底）。

## 阶段 B —— 起草四件套（有交底书时）
读取并执行 `.claude/skills/cnipa-drafting-workflow/SKILL.md` 标准工作流：Intake→Evidence Pack→PGTree 大纲→分块撰写（独权→从权、说明书绑证据）→RRAG 审查环→提交前门禁。由 `patent-orchestrator` 编排 11 个专家 agent，产出：
`00_发明要素表 / 01_检索报告 / 02_权利要求书 / 03_说明书 / 04_附图 / 05_摘要 / 06_审查自评26条 / 07_审查自评22条 / _oa_amendment_playbook`。

## 阶段 C —— 审查 / 门禁 / 改某环
按需调用分步能力（等价于原分步命令，仍可单独用）：
- 一致性+26条：`quality-reviewer` → `06_审查自评_26条.md`
- 三步法22条：`patentability-examiner` → `07_审查自评_22条.md`
- 改权项/说明书：`claim-drafter` / `specification-drafter`
- 合稿：`finalize` → `终稿_<发明名称>.md`
- 确定性门禁：`python scripts/patent_static_check.py output/<案件> --json`

## 用法示例
```
/patent 六棱铅笔 D:/项目/铅笔设计稿      # 从素材起步：A→B→C 全程
/patent 离线文件传输                      # 已有交底书：直接 B→C
/patent 离线文件传输 review               # 只做审查门禁
```

## 边界
- 严守 `knowledge/常见问题与避坑.md` 合规底线（禁编造对比文件号、AI 不列发明人、终稿需人工复核）。
- 收到审查意见要**进化系统**（而非改单个案子）→ 用 `/evolve-patent-system`。
