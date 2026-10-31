# Skill-RSI — mylib 评审/写作 skill 进化框架

## 建议（一句话）

用 **冻结评价器 + 单表面突变 + HarnessBank 式门控 + gene bank**，专门提高 mylib 里已有的评审与写作 skill；不要上 DGM 式开放自改，也不要让模型给自己打合入分。

## 为什么是这个，而不是别的 RSI

| 选项 | 结论 |
|---|---|
| HarnessBank + SPRA + Skill 合同 | **主线**：贴合 mylib、可贴合 C-MARS `g7` |
| RSIHub 风格工程壳 | 本目录实现其「冻结评价 / 声明可变面 / 谱系」子集 |
| DGM / RQGM | 不采用：会碰评价器与法律/指南内核 |
| 再导入几十个上游 peer-review | 不采用：稀释一等公民宿主 |

## 目录

```text
skills/skill-rsi/
├─ SKILL.md                 # 代理入口
├─ README.md
├─ agents/openai.yaml
├─ config/
│  ├─ defaults.json
│  └─ catalog.yaml          # 一等公民可进化目标
├─ schemas/
│  ├─ candidate.schema.json
│  └─ constitution.schema.json
├─ references/PROTOCOL.md
├─ templates/candidate_card.md
├─ gene_bank/               # 本框架归档的 admit/reject 卡
└─ scripts/skillrsi.py      # init / targets / propose / gate / admit / reject / status
```

工作区（`init` 后写在 `--root` 下）：

```text
.skillrsi/
├─ constitution.json        # 人维护：保护面与不变量
├─ archive.jsonl            # 只追加
├─ candidates/<id>.json
└─ wiki/README.md
```

## 门控顺序（代码，不是模型）

1. **validity** — 候选 schema、单表面、目标在 catalog  
2. **frozen_intact** — 未声明改动保护路径  
3. **activation** — beacon 非空且有 notes/evidence 路径或 metrics  
4. **domain_floors** — 若提供 metrics，各域外层不低于父代地板  
5. **reportable_discipline** — `reportable: true` 必须 `human_unlock: true`

全部通过才允许 `admit`。

## 与论文/申请书/专利

- 论文：默认挂 `paper_harness` / `Paper_CCF` 证据校准；合成分不可报告。  
- 申请书：外层必须能调用 `proposal-writing/scripts/validate_review_basis.py`。  
- 专利：锚点/门禁合同冻结；AHP 不是授权率。
