"""PatentARA — Agent-Native Research Artifact for Patents (CNIPA/USPTO), fused with PAA gates."""
from .model import (PROVENANCE_TAGS, SCHEMA_VERSION, Citation, Claim, ClaimElement,
                    ClaimVersion, DeadEnd, DesignAround, Example, Figure,
                    GraphEdge, GraphNode, InventiveConcept, Metadata, OAResponse,
                    PatentARA, ReferenceNumeral, SpecSection, TechnicalProblem)
from .claim_decomposer import ClaimDecomposer
from .parser import PatentParser
from .evaluator import ElementVerdict, Evaluator
from .gates import GateKeeper, GateResult
from .incopat_integration import IncopatClient, IncopatIntegrator
from .llm_evaluator import DeepSeekClient, LLMEvaluator
from .scorer_integration import PatentGrantScorer, integrate_scoring
from .export_paa import PAAExporter, export_paa

__all__ = ["PROVENANCE_TAGS", "SCHEMA_VERSION", "PatentARA", "Metadata", "Claim",
           "ClaimElement", "TechnicalProblem", "InventiveConcept", "SpecSection",
           "Figure", "Example", "ReferenceNumeral", "GraphNode", "GraphEdge",
           "Citation", "ClaimVersion", "DesignAround", "DeadEnd", "OAResponse",
           "ClaimDecomposer", "PatentParser", "ElementVerdict", "Evaluator",
           "GateKeeper", "GateResult", "IncopatClient", "IncopatIntegrator",
           "DeepSeekClient", "LLMEvaluator", "PatentGrantScorer", "integrate_scoring",
           "PAAExporter", "export_paa"]
