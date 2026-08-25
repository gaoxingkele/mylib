#!/usr/bin/env python3
"""test_patent_ara.py —— 可用 pytest 运行，也可直接 python 执行。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from patent_ara import (ClaimDecomposer, ElementVerdict, Evaluator, GateKeeper,
                        PatentParser)

CN_CLAIMS = """
1. 一种数据处理方法，其特征在于，包括以下步骤：
S1，获取目标设备的运行参数；
S2，根据所述运行参数构建状态特征向量；
S3，将所述状态特征向量输入预测模型，得到预测结果。
2. 根据权利要求1所述的数据处理方法，其特征在于，所述构建状态特征向量包括：对所述运行参数进行归一化处理。
3. 一种数据处理装置，其特征在于，包括：
获取模块，用于获取目标设备的运行参数；
构建模块，用于根据所述运行参数构建状态特征向量。
"""

US_CLAIMS = """
1. A data processing method comprising: receiving, by a processor, operating parameters of a target device; generating a state feature vector from the operating parameters; and outputting a prediction result based on the state feature vector.
2. The method of claim 1, wherein generating the state feature vector comprises normalizing the operating parameters.
"""

CN_FULL = """
发明名称：一种数据处理方法及装置

技术领域
本发明涉及数据处理技术领域。

背景技术
现有技术中设备状态预测准确率不足。

发明内容
本发明提供一种数据处理方法，解决预测准确率不足的问题。

附图说明
图1是本发明实施例的数据处理方法流程图。

具体实施方式
如图1所示，获取目标设备的运行参数，根据所述运行参数构建状态特征向量，将所述状态特征向量输入预测模型。处理器(101)执行上述步骤。

权利要求书
""" + CN_CLAIMS


def test_cn_decompose():
    claims = ClaimDecomposer(lang="zh").decompose_block(CN_CLAIMS)
    assert len(claims) == 3
    c1, c2, c3 = claims
    assert c1.claim_type == "independent" and c1.category == "method"
    assert c1.two_part_form and c1.elements[0].element_type == "preamble"
    steps = [e for e in c1.elements if e.element_type == "step"]
    assert len(steps) == 3 and steps[0].id == "C1.E2"
    assert c2.claim_type == "dependent" and c2.depends_on == [1]
    assert c2.elements[-1].element_type == "limitation"
    comps = [e for e in c3.elements if e.element_type == "component"]
    assert len(comps) == 2 and comps[0].function.startswith("获取目标设备")


def test_us_decompose():
    claims = ClaimDecomposer(lang="en").decompose_block(US_CLAIMS)
    assert len(claims) == 2
    c1, c2 = claims
    assert c1.category == "method" and len(c1.elements) >= 3
    assert c2.depends_on == [1]
    assert any(e.element_type == "limitation" for e in c2.elements)


def test_parser_and_graph():
    ara = PatentParser(lang="zh").parse(CN_FULL)
    assert ara.metadata.title.startswith("一种数据处理")
    assert len(ara.claims) == 3
    kinds = {s.kind for s in ara.spec_sections}
    assert {"field", "background", "summary", "embodiments", "claims"} <= kinds
    assert ara.figures and ara.figures[0].number == 1
    rels = {(e.source, e.relation) for e in ara.edges}
    assert ("C2", "depends_on") in rels and ("C1", "has_element") in rels
    assert any(e.relation == "supported_by" for e in ara.edges)
    # round-trip
    ara2 = type(ara).from_dict(ara.to_dict())
    assert [c.number for c in ara2.claims] == [1, 2, 3]
    assert len(ara2.claims[0].elements) == len(ara.claims[0].elements)


def test_evaluator_bottom_up():
    ara = PatentParser(lang="zh").parse(CN_FULL)
    # 模拟评估 agent：R1 披露了 C1 除 E4(预测模型输入) 外的全部要素
    verdicts = []
    for c in ara.claims:
        for e in c.elements:
            status = "not_disclosed" if e.id == "C1.E4" else "disclosed"
            verdicts.append(ElementVerdict(element_id=e.id, reference_id="R1",
                                           status=status, rationale="test"))
    # 补一篇披露全部要素的对比文件，验证 anticipate 逻辑作用于 C3（装置独权）
    for e in ara.claims[2].elements:
        verdicts.append(ElementVerdict(element_id=e.id, reference_id="R2", status="disclosed"))

    report = Evaluator(ara).evaluate(verdicts)
    c1 = next(r for r in report["claims"] if r["number"] == 1)
    assert c1["novel"] is True                      # 单篇未披露全部要素 -> 新颖
    assert c1["three_step"]["step1_closest_prior_art"] == "R1"
    assert any(d["element_id"] == "C1.E4"
               for d in c1["three_step"]["step2_distinguishing_features"])
    c3 = next(r for r in report["claims"] if r["number"] == 3)
    assert c3["novel"] is False and "R2" in c3["anticipated_by"]   # 全要素规则
    ov = report["overall"]
    assert 0.0 <= ov["score"] <= 1.0 and ov["grade"] in {"strong", "moderate", "weak", "high_risk"}


def test_gates():
    ara = PatentParser(lang="zh").parse(CN_FULL)
    ara.subject_matter = {"eligible": True, "article": "25/2.2", "rationale": "技术手段"}

    # 模拟评估报告
    eval_report = {
        "claims": [
            {"number": 1, "three_step": {"step2_distinguishing_features": [
                {"element_id": "C1.E4", "element_type": "step", "text": "S3", "bound_citations": []}
            ]}}
        ]
    }

    gk = GateKeeper(ara, eval_report)

    # Gate 1: 已注入适格判定，应通过
    g1 = gk.gate1_subject_matter()
    assert g1.passed is True

    # Gate 2: C1.E4 未绑定对比文件，应失败
    g2 = gk.gate2_evidence_binding()
    assert g2.passed is False
    assert any("C1.E4" in f for f in g2.findings)

    # Gate 4: 无引用，应通过（没有可编造的）
    g4 = gk.gate4_no_fabrication()
    assert g4.passed is True

    # 运行全部门禁
    report = gk.run_all()
    assert report["blocking_failures"] >= 1
    assert report["summary"].startswith("FAIL")


def test_provenance_and_trace():
    ara = PatentParser(lang="zh").parse(CN_FULL)
    # 新字段默认值
    assert ara.claims[0].elements[0].provenance == "ai-executed"
    assert ara.subject_matter == {}

    # 添加 trace 节点
    from patent_ara import ClaimVersion, DesignAround, DeadEnd
    ara.claim_versions.append(ClaimVersion(
        id="CV1", claim_number=1, version=1, text="原始权1",
        change_rationale="事实注入", provenance="user"))
    ara.design_arounds.append(DesignAround(
        id="DA1", target_feature="C1.E4", mechanism_substitution="改动词"))
    ara.dead_ends.append(DeadEnd(id="DE1", direction="纯算法", reason="客体不适格"))

    # 序列化/反序列化 round-trip
    d = ara.to_dict()
    ara2 = type(ara).from_dict(d)
    assert len(ara2.claim_versions) == 1
    assert ara2.claim_versions[0].provenance == "user"
    assert len(ara2.design_arounds) == 1
    assert len(ara2.dead_ends) == 1


if __name__ == "__main__":
    test_cn_decompose(); test_us_decompose(); test_parser_and_graph(); test_evaluator_bottom_up()
    test_gates(); test_provenance_and_trace()
    print("ALL TESTS PASSED")
