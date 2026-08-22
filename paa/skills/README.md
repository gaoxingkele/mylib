# Patent Skills (PAA Building Blocks)

PAA 的工件层 (application/) 与验证管线 (`scripts/validate.py`) 由以下四个 skill 协同驱动。它们
是 PAA 在 `~/.claude/skills/` / 项目级 `.claude/skills/` 中的**真实执行器**，本目录是它们的
**全局副本**（位于 `mylib/paa/skills/`），供任何 AI 工具（Claude Code / Codex / Kimi / Grok / Pi
/ Generic Agent）通过相对路径调用，避免环境差异。

## 四个 skill 一览

| Skill | 角色 | 在 PAA 中的位置 |
|---|---|---|
| **incopat-search** | 真实专利 API 查新（incoPat 开放平台，厦大平潭研究院测试账号） | feeds `evidence/prior_art_search/` 与 `evidence/prior_art_claims/` |
| **patent-grant-scorer** | AHP + SEM 四专家群决策的授权率预测 | feeds `evidence/scoring/scoring.json` |
| **cnipa-drafting-workflow** | CNIPA 申请文件起草与审查工作流（22 条三步法 / 26 条 / OA 预案） | produces `application/` 工件层 |
| **patent-disclosure-skill** | 从项目文档挖掘专利点并生成可交付技术交底书 | produces `logic/invention.md` 输入 |

## 调用模式（任一 AI 工具通用）

```
# 1. 载入 PAA 主指令
load: ./README.md              # 工具无关核心

# 2. 按需载入 skill（指向本地或全局路径）
load: ./skills/incopat-search/SKILL.md
load: ./skills/patent-grant-scorer/SKILL.md
load: ./skills/cnipa-drafting-workflow/SKILL.md
load: ./skills/patent-disclosure-skill/SKILL.md

# 3. 用工具自身的执行器（Python / Bash / shell）跑脚本
python ./scripts/scaffold.py <case-dir> --case-id P05-1 --case-name "..."
python ./scripts/validate.py <case-dir>      # 四门禁 + Seal 1
```

## 凭证处理（注意）

`incopat-search/scripts/credentials.json` 已在原项目 `.gitignore` 中——**没有随 skill 一起拷过来**（避免泄露真实 client_secret）。真实账号使用时只需：

```
# 把测试账号（或正式账号）凭证写到
echo '{"client_id":"...","client_secret":"...","username":"...","password":"..."}' \
  > /d/aicoding/mylib/paa/skills/incopat-search/scripts/credentials.json
```

或用环境变量 `INCOPAT_CLIENT_ID` / `INCOPAT_CLIENT_SECRET` / `INCOPAT_USERNAME` / `INCOPAT_PASSWORD` 覆盖。

## 从 PAA 顶层视角看

PAA 把分散的 10 个 agent + 4 个 skill + 1 个评分体系整合为统一四层架构（参见 `../README.md`）。
本目录中的 skill 是 PAA 的"工具层"——它们各司其职，PAA 在它们之上加了**探索图 + 四门禁 + 跨层绑定**，把
"散件"变成"可验证的整体"。

迁移历史（参见 wiki）：
- 2026-08-21：评分体系落地（patent-grant-scorer）
- 2026-08-22：incoPat API 接入 + 蒸馏速查卡 + AHP/SEM 群决策 + 设计绕行方法论
- 2026-08-22：PAA 上线（论文 ARA → 基金 GPA → 专利 PAA 的领域可移植性第三次证实）