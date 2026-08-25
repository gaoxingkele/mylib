from __future__ import annotations

from patent_ara import IncopatIntegrator, PatentParser
from patent_ara.incopat_integration import IncopatClient


def _client_with_response(response):
    client = IncopatClient.__new__(IncopatClient)
    client.client_id = "test-client"
    client._api = lambda path, params: response
    return client


def test_semantic_search_accepts_list_response_shape():
    client = _client_with_response(
        {"status": True, "result": {"list": [{"pn": "CN123A", "semanticsScore": "0.9"}]}}
    )

    rows = client.semantic_search("query", rows=5)

    assert rows == [{"pn": "CN123A", "semanticsScore": "0.9"}]


def test_get_claims_accepts_claim_or_response_shape():
    client = _client_with_response(
        {"status": True, "result": {"claim-or": "<p>1. 一种方法……</p>"}}
    )

    assert client.get_claims("CN123A") == "<p>1. 一种方法……</p>"


def test_integrator_keeps_enough_claim_text_for_element_review():
    class FakeClient:
        def semantic_search(self, text, rows=5):
            return [{"pn": "CN123A", "ti-cn": "对比文件"}]

        def get_claims(self, patent_number):
            return "技术特征" * 1000

    ara = PatentParser(lang="zh").parse(
        "发明名称：测试方法\n权利要求书\n"
        "1. 一种测试方法，其特征在于，包括：获取数据；处理所述数据。"
    )

    enriched = IncopatIntegrator(FakeClient()).enrich_ara(ara, max_citations=1)

    assert len(enriched.citations[0].claim_text_excerpt) > 3000
