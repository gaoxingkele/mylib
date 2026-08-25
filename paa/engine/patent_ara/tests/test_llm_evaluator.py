from __future__ import annotations

from patent_ara.llm_evaluator import DeepSeekClient


def test_json_chat_accepts_top_level_array(monkeypatch):
    client = DeepSeekClient(api_key="test")
    monkeypatch.setattr(
        client,
        "chat",
        lambda *args, **kwargs: '[{"element_id":"C1.E1","status":"disclosed","confidence":0.9}]',
    )

    result = client.json_chat("prompt")

    assert isinstance(result, list)
    assert result[0]["element_id"] == "C1.E1"


def test_json_chat_accepts_fenced_top_level_array(monkeypatch):
    client = DeepSeekClient(api_key="test")
    monkeypatch.setattr(client, "chat", lambda *args, **kwargs: "```json\n[]\n```")

    assert client.json_chat("prompt") == []
