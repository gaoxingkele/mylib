# Skill-RSI Protocol

## 1. Method stack

1. **SPRA**（C-MARS）：规范保持；Evaluator / ReviewSpec / 指南法律门禁不自改。  
2. **HarnessBank**：LLM 诊断与提案；代码做 validity → activation → paired/floors → held-out。  
3. **Skill 合同思想**（Skill-V / SkillSpec）：skill 变更要可证伪 beacon + 非回归。  
4. **metaRSI**：项目证据等级与影子规则；本框架管 skill 发布卡，不替代 `.metarsi/`。

## 2. Surfaces

| Surface | 可改什么 | 例子 |
|---|---|---|
| prompt | 角色说明、检查清单措辞 | pre-submission 禁用词表细化 |
| skill | 触发条件、步骤、输出合同 | review-grant 增加 basis 校验步骤 |
| harness | 路由、重试、质询触发、工具顺序 | paper_harness stage 门顺序 |
| context | 保留/压缩哪些状态 | 分歧边、少数 veto、开放 issue |

每次候选 **恰好一个** surface，且 `pathology.where` 必须与之兼容（knowledge/runtime/config 记在 pathology，但合入时仍映射到上表四类之一）。

## 3. Frozen kernel（默认写进 constitution）

- `proposal-writing/scripts/validate_review_basis.py`  
- 「禁止资助概率 / 官方分」类不变量  
- `paa` 权利要求锚点与硬门禁  
- Paper_CCF / ReviewSpec 构念与数字审计脚本  
- `.skillrsi/constitution.json` 自身  

## 4. Admit rule

`admit` 仅当：

1. `gate` 全绿；  
2. `--by` 提供人工标识（默认要求）；  
3. 若 `reportable: true`，必须事先 `human_unlock: true`；  
4. 写入 `gene_bank/<id>.md` 与 `archive.jsonl`。

拒绝时同样落盘 negative 卡，供后续禁止重组合。

## 5. Domain floors

若候选提供 `metrics.candidate_scores` 与 `metrics.parent_floors`：

- 每个域分数必须 `candidate >= parent_floor - 1e-9`  
- 缺域则跳过该域  
- 未提供 metrics 时允许结构门通过，但卡片必须标明 **metrics absent**

## 6. Non-goals

- 不自动改 skill 文件正文（代理或人改完后用本工具归档）。  
- 不平均 paper/proposal/patent 分数。  
- 不把 C-MARS 合成分写成可报告主结果。
