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


def test_get_specification_accepts_des_cn_response_shape():
    client = _client_with_response(
        {"status": True, "result": {"des-cn": "【0001】说明书正文"}}
    )

    assert client.get_specification("CN123A") == "【0001】说明书正文"


def test_expression_search_retries_confirmed_fields_after_extended_field_denial():
    client = IncopatClient.__new__(IncopatClient)
    client.client_id = "test-client"
    calls = []

    def fake_api(path, params):
        calls.append(dict(params))
        if "ipcm" in params["incoFields"]:
            return {"status": False, "message": "该字段(ipcm)没有权限查看"}
        return {"status": True, "result": {"rows": [{"pn": "CN123A"}]}}

    client._api = fake_api
    rows = client.search_by_expression("TI-CN=(测试)", rows=50)

    assert rows == [{"pn": "CN123A"}]
    assert len(calls) == 2
    assert calls[0]["rows"] == 50
    assert "ipcm" in calls[0]["incoFields"]
    assert "ipcm" not in calls[1]["incoFields"]


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
