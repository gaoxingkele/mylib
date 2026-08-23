#!/usr/bin/env python3
"""Deterministic structural regression checks for an IdeaSpark run dir.

Usage:
    python3 scripts/regression_check.py <run_dir> [<run_dir> ...]

Checks PROPERTY-level structure only (see references/regression-directions.md);
judgment-level criteria are out of scope here. Grandfather rule: fields
introduced by later skill versions (strength_grade, dry_run.execution,
alias_terms, composition_note) are checked for VALIDITY when present, never
demanded from runs produced before they existed.

Exit code 0 = all green; 1 = at least one FAIL.
"""
import json
import sys
from pathlib import Path

VALID_COHERENCE_VERDICTS = {"pass", "patched"}
VALID_T5_VERDICTS = {"confronts_obstacle", "equivalent_to_naive", "n_a"}
VALID_GRADES = {"established", "conditional", "overclaim", "empirical"}
VALID_ARBITRATIONS = {"executed-mc", "argument", "proof-obligations"}
VALID_THREADS = {"shared_object", "shared_question", "sequential_pipeline",
                 "shared_audit", "shared_evaluation", "n_a"}
CANDIDATE_REQUIRED = ["title", "gap_closure", "core_mechanism",
                      "core_mechanism_reasoning", "core_mechanism_steps",
                      "falsification_prediction", "compute_budget",
                      "signature_terms"]


def load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        return {"__load_error__": str(exc)}


class Report:
    def __init__(self, run_dir):
        self.run_dir = run_dir
        self.fails = []
        self.warns = []
        self.oks = 0

    def fail(self, msg):
        self.fails.append(msg)

    def warn(self, msg):
        self.warns.append(msg)

    def ok(self):
        self.oks += 1

    def check(self, cond, msg):
        if cond:
            self.ok()
        else:
            self.fail(msg)


def check_candidate(rep, cand, label):
    if "__load_error__" in cand:
        rep.fail(f"{label}: unreadable JSON ({cand['__load_error__']})")
        return
    for field in CANDIDATE_REQUIRED:
        rep.check(bool(cand.get(field)), f"{label}: missing/empty `{field}`")
    gc = cand.get("gap_closure") or []
    rep.check(1 <= len(gc) <= 3,
              f"{label}: gap_closure has {len(gc)} entries (expected 1-3)")
    patterns = set()
    for i, g in enumerate(gc):
        for field in ("gap", "main_pattern", "sub_pattern", "how_closed"):
            rep.check(bool(g.get(field)),
                      f"{label}: gap_closure[{i}] missing `{field}`")
        if g.get("main_pattern"):
            patterns.add(g["main_pattern"])
        if g.get("companion_pattern"):
            patterns.add(g["companion_pattern"])
    if len(patterns) == 1:
        note = (cand.get("composition_note") or "").strip()
        rep.check(bool(note),
                  f"{label}: single distinct pattern but composition_note "
                  "is empty (pattern-count commitment)")
    reasoning = cand.get("core_mechanism_reasoning") or ""
    # BLOCK structure introduced with the naive-audit version; warn-only when absent.
    if "NAIVE" not in reasoning.upper():
        rep.warn(f"{label}: core_mechanism_reasoning has no naive-baseline "
                 "audit marker (pre-audit-era run?)")
    else:
        rep.ok()
    if "alias_terms" in cand:
        rep.check(isinstance(cand["alias_terms"], list),
                  f"{label}: alias_terms present but not a list")


def check_coherence(rep, run_dir):
    cpath = run_dir / "phase2_coherence" / "phase2_coherence_output.json"
    if not cpath.exists():
        rep.warn("no phase2_coherence output (pre-2.3 run or not yet reached)")
        return
    coh = load(cpath)
    if "__load_error__" in coh:
        rep.fail(f"coherence: unreadable JSON ({coh['__load_error__']})")
        return
    verdict = coh.get("verdict")
    rep.check(verdict in VALID_COHERENCE_VERDICTS,
              f"coherence: invalid verdict {verdict!r}")
    revisions = coh.get("applied_revisions") or []
    if verdict == "pass":
        rep.check(not revisions,
                  "coherence: verdict=pass but applied_revisions non-empty")
    if verdict == "patched":
        rep.check((run_dir / "phase2_coherence" / "refined_candidate.json").exists(),
                  "coherence: verdict=patched but refined_candidate.json missing "
                  "(merger not run — canonical candidate is broken)")
    tr = coh.get("trace_report") or {}
    dry = tr.get("dry_run") or {}
    rep.check(bool(dry.get("computed_quantities")),
              "coherence: dry_run has no computed_quantities (T2 not executed)")
    execution = dry.get("execution")
    if execution is not None:
        rep.check(execution.get("mode") in {"executed", "unexecuted"},
                  f"coherence: dry_run.execution.mode invalid: "
                  f"{execution.get('mode')!r}")
        if execution.get("mode") == "executed":
            rep.check(bool(execution.get("script")) and bool(execution.get("output")),
                      "coherence: execution.mode=executed but script/output missing")
    csm = tr.get("claim_step_map") or []
    rep.check(bool(csm), "coherence: claim_step_map empty (T4 not run)")
    for i, entry in enumerate(csm):
        rep.check(bool(entry.get("claim")) and bool(entry.get("established_by")),
                  f"coherence: claim_step_map[{i}] missing claim/established_by")
        grade = entry.get("strength_grade")
        if grade is not None:
            rep.check(grade in VALID_GRADES,
                      f"coherence: claim_step_map[{i}] invalid strength_grade "
                      f"{grade!r}")
            arb = entry.get("arbitration")
            rep.check(arb in VALID_ARBITRATIONS,
                      f"coherence: claim_step_map[{i}] graded but arbitration "
                      f"invalid: {arb!r}")
            if arb == "executed-mc":
                rep.check(entry.get("measured") not in (None, "", "null"),
                          f"coherence: claim_step_map[{i}] arbitration="
                          "executed-mc but no measured number")
    nc = tr.get("naive_comparison")
    if nc is None:
        rep.warn("coherence: no naive_comparison (pre-T5 run?)")
    else:
        rep.check(nc.get("verdict") in VALID_T5_VERDICTS,
                  f"coherence: T5 verdict invalid: {nc.get('verdict')!r}")
        rep.check(bool(nc.get("reasoning")),
                  "coherence: T5 verdict has empty reasoning "
                  "(n_a without a reason is fabrication-adjacent)")
        if nc.get("verdict") in {"confronts_obstacle", "equivalent_to_naive"}:
            beh = nc.get("instance_behavior") or {}
            rep.check(bool(beh.get("divergence")),
                      "coherence: T5 comparative verdict without a divergence "
                      "value")
    for i, u in enumerate(coh.get("unrepaired") or []):
        rep.check(u.get("severity") in {"blocking", "note"},
                  f"coherence: unrepaired[{i}] invalid severity "
                  f"{u.get('severity')!r}")


def check_select(rep, run_dir):
    spath = run_dir / "phase2_select" / "phase2_select_output.json"
    if not spath.exists():
        rep.warn("no phase2_select output")
        return
    sel = load(spath)
    if "__load_error__" in sel:
        rep.fail(f"select: unreadable JSON ({sel['__load_error__']})")
        return
    gaps = sel.get("selected_gaps") or []
    rep.check(1 <= len(gaps) <= 3,
              f"select: {len(gaps)} selected_gaps (expected 1-3)")
    thread = sel.get("coherence_thread_type")
    rep.check(thread in VALID_THREADS,
              f"select: invalid coherence_thread_type {thread!r}")
    if len(gaps) == 1:
        rep.check(thread == "n_a",
                  "select: anchor-only selection must declare "
                  "coherence_thread_type n_a")


def check_run(run_dir):
    rep = Report(run_dir)
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        rep.fail("run dir does not exist")
        return rep
    check_select(rep, run_dir)
    gpath = run_dir / "phase2_generate" / "phase2_generate_output.json"
    if gpath.exists():
        check_candidate(rep, load(gpath), "phase2_generate")
    else:
        rep.warn("no phase2_generate output (run not yet reached 2.2)")
    check_coherence(rep, run_dir)
    rpath = run_dir / "phase2_coherence" / "refined_candidate.json"
    if rpath.exists():
        check_candidate(rep, load(rpath), "refined_candidate")
    return rep


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    any_fail = False
    for arg in argv[1:]:
        rep = check_run(arg)
        status = "FAIL" if rep.fails else "GREEN"
        any_fail = any_fail or bool(rep.fails)
        print(f"[{status}] {arg}  ({rep.oks} checks ok, "
              f"{len(rep.fails)} failed, {len(rep.warns)} warnings)")
        for m in rep.fails:
            print(f"  FAIL: {m}")
        for m in rep.warns:
            print(f"  warn: {m}")
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
