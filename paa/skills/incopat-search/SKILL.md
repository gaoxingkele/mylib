---
name: incopat-search
description: >
  incoPat 开放数据平台专利检索 API（真实数据源，厦门大学平潭研究院测试账号）。
  凡涉及"专利查新 / 现有技术检索 / prior art / 新颖性检索 / 找最接近对比文件 /
  查权利要求原文 / 查说明书原文 / 查法律状态 / 专利价值评估 / 语义检索相似专利"，
  一律优先调用本 skill 的脚本获取真实专利数据，而不是仅靠 WebSearch 或凭记忆。
  prior-art-researcher / patentability-examiner 流程中的检索步骤也应通过本 skill 执行。
  TRIGGERS: 查新, 检索专利, 现有技术, prior art, 对比文件, X文件, 新颖性检索,
  incoPat, incopat, 专利检索, 相似专利, 法律状态, 权利要求原文, 合享价值度
---

# incoPat 专利检索 Skill

## 何时使用

1. `/patent` 流程第 2 步（prior-art-researcher 现有技术检索）——**必须**先用本 skill 拿真实数据，再综合 WebSearch 结果；
2. 用户要求查新、找对比文件、评估新颖性/创造性风险；
3. 需要某件专利（按公开号）的权利要求书、说明书、法律状态、价值评分原文；
4. 用一段技术方案文字找语义相似专利（比关键词检索召回更好，适合交底书查新）。

本 skill 解决的核心合规问题：**项目严禁编造专利号**——所有写入 `01_现有技术检索报告.md` 的对比文件号必须来自本 API 的真实返回。

## 用法（Bash 调用，Python = D:\Python314\python.exe）

脚本：`.claude/skills/incopat-search/scripts/incopat_api.py`（token 自动获取/缓存/刷新，无需手动认证；凭证读自同目录 `credentials.json`——已 gitignore 不入库，模板见 `credentials.example.json`，也可用 INCOPAT_* 环境变量覆盖）

```bash
cd "D:\aicoding\zhuanlishenqing" && export PYTHONIOENCODING=utf-8

# ① 检索式检索（返回 pn/标题/摘要/申请人/发明人/代理机构/申请日/公开日）
D:/Python314/python.exe .claude/skills/incopat-search/scripts/incopat_api.py \
  search "TI-CN=(变压器 AND 故障诊断) AND PNC=CN AND PD=[20200101 TO 20261231]" --rows 10 --order "PD DESC"

# ② 语义检索：整段技术方案文字 → 相似专利公开号+相似度分（查新首选，中文查中国专利，英文查国外）
D:/Python314/python.exe .claude/skills/incopat-search/scripts/incopat_api.py \
  semantic "一种基于知识图谱和检索增强生成的变压器油色谱故障诊断方法……" --rows 10

# ③ 按公开号取详情
D:/Python314/python.exe .claude/skills/incopat-search/scripts/incopat_api.py claim  CN103399241B   # 权利要求全文
D:/Python314/python.exe .claude/skills/incopat-search/scripts/incopat_api.py spec   CN103399241B   # 说明书全文
D:/Python314/python.exe .claude/skills/incopat-search/scripts/incopat_api.py legal  CN103399241B   # 法律状态 2.0
D:/Python314/python.exe .claude/skills/incopat-search/scripts/incopat_api.py value  CN103399241B   # 合享价值度评分
D:/Python314/python.exe .claude/skills/incopat-search/scripts/incopat_api.py assign CN103399241B   # 转让
D:/Python314/python.exe .claude/skills/incopat-search/scripts/incopat_api.py licence CN103399241B  # 许可
D:/Python314/python.exe .claude/skills/incopat-search/scripts/incopat_api.py reexam CN103399241B   # 复审无效决定

# ④ 批量（自动限速）
D:/Python314/python.exe .claude/skills/incopat-search/scripts/incopat_api.py batch CN116842422A CN113112164A --cmd claim
```

## 推荐查新工作流（三步漏斗）

1. **语义粗召回**：把交底书的"技术方案"段落（或独权草稿）整段丢给 `semantic --rows 20`，得到相似度排序的 pn 列表；
2. **关键词补充**：用 2~3 组不同角度的检索式跑 `search`（技术主题词 + 手段词组合），与语义结果并集去重；
3. **精读比对**：对相似度 ≥0.8 或标题高度相关的 top 5~8 件，逐件 `claim` + `spec` 拉全文，做区别特征分析，判定 X/Y/A 类；对候选 X 文件再查 `legal` 确认是否有效。

报告落稿要求：`01_现有技术检索报告.md` 中每件对比文件必须带真实 pn、标题、申请人、申请日、公开日（均来自 API 返回），语义检索的相似度分一并记录。

## 检索式语法要点（incoExp）

- 字段=（值）：`TI-CN=(豆浆机)`，`AP-OR=(九阳*)`（`*` 通配，不能放开头），`PNC=CN`，`PD=[20101012 TO 20221008]`
- 布尔：`AND` / `OR` / `NOT`；位置算符 W/N ≤20 个；不支持 `>` `<`，用 `[a TO b]` 区间代替
- 不支持大字段检索（FULL/TIABC/DES/CLAIM 等）；rows 每次 1-20；from 最大 100,000
- 检索式与 incoPat 网页版基本一致

## 测试账号权限边界（实测 2026-08-21）

- **可用接口**（token scope）：incosearch 检索、semanticsSearch 语义、claim 权利要求、spec 说明书、lgtxt2 法律状态、vlstar 价值度、assign 转让、licence 许可、reetxt 复审无效
- **不可用**：count 统计、info 单件详细著录、同族/引证接口、图形检索、PDF/附图、特征对比报告（返回 `未授权接口，拒绝访问`）→ 遇到时如实告知用户权限不足，不要重试
- **可用返回字段**：pn, an, ti-cn, ti-en, ab-cn, ap-or, in-or, agc, ad, pd（`ipc`/`lgd`/`status-lite` 无权限，切勿放进 --fields）
- 限速默认 10 请求/秒；token 2 小时有效（脚本自动缓存刷新）
- 授权截止 **2026-08-31**；测试域名 `https://apitest.incopat.com`（正式环境为 open.incopat.com，换正式账号时设环境变量 INCOPAT_BASE/INCOPAT_CLIENT_ID/INCOPAT_CLIENT_SECRET/INCOPAT_USERNAME/INCOPAT_PASSWORD 即可）

## 错误处理

- `code:500 + "未授权接口"` = 该接口不在测试账号 scope 内，换用可用接口或告知用户
- `code:500 + "该字段(X)没有权限查看"` = 从 --fields 去掉该字段重试
- `code:429` = 触发访问量限制，稍后重试
- `status:false + TOKEN 相关` = 脚本已自动重取 token；若仍失败检查授权是否过期（2026-08-31）

## 参考

- 技术手册：`references/incoPat开放数据平台接口技术手册.pdf`（96 页，含全部 20+ 接口）
- 账号信息：`references/incoPat数据接口_开通API测试账号基本信息-厦门大学平潭研究院-20260817.txt`
- 检索规则：https://www.incopat.com/help/sysdoc/principal.html
