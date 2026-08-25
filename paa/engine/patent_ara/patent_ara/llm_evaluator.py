#!/usr/bin/env python3
"""
llm_evaluator.py —— 用 LLM (DeepSeek) 生成 ElementVerdict，替代模拟数据。

流程：
1. 对每个独立权利要求，提取其要素列表
2. 对每篇对比文件，让 LLM 判断每个要素是否被披露
3. 生成 ElementVerdict 列表，供 Evaluator 使用
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import requests

from .evaluator import ElementVerdict
from .model import PatentARA


class DeepSeekClient:
    """轻量 DeepSeek API 客户端。"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.model = "deepseek-chat"

    def chat(self, prompt: str, system: Optional[str] = None, temperature: float = 0.3, max_tokens: int = 2000) -> str:
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not set")
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": False}
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    def json_chat(self, prompt: str, system: Optional[str] = None, temperature: float = 0.3) -> Any:
        text = self.chat(prompt, system=system, temperature=temperature)
        text = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        array_start = text.find("[")
        object_start = text.find("{")
        if array_start != -1 and (object_start == -1 or array_start < object_start):
            start = array_start
            end = text.rfind("]") + 1
        else:
            start = object_start
            end = text.rfind("}") + 1
        if start == -1 or end == 0:
            return {"raw": text}
        candidate = text[start:end]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # 尝试修复截断的 JSON
            open_braces = candidate.count("{") - candidate.count("}")
            open_brackets = candidate.count("[") - candidate.count("]")
            fixed = candidate + "]" * open_brackets + "}" * open_braces
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                return {"raw": candidate}


class LLMEvaluator:
    """用 LLM 对 PatentARA 的要素进行逐一评估。"""

    def __init__(self, llm_client: Optional[DeepSeekClient] = None):
        self.llm = llm_client or DeepSeekClient()

    def generate_verdicts(self, ara: PatentARA, reference_id: str, reference_text: str,
                          max_elements: int = 20) -> List[ElementVerdict]:
        """
        对指定的对比文件，为所有权利要求要素生成 ElementVerdict。

        为了控制 API 调用次数，采用批量评估：
        - 把多个要素打包到一个 prompt 中
        - 让 LLM 返回 JSON 数组
        """
        verdicts = []
        elements = []
        for claim in ara.claims:
            for elem in claim.elements:
                elements.append(elem)

        # 分批处理，每批最多 5 个要素
        batch_size = 5
        for i in range(0, min(len(elements), max_elements), batch_size):
            batch = elements[i:i + batch_size]
            batch_verdicts = self._evaluate_batch(batch, reference_id, reference_text)
            verdicts.extend(batch_verdicts)

        return verdicts

    def _evaluate_batch(self, elements: List, reference_id: str, reference_text: str) -> List[ElementVerdict]:
        """评估一批要素。"""
        system = (
            "You are a patent claim chart specialist. "
            "For each element below, determine if it is explicitly disclosed in the prior art reference. "
            "Return a JSON array with one object per element, in the same order. "
            "Each object must have: element_id (string), status (disclosed|partially_disclosed|not_disclosed), "
            "confidence (0-1), rationale (max 100 chars), evidence_excerpt (max 100 chars from reference)."
        )

        elements_text = ""
        for elem in elements:
            elements_text += f"\nElement {elem.id} ({elem.element_type}): {elem.text[:200]}\n"

        prompt = (
            f"PRIOR ART REFERENCE:\n{reference_text[:3000]}\n\n"
            f"ELEMENTS TO EVALUATE:{elements_text}\n"
            "Evaluate each element. Return only JSON array."
        )

        try:
            out = self.llm.json_chat(prompt, system=system)
            # out 应该是 list 或包含 list 的 dict
            if isinstance(out, dict) and "raw" in out:
                # 解析失败，返回默认
                return [ElementVerdict(element_id=e.id, reference_id=reference_id,
                                      status="not_disclosed", confidence=0.5,
                                      rationale="LLM parse failed") for e in elements]

            items = out if isinstance(out, list) else out.get("verdicts", out.get("elements", []))
            if not isinstance(items, list):
                items = []

            verdicts = []
            for j, elem in enumerate(elements):
                if j < len(items):
                    item = items[j]
                    verdicts.append(ElementVerdict(
                        element_id=elem.id,
                        reference_id=reference_id,
                        status=item.get("status", "not_disclosed"),
                        confidence=float(item.get("confidence", 0.5)),
                        rationale=str(item.get("rationale", ""))[:200],
                        evidence_excerpt=str(item.get("evidence_excerpt", ""))[:200],
                    ))
                else:
                    verdicts.append(ElementVerdict(
                        element_id=elem.id,
                        reference_id=reference_id,
                        status="not_disclosed",
                        confidence=0.5,
                        rationale="LLM response incomplete",
                    ))
            return verdicts
        except Exception as e:
            # 异常时返回默认
            return [ElementVerdict(element_id=e.id, reference_id=reference_id,
                                  status="not_disclosed", confidence=0.3,
                                  rationale=f"LLM error: {str(e)[:100]}") for e in elements]

    def evaluate_against_citation(self, ara: PatentARA, citation_id: str) -> List[ElementVerdict]:
        """对单篇对比文件评估所有要素。"""
        citation = next((c for c in ara.citations if c.id == citation_id), None)
        if citation is None:
            return []

        reference_text = citation.claim_text_excerpt or citation.title
        if not reference_text:
            return []

        return self.generate_verdicts(ara, citation_id, reference_text)

    def evaluate_all_citations(self, ara: PatentARA) -> List[ElementVerdict]:
        """对所有对比文件评估所有要素。"""
        all_verdicts = []
        for citation in ara.citations:
            verdicts = self.evaluate_against_citation(ara, citation.id)
            all_verdicts.extend(verdicts)
        return all_verdicts
