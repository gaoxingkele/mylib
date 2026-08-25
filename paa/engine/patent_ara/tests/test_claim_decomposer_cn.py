from __future__ import annotations

from patent_ara import ClaimDecomposer


def test_cn_dependency_accepts_any_one_in_range_expression():
    claim = ClaimDecomposer(lang="zh").decompose(
        "12. 根据权利要求1至11中任一项所述的方法，其特征在于，还包括记录结果。"
    )

    assert claim is not None
    assert claim.claim_type == "dependent"
    assert claim.depends_on == list(range(1, 12))
