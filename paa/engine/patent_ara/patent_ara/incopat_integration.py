#!/usr/bin/env python3
"""
incopat_integration.py —— 真实 Incopat 检索接入 PatentARA。

从 PatentARA 提取检索文本，调用 Incopat API 获取真实对比文件，
并自动绑定到 ClaimElement。
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from .model import Citation, PatentARA


class IncopatClient:
    """轻量 Incopat API 客户端（复用项目现有实现）。"""

    def __init__(self, credentials_path: Optional[str] = None):
        if credentials_path is None:
            # 默认路径：项目根目录下的 incopat-search skill
            base = os.path.dirname(os.path.abspath(__file__))
            credentials_path = os.path.join(
                base, "..", "..", ".claude", "skills", "incopat-search", "scripts", "credentials.json"
            )
        with open(credentials_path, encoding="utf-8") as f:
            self._cred = json.load(f)
        self.base_url = self._cred.get("base", "https://apitest.incopat.com")
        self.client_id = self._cred.get("client_id", "")
        self.client_secret = self._cred.get("client_secret", "")
        self.username = self._cred.get("username", "")
        self.password = self._cred.get("password", "")
        self._token = None
        self._token_expires = 0

    def _post(self, path: str, params: Dict, timeout: int = 60) -> Dict:
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code}: {body[:500]}")

    def _get_token(self) -> str:
        if self._token and self._token_expires > time.time() + 60:
            return self._token
        resp = self._post("/oauth/token", {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password,
        })
        if "access_token" not in resp:
            raise RuntimeError(f"获取 token 失败: {json.dumps(resp, ensure_ascii=False)}")
        self._token = resp["access_token"]
        self._token_expires = time.time() + int(resp.get("expires_in", 7200))
        return self._token

    def _api(self, path: str, params: Dict) -> Dict:
        params = dict(params)
        params["access_token"] = self._get_token()
        resp = self._post(path, params)
        msg = str(resp.get("message", ""))
        if resp.get("status") is False and ("TOKEN" in msg.upper() or resp.get("code") in (1006, 1007, "1006", "1007")):
            self._token = None
            params["access_token"] = self._get_token()
            resp = self._post(path, params)
        return resp

    def semantic_search(self, text: str, rows: int = 5) -> List[Dict]:
        resp = self._api(f"/api/semanticsApi/semanticsSearch/{self.client_id}", {
            "searchText": text[:2000],
            "rows": min(rows, 20),
        })
        if resp.get("status") is not True:
            return []
        result = resp.get("result", {}) or {}
        return result.get("rows") or result.get("list") or []

    def search_by_expression(self, expression: str, rows: int = 5) -> List[Dict]:
        resp = self._api(f"/api/search/incosearch/{self.client_id}", {
            "incoExp": expression,
            "rows": min(rows, 20),
            "from": 0,
            "incoFields": "pn,an,ti-cn,ti-en,ab-cn,ab-en,ap-or,in-or,pd,ad",
        })
        if resp.get("status") is not True:
            return []
        return resp.get("result", {}).get("rows", [])

    def get_claims(self, patent_number: str) -> str:
        resp = self._api(f"/api/search/claim/{self.client_id}", {"pn": patent_number})
        if resp.get("status") is not True:
            return ""
        result = resp.get("result", {}) or {}
        return result.get("claims") or result.get("claim-or") or result.get("claim-cn") or ""

    def get_specification(self, patent_number: str) -> str:
        resp = self._api(f"/api/search/spec/{self.client_id}", {"pn": patent_number})
        if resp.get("status") is not True:
            return ""
        return resp.get("result", {}).get("description", "")


class IncopatIntegrator:
    """把 Incopat 检索结果集成到 PatentARA。"""

    def __init__(self, client: Optional[IncopatClient] = None):
        self.client = client or IncopatClient()

    def enrich_ara(self, ara: PatentARA, max_citations: int = 5) -> PatentARA:
        """
        为 PatentARA 检索真实对比文件并绑定到要素。

        策略：
        1. 用独立权利要求的文本做语义检索
        2. 对每篇对比文件获取权利要求全文
        3. 用文本相似度绑定到 ClaimElement
        """
        # 找独立权利要求
        independent_claims = [c for c in ara.claims if c.claim_type == "independent"]
        if not independent_claims:
            return ara

        # 用第一条独立权利要求做检索
        main_claim = independent_claims[0]
        search_text = main_claim.text[:1500]

        # 语义检索
        try:
            results = self.client.semantic_search(search_text, rows=max_citations)
        except Exception as e:
            print(f"Incopat semantic search failed: {e}")
            results = []

        # 如果语义检索不足，用关键词检索补充
        if len(results) < 3 and ara.metadata.title:
            keywords = [w for w in ara.metadata.title.split() if len(w) > 1][:3]
            if keywords:
                expr = f"TI-CN=({' OR '.join(keywords)})"
                try:
                    expr_results = self.client.search_by_expression(expr, rows=max_citations)
                    seen = {r.get("pn") for r in results}
                    for r in expr_results:
                        if r.get("pn") not in seen:
                            results.append(r)
                            seen.add(r.get("pn"))
                except Exception as e:
                    print(f"Incopat expression search failed: {e}")

        # 为每篇对比文件创建 Citation 并获取权利要求
        for i, r in enumerate(results[:max_citations]):
            pn = r.get("pn", "")
            if not pn:
                continue

            # 获取权利要求全文
            try:
                claims_text = self.client.get_claims(pn)
            except Exception as e:
                print(f"Failed to get claims for {pn}: {e}")
                claims_text = ""

            citation = Citation(
                id=f"R{i+1}",
                patent_number=pn,
                title=r.get("ti-cn", r.get("ti-en", "")),
                kind="retrieved",
                relevance="unknown",
                relationship="contrasts",
                mapped_element_ids=[],  # 待绑定
                evidence_uri=f"incopat://{pn}",
                search_receipt=f"incopat semantic/expression search: {search_text[:100]}",
                # Keep enough primary claim text for element-level review.  A
                # 500-character excerpt routinely cuts off the distinguishing
                # limitations and makes the LLM comparison systematically
                # incomplete; LLMEvaluator applies its own prompt-size cap.
                claim_text_excerpt=claims_text[:6000] if claims_text else "",
                verified=True,
            )

            # 用文本相似度绑定到要素
            self._bind_citation_to_elements(ara, citation, claims_text or r.get("ab-cn", ""))
            ara.citations.append(citation)
            time.sleep(0.1)  # 限速

        return ara

    def _bind_citation_to_elements(self, ara: PatentARA, citation: Citation, prior_text: str):
        """用简单文本匹配把对比文件绑定到最相关的 ClaimElement。"""
        if not prior_text:
            return

        prior_text_lower = prior_text.lower()
        scores = []

        for claim in ara.claims:
            for elem in claim.elements:
                # 计算要素文本与对比文件的匹配度
                elem_text = elem.text.lower()
                # 简单匹配：要素中的关键词在对比文件中出现的比例
                words = [w for w in elem_text.split() if len(w) > 2]
                if not words:
                    continue
                matches = sum(1 for w in words if w in prior_text_lower)
                score = matches / len(words)
                scores.append((score, elem.id))

        # 绑定得分最高的要素
        scores.sort(reverse=True)
        threshold = 0.3
        for score, eid in scores[:5]:  # 最多绑定5个要素
            if score >= threshold:
                citation.mapped_element_ids.append(eid)

        # 根据绑定数量调整 relevance
        if len(citation.mapped_element_ids) >= 3:
            citation.relevance = "X"
        elif len(citation.mapped_element_ids) >= 1:
            citation.relevance = "Y"
        else:
            citation.relevance = "A"
