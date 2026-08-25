# claude-user-skills — 用户级 Claude skills 备份

Source: `C:/Users/iamaf/.claude/skills/`（全局，跨项目生效）。同步于 2026-08-25。

| Skill | 用途 |
|---|---|
| `ARA_DeepReport` | 深度研究报告引擎（多源检索→对抗核验→结构化合成，版本升级不遗忘） |
| `paper_compiler` | 任意研究输入 → ARA（机器可执行知识包） |
| `paper_research-manager` | 研究过程端到端记录器（渐进结晶） |
| `paper_rigor-reviewer` | ARA 语义认识论审查（Seal Level 2） |
| `proposal-compiler` | 科技部国际合作项目申报书 → GPA |
| `proposal-manager` | 申请书起草过程记录器（渐进结晶） |
| `proposal-reviewer` | GPA 模拟函评（八维 + 两硬门槛） |
| `anysearch` | 实时多源搜索引擎 |
| `codex-review-loop` | Codex 结对审查循环 |

## 安全约定

- `anysearch/.env`（真实凭据）**有意排除**，仅保留 `.env.example`
- 无其他内嵌密钥（2026-08-25 扫描确认）
- 同步命令：复制后删除 `anysearch/.env` 与所有 `__pycache__/`
