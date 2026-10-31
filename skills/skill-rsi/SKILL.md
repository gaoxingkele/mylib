---
name: skill-rsi
description: >-
  Gate and archive evolution of mylib review/writing skills under a frozen
  evaluator. Use when improving peer-review, proposal review, patent review,
  paper writing, or related skills; when proposing a skill/prompt/harness/context
  patch; or when admitting/rejecting a candidate into the skill gene bank.
  Not for rewriting ReviewSpec constructs, funding scores, or legal gates.
---

# Skill-RSI

目标：借助 **规范保持的递归适应（SPRA）+ HarnessBank 门控**，持续提高 mylib 里**已有**的评审与写作 skill，而不是开放自改评价器，也不是再堆一批无门控的 review skill。

## 核心建议（固定）

1. **只进化可变面**：`prompt` / `skill` / `harness` / `context` 每次只改一个。  
2. **冻结内核**：评价脚本、指南/模板合同、专利法律门禁、`validate_review_basis.py`、AHP/授权概率禁令、ReviewSpec 构念。  
3. **LLM 只诊断与提案；代码只计分与准入**（HarnessBank 分工）。  
4. **发布进 gene bank，拒绝进 negative**；禁止「平均分涨一点就合入」。  
5. 论文 / 申请书 / 专利 **分账**，不合成总分。

## 何时触发

- 用户要求进化、改进、门控合入某评审/写作 skill。  
- 某 skill 反复误报、漏报、模板化、依据不适用、权利要求无锚点。  
- 要把 C-MARS / HarnessBank / metaRSI 结论落到 mylib skill 包。

## 不要触发

- 改 `proposal-writing` 的「禁止资助概率」等宪法级规则。  
- 把 `Auto-Empirical-Research-Skills` 整包 peer-review 推进进化环。  
- 用模型自评当 held-out 证据。  
- 一次同时改多个表面或多个无关 skill。

## 命令

在 mylib 根或任意项目根：

```powershell
python C:/aicoding/mylib/skills/skill-rsi/scripts/skillrsi.py --root <项目或mylib根> <命令>
```

常用：

```powershell
# 初始化本库进化工作区
python .../skillrsi.py --root C:/aicoding/mylib init

# 列出可进化一等公民目标
python .../skillrsi.py --root C:/aicoding/mylib targets

# 登记候选（不改文件，只建档案）
python .../skillrsi.py --root C:/aicoding/mylib propose `
  --target paper_harness.reviewer_protocol `
  --surface context `
  --title "preserve disagreement under compression" `
  --beacon "inquiry_fires_when_open_unsupported_claim_remains" `
  --parent-id g7_stable_replay `
  --notes-path path/to/diff-notes.md

# 跑门控
python .../skillrsi.py --root C:/aicoding/mylib gate --candidate-id <id>

# 合入或拒绝（写 gene_bank 卡 + archive）
python .../skillrsi.py --root C:/aicoding/mylib admit --candidate-id <id> --by "name"
python .../skillrsi.py --root C:/aicoding/mylib reject --candidate-id <id> --reason "..." --by "name"

# 状态
python .../skillrsi.py --root C:/aicoding/mylib status
```

## 与现有组件的关系

| 组件 | 角色 |
|---|---|
| 本 skill（Skill-RSI） | 评审/写作 skill 的进化环与 gene bank |
| `HarnessBank` | 门控方法论（validity→activation→paired→held-out） |
| `meta-rsi` | 项目级证据账本；进化试验可另记 trial |
| `paper_harness/gene_bank` | 论文宿主已有卡；本框架可引用，不重复发明门控语义 |
| `C-MARS`（agent_framework） | 合成/外层实验床；分数默认 `reportable: false` |
| `proposal-writing` / `paa` / `Paper_CCF` | **被进化的宿主**，其校验脚本属于冻结内核 |

## 工作流（代理必遵）

1. `targets` 确认目标在目录内且 `evolved: true`。  
2. 读目标 skill 与 `references/PROTOCOL.md`。  
3. 只改一个表面；写出父代、病理 `(where, why)`、验收 beacon。  
4. `propose` → 填 metrics（若有）→ `gate`。  
5. 门控全绿且人确认后 `admit`；否则 `reject` 并写清原因。  
6. 合入后更新目标 skill 的正文或附属协议，并在卡片里写回放命令。

细节见 [README.md](README.md) 与 [references/PROTOCOL.md](references/PROTOCOL.md)。
