#!/usr/bin/env python3
"""
gates.py —— PAA 四门禁（一票否决），复用 evaluator/parser 已有数据。

Gate 1: 客体适格 (Article 25 / 2.2)
Gate 2: 新颖性/创造性证据绑定 (每条区别特征必须绑定 ≥1 真实对比文件)
Gate 3: 充分公开 (Article 26.3，每条特征必须有实施例支持)
Gate 4: 禁编造对比文件 (每条引用必须有检索凭证或原文转录)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .model import PatentARA


@dataclass
class GateResult:
    gate: str            # gate1_subject_matter | gate2_evidence_binding | gate3_disclosure | gate4_no_fabrication
    passed: bool
    blocking: bool = True
    findings: list[str] = field(default_factory=list)   # 具体问题
    fix_instructions: list[str] = field(default_factory=list)


class GateKeeper:
    def __init__(self, ara: PatentARA, eval_report: Optional[dict] = None):
        self.ara = ara
        self.eval_report = eval_report or {}

    def gate1_subject_matter(self) -> GateResult:
        """客体适格门禁：Article 25 / 2.2。"""
        result = GateResult(gate="gate1_subject_matter", passed=True)
        sm = self.ara.subject_matter

        if not sm:
            result.passed = False
            result.findings.append("未注入客体适格判定 (subject_matter 为空)")
            result.fix_instructions.append("由 agent 分析发明是否属于专利保护客体，并写入 ara.subject_matter")
            return result

        eligible = sm.get("eligible")
        if eligible is None:
            result.passed = False
            result.findings.append("subject_matter.eligible 未设置")
            result.fix_instructions.append("明确判定 eligible=True/False")
        elif eligible is False:
            result.passed = False
            result.blocking = True
            result.findings.append(f"客体不适格: {sm.get('rationale', '未说明理由')}")
            result.fix_instructions.append("修改技术方案，使其属于专利保护客体（技术手段/技术效果）")

        # 启发式检查：方法类权利要求是否包含技术手段词
        tech_words = ("模块", "单元", "步骤", "处理器", "信号", "数据", "存储", "计算", "检测", "控制")
        for claim in self.ara.claims:
            if claim.category == "method":
                text = claim.text
                if not any(w in text for w in tech_words):
                    result.findings.append(f"权{claim.number}为方法权利要求但缺少明确技术手段词")
                    result.fix_instructions.append(f"检查权{claim.number}是否属于智力活动规则")

        return result

    def gate2_evidence_binding(self) -> GateResult:
        """新颖性/创造性证据绑定门禁：每条区别特征必须绑定 ≥1 真实对比文件。"""
        result = GateResult(gate="gate2_evidence_binding", passed=True)

        # 构建 element_id -> verified citations 映射
        elem_to_citations = {}
        for cit in self.ara.citations:
            if cit.verified:
                for eid in cit.mapped_element_ids:
                    elem_to_citations.setdefault(eid, []).append(cit)

        # 从 eval_report 获取区别特征
        for claim_result in self.eval_report.get("claims", []):
            claim_num = claim_result.get("number")
            distinguishing = claim_result.get("three_step", {}).get("step2_distinguishing_features", [])

            for feat in distinguishing:
                eid = feat.get("element_id")
                bound = elem_to_citations.get(eid, [])
                if not bound:
                    result.passed = False
                    result.findings.append(f"权{claim_num} 区别特征 {eid} 未绑定任何真实对比文件")
                    result.fix_instructions.append(f"为 {eid} 运行 incopat-search 检索真实对比文件并绑定")
                else:
                    unverified = [c for c in bound if not c.verified]
                    if unverified:
                        result.findings.append(f"权{claim_num} 区别特征 {eid} 绑定的对比文件未验证")
                        result.fix_instructions.append(f"验证对比文件 {unverified[0].patent_number} 的真实性")

        return result

    def gate3_disclosure(self) -> GateResult:
        """充分公开门禁：Article 26.3，每条特征必须有实施例支持。"""
        result = GateResult(gate="gate3_disclosure", passed=True)

        for claim in self.ara.claims:
            for elem in claim.elements:
                # 检查 support_section_ids 或 supported_by 边
                has_support = bool(elem.support_section_ids)
                if not has_support:
                    support_edges = [e for e in self.ara.edges
                                    if e.relation == "supported_by" and e.source == elem.id]
                    has_support = bool(support_edges)

                if not has_support:
                    result.passed = False
                    result.findings.append(f"权{claim.number} 要素 {elem.id} 缺少实施例支持")
                    result.fix_instructions.append(f"在说明书具体实施方式中添加支持 {elem.id} 的段落")
                else:
                    # 检查支持强度
                    weight = self.ara.support_weight(elem.id)
                    if weight is not None and weight < 0.5:
                        result.findings.append(f"权{claim.number} 要素 {elem.id} 支持强度不足 ({weight:.2f})")
                        result.fix_instructions.append(f"增强说明书对 {elem.id} 的描述")

        return result

    def gate4_no_fabrication(self) -> GateResult:
        """禁编造对比文件门禁：每条引用必须有检索凭证或原文转录。"""
        result = GateResult(gate="gate4_no_fabrication", passed=True)

        for cit in self.ara.citations:
            has_receipt = bool(cit.search_receipt or cit.evidence_uri)
            has_excerpt = bool(cit.claim_text_excerpt)

            if not has_receipt and not has_excerpt:
                result.passed = False
                result.findings.append(f"对比文件 {cit.patent_number} 缺少检索凭证和原文转录")
                result.fix_instructions.append(f"为 {cit.patent_number} 补充 incopat 检索凭证或权利要求原文")
            elif not cit.verified:
                result.findings.append(f"对比文件 {cit.patent_number} 未标记为已验证")
                result.fix_instructions.append(f"确认 {cit.patent_number} 来自真实检索结果")

        return result

    def run_all(self) -> dict[str, Any]:
        """运行全部四门禁。"""
        gates = [
            self.gate1_subject_matter(),
            self.gate2_evidence_binding(),
            self.gate3_disclosure(),
            self.gate4_no_fabrication(),
        ]

        blocking_failures = [g for g in gates if not g.passed and g.blocking]
        all_passed = all(g.passed for g in gates)

        return {
            "passed": all_passed,
            "gates": [
                {
                    "gate": g.gate,
                    "passed": g.passed,
                    "blocking": g.blocking,
                    "findings": g.findings,
                    "fix_instructions": g.fix_instructions,
                }
                for g in gates
            ],
            "blocking_failures": len(blocking_failures),
            "summary": "PASS" if all_passed else f"FAIL ({len(blocking_failures)} blocking)",
        }
