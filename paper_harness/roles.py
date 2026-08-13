"""Role prompts for planner, executor, reviewer, and attribution."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from . import transport

JOURNALS_DIR = Path(r"D:/aicoding/paper_reviews/config/journals")
RESOURCES_DIR = Path(__file__).resolve().parent / "resources"
EXPERIENCE_PATH = RESOURCES_DIR / "paper_experience_digest.json"
REVIEW_PROTOCOL_PATH = RESOURCES_DIR / "reviewer_protocol.md"
MAX_REVIEW_CHARS = 240_000


def _repo_overview(paper_dir: Path, max_entries: int = 100) -> str:
    entries: list[str] = []
    for path in sorted(paper_dir.rglob("*")):
        if any(part in (".git", ".paper_harness", ".codex", "__pycache__") for part in path.parts):
            continue
        entries.append(str(path.relative_to(paper_dir)))
        if len(entries) >= max_entries:
            entries.append("...")
            break
    return "\n".join(entries)


def _experience_text() -> str:
    if not EXPERIENCE_PATH.exists():
        return "(No local experience digest was found.)"
    return EXPERIENCE_PATH.read_text(encoding="utf-8", errors="replace")


def plan_with_codex(goal: str, paper_dir: str | Path, model: str | None, command: str) -> str:
    """Create a read-only, evidence-preserving, staged plan."""
    paper_dir = Path(paper_dir)
    prompt = f"""You are the planner for an academic-paper harness.
Produce only Markdown with YAML frontmatter in this exact shape:
---
stages:
  - id: s1
    title: concise title
    objective: an executable and verifiable objective
    acceptance:
      - latex_build
      - no_placeholders
---
Then add a concise plan rationale after the closing ---.

Plan rules:
- Preserve every observed result, direction, sample size, statistical decision, and evidence boundary.
- Never plan to invent authors, affiliations, funding, citations, expert labels, data, runs, or results.
- Separate narrative alignment, method/evidence alignment, experiment/statistics work, and final artifact QA.
- A new experiment stage must name its estimand, control, analysis unit, stopping rule, and the claim it could support.
- Each stage must be accepted before the next stage runs. Use only these deterministic checks:
  latex_build / no_placeholders / declarations / narrative_structure /
  artifact_consistency / pdf_integrity / manuscript_hygiene / custom:<script path>.
- Put final scientific and submission checks in the last stage.

## Local evidence-alignment contract
{_experience_text()}

## Goal
{goal}

## Paper project structure
{_repo_overview(paper_dir)}
"""
    code, out = transport.codex_exec(prompt, cwd=paper_dir, sandbox="read-only", model=model, command=command)
    if code != 0:
        raise RuntimeError(f"planner call failed (exit {code}):\n{out[:2000]}")
    return out.strip()


def execute_stage(
    stage: dict,
    workdir: str | Path,
    model: str | None,
    command: str,
    log_path: Path,
) -> bool:
    """Execute one approved stage in its isolated worktree."""
    if transport.is_mock():
        log_path.write_text(
            "[MOCK EXECUTOR] No CLI was called. Objective recorded as completed.\n\n"
            f"stage: {stage['id']}\ntitle: {stage.get('title', '')}\nobjective:\n{stage['objective']}\n",
            encoding="utf-8",
        )
        return True
    prompt = f"""You are the executor for one approved academic-paper stage.
Work only inside the current isolated worktree and only within the approved objective.

Non-negotiable evidence rules:
- Do not invent or silently infer authors, affiliations, funding, citations, datasets, expert labels,
  experiment runs, numerical results, p-values, or deployment evidence.
- Do not tune toward a prettier result or change a negative/null finding into a positive claim.
- If the evidence cannot support the requested statement, preserve the limitation and report the blocker.
- Keep title, contribution, method, experiment, result, discussion, and conclusion claims aligned.
- Combined ablations support joint conclusions only; proxy or historical studies retain their scope qualifiers.
- Keep version histories, hashes, and incident detail in supplementary/internal records unless scientifically necessary.
- Inspect the relevant source and evidence files before editing. Preserve unrelated user changes.
- Run all listed acceptance checks or their underlying build/test commands before reporting completion.

## Stage {stage['id']}: {stage.get('title', '')}

## Approved objective
{stage['objective']}

## Acceptance checks
""" + "\n".join(f"- {item}" for item in stage.get("acceptance", []))
    code, out = transport.codex_exec(prompt, cwd=workdir, sandbox="workspace-write", model=model, command=command)
    log_path.write_text(f"exit_code={code}\n\n{out}", encoding="utf-8")
    return code == 0


def _load_journal_profile(venue: str) -> str:
    parts: list[str] = []
    yaml_path = JOURNALS_DIR / f"{venue}.yaml"
    profile_path = JOURNALS_DIR / f"{venue}_accepted_profile.md"
    if yaml_path.exists():
        parts.append(f"## Journal profile ({venue})\n" + yaml_path.read_text(encoding="utf-8", errors="replace"))
    if profile_path.exists():
        parts.append("## Accepted-paper calibration\n" + profile_path.read_text(encoding="utf-8", errors="replace"))
    return "\n\n".join(parts)


def _load_manuscript(path: Path) -> tuple[str, dict]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    total = len(raw)
    if total <= MAX_REVIEW_CHARS:
        supplied = raw
        complete = True
    else:
        half = MAX_REVIEW_CHARS // 2
        supplied = (
            raw[:half]
            + "\n\n% [PAPER_HARNESS: middle omitted because manuscript exceeded review limit]\n\n"
            + raw[-half:]
        )
        complete = False
    section_names = re.findall(r"\\(?:sub)*section\*?\{([^{}]+)\}", raw)
    coverage = {
        "characters_total": total,
        "characters_supplied": len(supplied),
        "complete": complete,
        "sections_detected": section_names,
    }
    return supplied, coverage


def _extract_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end <= start:
            raise RuntimeError("reviewer output did not contain a JSON object")
        try:
            data = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"reviewer output was not valid JSON: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("issues", []), list):
        raise RuntimeError("reviewer JSON must be an object with an issues list")
    return data


def review(paper_dir: str | Path, venue: str, manuscript: str, model: str | None, command: str) -> str:
    """Run a read-only, full-manuscript journal review and return canonical JSON."""
    paper_dir = Path(paper_dir)
    manuscript_path = paper_dir / manuscript
    if not manuscript_path.exists():
        raise RuntimeError(f"manuscript not found: {manuscript_path}")
    manuscript_text, coverage = _load_manuscript(manuscript_path)
    digest = hashlib.sha256(manuscript_path.read_bytes()).hexdigest()
    if transport.is_mock():
        return json.dumps(
            {
                "schema_version": "paper_harness.review.v2",
                "venue": venue,
                "manuscript": manuscript,
                "manuscript_sha256": digest,
                "coverage": coverage,
                "decision": "blocked" if not coverage["complete"] else "minor_revision",
                "primary_story": "mock mode: not evaluated",
                "primary_result": "mock mode: not evaluated",
                "positive_findings": [],
                "issues": [],
                "summary": "Mock mode produced an empty issue matrix; no scientific review was performed.",
            },
            ensure_ascii=False,
            indent=2,
        )
    profile = _load_journal_profile(venue) or f"(No journal profile found for {venue}; use general standards.)"
    protocol = REVIEW_PROTOCOL_PATH.read_text(encoding="utf-8", errors="replace") if REVIEW_PROTOCOL_PATH.exists() else ""
    prompt = f"""You are a rigorous journal reviewer. Review the supplied manuscript as a scientific argument.
Return one JSON object and no Markdown. Use this schema:
{{
  "schema_version": "paper_harness.review.v2",
  "venue": "{venue}",
  "manuscript": "{manuscript}",
  "manuscript_sha256": "{digest}",
  "coverage": {json.dumps(coverage, ensure_ascii=False)},
  "decision": "accept|minor_revision|major_revision|reject|blocked",
  "primary_story": "one sentence",
  "primary_result": "one sentence with scope",
  "positive_findings": ["..."],
  "issues": [
    {{
      "id": "I001",
      "type": "one taxonomy value",
      "dimension": "novelty|soundness|experiments|statistics|reproducibility|related_work|clarity|ethics|submission",
      "severity": "blocker|major|minor|advisory",
      "location": "section/table/figure/line cue",
      "manuscript_evidence": "what the paper actually says or reports",
      "reviewer_inference": "why this is a problem under the venue profile",
      "required_action": "specific evidence-preserving correction",
      "acceptance_test": "observable condition for closure",
      "evidence_boundary": "the strongest conclusion licensed after closure"
    }}
  ],
  "claim_map": [
    {{"claim": "...", "method_support": "...", "experiment_support": "...", "status": "supported|partial|unsupported|blocked"}}
  ],
  "summary": "concise review"
}}

Do not penalize a scientifically informative negative result or absence of SOTA. Do penalize claim/evidence mismatch,
unfair comparison, missing controls, statistical over-interpretation, stale artifact QA, and narrative dominated by audit history.
Do not invent missing facts or citations. If the full manuscript was not supplied, mark coverage-sensitive conclusions blocked.
If a bibliography, dataset, code asset, or external source was not supplied, describe that item as unverified or blocked;
do not assign a major scientific defect solely because external verification is outside the supplied evidence. Use major/blocker
only when the manuscript itself has unresolved citations, contradictory metadata, or a load-bearing claim that cannot be evaluated.

## Reviewer protocol
{protocol}

## Cross-paper experience contract and issue taxonomy
{_experience_text()}

{profile}

## Manuscript coverage
{json.dumps(coverage, ensure_ascii=False, indent=2)}

## Manuscript
{manuscript_text}
"""
    code, out = transport.codex_exec(prompt, cwd=paper_dir, sandbox="read-only", model=model, command=command)
    if code != 0:
        raise RuntimeError(f"reviewer call failed (exit {code}):\n{out[:2000]}")
    data = _extract_json(out)
    data["schema_version"] = "paper_harness.review.v2"
    data["venue"] = venue
    data["manuscript"] = manuscript
    data["manuscript_sha256"] = digest
    data["coverage"] = coverage
    return json.dumps(data, ensure_ascii=False, indent=2)


def attribute(stage: dict, scene: str, paper_dir: str | Path, model: str | None, command: str) -> str:
    """Classify a blocked stage without mutating the project."""
    paper_dir = Path(paper_dir)
    if transport.is_mock():
        return (
            f"# Attribution (MOCK) - stage {stage['id']}\n\n"
            "No CLI was called.\n\n## Scene\n\n```\n" + scene[:2000] + "\n```\n"
        )
    prompt = f"""You are the attribution analyst for a blocked academic-paper stage.
Produce Markdown with: (1) proximate cause, (2) root cause, (3) classification as manuscript/evidence,
executor, harness, environment, or human-input blocker, (4) safe recovery, and (5) a harness improvement proposal.
Never propose bypassing the Hard Gate or fabricating missing scientific evidence.

## Stage
```json
{json.dumps(stage, ensure_ascii=False, indent=2)}
```

## Preserved scene
{scene}
"""
    code, out = transport.codex_exec(prompt, cwd=paper_dir, sandbox="read-only", model=model, command=command)
    if code != 0:
        raise RuntimeError(f"attribution call failed (exit {code}):\n{out[:2000]}")
    return out.strip()
