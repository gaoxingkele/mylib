#!/usr/bin/env python3
"""
export_paa.py —— 把 PatentARA 导出为 PAA 目录格式。

生成：
  MANIFEST.md
  logic/invention.md
  logic/subject_matter.md
  logic/claims_analysis.md
  logic/inventive_concepts.md
  logic/prior_art.md
  application/claims.md
  application/specification.md
  application/drawings.md
  application/abstract.md
  trace/exploration_tree.yaml
  evidence/prior_art_search/
  evidence/prior_art_claims/
  evidence/scoring/
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .model import PatentARA


class PAAExporter:
    """把 PatentARA 导出为 PAA 目录结构。"""

    def __init__(self, ara: PatentARA, output_dir: str | Path):
        self.ara = ara
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, gate_report: Optional[Dict] = None, scoring_report: Optional[Dict] = None) -> Path:
        """导出完整 PAA 目录。"""
        self._write_manifest(gate_report, scoring_report)
        self._write_logic()
        self._write_application()
        self._write_trace()
        self._write_evidence(scoring_report)
        return self.output_dir

    def _write_manifest(self, gate_report: Optional[Dict], scoring_report: Optional[Dict]):
        """写 MANIFEST.md。"""
        md = self.ara.metadata
        lines = [
            "---",
            f"title: \"{md.title}\"",
            f"application_number: \"{md.application_number}\"",
            f"jurisdiction: {md.jurisdiction}",
            f"language: {md.language}",
            f"schema_version: {self.ara.schema_version}",
            f"export_date: \"{self._today()}\"",
            "---",
            "",
            f"# {md.title}",
            "",
            "## Layer Index",
            "",
            "- `logic/` — 认知层：发明点、客体适格、权利要求分析、对比文件",
            "- `application/` — 工件层：权利要求书、说明书、附图、摘要",
            "- `trace/` — 探索图：权利要求改版史、设计绕行、被否方向",
            "- `evidence/` — 证据层：对比文件检索、权利要求原文、评分数据",
            "",
            "## Gates Status",
            "",
        ]

        if gate_report:
            lines.append(f"Overall: **{gate_report.get('summary', 'UNKNOWN')}**")
            lines.append("")
            for g in gate_report.get("gates", []):
                status = "✅ PASS" if g["passed"] else "❌ FAIL"
                lines.append(f"- {g['gate']}: {status}")
                if g["findings"]:
                    for f in g["findings"][:3]:
                        lines.append(f"  - {f}")
        else:
            lines.append("Not evaluated")

        if scoring_report:
            lines.extend([
                "",
                "## Scoring Summary",
                "",
                f"- Overall Score: {scoring_report.get('scores', {}).get('overall', 'N/A')}",
                f"- Grade: {scoring_report.get('grade', 'N/A')}",
                f"- Recommendation: {scoring_report.get('recommendation', 'N/A')}",
            ])

        (self.output_dir / "MANIFEST.md").write_text("\n".join(lines), encoding="utf-8")

    def _write_logic(self):
        """写 logic/ 目录。"""
        logic_dir = self.output_dir / "logic"
        logic_dir.mkdir(exist_ok=True)

        # invention.md
        md = self.ara.metadata
        invention_lines = [
            f"# 发明内容分析",
            "",
            f"## 技术领域",
            f"{md.title}",
            "",
            "## 技术问题",
        ]
        for p in self.ara.technical_problems:
            invention_lines.append(f"- {p.statement}")
        if not self.ara.technical_problems:
            invention_lines.append("- （待提取）")
        invention_lines.extend([
            "",
            "## 技术手段",
            "见 `claims_analysis.md` 中的要素分解。",
            "",
            "## 技术效果",
            "（待分析）",
        ])
        (logic_dir / "invention.md").write_text("\n".join(invention_lines), encoding="utf-8")

        # subject_matter.md
        sm = self.ara.subject_matter
        sm_lines = [
            "# 客体适格分析 (Article 25 / 2.2)",
            "",
            f"**判定结果**: {'适格' if sm.get('eligible') else '不适格' if sm.get('eligible') is False else '未判定'}",
            "",
            f"**理由**: {sm.get('rationale', '（未提供）')}",
            "",
            f"**分析者**: {sm.get('analyzed_by', 'agent')}",
        ]
        (logic_dir / "subject_matter.md").write_text("\n".join(sm_lines), encoding="utf-8")

        # claims_analysis.md
        claims_lines = ["# 权利要求分析", ""]
        for claim in self.ara.claims:
            claims_lines.extend([
                f"## 权利要求 {claim.number} ({claim.claim_type})",
                "",
                f"**类别**: {claim.category}",
                f"**两段式**: {'是' if claim.two_part_form else '否'}",
                "",
                "### 要素分解",
                "",
            ])
            for elem in claim.elements:
                claims_lines.append(f"- **{elem.id}** ({elem.element_type}): {elem.text[:100]}")
            claims_lines.append("")
        (logic_dir / "claims_analysis.md").write_text("\n".join(claims_lines), encoding="utf-8")

        # inventive_concepts.md
        ic_lines = ["# 创造性点分析", ""]
        for ic in self.ara.inventive_concepts:
            ic_lines.extend([
                f"## {ic.id}: {ic.name}",
                "",
                f"**描述**: {ic.description}",
                "",
                f"**关联要素**: {', '.join(ic.core_element_ids) if ic.core_element_ids else '（未绑定）'}",
                "",
            ])
        if not self.ara.inventive_concepts:
            ic_lines.append("（待提取）")
        (logic_dir / "inventive_concepts.md").write_text("\n".join(ic_lines), encoding="utf-8")

        # prior_art.md
        pa_lines = ["# 对比文件分析", ""]
        for cit in self.ara.citations:
            pa_lines.extend([
                f"## {cit.id}: {cit.patent_number}",
                "",
                f"**标题**: {cit.title}",
                f"**关系**: {cit.relationship}",
                f"**相关度**: {cit.relevance}",
                f"**验证状态**: {'已验证' if cit.verified else '未验证'}",
                "",
                f"**绑定要素**: {', '.join(cit.mapped_element_ids) if cit.mapped_element_ids else '（未绑定）'}",
                "",
            ])
        (logic_dir / "prior_art.md").write_text("\n".join(pa_lines), encoding="utf-8")

    def _write_application(self):
        """写 application/ 目录。"""
        app_dir = self.output_dir / "application"
        app_dir.mkdir(exist_ok=True)

        # claims.md
        claims_lines = ["# 权利要求书", ""]
        for claim in self.ara.claims:
            claims_lines.append(f"{claim.number}. {claim.text}")
            claims_lines.append("")
        (app_dir / "claims.md").write_text("\n".join(claims_lines), encoding="utf-8")

        # specification.md
        spec_lines = ["# 说明书", ""]
        for section in self.ara.spec_sections:
            spec_lines.extend([
                f"## {section.title or section.kind}",
                "",
                section.text[:2000],  # 限制长度
                "",
            ])
        (app_dir / "specification.md").write_text("\n".join(spec_lines), encoding="utf-8")

        # drawings.md
        draw_lines = ["# 附图说明", ""]
        for fig in self.ara.figures:
            draw_lines.append(f"- 图{fig.number}: {fig.caption}")
        if not self.ara.figures:
            draw_lines.append("（无附图）")
        (app_dir / "drawings.md").write_text("\n".join(draw_lines), encoding="utf-8")

        # abstract.md
        abstract = next((s for s in self.ara.spec_sections if s.kind == "abstract"), None)
        abstract_text = abstract.text[:500] if abstract else "（无摘要）"
        (app_dir / "abstract.md").write_text(f"# 说明书摘要\n\n{abstract_text}", encoding="utf-8")

    def _write_trace(self):
        """写 trace/ 目录。"""
        trace_dir = self.output_dir / "trace"
        trace_dir.mkdir(exist_ok=True)

        # exploration_tree.yaml (简化版，用 JSON 格式)
        tree = {
            "claim_versions": [
                {
                    "id": v.id,
                    "claim_number": v.claim_number,
                    "version": v.version,
                    "change_rationale": v.change_rationale,
                    "supersedes": v.supersedes,
                    "provenance": v.provenance,
                }
                for v in self.ara.claim_versions
            ],
            "design_arounds": [
                {
                    "id": d.id,
                    "target_feature": d.target_feature,
                    "mechanism_substitution": d.mechanism_substitution,
                    "prior_art_id": d.prior_art_id,
                    "provenance": d.provenance,
                }
                for d in self.ara.design_arounds
            ],
            "dead_ends": [
                {
                    "id": d.id,
                    "direction": d.direction,
                    "reason": d.reason,
                    "provenance": d.provenance,
                }
                for d in self.ara.dead_ends
            ],
            "oa_responses": [
                {
                    "id": o.id,
                    "office_action_ref": o.office_action_ref,
                    "opinion_summary": o.opinion_summary,
                    "response_strategy": o.response_strategy,
                }
                for o in self.ara.oa_responses
            ],
        }

        # 尝试用 YAML，失败则用 JSON
        try:
            import yaml
            content = yaml.safe_dump(tree, allow_unicode=True, sort_keys=False)
            ext = "yaml"
        except ImportError:
            content = json.dumps(tree, ensure_ascii=False, indent=2)
            ext = "json"

        (trace_dir / f"exploration_tree.{ext}").write_text(content, encoding="utf-8")

    def _write_evidence(self, scoring_report: Optional[Dict]):
        """写 evidence/ 目录。"""
        ev_dir = self.output_dir / "evidence"
        ev_dir.mkdir(exist_ok=True)

        # prior_art_search/
        search_dir = ev_dir / "prior_art_search"
        search_dir.mkdir(exist_ok=True)
        for cit in self.ara.citations:
            search_data = {
                "patent_number": cit.patent_number,
                "title": cit.title,
                "search_receipt": cit.search_receipt,
                "relationship": cit.relationship,
                "relevance": cit.relevance,
                "verified": cit.verified,
                "mapped_element_ids": cit.mapped_element_ids,
            }
            (search_dir / f"{cit.patent_number}.json").write_text(
                json.dumps(search_data, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        # prior_art_claims/
        claims_dir = ev_dir / "prior_art_claims"
        claims_dir.mkdir(exist_ok=True)
        for cit in self.ara.citations:
            if cit.claim_text_excerpt:
                (claims_dir / f"{cit.patent_number}.md").write_text(
                    f"# {cit.patent_number} 权利要求摘录\n\n{cit.claim_text_excerpt}",
                    encoding="utf-8"
                )

        # scoring/
        if scoring_report:
            score_dir = ev_dir / "scoring"
            score_dir.mkdir(exist_ok=True)
            (score_dir / "scoring.json").write_text(
                json.dumps(scoring_report, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    def _today(self) -> str:
        from datetime import date
        return date.today().isoformat()


def export_paa(ara: PatentARA, output_dir: str | Path,
               gate_report: Optional[Dict] = None,
               scoring_report: Optional[Dict] = None) -> Path:
    """便捷函数：导出 PAA 目录。"""
    exporter = PAAExporter(ara, output_dir)
    return exporter.export(gate_report, scoring_report)
