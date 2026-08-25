#!/usr/bin/env python3
"""
model.py —— PatentARA 数据模型（四层：metadata / cognitive / artifacts / exploration_graph）。

纯 stdlib；PyYAML 与 jsonschema 为可选依赖（存在则启用 YAML IO 与 schema 校验）。
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Optional

SCHEMA_VERSION = "1.1.0"

PROVENANCE_TAGS = ("user", "ai-suggested", "ai-executed", "user-revised")

try:
    import yaml  # type: ignore
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

try:
    import jsonschema  # type: ignore
    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False


# ---------- metadata ----------
@dataclass
class Metadata:
    title: str = ""
    jurisdiction: str = "CNIPA"          # CNIPA | USPTO | EPO | PCT | OTHER
    language: str = "zh"                 # zh | en
    doc_type: str = "application"
    application_number: str = ""
    publication_number: str = ""
    filing_date: str = ""
    publication_date: str = ""
    priority_date: str = ""
    applicants: list[str] = field(default_factory=list)
    inventors: list[str] = field(default_factory=list)
    ipc_classifications: list[str] = field(default_factory=list)
    cpc_classifications: list[str] = field(default_factory=list)


# ---------- cognitive ----------
@dataclass
class TechnicalProblem:
    id: str                              # P1, P2 ...
    statement: str
    source_section_ids: list[str] = field(default_factory=list)


@dataclass
class InventiveConcept:
    id: str                              # IC1 ...
    name: str
    description: str = ""
    problem_ids: list[str] = field(default_factory=list)
    core_element_ids: list[str] = field(default_factory=list)


@dataclass
class ClaimElement:
    id: str                              # C{claim}.E{idx}
    claim_number: int
    element_type: str                    # preamble|step|component|limitation|feature|use_function
    text: str
    function: str = ""
    order: int = 0
    refines_element_id: Optional[str] = None
    characterizing: bool = True
    provenance: str = "ai-executed"      # PAA Stage-1 provenance tag
    support_section_ids: list[str] = field(default_factory=list)  # explicit 26.3 bindings


@dataclass
class Claim:
    id: str                              # C{number}
    number: int
    claim_type: str                      # independent | dependent
    category: str                        # method|apparatus|system|medium|computer_program_product|other
    text: str
    title: str = ""
    depends_on: list[int] = field(default_factory=list)
    two_part_form: bool = False
    elements: list[ClaimElement] = field(default_factory=list)

    @property
    def element_ids(self) -> list[str]:
        return [e.id for e in self.elements]


# ---------- artifacts ----------
@dataclass
class SpecSection:
    id: str                              # S1 ...
    kind: str                            # field|background|summary|drawings_brief|embodiments|claims|abstract|other
    text: str
    title: str = ""


@dataclass
class Figure:
    id: str                              # F1 ...
    number: int
    caption: str = ""
    reference_numerals: list[int] = field(default_factory=list)


@dataclass
class Example:
    id: str                              # EX1 ...
    title: str = ""
    description: str = ""
    figure_ids: list[str] = field(default_factory=list)
    supports_element_ids: list[str] = field(default_factory=list)


@dataclass
class ReferenceNumeral:
    numeral: int
    name: str


# ---------- exploration graph ----------
@dataclass
class GraphNode:
    id: str
    node_type: str                       # claim|element|concept|problem|section|figure|example|prior_art
    label: str = ""


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str
    weight: float = 1.0
    evidence: str = ""


@dataclass
class Citation:
    id: str                              # R1 ...
    patent_number: str
    title: str = ""
    kind: str = "retrieved"
    relevance: str = "unknown"           # X|Y|A|O|unknown
    mapped_element_ids: list[str] = field(default_factory=list)
    evidence_uri: str = ""
    relationship: str = "contrasts"      # conflicts | contrasts | background
    search_receipt: str = ""             # 检索式/来源 — gate-4 anti-fabrication anchor
    claim_text_excerpt: str = ""         # 对比文件权项原文转录
    verified: bool = False               # True only when from real search


# ---------- PAA trace dataclasses ----------
@dataclass
class ClaimVersion:
    id: str                    # CV1, CV2 ...
    claim_number: int
    version: int
    text: str
    change_rationale: str = "" # 为什么改：事实注入/冲突标记/封箱...
    supersedes: str = ""       # previous ClaimVersion id
    provenance: str = "ai-executed"


@dataclass
class DesignAround:
    id: str                    # DA1
    target_feature: str        # 被绕开的特征 / element_id
    mechanism_substitution: str = ""  # 改了什么动词/机制
    prior_art_id: str = ""     # 触发绕行的 Citation id
    provenance: str = "ai-executed"


@dataclass
class DeadEnd:
    id: str                    # DE1
    direction: str             # 被否的撰写方向
    reason: str = ""
    provenance: str = "ai-executed"


@dataclass
class OAResponse:
    id: str                    # OA1
    office_action_ref: str = ""
    opinion_summary: str = ""
    response_strategy: str = ""
    resulting_claim_version_id: str = ""


# ---------- container ----------
@dataclass
class PatentARA:
    metadata: Metadata = field(default_factory=Metadata)
    technical_problems: list[TechnicalProblem] = field(default_factory=list)
    inventive_concepts: list[InventiveConcept] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    spec_sections: list[SpecSection] = field(default_factory=list)
    figures: list[Figure] = field(default_factory=list)
    examples: list[Example] = field(default_factory=list)
    reference_numerals: list[ReferenceNumeral] = field(default_factory=list)
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    claim_versions: list[ClaimVersion] = field(default_factory=list)
    design_arounds: list[DesignAround] = field(default_factory=list)
    dead_ends: list[DeadEnd] = field(default_factory=list)
    oa_responses: list[OAResponse] = field(default_factory=list)
    subject_matter: dict = field(default_factory=dict)  # {"eligible": bool|None, "article": "25/2.2", "rationale": str}
    schema_version: str = SCHEMA_VERSION

    # ---- helpers ----
    def claim(self, number: int) -> Optional[Claim]:
        return next((c for c in self.claims if c.number == number), None)

    def elements(self, claim_number: int, transitive: bool = False) -> list[ClaimElement]:
        """claim 的要素；transitive=True 时沿 depends_on 链并入父权项要素（用于新颖性整体判断）。"""
        c = self.claim(claim_number)
        if c is None:
            return []
        out = list(c.elements)
        if transitive:
            for p in c.depends_on:
                out.extend(self.elements(p, transitive=True))
        return out

    def support_weight(self, element_id: str) -> Optional[float]:
        ws = [e.weight for e in self.edges
              if e.relation == "supported_by" and e.source == element_id]
        return max(ws) if ws else None

    # ---- serialization ----
    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "metadata": asdict(self.metadata),
            "cognitive": {
                "technical_problems": [asdict(p) for p in self.technical_problems],
                "inventive_concepts": [asdict(c) for c in self.inventive_concepts],
                "claims": [
                    {**{k: v for k, v in asdict(c).items() if k != "elements"},
                     "element_ids": c.element_ids}
                    for c in self.claims
                ],
                "claim_elements": [asdict(e) for c in self.claims for e in c.elements],
            },
            "artifacts": {
                "spec_sections": [asdict(s) for s in self.spec_sections],
                "figures": [asdict(f) for f in self.figures],
                "examples": [asdict(x) for x in self.examples],
                "reference_numerals": [asdict(r) for r in self.reference_numerals],
            },
            "exploration_graph": {
                "nodes": [asdict(n) for n in self.nodes],
                "edges": [asdict(e) for e in self.edges],
                "citations": [asdict(c) for c in self.citations],
            },
            "trace": {
                "claim_versions": [asdict(v) for v in self.claim_versions],
                "design_arounds": [asdict(d) for d in self.design_arounds],
                "dead_ends": [asdict(d) for d in self.dead_ends],
                "oa_responses": [asdict(o) for o in self.oa_responses],
            },
            "subject_matter": self.subject_matter,
        }

    @staticmethod
    def _mk(cls, d: dict[str, Any]):
        names = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in (d or {}).items() if k in names})

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PatentARA":
        cog, art, g = d.get("cognitive", {}), d.get("artifacts", {}), d.get("exploration_graph", {})
        elems_by_claim: dict[int, list[ClaimElement]] = {}
        for e in cog.get("claim_elements", []):
            el = cls._mk(ClaimElement, e)
            elems_by_claim.setdefault(el.claim_number, []).append(el)
        claims = []
        for c in cog.get("claims", []):
            cl = cls._mk(Claim, c)
            cl.elements = sorted(elems_by_claim.get(cl.number, []), key=lambda x: x.order)
            claims.append(cl)
        trace = d.get("trace", {})
        return cls(
            metadata=cls._mk(Metadata, d.get("metadata", {})),
            technical_problems=[cls._mk(TechnicalProblem, p) for p in cog.get("technical_problems", [])],
            inventive_concepts=[cls._mk(InventiveConcept, c) for c in cog.get("inventive_concepts", [])],
            claims=sorted(claims, key=lambda x: x.number),
            spec_sections=[cls._mk(SpecSection, s) for s in art.get("spec_sections", [])],
            figures=[cls._mk(Figure, f) for f in art.get("figures", [])],
            examples=[cls._mk(Example, x) for x in art.get("examples", [])],
            reference_numerals=[cls._mk(ReferenceNumeral, r) for r in art.get("reference_numerals", [])],
            nodes=[cls._mk(GraphNode, n) for n in g.get("nodes", [])],
            edges=[cls._mk(GraphEdge, e) for e in g.get("edges", [])],
            citations=[cls._mk(Citation, c) for c in g.get("citations", [])],
            claim_versions=[cls._mk(ClaimVersion, v) for v in trace.get("claim_versions", [])],
            design_arounds=[cls._mk(DesignAround, d2) for d2 in trace.get("design_arounds", [])],
            dead_ends=[cls._mk(DeadEnd, d3) for d3 in trace.get("dead_ends", [])],
            oa_responses=[cls._mk(OAResponse, o) for o in trace.get("oa_responses", [])],
            subject_matter=d.get("subject_matter", {}),
            schema_version=d.get("schema_version", SCHEMA_VERSION),
        )

    def save(self, path: str | Path) -> None:
        path = Path(path)
        data = self.to_dict()
        if path.suffix in (".yaml", ".yml"):
            if not _HAS_YAML:
                raise RuntimeError("PyYAML 未安装，请用 .json 输出")
            path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        else:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "PatentARA":
        path = Path(path)
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text) if path.suffix in (".yaml", ".yml") and _HAS_YAML else json.loads(text)
        return cls.from_dict(data)

    def validate(self, schema_path: str | Path) -> list[str]:
        """用 JSON Schema 校验；无 jsonschema 库时返回提示。"""
        if not _HAS_JSONSCHEMA:
            return ["jsonschema 未安装，跳过校验"]
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
        return [f"{list(e.absolute_path)}: {e.message}"
                for e in jsonschema.Draft202012Validator(schema).iter_errors(self.to_dict())]
