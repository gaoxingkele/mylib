"""Screen one published document against claim elements. Stdlib plus jev-help-decide's API client."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HIGH = 0.72
LOW = 0.28
MAX_ELEMENTS = 6
MAX_CANDIDATES = 8
MAX_STATE_CHARS = 8000

DISPOSITION = {
    "type": "choice",
    "instructions": "仅根据 `candidate.title`、`candidate.abstract` 和 `candidate.passage`，下一步应如何处理这篇文献？不要判断新颖性、创造性或能否授权。",
    "criteria": {
        "read_original": "这些文字已经比较具体地写出了 `elements` 中的目标特征，值得取原文逐字核对",
        "hold_for_person": "主题相近，但从这些文字看不出目标特征是否真的被写出",
        "stop": "这些文字没有写出目标特征",
    },
}


def load_decide():
    path = Path(__file__).resolve().parents[4] / "skills" / "jev-help-decide" / "scripts" / "decide.py"
    spec = importlib.util.spec_from_file_location("jev_decide", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load JEV API client")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def element_question(text: str) -> dict:
    return {
        "type": "noul",
        "instructions": (
            "仅根据 `candidate.title`、`candidate.abstract` 和 `candidate.passage`，"
            "该文献是否写出了这一技术特征：" + text + "。"
            "特征只出现在未提供的其他章节时，回答否。"
        ),
    }


def covers_question() -> dict:
    return {
        "type": "noul",
        "instructions": "仅根据 `candidate.title`、`candidate.abstract` 和 `candidate.passage`，该文献是否把 `elements` 里的每一项技术特征都写了出来？缺任何一项就回答否。",
    }


def clean_text(value, limit: int) -> str:
    if not isinstance(value, str):
        raise ValueError("Text fields must be strings")
    text = value.strip()
    if len(text) > limit:
        raise ValueError("A text field exceeds its limit; split the screening instead of truncating")
    return text


def validate_packet(packet: dict) -> dict:
    if not isinstance(packet, dict):
        raise ValueError("Input must be a JSON object")
    if packet.get("disclosure") != "public_prior_art":
        raise ValueError("disclosure must be public_prior_art; send elements plus one published document, not an unpublished specification")
    if packet.get("lane") not in ("product", "mechanism"):
        raise ValueError("lane must be product or mechanism")
    elements = packet.get("elements")
    if not isinstance(elements, list) or not 1 <= len(elements) <= MAX_ELEMENTS:
        raise ValueError("elements must contain 1 to 6 items")
    seen = set()
    clean_elements = []
    for item in elements:
        if not isinstance(item, dict):
            raise ValueError("Each element must be an object")
        eid = item.get("id")
        if not isinstance(eid, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,31}", eid):
            raise ValueError("Element id must be a short lowercase identifier")
        if eid in seen or eid in ("covers_all", "disposition"):
            raise ValueError("Duplicate or reserved element id")
        seen.add(eid)
        clean_elements.append({"id": eid, "text": clean_text(item.get("text"), 240)})
    candidates = packet.get("candidates", [packet.get("candidate")])
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= MAX_CANDIDATES:
        raise ValueError("Provide 1 to 8 candidates")
    clean_candidates = []
    for item in candidates:
        if not isinstance(item, dict):
            raise ValueError("Each candidate must be an object")
        level = item.get("source_level")
        if level not in ("abstract", "original_passage"):
            raise ValueError("source_level must be abstract or original_passage")
        pub = clean_text(item.get("pub_number", ""), 40)
        if not re.fullmatch(r"[A-Z]{2}[A-Z0-9]{4,20}", pub):
            raise ValueError("pub_number must be a real publication or literature identifier")
        clean_candidates.append({
            "pub_number": pub,
            "title": clean_text(item.get("title", ""), 300),
            "abstract": clean_text(item.get("abstract", ""), 2500),
            "passage": clean_text(item.get("passage", ""), 4000),
            "source_level": level,
        })
    target = clean_text(packet.get("target_sentence", ""), 400)
    case_id = clean_text(packet.get("case_id", ""), 40)
    claim_hash = clean_text(packet.get("claim_hash", ""), 80)
    state_probe = json.dumps({"target_sentence": target, "elements": clean_elements, "candidate": clean_candidates[0]}, ensure_ascii=False)
    if len(state_probe) > MAX_STATE_CHARS:
        raise ValueError("State exceeds 8000 characters")
    if re.search(r"apikey_[A-Za-z0-9_-]{12,}|sk-[A-Za-z0-9_-]{16,}|Bearer\s+\S+", state_probe):
        raise ValueError("Credential-like content detected")
    return {
        "lane": packet["lane"],
        "case_id": case_id,
        "claim_hash": claim_hash,
        "target_sentence": target,
        "elements": clean_elements,
        "candidates": clean_candidates,
    }


def questions_for(elements: list[dict]) -> dict:
    questions = {item["id"]: element_question(item["text"]) for item in elements}
    questions["covers_all"] = covers_question()
    questions["disposition"] = DISPOSITION
    return questions


def payload_for(packet: dict, candidate: dict) -> dict:
    state = {
        "target_sentence": packet["target_sentence"],
        "elements": packet["elements"],
        "candidate": {k: candidate[k] for k in ("title", "abstract", "passage")},
    }
    return {"model": "jev-latest", "state": state, "questions": questions_for(packet["elements"])}


def compose(packet_lane: str, candidate: dict, answers: dict, elements: list[dict]) -> dict:
    nouls = {item["id"]: answers[item["id"]]["noul"] for item in elements}
    cover = answers["covers_all"]["noul"]
    disposition = answers["disposition"]["choice"]
    high = all(v >= HIGH for v in nouls.values()) and cover >= HIGH
    low = all(v <= LOW for v in nouls.values()) and cover <= LOW
    if high and disposition == "read_original":
        route = "map_passage" if candidate["source_level"] == "original_passage" else "fetch_original"
    elif low and disposition == "stop":
        route = "stop"
    else:
        route = "human_review"
    return {
        "pub_number": candidate["pub_number"],
        "lane": packet_lane,
        "source_level": candidate["source_level"],
        "element_nouls": nouls,
        "covers_all": cover,
        "disposition": disposition,
        "disposition_confidence": answers["disposition"]["confidence"],
        "suggested_route": route,
        "legal_conclusion": None,
    }


def graphene_stop(candidate: dict) -> dict | None:
    blob = candidate["title"] + "\n" + candidate["abstract"]
    if "石墨烯" in blob:
        return None
    return {
        "ok": True,
        "api_called": False,
        "pub_number": candidate["pub_number"],
        "lane": "product",
        "source_level": candidate["source_level"],
        "suggested_route": "stop",
        "reason": "graphene_absent_from_title_and_abstract",
        "legal_conclusion": None,
    }


def screen(packet: dict, decide, opener=None) -> dict:
    rows = []
    key = None
    for candidate in packet["candidates"]:
        if packet["lane"] == "product":
            stopped = graphene_stop(candidate)
            if stopped:
                rows.append(stopped)
                continue
        payload = payload_for(packet, candidate)
        if opener is None:
            if key is None:
                key = decide.credential(Path.cwd())
            raw = decide.evaluate(payload, key)
        else:
            raw = decide.evaluate(payload, "test", opener)
        if not raw.get("ok"):
            rows.append({"ok": False, "pub_number": candidate["pub_number"], "error": raw.get("error", "request_failed"), "legal_conclusion": None})
            continue
        row = compose(packet["lane"], candidate, raw["answers"], packet["elements"])
        row.update(ok=True, api_called=True, model=raw.get("model"))
        rows.append(row)
    return {"ok": all(row.get("ok") for row in rows), "results": rows}


def self_test() -> None:
    decide = load_decide()
    base = {
        "disclosure": "public_prior_art",
        "lane": "mechanism",
        "case_id": "SMX01",
        "claim_hash": "abc123",
        "target_sentence": "比较出厂热容并在超限时禁止加热",
        "elements": [
            {"id": "factory", "text": "保存出厂热容"},
            {"id": "inhibit", "text": "超限后禁止加热"},
        ],
        "candidate": {
            "pub_number": "CN112805054A",
            "title": "加湿器",
            "abstract": "比较热容并在异常时限制加热。",
            "passage": "",
            "source_level": "abstract",
        },
    }
    packet = validate_packet(base)
    product = validate_packet({**base, "lane": "product"})
    stopped = screen(product, decide, opener=lambda *a, **k: (_ for _ in ()).throw(AssertionError("API called")))
    assert stopped["results"][0]["reason"] == "graphene_absent_from_title_and_abstract"

    def mock(choice, nouls):
        from io import BytesIO
        answers = {
            "factory": {"type": "noul", "noul": nouls[0]},
            "inhibit": {"type": "noul", "noul": nouls[1]},
            "covers_all": {"type": "noul", "noul": nouls[2]},
            "disposition": {"type": "choice", "choice": choice, "confidence": 0.8, "probabilities": {
                "read_original": 1 if choice == "read_original" else 0,
                "hold_for_person": 1 if choice == "hold_for_person" else 0,
                "stop": 1 if choice == "stop" else 0,
            }},
        }
        body = json.dumps({"model": "mock", "answers": answers}).encode()
        return BytesIO(body)

    high = screen(packet, decide, opener=lambda *a, **k: mock("read_original", (0.9, 0.9, 0.9)))
    assert high["results"][0]["suggested_route"] == "fetch_original"
    low = screen(packet, decide, opener=lambda *a, **k: mock("stop", (0.1, 0.1, 0.1)))
    assert low["results"][0]["suggested_route"] == "stop"
    mixed = screen(packet, decide, opener=lambda *a, **k: mock("read_original", (0.9, 0.2, 0.4)))
    assert mixed["results"][0]["suggested_route"] == "human_review"
    original = validate_packet({**base, "candidate": {**base["candidate"], "source_level": "original_passage", "passage": "原文段落。"}})
    mapped = screen(original, decide, opener=lambda *a, **k: mock("read_original", (0.9, 0.9, 0.9)))
    assert mapped["results"][0]["suggested_route"] == "map_passage"
    assert mapped["results"][0]["legal_conclusion"] is None
    try:
        validate_packet({**base, "disclosure": "unpublished_spec"})
    except ValueError:
        pass
    else:
        raise AssertionError("Unpublished disclosure accepted")
    print(json.dumps({"ok": True, "self_test": "graphene gate, routes, and disclosure boundary passed"}))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    started = time.monotonic()
    digest = None
    try:
        if not args.input:
            raise ValueError("--input is required")
        packet = validate_packet(json.loads(args.input.read_text(encoding="utf-8-sig")))
        digest = hashlib.sha256(json.dumps(packet, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if args.dry_run:
            sample = payload_for(packet, packet["candidates"][0])
            print(json.dumps({"ok": True, "dry_run": True, "question_ids": list(sample["questions"]), "candidates": len(packet["candidates"])}, ensure_ascii=False))
            return 0
        result = screen(packet, load_decide())
    except (ValueError, OSError, RuntimeError) as exc:
        result = {"ok": False, "error": "input_or_credential", "detail": str(exc)}
    result.update(timestamp=datetime.now(timezone.utc).isoformat(), input_hash=digest, elapsed_ms=round((time.monotonic() - started) * 1000))
    try:
        log = ROOT / "runtime" / "calls.jsonl"
        log.parent.mkdir(exist_ok=True)
        with log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({k: result[k] for k in result if k != "results"} | {"routes": [row.get("suggested_route") for row in result.get("results", [])]}, ensure_ascii=False) + "\n")
    except OSError:
        result["audit_error"] = "local_log_write_failed"
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
