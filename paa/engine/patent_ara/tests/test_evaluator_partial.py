from __future__ import annotations

from patent_ara import Claim, ClaimElement, Citation, ElementVerdict, Evaluator, PatentARA


def test_partial_disclosure_reduces_distinguishing_feature_strength():
    ara = PatentARA()
    ara.claims = [
        Claim(
            id="C1",
            number=1,
            claim_type="independent",
            category="method",
            text="1. 一种方法，其特征在于，包括特征一和特征二。",
            elements=[
                ClaimElement(id="C1.E1", claim_number=1, element_type="feature", text="特征一"),
                ClaimElement(id="C1.E2", claim_number=1, element_type="feature", text="特征二"),
            ],
        )
    ]
    ara.citations = [Citation(id="R1", patent_number="CN1", verified=True)]
    verdicts = [
        ElementVerdict("C1.E1", "R1", "partially_disclosed"),
        ElementVerdict("C1.E2", "R1", "not_disclosed"),
    ]

    result = Evaluator(ara).evaluate(verdicts)["claims"][0]

    assert result["novel"] is True
    assert result["three_step"]["step1_closest_prior_art"] == "R1"
    assert result["feature_strength"] == 0.75
