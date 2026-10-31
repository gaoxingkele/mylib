#!/usr/bin/env python3
"""Skill-RSI CLI: init, targets, propose, gate, admit, reject, status.

Deterministic gates only. No model calls. LLM agents propose; this script credits.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None


SKILL_ROOT = Path(__file__).resolve().parents[1]
DEFAULTS_PATH = SKILL_ROOT / "config" / "defaults.json"
CATALOG_PATH = SKILL_ROOT / "config" / "catalog.yaml"
TEMPLATE_PATH = SKILL_ROOT / "templates" / "candidate_card.md"
GENE_BANK_DIR = SKILL_ROOT / "gene_bank"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_defaults() -> dict[str, Any]:
    return load_json(DEFAULTS_PATH)


def load_catalog() -> dict[str, Any]:
    if yaml is None:
        raise SystemExit("PyYAML is required: pip install pyyaml")
    return yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8"))


def workspace(root: Path, defaults: dict[str, Any]) -> Path:
    return root / str(defaults["workspace_dir"])


def append_archive(ws: Path, defaults: dict[str, Any], event: dict[str, Any]) -> None:
    path = ws / str(defaults["archive_name"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def default_constitution(project: str) -> dict[str, Any]:
    return {
        "project": project,
        "mutable_surfaces": ["prompt", "skill", "harness", "context"],
        "protected": [
            {
                "path": ".skillrsi/constitution.json",
                "human": True,
                "note": "Constitution is human-edited only.",
            },
            {
                "path": "proposal-writing/scripts/validate_review_basis.py",
                "human": True,
                "note": "Proposal basis applicability gate stays frozen.",
            },
            {
                "path": "proposal-writing/references/review-revise.md",
                "note": "No funding probabilities or official panel scores from evolution.",
            },
            {
                "path": "paa/agents/cn-patent-examiner.toml",
                "note": "Claim-term anchor contract stays frozen.",
            },
            {
                "path": "Paper_CCF/scripts/audit_review_numbers.py",
                "note": "Numeric audit helper stays frozen.",
            },
        ],
        "invariants": [
            "Evaluator scripts and legal/guide contracts do not self-modify under Skill-RSI.",
            "Each candidate mutates exactly one surface: prompt, skill, harness, or context.",
            "Paper, proposal, and patent outer scores are never averaged into one release score.",
            "Model judgments alone cannot unlock reportable:true or rewrite protected paths.",
            "Synthetic or miniset scores remain reportable:false unless a human sets human_unlock.",
        ],
    }


def cmd_init(root: Path, defaults: dict[str, Any]) -> int:
    ws = workspace(root, defaults)
    if (ws / "constitution.json").exists():
        print(f"already initialized: {ws}")
        return 0
    dump_json(ws / "constitution.json", default_constitution(str(root)))
    (ws / str(defaults["candidates_dir"])).mkdir(parents=True, exist_ok=True)
    wiki = ws / str(defaults["wiki_dir"])
    wiki.mkdir(parents=True, exist_ok=True)
    (wiki / "README.md").write_text(
        "# Skill-RSI workspace\n\nRun `skillrsi.py status` for archive summary.\n",
        encoding="utf-8",
    )
    (ws / str(defaults["archive_name"])).write_text("", encoding="utf-8")
    append_archive(
        ws,
        defaults,
        {"event": "init", "at": utc_now(), "root": str(root)},
    )
    print(f"initialized {ws}")
    return 0


def cmd_targets(root: Path) -> int:
    catalog = load_catalog()
    missing = 0
    for item in catalog.get("targets", []):
        path = root / item["path"]
        exists = path.is_file()
        if not exists:
            missing += 1
        flag = "OK" if exists else "MISSING"
        print(
            f"{flag}\t{item['id']}\tdomain={item['domain']}\tevolved={item.get('evolved')}\t{item['path']}"
        )
    return 1 if missing else 0


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return (slug[:48] or "candidate")


def cmd_propose(root: Path, defaults: dict[str, Any], args: argparse.Namespace) -> int:
    ws = workspace(root, defaults)
    if not (ws / "constitution.json").exists():
        raise SystemExit("workspace missing; run init first")
    catalog = {item["id"]: item for item in load_catalog().get("targets", [])}
    if args.target not in catalog:
        raise SystemExit(f"unknown target: {args.target}")
    if args.surface not in defaults["surfaces"]:
        raise SystemExit(f"invalid surface: {args.surface}")
    if args.where and args.where not in {
        "prompt",
        "skill",
        "harness",
        "context",
        "knowledge",
        "runtime",
        "config",
    }:
        raise SystemExit(f"invalid pathology where: {args.where}")
    notes_path = args.notes_path
    if notes_path:
        note = Path(notes_path)
        if not note.is_file():
            raise SystemExit(f"notes_path not found: {notes_path}")
    candidate_id = args.candidate_id or f"{_slug(args.title)}-{uuid4().hex[:8]}"
    cand_path = ws / str(defaults["candidates_dir"]) / f"{candidate_id}.json"
    if cand_path.exists():
        raise SystemExit(f"candidate already exists: {candidate_id}")
    touched = [item.strip() for item in (args.touched_paths or "").split(",") if item.strip()]
    payload = {
        "candidate_id": candidate_id,
        "target_id": args.target,
        "surface": args.surface,
        "title": args.title,
        "beacon": args.beacon,
        "parent_id": args.parent_id or "none",
        "pathology": {
            "where": args.where or args.surface,
            "why": args.why or args.title,
        },
        "notes_path": notes_path,
        "touched_paths": touched,
        "metrics": None,
        "reportable": bool(args.reportable),
        "human_unlock": bool(args.human_unlock),
        "status": "proposed",
        "gate_receipt": None,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "decision_by": None,
        "decision_reason": None,
    }
    if args.metrics_json:
        payload["metrics"] = load_json(Path(args.metrics_json))
    dump_json(cand_path, payload)
    append_archive(
        ws,
        defaults,
        {"event": "propose", "at": utc_now(), "candidate_id": candidate_id, "target_id": args.target},
    )
    print(candidate_id)
    return 0


def _load_candidate(ws: Path, defaults: dict[str, Any], candidate_id: str) -> tuple[Path, dict[str, Any]]:
    path = ws / str(defaults["candidates_dir"]) / f"{candidate_id}.json"
    if not path.is_file():
        raise SystemExit(f"candidate not found: {candidate_id}")
    return path, load_json(path)


def run_gates(
    root: Path,
    defaults: dict[str, Any],
    constitution: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    catalog = {item["id"]: item for item in load_catalog().get("targets", [])}
    results: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        results.append({"gate": name, "pass": ok, "detail": detail})

    # validity
    target = catalog.get(candidate.get("target_id"))
    if target is None:
        add("validity", False, "target_id not in catalog")
    elif candidate.get("surface") not in defaults["surfaces"]:
        add("validity", False, "surface not allowed")
    elif not isinstance(candidate.get("beacon"), str) or len(candidate["beacon"]) < int(
        defaults["min_beacon_chars"]
    ):
        add("validity", False, "beacon too short")
    elif candidate.get("surface") not in constitution.get("mutable_surfaces", []):
        add("validity", False, "surface blocked by constitution")
    else:
        target_path = root / target["path"]
        add("validity", target_path.is_file(), f"target path {target['path']}")

    # frozen_intact
    protected = {item["path"] for item in constitution.get("protected", [])}
    touched = set(candidate.get("touched_paths") or [])
    collisions = sorted(protected & touched)
    add(
        "frozen_intact",
        not collisions,
        "ok" if not collisions else f"touched protected: {', '.join(collisions)}",
    )

    # activation
    notes = candidate.get("notes_path")
    notes_ok = bool(notes) and Path(str(notes)).is_file()
    metrics = candidate.get("metrics") or {}
    has_metrics = bool(metrics.get("candidate_scores"))
    add(
        "activation",
        notes_ok or has_metrics or bool(candidate.get("beacon")),
        "notes or metrics or beacon present",
    )

    # domain_floors
    floors = (metrics.get("parent_floors") or {}) if isinstance(metrics, dict) else {}
    scores = (metrics.get("candidate_scores") or {}) if isinstance(metrics, dict) else {}
    if not floors and not scores:
        add("domain_floors", True, "metrics absent; structural gates only")
    else:
        regressions = []
        for key, floor in floors.items():
            if key not in scores:
                regressions.append(f"missing score for {key}")
                continue
            if float(scores[key]) + 1e-9 < float(floor):
                regressions.append(f"{key}: {scores[key]} < floor {floor}")
        add("domain_floors", not regressions, "ok" if not regressions else "; ".join(regressions))

    # reportable_discipline
    if candidate.get("reportable") and not candidate.get("human_unlock"):
        add("reportable_discipline", False, "reportable:true requires human_unlock:true")
    else:
        add("reportable_discipline", True, "ok")

    passed = all(item["pass"] for item in results)
    return {
        "passed": passed,
        "gates": results,
        "checked_at": utc_now(),
    }


def cmd_gate(root: Path, defaults: dict[str, Any], candidate_id: str) -> int:
    ws = workspace(root, defaults)
    path, candidate = _load_candidate(ws, defaults, candidate_id)
    constitution = load_json(ws / "constitution.json")
    receipt = run_gates(root, defaults, constitution, candidate)
    candidate["gate_receipt"] = receipt
    candidate["status"] = "gated_pass" if receipt["passed"] else "gated_fail"
    candidate["updated_at"] = utc_now()
    dump_json(path, candidate)
    append_archive(
        ws,
        defaults,
        {
            "event": "gate",
            "at": utc_now(),
            "candidate_id": candidate_id,
            "passed": receipt["passed"],
            "gates": receipt["gates"],
        },
    )
    for item in receipt["gates"]:
        mark = "PASS" if item["pass"] else "FAIL"
        print(f"{mark}\t{item['gate']}\t{item['detail']}")
    print("RESULT", "PASS" if receipt["passed"] else "FAIL")
    return 0 if receipt["passed"] else 2


def _render_card(candidate: dict[str, Any], bank_decision: str) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    receipt = candidate.get("gate_receipt") or {}
    rows = receipt.get("gates") or []
    if rows:
        gate_table = "| Gate | Result | Detail |\n|---|---|---|\n"
        gate_table += "\n".join(
            f"| {row['gate']} | {'PASS' if row['pass'] else 'FAIL'} | {row['detail']} |"
            for row in rows
        )
    else:
        gate_table = "_No gate receipt._"
    metrics = candidate.get("metrics")
    metrics_block = (
        "```json\n" + json.dumps(metrics, ensure_ascii=False, indent=2) + "\n```"
        if metrics
        else "_metrics absent_"
    )
    pathology = candidate.get("pathology") or {}
    return (
        template.replace("{{title}}", str(candidate.get("title", "")))
        .replace("{{candidate_id}}", str(candidate.get("candidate_id", "")))
        .replace("{{target_id}}", str(candidate.get("target_id", "")))
        .replace("{{surface}}", str(candidate.get("surface", "")))
        .replace("{{parent_id}}", str(candidate.get("parent_id", "")))
        .replace("{{status}}", str(candidate.get("status", "")))
        .replace("{{reportable}}", str(candidate.get("reportable", False)))
        .replace("{{where}}", str(pathology.get("where", "")))
        .replace("{{why}}", str(pathology.get("why", "")))
        .replace("{{beacon}}", str(candidate.get("beacon", "")))
        .replace("{{gate_table}}", gate_table)
        .replace("{{metrics_block}}", metrics_block)
        .replace("{{decision_by}}", str(candidate.get("decision_by") or ""))
        .replace("{{decision_reason}}", str(candidate.get("decision_reason") or ""))
        .replace("{{bank_decision}}", bank_decision)
    )


def cmd_admit(root: Path, defaults: dict[str, Any], args: argparse.Namespace) -> int:
    ws = workspace(root, defaults)
    path, candidate = _load_candidate(ws, defaults, args.candidate_id)
    if candidate.get("status") != "gated_pass":
        raise SystemExit("candidate must be gated_pass before admit; run gate")
    if defaults.get("require_human_on_admit") and not args.by:
        raise SystemExit("--by is required for admit")
    candidate["status"] = "admitted"
    candidate["decision_by"] = args.by
    candidate["decision_reason"] = args.reason or "admitted after gated_pass"
    candidate["updated_at"] = utc_now()
    dump_json(path, candidate)
    card = _render_card(
        candidate,
        "Admit to Skill-RSI gene bank as an elite/reusable patch for the named target. "
        "Do not treat synthetic metrics as reportable unless human_unlock was set.",
    )
    out = GENE_BANK_DIR / f"{candidate['candidate_id']}.md"
    out.write_text(card + "\n", encoding="utf-8")
    append_archive(
        ws,
        defaults,
        {
            "event": "admit",
            "at": utc_now(),
            "candidate_id": candidate["candidate_id"],
            "by": args.by,
            "card": str(out),
        },
    )
    print(out)
    return 0


def cmd_reject(root: Path, defaults: dict[str, Any], args: argparse.Namespace) -> int:
    ws = workspace(root, defaults)
    path, candidate = _load_candidate(ws, defaults, args.candidate_id)
    if not args.reason:
        raise SystemExit("--reason is required for reject")
    if defaults.get("require_human_on_admit") and not args.by:
        raise SystemExit("--by is required for reject")
    # Allow reject from proposed/gated_fail/gated_pass
    candidate["status"] = "rejected"
    candidate["decision_by"] = args.by
    candidate["decision_reason"] = args.reason
    candidate["updated_at"] = utc_now()
    if candidate.get("gate_receipt") is None:
        constitution = load_json(ws / "constitution.json")
        candidate["gate_receipt"] = run_gates(root, defaults, constitution, candidate)
    dump_json(path, candidate)
    card = _render_card(
        candidate,
        "Keep as a negative / do-not-recombine card unless pathology is explicitly rematched "
        "and a new candidate clears gates.",
    )
    out = GENE_BANK_DIR / f"{candidate['candidate_id']}-reject.md"
    out.write_text(card + "\n", encoding="utf-8")
    append_archive(
        ws,
        defaults,
        {
            "event": "reject",
            "at": utc_now(),
            "candidate_id": candidate["candidate_id"],
            "by": args.by,
            "reason": args.reason,
            "card": str(out),
        },
    )
    print(out)
    return 0


def cmd_status(root: Path, defaults: dict[str, Any]) -> int:
    ws = workspace(root, defaults)
    if not ws.exists():
        print("not initialized")
        return 1
    cand_dir = ws / str(defaults["candidates_dir"])
    counts: dict[str, int] = {}
    for path in sorted(cand_dir.glob("*.json")):
        status = load_json(path).get("status", "unknown")
        counts[status] = counts.get(status, 0) + 1
    archive = ws / str(defaults["archive_name"])
    events = 0
    if archive.is_file():
        events = sum(1 for line in archive.read_text(encoding="utf-8").splitlines() if line.strip())
    print(f"workspace\t{ws}")
    print(f"archive_events\t{events}")
    print(f"gene_bank_cards\t{len(list(GENE_BANK_DIR.glob('*.md'))) - 1}")  # minus README
    for key in sorted(counts):
        print(f"candidates_{key}\t{counts[key]}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Skill-RSI: gated evolution for mylib skills")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project or mylib root")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="create .skillrsi workspace")
    sub.add_parser("targets", help="list catalog targets and path existence")
    sub.add_parser("status", help="summarize workspace and gene bank")

    propose = sub.add_parser("propose", help="register a candidate")
    propose.add_argument("--target", required=True)
    propose.add_argument("--surface", required=True, choices=["prompt", "skill", "harness", "context"])
    propose.add_argument("--title", required=True)
    propose.add_argument("--beacon", required=True)
    propose.add_argument("--parent-id", default="none")
    propose.add_argument("--where", default=None)
    propose.add_argument("--why", default=None)
    propose.add_argument("--notes-path", default=None)
    propose.add_argument("--touched-paths", default="", help="comma-separated paths relative to root")
    propose.add_argument("--metrics-json", default=None)
    propose.add_argument("--candidate-id", default=None)
    propose.add_argument("--reportable", action="store_true")
    propose.add_argument("--human-unlock", action="store_true")

    gate = sub.add_parser("gate", help="run deterministic gates")
    gate.add_argument("--candidate-id", required=True)

    admit = sub.add_parser("admit", help="admit gated_pass candidate to gene bank")
    admit.add_argument("--candidate-id", required=True)
    admit.add_argument("--by", required=True)
    admit.add_argument("--reason", default="")

    reject = sub.add_parser("reject", help="reject candidate and write negative card")
    reject.add_argument("--candidate-id", required=True)
    reject.add_argument("--by", required=True)
    reject.add_argument("--reason", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root.resolve()
    defaults = load_defaults()
    if args.command == "init":
        return cmd_init(root, defaults)
    if args.command == "targets":
        return cmd_targets(root)
    if args.command == "status":
        return cmd_status(root, defaults)
    if args.command == "propose":
        return cmd_propose(root, defaults, args)
    if args.command == "gate":
        return cmd_gate(root, defaults, args.candidate_id)
    if args.command == "admit":
        return cmd_admit(root, defaults, args)
    if args.command == "reject":
        return cmd_reject(root, defaults, args)
    parser.error(f"unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
