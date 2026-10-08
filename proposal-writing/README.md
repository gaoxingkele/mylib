# 申报书模块

统一入口：[SKILL.md](SKILL.md)。按当年指南和模板选择科研基金、科技项目、教改项目或人才计划；上游 skill 在模块内部按需读取。准备当年指南、空白模板、已有基础、研究/工作构想并编号，先输出缺口、对应表和提纲，再逐节起草。已有草稿需要审查或升级时，加载 [评审与修订适配](references/review-revise.md)，形成可追溯的意见和修订台账。

| 类型 | 适配说明 | 上游原文 |
|---|---|---|
| 科研基金 | [research-fund](references/research-fund.md) | [fund-research-content-writer](skills/fund-research-content-writer/SKILL.md) |
| 科技项目 | [technology-project](references/technology-project.md) | [research-grants](skills/research-grants/SKILL.md) |
| 教改项目 | [teaching-reform](references/teaching-reform.md) | [doc-coauthoring](skills/doc-coauthoring/SKILL.md) |
| 人才计划 | [talent-program](references/talent-program.md) | [doc-coauthoring](skills/doc-coauthoring/SKILL.md) |
| 评审与修订 | [review-revise](references/review-revise.md) | [review-grant](skills/review-grant/SKILL.md)、[peer-review](skills/peer-review/SKILL.md) |

## 来源与许可

完整子目录通过 Codex skill-installer 从指定 GitHub commit 下载；未导入整套仓库、其他 skill 或代码依赖。上游文件原样保留，适配写在本模块入口与 `references/`。

| 上游仓库 | 固定 commit | 保留的来源证据 | 许可边界 |
|---|---|---|---|
| [HuiyuLi-2000/Chinese-Grant-Writer-Skills](https://github.com/HuiyuLi-2000/Chinese-Grant-Writer-Skills) | `7a92d86adeb35a6a5b6e5f25ca0a666daf0a6b2f` | [LICENSE](upstream/chinese-grant-writer/LICENSE)、[README](upstream/chinese-grant-writer/README.md) | MIT，保留版权与许可声明 |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | `92ace75ac21efe19a620434e0ca4e356081fe807` | [LICENSE.md](upstream/research-grants/LICENSE.md)、[README](upstream/research-grants/README.md) | MIT，保留版权与许可声明 |
| [anthropics/skills](https://github.com/anthropics/skills) | `683bc88e56f3e09ba94f7055977f3d3aa499f202` | [README](upstream/doc-coauthoring/README.md) | README 概述 many skills 为 Apache 2.0；此固定版本未见根目录或 doc-coauthoring 单独 LICENSE，不将概述认定为该文件的明确许可 |
| [claesbackman/AI-research-feedback](https://github.com/claesbackman/AI-research-feedback) | `d12975697b8603ec4dd6f0e922fcc1251d5355d1` | [LICENSE](upstream/review-grant/LICENSE)、[README](upstream/review-grant/README.md) | MIT，保留版权与许可声明 |

初始写作快照下载于2026-10-07，评审快照下载于2026-10-08；各目录的固定版本、下载日期、上游 Git blob SHA 和本地 SHA-256 见 [sources.json](upstream/sources.json)。

上游声称的历史成功申请书不是本模块的事实材料；K-Dense 的示例预算、海外规则及其工具论文不能自动成为国内项目依据；Anthropic 的 Claude 工具名映射到当前环境。其他技能、API 绘图和外部服务均为可选，下载本模块不等于具备这些能力。

`review-grant` 的上游原文保存在 `skills/review-grant/UPSTREAM_SKILL.md`；同目录 `SKILL.md` 是本地 Codex 适配入口，仅为通过运行时 YAML 审计并指向原文，不改写上游内容。

## 注册与使用

运行时只注册 [proposal-writing 入口](../skill-runtime/routers/proposal-writing/SKILL.md)，由 [manifest.json](../skill-runtime/manifest.json) 维护。不要将本模块整棵树链接进自动递归发现目录，也不要单独注册写作或评审叶技能，以免重复发现并绕过中文适配。

加载入口后可直接发送：

> 用申报书模块处理本项目。以所附当年指南和模板为准，先核对材料编号和缺口，再按项目类型给对应表和提纲。事实注明材料编号，缺项【待补】，不得编造。

## 更新与验证

先保留本地未提交工作，再拉取 mylib 远端最新更新；按固定版本在临时目录重新下载所选完整 skill，审阅差异，保留新版本许可与来源证据后更新来源记录和适配。不要直接从未固定的 `main` 覆盖当前文件。

在 mylib 根目录运行：

```powershell
python proposal-writing/scripts/verify_sources.py
python proposal-writing/scripts/test_revision_ledger.py
python skill-runtime/audit_skill_paths.py --source-only --json
python -X utf8 C:/Users/iamaf/.codex/skills/.system/skill-creator/scripts/quick_validate.py proposal-writing
python -X utf8 C:/Users/iamaf/.codex/skills/.system/skill-creator/scripts/quick_validate.py skill-runtime/routers/proposal-writing
git diff --cached --check -- . ":(exclude)proposal-writing/skills/**" ":(exclude)proposal-writing/upstream/**"
```

`verify_sources.py` 检查完整文件集与来源哈希；`test_revision_ledger.py` 使用合成记录验证本地修订台账规则；运行时审计检查注册数量、YAML 和路径。上游 `research-grants` 和 `peer-review` 的标准 `compatibility` 字段不被当前旧版 quick_validate 接受，因此保留原文，以运行时 YAML/路径审计和来源校验验证叶技能。

上游快照保留原有空白与 Markdown 换行，空白检查只针对本地维护内容；来源校验负责确认快照未被改写。

独立只读检查通过五类请求场景：国社科栏目适配、科技项目指标与预算缺失、教改仅有满意度、人才个人贡献与配套证据缺失，以及类别不明确的混合请求。检查覆盖路线选择、首轮产物、缺项处理和链接；不代表已运行真实申报项目，也不证明外部执行器始终遵守工具限制。

这些校验不证明任何项目已经获批、事实真实或满足全部报送条件。本地流程验证覆盖合成台账，以及实际指南约束下的修订、栏目限字和文档导出检查；私人申报材料不存入技能库。资格、经费、成果权属、数据授权和单位承诺仍须由申报主体核实，并经过同行及单位审签。
