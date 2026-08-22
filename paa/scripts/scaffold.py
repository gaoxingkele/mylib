# -*- coding: utf-8 -*-
"""PAA scaffold: create an empty Patent Application Artifact directory structure.
Usage:
    python scaffold.py <paa-dir> [--case-id P05-1] [--case-name "..."]

Reads the four-layer structure from README.md and creates empty files with frontmatter
placeholders. Validation gates are NOT run here — use validate.py for that.
"""
import argparse
import os
import sys
from pathlib import Path

DEFAULT_CASE = "P00-0"
DEFAULT_NAME = "新案件"

LAYER_DIRS = [
    "logic/solution",
    "application",
    "trace",
    "evidence/prior_art_search",
    "evidence/prior_art_claims",
    "evidence/scoring",
    "evidence/design_around",
]

# Each file: path → placeholder content
FILES = {
    "MANIFEST.md": """# MANIFEST — <case-name>

> 案件编号 <case-id> · <case-name>

## Gate Status

| Gate | Status | Evidence |
|---|---|---|
| 1. 客体适格 | PENDING | logic/subject_matter.md |
| 2. 新颖性/创造性证据绑定 | PENDING | logic/prior_art.md |
| 3. 充分公开 | PENDING | application/specification.md |
| 4. 禁编造对比文件 | PENDING | evidence/prior_art_search/ |

## Layer Index

- `logic/` — 认知层（发明要素、客体、独权拆解、创造性点、对比文件、方案）
- `application/` — 工件层（权利要求、说明书、附图、摘要）
- `trace/exploration_tree.yaml` — 探索图（权利要求改版史 + 绕行决策）
- `evidence/` — 证据（真实查新 + 对比文件claim全文 + 评分 + 设计绕行）

## Gap Report

PENDING — filled by validate.py output.
""",

    "logic/invention.md": """# 发明要素（认知层）

技术问题（待补）：
- T1.

技术手段（待补）：
- S1.

技术效果（待补）：
- E1.

→ application/claims.md
→ application/specification.md §具体实施方式
""",

    "logic/subject_matter.md": """#  客体适格性分析（认知层）

- [ ] Article 25 检查：是否有智力活动规则/商业方法？→ 风险等级
- [ ] Article 2.2 检查：是否有非技术领域？
- [ ] 技术特征 vs 业务规则 占比估计
- [  ] 绑定 → gates-checklist.md Gate 1
""",

    "logic/claims_analysis.md": """#  权利要求拆解（认知层）

## C01: 独立权利要求 1（待补）

- 名称（待补）

### 前序（preamble）
（待补）verbatim from application/claims.md

### 特征部分（characterizing portion）
（待补）verbatim from application/claims.md

### 区别特征
- D01: （待补）描述 → embodiment ref → prior_art ref → score ref
- D02: ...
""",

    "logic/inventive_concepts.md": """#  创造性点（认知层）

### C01: 概念1（待补）

- Statement: （待补）
- Status: CONFIRMED | UNSUPPORTED | NEEDS-EVIDENCE
- Proof: → application/specification.md §embodiment_X
        → logic/prior_art.md §PA-YY
        → evidence/scoring/scoring.json → I_value
- 非显而易见性论证（for 三步法预答辩）
""",

    "logic/prior_art.md": """#  对比文件（认知层）

## D01: （待补）closest prior art

- pn: <real patent number>
- applicant / ad / pd: <real fields>
- relationship: conflicts | contrasts | background
- contested_features: [D-01, D-02]
- preamble 与本案的共有特征
- 区别特征：详见 claims_analysis.md
- Source: → evidence/prior_art_search/<pn>.json
          → evidence/prior_art_claims/<pn>.md
""",

    "logic/related_work.md": """#  相关工作（认知层）

非冲突文献（学术、技术标准等），保持精简。
""",

    "logic/solution/constraints.md": """#  撰写策略（认知层）

## 限制与假设
- (待补)

## 撰写策略
- (待补)

## 机制级绕行决策
- (待补，参考 README § "Four patent-specific gates" 和 exploration-tree-spec.md § "Worked example")
""",

    "application/claims.md": """#  权利要求书（工件层）

## 独立权利要求

### 1. （待补）一种…的方法，包括：...；
   其特征在于，...。

## 从属权利要求

### 2-9. （待补）
""",

    "application/specification.md": """#  说明书（工件层）

## 技术领域
（待补）

## 背景技术
现有技术方案及其不足，引对比文件 from logic/prior_art.md（必须真实 pn）。

## 发明内容
三步法预答辩逻辑（区别特征→实际解决的技术问题→非显而易见性→有益效果）

## 附图说明
（待补，引 application/drawings.md）

## 具体实施方式
### 实施例一
（待补，含数值实例）

### 实施例二
（待补）
""",

    "application/drawings.md": """#  附图清单与描述（工件层）

| 图号 | 图名 | 对应实施例 | 摘要附图 |
|---|---|---|---|

## 附图描述（Mermaid）
（每幅图 Mermaid 描述，统一附图标号体系如 100/200 系）
""",

    "application/abstract.md": """#  说明书摘要（工件层）

（待补，≤300字；含技术领域、技术问题、方案要点、用途/效果；指定摘要附图）
""",

    "trace/exploration_tree.yaml": """# PAA Exploration Graph
artifact: <case-id>
schema_version: "1.0"
root_questions:
  - id: R01
    text: <central question>
    support_level: inferred
    source_ref: <file or §>

nodes: []
edges: []

# 注: claim-version / prior-art / design-around / dead-end / oa-response 节点类型
# 详见 references/exploration-tree-spec.md
""",

    "evidence/README.md": """#  Evidence Index

## 真实查新记录
（每个 pn 一份 evidence/prior_art_search/<pn>.json）

## 对比文件权利要求全文
（每个 pn 一份 evidence/prior_art_claims/<pn>.md + 可选 .png 截图）

## 评分数据
evidence/scoring/scoring.json

## 设计绕行记录
evidence/design_around/round_N_*.md
""",
}


def main():
    ap = argparse.ArgumentParser(description="Scaffold an empty PAA directory")
    ap.add_argument("dir", help="target PAA directory (will be created if missing)")
    ap.add_argument("--case-id", default=DEFAULT_CASE, help="case ID, e.g. P05-1")
    ap.add_argument("--case-name", default=DEFAULT_NAME, help="case name")
    args = ap.parse_args()

    paa_dir = Path(args.dir)
    paa_dir.mkdir(parents=True, exist_ok=True)

    # Layer directories
    for d in LAYER_DIRS:
        (paa_dir / d).mkdir(parents=True, exist_ok=True)

    # Files with placeholders (substitute case-id/case-name)
    for path, content in FILES.items():
        content = content.replace("<case-id>", args.case_id).replace("<case-name>", args.case_name)
        out = paa_dir / path
        out.write_text(content, encoding="utf-8")

    # Summary
    print(f"PAA scaffolded at: {paa_dir}")
    print(f"  Case: {args.case_id} - {args.case_name}")
    print(f"  Files: {len(FILES)}  Dirs: {len(LAYER_DIRS)}")
    print()
    print("Next steps:")
    print("  1. Edit logic/invention.md with your 技术问题/手段/效果")
    print("  2. Run incopat-search skill to populate evidence/prior_art_search/")
    print("  3. Edit application/* with your draft output")
    print("  4. Run python " + str(Path(__file__).parent / "validate.py") + " " + str(paa_dir) + " to run gates")


if __name__ == "__main__":
    main()