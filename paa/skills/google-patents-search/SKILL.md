---
name: google-patents-search
description: >
  Google Patents 免费检索与原文核验（无需 API key）。用于发明专利研究过程中的
  查新（现有技术检索 / 候选对比文件发现）与验证（按公开号取权利要求与说明书原文、
  逐字引用核验、公开日资格判断）。当 incoPat 不可用、授权过期、额度耗尽，或需要
  做第二轮独立复检索时使用本 skill；也可单独用于"某公开号到底公开了什么"的溯源。
  TRIGGERS: google patents, Google Patents 检索, 免费专利检索, 查新, 现有技术检索,
  prior art, 对比文件, 新颖性检索, 创造性检索, 公开号核验, 权利要求原文, 说明书原文,
  专利溯源, incoPat 不可用时的检索, 第二轮复检索
---

# Google Patents 免费检索与核验

本 skill 解决两件事：

1. **查新/检索**：用免费通道把候选对比文件找出来（`gp_search.py`）；
2. **验证/核验**：把候选升级为**可引用的原文证据**，或明确判定"核验不通过"（`gp_fetch.py` + `gp_verify.py`）。

它是本仓红线（**不得编造公开号**、**不得用检索片段当已核验原文**）在"免费渠道"上的执行器。

## 何时使用

- incoPat 走不通时（账号授权过期 / 未授权接口 / 429 配额耗尽）——本 skill **无需任何 key**；
- 已有一轮检索结论，需要**第二轮独立复检索**（换检索轴、换库）以降低单轮锚定偏置；
- 需要复核某公开号**到底公开了什么**（逐字引用 + 定位 + 取回时间 + sha256）；
- 需要在申请日前公开性的意义上筛选候选（`gp_verify.py --cutoff`）。

## 取数路线（2026-09-26 实测，详见 references/troubleshooting.md）

Google 的自动化拦截是**会话级**的：同一台机器上 `requests` 与无头 chromium 都返回 503 "Sorry…"，
而**用户真实 Chrome 会话**正常。所以路线按可靠度排序：

| 路线 | 命令 | 适用 |
| --- | --- | --- |
| A. CDP 挂载真实 Chrome（推荐，可脚本化） | `--cdp 9222`（Chrome 需以 `--remote-debugging-port=9222` 启动） | 批量、无人值守 |
| B. MCP 浏览器（人工在场最稳） | `--print-url` → `browser_navigate` → `browser_run_code_unsafe` 跑 `scripts/gp_parse_current_search.js` / `gp_parse_current_patent.js` | 单件核验、救援路线 A 被拦时 |
| C. 无头/有头 chromium | `--route headless` / `--headed` | 仅作探测：被拦时退出码 3 + `GP_BLOCKED`，**不会**伪装成 0 命中 |
| D. 离线复算 | `--html <已保存页面>` | 回归测试、复盘、无网络时 |

## 快速开始

```bash
P="D:/aicoding/mylib/paa/skills/google-patents-search/scripts"
export PYTHONIOENCODING=utf-8

# 0) 一次性安装依赖
pip install -r D:/aicoding/mylib/paa/skills/google-patents-search/requirements.txt
python -m playwright install chromium

# 1) 推荐：让 Chrome 带调试端口启动一次（复用真实会话，能过拦截）
#    & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222

# 2) 检索（三步漏斗的第一步：粗召回）
python "$P/gp_search.py" --query '石墨烯 眼罩 采集电极 country=CN' --cdp 9222 \
  --out hits.json --audit audit.jsonl

# 3) 取候选原文（核验腿；可批量）
python "$P/gp_fetch.py" CN103399241B US20230013787A1 --cdp 9222 \
  --out evidence/gp --save-html --audit audit.jsonl

# 4) 核验门禁：只有全部 verified 才允许写进检索报告
python "$P/gp_verify.py" --citations citations.json --docs evidence/gp \
  --cutoff 2026-09-25 --strict-locator --out verify.json
echo "exit=$?"     # 0=全部通过；1=有未通过项（应阻断落稿）

# 5) MCP 浏览器路线（人工在场时）
python "$P/gp_search.py" --query 'CPC=A61B5/00 (脑电 OR EEG) 眼罩' --print-url
#    → 浏览器打开该 URL，然后 browser_run_code_unsafe filename=$P/gp_parse_current_search.js
```

## 输出契约（与仓库内 `cnipa_epub_search.py` 一致，便于 Agent 解析）

- **stdout 仅一行**：`GP_HITS_JSON:` / `GP_DOC_JSON:` / `GP_VERIFY_JSON:` + JSON（UTF-8，可含中文）；
- **stderr 只写诊断**：`GP_NOTE:` / `GP_HINT:` / `GP_BLOCKED:`（ASCII 前缀，减轻 PowerShell 把中文 stderr 当错误流）；
- **退出码**：检索 `0` 有命中 / `3` 被反爬 / `4` 无命中 / `2` 参数 / `5` 运行时；
  取件 `0` 有原文 / `3` 被反爬 / `4` 只有元数据 / `2` / `5`；
  **核验 `0` 全部通过 / `1` 有未通过项（供流水线阻断）/ `2` 输入错误**。

## 工作流（融合 incoPat skill 的三步漏斗 + 本仓证据门禁）

1. **粗召回**：写 3–6 组不同角度的检索式（主题词、手段词、效果词、分类号、申请人），逐组 `gp_search.py`；
   每组结果落盘并追加审计；结果项一律标 `snippet-degraded`。
2. **并集去重**：以 `pub_number` 为主键合并候选池——**这一步只产生候选，不产生结论**。
3. **精读取原文**：对 top 5–8 件执行 `gp_fetch.py`，得到 `original-text` 级别的权利要求与说明书；
   可选把 `<PN>.md` 交给 `patent-disclosure-skill/tools/patent_reader/extract_patent_text.py`
   进一步拆成 claim_tree / raw_sections，用于逐特征比对表。
4. **核验与分类**：对每条拟引用写 `{pn, role, quote, locator}`，跑 `gp_verify.py`；
   只有 `verified` 的条目可以进入报告，并按 `references/verification_protocol.md` 判 X/Y/A。
5. **落稿**：按 `templates/01_现有技术检索报告_template.md` 出报告，附限制声明与审计文件路径。

## 常见坑

- **别在无头模式下反复重试**：一次 `GP_BLOCKED` 就应切路线（A/B），反复重试会加重拦截；
- **0 命中 ≠ 没有现有技术**：先按 `references/query_syntax.md` 放宽检索式，再考虑换轴复检索；
- **摘要片段不能当证据**：`gp_verify.py` 会直接拒绝 `snippet-degraded` 条目，这是设计如此；
- **公开号规范化**：`US:20230013787:A1` 与 `us20230013787a1` 都会规范为 `US20230013787A1`；
- **中文全文**：`country=CN` 走 `/zh` 路径；个别号只有 A 文献没有 B 文献，需试同族或换源。

## 与 incoPat 的分工

| 维度 | incoPat（本仓首选） | 本 skill |
| --- | --- | --- |
| 凭证 | 需要账号（测试账号授权 2026-08-31 已到期） | 无需 key |
| 语义检索 / 法律状态 / 价值度 | 有 | 无（本 skill 不抓法律状态） |
| 定位 | 法定检索、范围与法律状态 | 免费候选发现 + **原文核验** + 第二轮独立复检索 |

两者都可用时：incoPat 定范围，本 skill 做第二轴复检索与逐字核验，并按公开号取并集。

## 边界（必须如实写进报告）

Google Patents **不是法定检索**；数据有覆盖缺口与延迟；本 skill **不判断**抵触申请、
不做法律状态结论、不代替代理师的检索报告。所有"未发现"只能表述为"本轮检索未发现"。
