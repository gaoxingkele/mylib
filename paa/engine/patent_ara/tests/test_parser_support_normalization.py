from __future__ import annotations

from patent_ara import PatentParser


def test_support_matching_normalizes_claim_and_specification_symmetrically():
    text = """发明名称：计数器处理方法

技术领域
本发明涉及任务处理技术。

具体实施方式
每个OCR处理子任务完成后执行DECR指令原子递减所述原子计数器。

权利要求书
1. 一种计数器处理方法，其特征在于，包括：每个OCR处理子任务完成后执行DECR指令原子递减所述原子计数器。
"""

    ara = PatentParser(lang="zh").parse(text)
    element = ara.claims[0].elements[-1]

    assert ara.support_weight(element.id) == 1.0
