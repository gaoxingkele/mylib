#!/usr/bin/env python
"""metaRSI v0: evidence ledger, verification tiers and admission control.

Standard library only. This directory holds code and defaults (config/); a
project that uses metaRSI keeps all of its state in its own .metarsi/ folder:

  constitution.json  written once by `init`, afterwards edited only by a person
  metarsi.db         SQLite. `events` is the append-only, hash-chained record;
                     the other tables are views rebuilt from it after each write
  wiki/              Markdown pages in the LLM-wiki style (README, graph, nodes,
                     trials, negatives, log, playbooks), rewritten from the
                     database after each write so people, agents and git diffs
                     can read what the database holds

What the tool decides and what it only records:
  decides  - the evidence tier of a trial (from where the rule was chosen and
             where it was scored, not from what the caller claims);
           - whether a planned read touches a reserved window, and whether a
             planned write touches a protected surface;
           - whether a proposed change has enough evidence to be put in front
             of a human. It never admits a change to a protected surface on
             its own.
           - on `tick`, whether the project should only keep learning in the
             background or start an evolution step, from what the record and
             the calendar say (never from a model's self-assessment).
  records  - episodes, trials, rejected ideas, pre-registered shadow rules,
             signals raised while the project runs, admission decisions, and
             every check that was run.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import NormalDist

# Strongest first. "formal" is a machine check (tests, exact reproduction);
# "judge" is any model's or person's opinion without an outcome behind it.
DEFAULTS = json.loads((Path(__file__).resolve().parents[1] / "config/defaults.json").read_text(encoding="utf-8"))
DEFAULT_TIERS = DEFAULTS["tiers"]
LEDGERS = ("windows", "trials", "negatives", "shadows", "admissions", "episodes", "signals", "modes", "models", "audit")
OPEN_END = "99999999"
GENESIS = "0" * 16

CONSTITUTION_TEMPLATE = {
    **DEFAULTS["constitution_template"],
    "tiers": DEFAULT_TIERS,
    "default_min_tier": DEFAULTS["default_min_tier"],
}

EVENTS_DDL = """CREATE TABLE IF NOT EXISTS events (
    seq INTEGER PRIMARY KEY AUTOINCREMENT, ledger TEXT NOT NULL, id TEXT NOT NULL, ts TEXT NOT NULL,
    by TEXT NOT NULL, data TEXT NOT NULL, prev TEXT NOT NULL, hash TEXT NOT NULL)"""
VIEWS = {
    "windows": ["name", "start", "end", "state", "note"],
    "trials": ["id", "ts", "by", "rule_id", "family", "question", "kind", "selected_on", "scored_on", "shadow", "tier",
               "n_compared", "metric", "effect", "t", "n_obs", "verdict", "artifacts", "wiki", "note"],
    "negatives": ["id", "ts", "by", "idea", "reason", "lesson", "trials", "wiki"],
    "shadows": ["id", "ts", "by", "rule", "rule_sha", "metric", "window", "min_matured", "primary", "note", "open",
                "outcome", "trial"],
    "admissions": ["id", "ts", "by", "surface", "summary", "evidence", "required_tier", "best_tier", "checks",
                   "decision", "decided_by", "reason"],
    "episodes": ["id", "ts", "by", "question", "answer", "open", "trials", "wiki"],
    "signals": ["id", "ts", "by", "kind", "name", "value", "note", "open", "resolution"],
    "modes": ["id", "ts", "by", "mode", "stage", "reasons", "needs_human"],
    "models": ["name", "role", "recipe", "recipe_sha", "trees", "market_gain", "flags", "note"],
    "model_blocks": ["model", "block", "relation", "metric", "value", "days", "fit_days", "scored_by", "profile"],
}


class Violation(Exception):
    pass


class Project:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        store = DEFAULTS["store"]
        self.dir = self.root / store["dir"]
        self.db_path = self.dir / store["database"]
        self.wiki_dir = self.dir / store["wiki"]
        self.dirty = False

    def db(self) -> sqlite3.Connection:
        self.dir.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.db_path)
        con.execute(EVENTS_DDL)
        return con

    # ---------------------------------------------------------------- files
    def constitution(self) -> dict:
        path = self.dir / "constitution.json"
        if not path.exists():
            raise SystemExit(f"no constitution at {path}; run `metarsi.py init --project {self.root}` first")
        return json.loads(path.read_text(encoding="utf-8"))

    def tiers(self) -> list[str]:
        return list(self.constitution().get("tiers") or DEFAULT_TIERS)

    def read(self, name: str) -> list[dict]:
        if not self.db_path.exists():
            return []
        with closing(self.db()) as con:
            rows = con.execute("SELECT data FROM events WHERE ledger = ? ORDER BY seq", (name,)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def append(self, name: str, record: dict, prefix: str, by: str = "agent", ts: str | None = None) -> dict:
        with closing(self.db()) as con:
            count = con.execute("SELECT COUNT(*) FROM events WHERE ledger = ?", (name,)).fetchone()[0]
            last = con.execute("SELECT hash FROM events WHERE ledger = ? ORDER BY seq DESC LIMIT 1", (name,)).fetchone()
            prev = last[0] if last else GENESIS
            record = {
                "id": record.get("id") or f"{prefix}{count + 1:04d}",
                "ts": ts or datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "by": by,
                **{k: v for k, v in record.items() if k not in ("id", "ts", "by", "prev") and v is not None},
            }
            data = json.dumps(record, ensure_ascii=False, sort_keys=True)
            digest = hashlib.sha256((prev + data).encode("utf-8")).hexdigest()[:16]
            con.execute("INSERT INTO events (ledger, id, ts, by, data, prev, hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (name, record["id"], record["ts"], by, data, prev, digest))
            con.commit()
        self.dirty = True
        return record

    def verify_chain(self) -> list[str]:
        if not self.db_path.exists():
            return []
        with closing(self.db()) as con:
            rows = con.execute("SELECT seq, ledger, data, prev, hash FROM events ORDER BY seq").fetchall()
        problems, last = [], {}
        for seq, ledger, data, prev, digest in rows:
            if prev != last.get(ledger, GENESIS) or hashlib.sha256((prev + data).encode("utf-8")).hexdigest()[:16] != digest:
                problems.append(f"{ledger} event seq {seq}: chain broken")
            last[ledger] = digest
        return problems

    def sync(self) -> None:
        """Rebuild the query tables and the wiki pages from the event record."""
        state = {
            "windows": list(self.windows().values()), "trials": self.read("trials"), "negatives": self.read("negatives"),
            "shadows": list(self.shadows().values()), "admissions": list(self.admissions().values()),
            "episodes": self.read("episodes"), "signals": list(self.signals().values()), "modes": self.read("modes"),
        }
        models = self.models()
        state["models"] = [{**m, "flags": model_flags(self, m)} for m in models.values()]
        state["model_blocks"] = [{"model": m["name"], **b} for m in models.values() for b in m["blocks"]]
        with closing(self.db()) as con:
            for table, columns in VIEWS.items():
                con.execute(f'DROP TABLE IF EXISTS "{table}"')
                con.execute(f'CREATE TABLE "{table}" ({", ".join(chr(34) + c + chr(34) for c in columns)})')
                for rec in state[table]:
                    values = [json.dumps(rec.get(c), ensure_ascii=False) if isinstance(rec.get(c), (list, dict))
                              else rec.get(c) for c in columns]
                    con.execute(f'INSERT INTO "{table}" VALUES ({", ".join("?" * len(columns))})', values)
            con.commit()
        render_wiki(self, state)
        self.dirty = False

    # ---------------------------------------------------------------- state
    def windows(self) -> dict[str, dict]:
        state: dict[str, dict] = {}
        for event in self.read("windows"):
            if event["op"] == "add":
                state[event["name"]] = {k: event.get(k) for k in ("name", "start", "end", "state", "note")}
            elif event["op"] == "set_state" and event["name"] in state:
                state[event["name"]]["state"] = event["state"]
        return state

    def shadows(self) -> dict[str, dict]:
        state: dict[str, dict] = {}
        for event in self.read("shadows"):
            if event["op"] == "add":
                state[event["id"]] = {**event, "open": True}
            elif event["op"] == "close" and event["ref"] in state:
                state[event["ref"]].update(open=False, outcome=event.get("outcome"), trial=event.get("trial"))
        return state

    def signals(self) -> dict[str, dict]:
        state: dict[str, dict] = {}
        for event in self.read("signals"):
            if event["op"] == "add":
                state[event["id"]] = {**event, "open": True}
            elif event["op"] == "resolve" and event["ref"] in state:
                state[event["ref"]].update(open=False, resolution=event.get("note"))
        return state

    def models(self) -> dict[str, dict]:
        state: dict[str, dict] = {}
        for event in self.read("models"):
            if event["op"] == "register":
                old = state.get(event["name"], {})
                state[event["name"]] = {**{k: event.get(k) for k in ("name", "role", "recipe", "recipe_sha", "trees", "market_gain", "note")},
                                        "blocks": old.get("blocks", [])}
            elif event["op"] == "block" and event["model"] in state:
                blocks = [b for b in state[event["model"]]["blocks"] if b["block"] != event["block"]]
                blocks.append({k: event.get(k) for k in ("block", "relation", "metric", "value", "days", "fit_days", "scored_by", "profile")})
                state[event["model"]]["blocks"] = blocks
        return state

    def policy(self) -> dict:
        return {**DEFAULTS["policy"], **(self.constitution().get("policy") or {})}

    def matured(self, window: dict) -> int | None:
        """Signal days in the window whose outcome horizon has fully passed, from the project calendar."""
        cal = self.constitution().get("calendar") or {}
        if not cal.get("glob"):
            return None
        stems = sorted(path.stem for path in self.root.glob(cal["glob"]))
        horizon = int(cal.get("horizon", 0))
        end = window["end"] or OPEN_END
        return sum(1 for i, day in enumerate(stems) if window["start"] <= day <= end and i + horizon < len(stems))

    def admissions(self) -> dict[str, dict]:
        state: dict[str, dict] = {}
        for event in self.read("admissions"):
            if event["op"] == "propose":
                state[event["id"]] = dict(event)
            elif event["op"] == "decide" and event["ref"] in state:
                state[event["ref"]].update(decision=event["decision"], decided_by=event["by"], reason=event.get("reason"))
        return state

    def protected_rule(self, rel_path: str) -> dict | None:
        rel = rel_path.replace("\\", "/")
        for rule in self.constitution().get("protected", []):
            if fnmatch.fnmatch(rel, rule["path"]):
                return rule
        return None

    def relative(self, path: str) -> str:
        p = Path(path)
        if p.is_absolute():
            try:
                return p.resolve().relative_to(self.root).as_posix()
            except ValueError:
                return p.as_posix()
        return p.as_posix()

    # ---------------------------------------------------------------- logic
    def tier_of(self, kind: str, selected_on: str | None, scored_on: str | None, family: str, shadow: str | None) -> str:
        if kind in ("formal", "judge"):
            return kind
        if shadow:
            sh = self.shadows().get(shadow)
            if sh and sh["open"] and sh["window"] == scored_on:
                return "prospective"
        if selected_on and selected_on == scored_on:
            return "in_sample"
        earlier = [t for t in self.read("trials") if t.get("family") == family and t.get("scored_on") == scored_on]
        return "holdout_once" if not earlier else "reused_holdout"

    def stronger_or_equal(self, tier: str, required: str) -> bool:
        order = self.tiers()
        return order.index(tier) <= order.index(required)

    def check(self, read: str | None, writes: list[str], shadow: str | None, matured: int | None) -> list[str]:
        violations: list[str] = []
        if read:
            start, _, end = read.partition("..")
            end = end or OPEN_END
            for w in self.windows().values():
                if w["state"] != "reserved":
                    continue
                if start <= (w["end"] or OPEN_END) and end >= w["start"]:
                    sh = self.shadows().get(shadow or "")
                    if sh and sh["open"] and sh["window"] == w["name"] and (matured or 0) >= int(sh.get("min_matured") or 0):
                        continue
                    violations.append(
                        f"read {read} overlaps reserved window {w['name']} ({w['start']}..{w['end'] or ''}); "
                        "it may only be read to score an open shadow rule whose maturity is reached"
                    )
        admitted = {a["surface"] for a in self.admissions().values() if a.get("decision") == "admitted"}
        for path in writes:
            rel = self.relative(path)
            rule = self.protected_rule(rel)
            if rule and rel not in admitted and rule["path"] not in admitted:
                violations.append(f"write {rel} is a protected surface ({rule.get('note', rule['path'])}); needs an admitted proposal")
        return violations


def guard_read(project_root: str | Path, start: str, end: str = "") -> None:
    """For experiment scripts: raise if the date range touches a reserved window."""
    bad = Project(project_root).check(f"{start}..{end}", [], None, None)
    if bad:
        raise PermissionError("; ".join(bad))


def reserved_from(project_root: str | Path) -> str | None:
    """Earliest start date of any reserved window, or None."""
    starts = [w["start"] for w in Project(project_root).windows().values() if w["state"] == "reserved"]
    return min(starts) if starts else None


def emit_signal(project_root: str | Path, kind: str, name: str, note: str = "", value: float | None = None,
                by: str = "script") -> str:
    """For project scripts: report a failure, drift, request or opportunity while the project runs."""
    project = Project(project_root)
    rec = project.append("signals", {"op": "add", "kind": kind, "name": name, "note": note, "value": value}, "G", by)
    project.sync()
    return rec["id"]


def bonferroni_t(n: int) -> float:
    return NormalDist().inv_cdf(1 - 0.05 / (2 * max(n, 1)))


# ---------------------------------------------------------------- commands
def cmd_init(p: Project, a) -> int:
    p.dir.mkdir(parents=True, exist_ok=True)
    path = p.dir / "constitution.json"
    if path.exists():
        print(f"constitution already exists, left untouched: {path}")
    else:
        doc = dict(CONSTITUTION_TEMPLATE, project=a.name or p.root.name)
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"created {path}; edit it by hand to list the project's protected surfaces")
    p.sync()
    print(f"database {p.db_path}\nwiki     {p.wiki_dir}")
    return 0


def cmd_window(p: Project, a) -> int:
    if a.action == "add":
        if a.name in p.windows():
            raise SystemExit(f"window {a.name} already exists")
        p.append("windows", {"op": "add", "name": a.name, "start": a.start, "end": a.end or "", "state": a.state, "note": a.note}, "W", a.by)
    elif a.action == "set":
        if a.name not in p.windows():
            raise SystemExit(f"unknown window {a.name}")
        if p.windows()[a.name]["state"] == "reserved" and a.by == "agent":
            raise SystemExit("only a person releases a reserved window (pass --by <name>)")
        p.append("windows", {"op": "set_state", "name": a.name, "state": a.state, "note": a.note}, "W", a.by)
    for w in p.windows().values():
        print(f"{w['name']:28s} {w['start']}..{w['end'] or '':8s} {w['state']:9s} {w.get('note') or ''}")
    return 0


def cmd_trial(p: Project, a) -> int:
    windows = p.windows()
    if a.kind == "empirical":
        if a.scored_on not in windows:
            raise SystemExit(f"unknown window {a.scored_on}; add it with `window add` first")
        tier = p.tier_of(a.kind, a.selected_on, a.scored_on, a.family, a.shadow)
        if windows[a.scored_on]["state"] == "reserved" and tier != "prospective":
            p.append("audit", {"op": "refused_trial", "rule_id": a.rule_id, "window": a.scored_on}, "A", a.by)
            raise SystemExit(f"refused: {a.scored_on} is reserved and this trial is not the scoring of an open shadow rule")
    else:
        tier = a.kind
    artifacts = []
    for item in a.artifact or []:
        path = Path(item) if Path(item).is_absolute() else p.root / item
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16] if path.is_file() else None
        artifacts.append({"path": p.relative(item), "sha256": digest})
    family_n = sum(int(t.get("n_compared") or 1) for t in p.read("trials")
                   if t.get("family") == a.family and t.get("scored_on") == a.scored_on) + int(a.n_compared)
    rec = p.append("trials", {
        "rule_id": a.rule_id, "family": a.family, "question": a.question, "kind": a.kind,
        "selected_on": a.selected_on, "scored_on": a.scored_on, "shadow": a.shadow, "tier": tier,
        "n_compared": int(a.n_compared), "metric": a.metric, "effect": a.effect, "t": a.t, "n_obs": a.n_obs,
        "verdict": a.verdict, "artifacts": artifacts, "wiki": a.wiki, "note": a.note,
    }, "T", a.by)
    if a.kind == "empirical" and windows[a.scored_on]["state"] == "open":
        p.append("windows", {"op": "set_state", "name": a.scored_on, "state": "consumed", "note": f"first scored by {rec['id']}"}, "W", a.by)
    print(f"{rec['id']} tier={tier} verdict={a.verdict}")
    if a.kind == "empirical":
        print(f"rules compared so far in family '{a.family}' on {a.scored_on}: {family_n}; "
              f"|t| needed at 5% after Bonferroni: {bonferroni_t(family_n):.2f}")
        if not artifacts or any(x["sha256"] is None for x in artifacts):
            print("warning: no readable artifact attached; a result without a file behind it cannot be re-checked")
    return 0


def cmd_negative(p: Project, a) -> int:
    rec = p.append("negatives", {"idea": a.idea, "reason": a.reason, "lesson": a.lesson, "trials": a.trial, "wiki": a.wiki}, "N", a.by)
    print(rec["id"])
    return 0


def cmd_shadow(p: Project, a) -> int:
    if a.action == "add":
        if a.window not in p.windows():
            raise SystemExit(f"unknown window {a.window}")
        if a.primary and any(s["open"] and s.get("primary") and s["window"] == a.window for s in p.shadows().values()):
            raise SystemExit(f"window {a.window} already has an open primary shadow rule")
        rec = p.append("shadows", {
            "op": "add", "rule": a.rule, "rule_sha": hashlib.sha256(a.rule.encode("utf-8")).hexdigest()[:16],
            "metric": a.metric, "window": a.window, "min_matured": a.min_matured, "primary": bool(a.primary), "note": a.note,
        }, "S", a.by)
        print(rec["id"], "rule_sha", rec["rule_sha"])
    elif a.action == "close":
        if a.id not in p.shadows():
            raise SystemExit(f"unknown shadow {a.id}")
        p.append("shadows", {"op": "close", "id": None, "ref": a.id, "outcome": a.outcome, "trial": a.trial_id}, "S", a.by)
    for s in p.shadows().values():
        flag = "primary" if s.get("primary") else "       "
        state = "open  " if s["open"] else f"closed:{s.get('outcome')}"
        print(f"{s['id']} {state} {flag} window={s['window']} min_matured={s.get('min_matured')} | {s['rule']}")
    return 0


def cmd_check(p: Project, a) -> int:
    violations = p.check(a.read, a.write or [], a.shadow, a.matured)
    p.append("audit", {"op": "check", "read": a.read, "write": a.write, "shadow": a.shadow, "violations": violations}, "A", a.by)
    if violations:
        print("VIOLATION")
        for v in violations:
            print(" -", v)
        return 2
    print("OK")
    return 0


def cmd_propose(p: Project, a) -> int:
    surface = p.relative(a.surface)
    rule = p.protected_rule(surface) or {}
    required = rule.get("min_tier") or p.constitution().get("default_min_tier", "holdout_once")
    trials = {t["id"]: t for t in p.read("trials")}
    missing = [t for t in a.evidence or [] if t not in trials]
    if missing:
        raise SystemExit(f"unknown trial ids: {missing}")
    passing = [trials[t] for t in a.evidence or [] if trials[t].get("verdict") == "pass"]
    order = p.tiers()
    best = min((t["tier"] for t in passing), key=order.index, default=None)
    checks = []
    for item in a.check or []:
        name, _, result = item.partition("=")
        checks.append({"name": name, "passed": result.strip().lower() in ("pass", "passed", "ok", "true")})
    reasons = []
    if best is None:
        reasons.append("no passing trial among the evidence")
    elif not p.stronger_or_equal(best, required):
        reasons.append(f"best evidence tier is {best}; this surface needs {required} or stronger")
    reasons += [f"regression check failed: {c['name']}" for c in checks if not c["passed"]]
    if getattr(a, "model", None):
        m = p.models().get(a.model)
        if not m:
            reasons.append(f"model {a.model} is not registered")
        else:
            reasons += [f"model audit: {text}" for text in model_flags(p, m)]
    if reasons:
        decision = "rejected"
    elif rule.get("human", True):
        decision = "pending_human"
    else:
        decision = "admitted"
    rec = p.append("admissions", {
        "op": "propose", "surface": surface, "summary": a.summary, "evidence": a.evidence, "required_tier": required,
        "best_tier": best, "checks": checks, "decision": decision, "reasons": reasons,
    }, "P", a.by)
    print(f"{rec['id']} decision={decision} required={required} best={best}")
    for r in reasons:
        print(" -", r)
    return 0 if decision != "rejected" else 2


def cmd_decide(p: Project, a) -> int:
    adm = p.admissions().get(a.id)
    if not adm:
        raise SystemExit(f"unknown proposal {a.id}")
    if adm["decision"] != "pending_human":
        raise SystemExit(f"{a.id} is {adm['decision']}; only pending proposals can be decided")
    if a.by == "agent":
        raise SystemExit("a person decides; pass --by <name> and only on that person's explicit instruction")
    decision = "admitted" if a.approve else "rejected"
    p.append("admissions", {"op": "decide", "id": None, "ref": a.id, "decision": decision, "reason": a.reason}, "P", a.by)
    print(f"{a.id} {decision} by {a.by}")
    return 0


def cmd_episode(p: Project, a) -> int:
    rec = p.append("episodes", {"question": a.question, "answer": a.answer, "open": a.open, "trials": a.trial, "wiki": a.wiki}, "E", a.by)
    print(rec["id"])
    return 0


def cmd_search(p: Project, a) -> int:
    words = [w.lower() for w in a.words]
    hits = 0
    for name in ("negatives", "trials", "shadows", "episodes", "admissions"):
        for rec in p.read(name):
            text = json.dumps(rec, ensure_ascii=False).lower()
            if all(w in text for w in words):
                hits += 1
                brief = rec.get("idea") or rec.get("rule_id") or rec.get("rule") or rec.get("question") or rec.get("summary") or ""
                extra = rec.get("reason") or rec.get("verdict") or rec.get("answer") or rec.get("decision") or ""
                print(f"[{name}] {rec.get('id')} {brief} | {extra} | {rec.get('wiki') or ''}")
    print(f"{hits} match(es)")
    return 0


def calibration(p: Project) -> tuple[list[str], int, int]:
    """How often a result found at a weaker tier held up at a stronger one."""
    order = p.tiers()
    by_rule: dict[str, list[dict]] = {}
    for t in p.read("trials"):
        if t.get("t") is not None:
            by_rule.setdefault(t["rule_id"], []).append(t)
    lines, tested, held = [], 0, 0
    for rule_id, trials in sorted(by_rule.items()):
        for first in (t for t in trials if abs(float(t["t"])) >= 2):
            later = [t for t in trials if order.index(t["tier"]) < order.index(first["tier"])]
            if not later:
                continue
            strongest = min(later, key=lambda t: order.index(t["tier"]))
            ok = float(strongest["t"]) * float(first["t"]) > 0 and abs(float(strongest["t"])) >= 2
            tested += 1
            held += ok
            lines.append(f"{rule_id}: {first['tier']} t={float(first['t']):+.2f} ({first['scored_on']}) -> "
                         f"{strongest['tier']} t={float(strongest['t']):+.2f} ({strongest['scored_on']}) "
                         f"{'held' if ok else 'did not hold'}")
            break
    return lines, tested, held


def cmd_calibration(p: Project, a) -> int:
    lines, tested, held = calibration(p)
    for line in lines:
        print(line)
    print(f"significant at a weaker tier and re-scored at a stronger one: {tested}; held: {held}"
          + (f" ({100 * held / tested:.0f}%)" if tested else ""))
    return 0


# ---------------------------------------------------------------- models
def model_flags(p: Project, m: dict) -> list[str]:
    """What stands between a model's recorded evidence and trusting it on new data.

    The project measures and submits the facts (blocks, tree counts, gain shares, selection
    profile); this function only applies fixed rules to them.
    """
    rule = {**DEFAULTS["policy"]["model"], **((p.constitution().get("policy") or {}).get("model") or {})}
    flags = []
    blocks = m["blocks"]
    foreign = sorted({b["scored_by"] for b in blocks if b.get("scored_by") and b["scored_by"] != m["name"]})
    if foreign:
        flags.append(f"评估与上线不是同一个模型：有 {sum(1 for b in blocks if b.get('scored_by') in foreign)} 个区块的分数来自 {'、'.join(foreign)}")
    trees = [int(t) for t in (m.get("trees") or [])]
    if trees:
        if min(trees) < rule["min_trees"]:
            flags.append(f"有的子模型只有 {min(trees)} 棵树（下限 {rule['min_trees']}），早停可能塌缩")
        if min(trees) > 0 and max(trees) / min(trees) > rule["max_tree_ratio"]:
            flags.append(f"各次训练的树数相差 {max(trees) / min(trees):.0f} 倍（{min(trees)}～{max(trees)}），同一做法产出的不是同一类模型")
    fit_days = [b["fit_days"] for b in blocks if b.get("fit_days")] + ([m["fit_days"]] if m.get("fit_days") else [])
    if fit_days and min(fit_days) < rule["min_fit_days"]:
        flags.append(f"拟合窗口最短只有 {min(fit_days)} 个交易日（下限 {rule['min_fit_days']}）")
    oos = [b for b in blocks if b.get("relation") == "oos" and b.get("value") is not None and b.get("scored_by", m["name"]) == m["name"]]
    seen = [b for b in blocks if b.get("relation") in ("fit", "tune") and b.get("value") is not None]
    if len(oos) < rule["min_oos_blocks"]:
        flags.append(f"它自己打分的样本外区块只有 {len(oos)} 个（至少 {rule['min_oos_blocks']} 个）")
    if oos:
        share = sum(1 for b in oos if b["value"] > 0) / len(oos)
        if share < rule["min_oos_positive_share"]:
            flags.append(f"样本外区块里只有 {100 * share:.0f}% 为正")
        ordered = sorted(oos, key=lambda b: str(b["block"]))
        if len(ordered) >= 4:
            half = len(ordered) // 2
            early = sum(b["value"] for b in ordered[:half]) / half
            late = sum(b["value"] for b in ordered[half:]) / (len(ordered) - half)
            if early > 0 and late <= 0:
                flags.append(f"样本外前好后差：较早的区块平均 {early:+.2f}，最近的区块平均 {late:+.2f}，在最近的行情下不成立")
        if seen:
            inside = sum(b["value"] for b in seen) / len(seen)
            outside = sum(b["value"] for b in oos) / len(oos)
            if inside > 0 and outside < inside / 2:
                flags.append(f"拟合和调参窗口内平均 {inside:+.2f}，样本外平均 {outside:+.2f}，外推损失超过一半")
    if m.get("market_gain") is not None and float(m["market_gain"]) > rule["max_market_gain"]:
        flags.append(f"增益有 {100 * float(m['market_gain']):.0f}% 落在全市场同值的特征上，学的主要是日子的好坏")
    for b in blocks:
        prof = b.get("profile") or {}
        for key, value in prof.items():
            ref = prof.get(f"{key}_market")
            if ref is not None and abs(float(value) - float(ref)) > rule["profile_gap"]:
                flags.append(f"区块 {b['block']}：选出的股票 {key} 为 {float(value):.2f}，全市场 {float(ref):.2f}，偏向很重")
    return flags


def own_oos(m: dict) -> dict[str, float]:
    return {b["block"]: float(b["value"]) for b in m["blocks"]
            if b.get("relation") == "oos" and b.get("value") is not None and b.get("scored_by", m["name"]) == m["name"]}


def diagnose_models(p: Project) -> list[str]:
    """Where to spend the next effort: on how models are trained, or on something no training recipe fixes.

    Compares the registered models block by block, using only blocks each model scored itself and
    had not been fitted or tuned on. If structurally different models fail together, the cause is
    outside the recipe; if they fail in different blocks, they are complementary.
    """
    series = {name: own_oos(m) for name, m in p.models().items()}
    series = {k: v for k, v in series.items() if len(v) >= 3}
    if len(series) < 2:
        return ["登记了样本外区块的模型不到两个，无法比较。"]
    blocks = sorted({b for v in series.values() for b in v})
    lines = ["| 区块 | " + " | ".join(series) + " | 都算进来的均值 |", "|---|" + "---:|" * (len(series) + 1)]
    together, split, blend = [], [], []
    for b in blocks:
        vals = {n: v[b] for n, v in series.items() if b in v}
        if len(vals) < 2:
            continue
        mean = sum(vals.values()) / len(vals)
        blend.append(mean)
        lines.append(f"| {b} | " + " | ".join(f"{series[n][b]:+.2f}" if b in series[n] else "" for n in series) + f" | {mean:+.2f} |")
        if all(x <= 0 for x in vals.values()):
            together.append(b)
        elif any(x <= 0 for x in vals.values()):
            split.append((b, [n for n, x in vals.items() if x > 0]))
    lines.append("")
    for name, v in series.items():
        lines.append(f"- {name}：样本外区块 {len(v)} 个，为正 {sum(1 for x in v.values() if x > 0)} 个，最差 {min(v.values()):+.2f}，平均 {sum(v.values()) / len(v):+.2f}")
    if blend:
        lines.append(f"- 各模型等权合在一起：最差区块 {min(blend):+.2f}，平均 {sum(blend) / len(blend):+.2f}")
    lines.append("")
    if together:
        lines.append(f"判断一：{'、'.join(together)} 这些区块所有模型都不为正。做法不同的模型一起失效，原因在模型之外（行情），改训练做法解决不了，这部分该由仓位和风控去管。")
    if split:
        text = "；".join(f"{b} 只有 {'、'.join(win)} 为正" for b, win in split)
        lines.append(f"判断二：模型在不同区块失效（{text}）。它们是互补的，下一步该验证的假设是组合或按行情切换，而不是继续改单个模型的训练做法。")
    always = [n for n, v in series.items() if all(x > 0 for x in v.values())]
    if always:
        lines.append(f"判断三：{'、'.join(always)} 在自己的全部样本外区块都为正。")
    if not together and not split:
        lines.append("各模型在共同区块上同为正，没有需要区分的失效。")
    lines.append("以上只是把已登记的数字摆在一起的分类，不构成验证；任何新做法仍要登记成影子、在保留窗口上验。")
    return lines


def cmd_model(p: Project, a) -> int:
    if a.action == "diagnose":
        for line in diagnose_models(p):
            print(line)
        p.append("audit", {"op": "model_diagnose"}, "A", a.by)
        return 0
    if a.action == "register":
        if not a.name or not a.recipe:
            raise SystemExit("model register needs --name and --recipe")
        trees = [int(x) for x in a.trees.split(",")] if a.trees else None
        p.append("models", {"op": "register", "name": a.name, "role": a.role, "recipe": a.recipe,
                            "recipe_sha": hashlib.sha256(a.recipe.encode("utf-8")).hexdigest()[:16],
                            "trees": trees, "market_gain": a.market_gain, "note": a.note}, "D", a.by)
    elif a.action == "block":
        if a.name not in p.models():
            raise SystemExit(f"unknown model {a.name}; register it first")
        profile = {}
        for item in a.profile or []:
            key, _, value = item.partition("=")
            profile[key] = float(value)
        p.append("models", {"op": "block", "model": a.name, "block": a.block, "relation": a.relation, "metric": a.metric_name,
                            "value": a.value, "days": a.days, "fit_days": a.fit_days, "scored_by": a.scored_by or a.name,
                            "profile": profile or None}, "D", a.by)
    names = [a.name] if a.name and a.action == "audit" else list(p.models())
    for name in names:
        m = p.models().get(name)
        if not m:
            raise SystemExit(f"unknown model {name}")
        flags = model_flags(p, m)
        oos = [b for b in m["blocks"] if b.get("relation") == "oos" and b.get("value") is not None]
        print(f"{name} [{m.get('role')}] blocks {len(m['blocks'])} (样本外 {len(oos)}) -> {'通过' if not flags else f'{len(flags)} 条问题'}")
        if a.action in ("audit", "list"):
            for b in sorted(m["blocks"], key=lambda x: str(x["block"])):
                by = "" if b.get("scored_by") == name else f" 分数来自 {b.get('scored_by')}"
                print(f"    {b['block']:20s} {b.get('relation') or '':5s} {b.get('metric') or ''} {b['value'] if b.get('value') is not None else ''}{by}")
        for text in flags:
            print(f"  - {text}")
    if a.action == "audit":
        p.append("audit", {"op": "model_audit", "models": names}, "A", a.by)
    return 0


# ---------------------------------------------------------------- learn or evolve
MODE_TEXT = {
    ("learn", None): (
        "后台学习",
        "记录问答、试验和否决项；做描述性分析（只能算 in_sample 或 reused_holdout）；整理 wiki；可以把新想法登记成影子规则",
        "在已用过的窗口上搜新规则并当作验证；读保留窗口；改受保护面",
    ),
    ("evolve", "verify"): (
        "进化（验证阶段）",
        "只为到期的影子规则读一次保留窗口并计分（check --shadow），然后 trial log、shadow close；结果通过再 propose",
        "顺带在保留窗口上看别的规则；计分后回头改规则",
    ),
    ("evolve", "holdout"): (
        "进化（留出验证）",
        "在开发数据上把规则选定，由代码在未用过的窗口上计分一次；避开已经疲劳的类别",
        "看过留出窗口的结果后再调规则；读保留窗口",
    ),
    ("evolve", "shadow"): (
        "进化（只能登记影子）",
        "提出假设并 shadow add，等保留窗口成熟后再计分",
        "在已用过的窗口上宣称验证；读保留窗口",
    ),
}


def decide_mode(p: Project) -> dict:
    """learn = keep recording in the background; evolve = start an improvement step.

    Evolution needs two things at once: a reason (a shadow rule has come due, the
    user asked, or failures and drift have piled up) and a way to check the result
    that is stronger than looking at used data again. Without both, the answer is learn.
    """
    policy = p.policy()
    windows = p.windows()
    shadows = [s for s in p.shadows().values() if s["open"]]
    reasons, humans, ready = [], [], []
    open_windows = [w["name"] for w in windows.values() if w["state"] == "open"]
    reserved = [w for w in windows.values() if w["state"] == "reserved"]
    for w in reserved:
        here = [s for s in shadows if s["window"] == w["name"]]
        if not here:
            continue
        m = p.matured(w)
        if m is None:
            reasons.append(f"保留窗口 {w['name']}：宪法里没有配置日历，无法自动判断影子规则是否到期")
        else:
            gaps = [max(int(s.get("min_matured") or 0) - m, 0) for s in here]
            ready += [s for s, gap in zip(here, gaps) if gap == 0]
            text = f"保留窗口 {w['name']} 已成熟 {m} 个信号日；{len(here)} 条影子规则里 {sum(g == 0 for g in gaps)} 条到期"
            if any(gaps):
                text += f"，最近的一条还差 {min(g for g in gaps if g)} 个"
            reasons.append(text)
        if len(here) > 1 and not any(s.get("primary") for s in here):
            humans.append(f"{w['name']} 上有 {len(here)} 条影子规则但没有主规则，请用户指定")
    pending = [x for x in p.admissions().values() if x["decision"] == "pending_human"]
    if pending:
        humans.append(f"{len(pending)} 条提议等用户批准：" + "、".join(x["id"] for x in pending))

    cutoff = (datetime.now(timezone.utc) - timedelta(days=int(policy["alarm_lookback_days"]))).isoformat(timespec="seconds")
    live = [g for g in p.signals().values() if g["open"]]
    requests = [g for g in live if g["kind"] == "request"]
    alarms = [g for g in live if g["kind"] in ("failure", "drift") and g["ts"] >= cutoff]
    need = bool(requests) or len(alarms) >= int(policy["alarm_threshold"])

    by_family: dict[str, list[dict]] = {}
    for t in p.read("trials"):
        by_family.setdefault(t["family"], []).append(t)
    k = int(policy["fatigue_fails"])
    exhausted = sorted(f for f, ts in by_family.items() if len(ts) >= k and all(t["verdict"] != "pass" for t in ts[-k:]))
    _, tested, held = calibration(p)

    mode, stage, target = "learn", None, None
    named = [s for s in ready if s.get("primary")]
    if ready and (named or len(ready) == 1):
        mode, stage, target = "evolve", "verify", (named or ready)[0]["id"]
        reasons.append(f"影子规则 {target} 已到期，可以在保留窗口上计分一次")
    elif ready:
        reasons.append("有影子规则到期，但主规则未定，先不计分")
    elif need and open_windows:
        mode, stage = "evolve", "holdout"
        reasons.append(f"有待处理的信号，且有未用过的留出窗口：{'、'.join(open_windows)}")
    elif need and reserved and len(shadows) < int(policy["max_open_shadows"]):
        mode, stage = "evolve", "shadow"
        reasons.append("有待处理的信号，但没有未用过的留出窗口：新想法只能登记成影子规则")
    elif need:
        reasons.append("有待处理的信号，但没有未用过的留出窗口，影子规则也已到上限")
    else:
        reasons.append(f"没有需要处理的信号（用户请求 {len(requests)} 条；近 {policy['alarm_lookback_days']} 天故障或漂移 "
                       f"{len(alarms)} 条，阈值 {policy['alarm_threshold']}）")
    if not open_windows and stage != "verify":
        reasons.append("没有未用过的留出窗口，新规则在已用窗口上最多算 reused_holdout")
    if tested:
        reasons.append(f"校准：弱证据上显著、又到更强证据复验的结果 {tested} 条，成立 {held} 条")
    for m in p.models().values():
        if m.get("role") == "shipped":
            flags = model_flags(p, m)
            if flags:
                reasons.append(f"上线模型 {m['name']} 的审计有 {len(flags)} 条问题（model audit 查看），它的历史成绩要按问题打折")
                better = [c["name"] for c in p.models().values()
                          if c.get("role") == "candidate" and len(model_flags(p, c)) < len(flags)]
                if better:
                    reasons.append(f"审计问题更少的候选模型：{'、'.join(better)}。要替换先看 model diagnose，再登记成影子在保留窗口上并行验证")
    label, allowed, forbidden = MODE_TEXT[(mode, stage)]
    return {
        "mode": mode, "stage": stage, "label": label, "target": target, "reasons": reasons, "needs_human": humans,
        "exhausted": exhausted, "allowed": allowed, "forbidden": forbidden,
        "signals": [f"{g['id']} {g['kind']} {g['name']}" for g in live],
        "open_shadows": len(shadows), "max_open_shadows": int(policy["max_open_shadows"]),
    }


def cmd_tick(p: Project, a) -> int:
    d = decide_mode(p)
    history = p.read("modes")
    last = history[-1] if history else {}
    if (last.get("mode"), last.get("stage")) != (d["mode"], d["stage"]):
        p.append("modes", {"mode": d["mode"], "stage": d["stage"], "reasons": d["reasons"], "needs_human": d["needs_human"]}, "M", a.by)
    print(f"模式：{d['label']}")
    for text in d["reasons"]:
        print(f"  - {text}")
    print(f"现在可以做：{d['allowed']}")
    print(f"现在不做：{d['forbidden']}")
    if d["exhausted"]:
        print(f"已疲劳的类别（最近 {p.policy()['fatigue_fails']} 条试验都没有通过，除非换数据或换思路否则不再找规则）：{'、'.join(d['exhausted'])}")
    if d["signals"]:
        print("未处理的信号：" + "；".join(d["signals"]))
    print(f"未结影子规则 {d['open_shadows']} / 上限 {d['max_open_shadows']}")
    for text in d["needs_human"]:
        print(f"需要用户决定：{text}")
    return 0


def hook_text(d: dict, full: bool) -> str:
    if full:
        lines = [f"[metaRSI] 模式：{d['label']}"] + [f"- {text}" for text in d["reasons"]]
        lines += [f"现在可以做：{d['allowed']}", f"现在不做：{d['forbidden']}"]
        if d["exhausted"]:
            lines.append(f"已疲劳的类别：{'、'.join(d['exhausted'])}")
        if d["signals"]:
            lines.append("未处理的信号：" + "；".join(d["signals"]))
    else:
        lines = [f"[metaRSI] 模式：{d['label']}（未变）。现在不做：{d['forbidden']}。用户明确要求的分析照做，并说明能达到的证据等级。"]
    lines += [f"需要用户决定：{text}" for text in d["needs_human"]]
    return "\n".join(lines)


def cmd_hook(p: Project, a) -> int:
    """Entry point for a host hook (Claude Code SessionStart / UserPromptSubmit).

    Reads the hook payload on stdin, prints JSON whose additionalContext carries the
    current mode, and never blocks the prompt: any failure becomes a visible warning.
    """
    event = "UserPromptSubmit"
    try:
        raw = "" if sys.stdin is None or sys.stdin.isatty() else sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        event = payload.get("hook_event_name") or event
        project = Project(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or a.project)
        if not (project.dir / "constitution.json").exists():
            return 0                       # this project does not use metaRSI
        d = decide_mode(project)
        history = project.read("modes")
        last = history[-1] if history else {}
        changed = (last.get("mode"), last.get("stage")) != (d["mode"], d["stage"])
        if changed:
            project.append("modes", {"mode": d["mode"], "stage": d["stage"], "reasons": d["reasons"],
                                     "needs_human": d["needs_human"]}, "M", "hook")
            project.sync()
        text = hook_text(d, full=changed or event == "SessionStart")
        if changed and history:
            text = f"[metaRSI] 模式已变化，请在回答里告诉用户一句。\n{text}"
        out = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}
    except Exception as error:  # noqa: BLE001  a hook must not break the session
        out = {"systemMessage": f"metaRSI hook failed: {type(error).__name__}: {error}"}
    sys.stdout.write(json.dumps(out) + "\n")   # ASCII-escaped, safe under any console code page
    return 0


def cmd_signal(p: Project, a) -> int:
    if a.action == "log":
        if not a.kind or not a.name:
            raise SystemExit("signal log needs --kind and --name")
        rec = p.append("signals", {"op": "add", "kind": a.kind, "name": a.name, "note": a.note, "value": a.value}, "G", a.by)
        print(rec["id"])
    elif a.action == "resolve":
        if a.id not in p.signals():
            raise SystemExit(f"unknown signal {a.id}")
        p.append("signals", {"op": "resolve", "id": None, "ref": a.id, "note": a.note}, "G", a.by)
    for g in p.signals().values():
        print(f"{g['id']} {'open  ' if g['open'] else 'closed'} {g['kind']:11s} {g['name']} | {g.get('note') or ''}")
    return 0


# ---------------------------------------------------------------- wiki pages
PLAYBOOKS = """# 调用手册

metaRSI 不是每轮问答都调用，在四个时点用。命令前缀：
`python <mylib>/skills/meta-rsi/scripts/metarsi.py --project <项目根目录>`

## 0) 每个回合开始实质工作之前
1. `tick`：由账本和日历判断现在是「后台学习」还是「进化」，并列出现在可以做和不做的事。
2. 后台学习时照常干活和记录，但不在已用过的窗口上搜新规则当验证；用户明确要求的分析照做，并说明它能达到的证据等级。
3. 用户提出改进要求、项目运行出故障或指标漂移时，`signal log --kind request|failure|drift`；处理完 `signal resolve`。

## 1) 开始一个实验之前
1. `search <关键词>`：这个想法是否已经试过、为什么被否决（也可以直接读 `negatives.md`）。
2. `check --read 起..止 --write 路径`：要读的日期是否碰到保留窗口，要写的文件是否受保护。
3. 返回码 2 就停下并告知用户，不绕过。

## 2) 实验有结论之后
1. 每条规则 `trial log`，写清在哪段数据上选定、在哪段数据上计分，附结果文件。等级由工具算。
2. 被否决的想法 `negative add`，写原因和教训。
3. 回合结束 `episode log`，记用户问了什么、答了什么、留下什么。

## 3) 提出「以后再验」的规则
1. `shadow add`：规则原文、指标、窗口、最少成熟天数写死。
2. 一个窗口只有一条主规则（`--primary`），由用户指定。

## 5) 训练或更换模型
1. 每一折和最终模型用同一种做法：窗口怎么取、树多少棵、特征怎么处理都写死，不让早停在不同窗口上产出不同的东西。
2. 被评估的每个区块都排在训练数据之后；拟合窗口、调参窗口和样本外分开报，不合成一个数。
3. 把上线模型放回历史上它没见过的日子里重新打分；引用成绩时只用它自己打的分。
4. 量三样东西并登记（`model register` / `model block`）：各次训练的树数、市场状态特征的增益占比、选出的股票和全市场的差别（选股画像）。
5. `model audit` 有问题的模型不提议进合约；`propose --model 名称` 会自动带上审计结果。

## 4) 要改受保护的文件
1. `propose --surface 路径 --evidence 试验编号`。证据等级不够直接拒绝，够了也只到「待人批」。
2. `decide` 只在用户明确指示后执行，并署用户的名字。
"""


def _cell(value) -> str:
    return "" if value is None else str(value).replace("|", "/").replace("\n", " ")


def _label(text: str, width: int = 30) -> str:
    text = "".join(ch for ch in str(text) if ch not in '"[]{}|<>`')
    return text if len(text) <= width else text[: width - 1] + "…"


def render_wiki(p: Project, state: dict) -> None:
    c = p.constitution()
    wiki = p.wiki_dir
    wiki.mkdir(parents=True, exist_ok=True)
    trials, shadows = state["trials"], state["shadows"]
    head = "> 由 `metarsi.py` 从 `metarsi.db` 生成，每次写入后重写。不要手改；改记录请用命令。\n"

    def link(target: str | None) -> str:
        if not target:
            return ""
        rel = os.path.relpath(p.root / target, wiki).replace(os.sep, "/")
        return f"[{target}]({rel})"

    def family_counts(window: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for t in trials:
            if t.get("scored_on") == window:
                out[t["family"]] = out.get(t["family"], 0) + int(t.get("n_compared") or 1)
        return out

    # README
    mode = decide_mode(p)
    _, tested, held = calibration(p)
    open_shadows = [s for s in shadows if s["open"]]
    primary = [s["id"] for s in open_shadows if s.get("primary")]
    pending = [x for x in state["admissions"] if x["decision"] == "pending_human"]
    problems = p.verify_chain()
    lines = [f"# metaRSI 账本 — {c.get('project')}", "", head, "## 入口", "",
             "- 总图：`graph.md`", "- 节点（窗口、受保护面、影子规则、准入提议）：`nodes.md`", "- 试验：`trials.md`",
             "- 否决过的想法：`negatives.md`", "- 模型与模型审计：`models.md`", "- 问答日志：`log.md`", "- 调用手册：`playbooks.md`", "",
             "## 当前模式", "", f"**{mode['label']}**", ""]
    lines += [f"- {text}" for text in mode["reasons"]]
    lines += [f"- 现在可以做：{mode['allowed']}", f"- 现在不做：{mode['forbidden']}"]
    if mode["exhausted"]:
        lines.append(f"- 已疲劳的类别：{'、'.join(mode['exhausted'])}")
    lines += [f"- 需要用户决定：{text}" for text in mode["needs_human"]]
    lines += ["", "## 当前状态", "", f"- 证据等级（强到弱）：{' > '.join(p.tiers())}", "",
             "| 窗口 | 起 | 止 | 状态 | 试验数 | 同类问题已比较的规则数（需要的 /t/） |", "|---|---|---|---|---:|---|"]
    for w in state["windows"]:
        fam = "；".join(f"{k}: {v} 条（{bonferroni_t(v):.2f}）" for k, v in family_counts(w["name"]).items())
        n = sum(1 for t in trials if t.get("scored_on") == w["name"])
        lines.append(f"| {w['name']} | {w['start']} | {w['end'] or ''} | {w['state']} | {n} | {fam} |")
    lines += ["", f"- 未结的影子规则：{len(open_shadows)} 条；主规则：{'、'.join(primary) if primary else '未指定'}",
              f"- 等人批准的提议：{len(pending)} 条",
              f"- 试验 {len(trials)} 条，否决 {len(state['negatives'])} 条，问答 {len(state['episodes'])} 条",
              f"- 校准：在较弱等级上显著、又在更强等级上复验过的结果 {tested} 条，其中成立 {held} 条",
              f"- 账本链：{'完整' if not problems else '；'.join(problems)}", "", "## 不变量", ""]
    lines += [f"- {text}" for text in c.get("invariants", [])]
    (wiki / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # graph
    g = ["# 证据图", "", head, "```mermaid", "graph TD"]
    node: dict[tuple, str] = {}

    def nid(kind: str, key: str) -> str:
        return node.setdefault((kind, key), f"{kind}{len(node)}")

    for w in state["windows"]:
        g.append(f'    {nid("W", w["name"])}["{_label(w["name"])}<br/>{w["state"]}"]')
        for fam, n in family_counts(w["name"]).items():
            f = nid("F", w["name"] + fam)
            g.append(f'    {nid("W", w["name"])} --> {f}["{_label(fam)}<br/>已比较 {n} 条"]')
    for t in trials:
        if not t.get("scored_on"):
            continue
        tv = f" t={float(t['t']):+.2f}" if t.get("t") is not None else ""
        g.append(f'    {nid("F", t["scored_on"] + t["family"])} --> {nid("T", t["id"])}'
                 f'["{t["id"]} {_label(t["rule_id"], 24)}<br/>{t["tier"]} {t["verdict"]}{tv}"]')
    for s_ in shadows:
        state_text = "未结" if s_["open"] else f"已结 {s_.get('outcome') or ''}"
        g.append(f'    {nid("S", s_["id"])}["{s_["id"]} 影子{"（主）" if s_.get("primary") else ""}<br/>{_label(s_["rule"], 26)}<br/>{state_text}"]'
                 f' -.-> {nid("W", s_["window"])}')
    for n_ in state["negatives"]:
        g.append(f'    {nid("N", n_["id"])}["{n_["id"]} 否决<br/>{_label(n_["idea"], 26)}"]')
        for tid in n_.get("trials") or []:
            if ("T", tid) in node:
                g.append(f'    {node[("T", tid)]} -.-> {node[("N", n_["id"])]}')
    g.append("```")
    (wiki / "graph.md").write_text("\n".join(g) + "\n", encoding="utf-8")

    # nodes
    n = ["# 节点", "", head, "## 窗口", ""]
    for w in state["windows"]:
        n += [f"### `{w['name']}`", f"- 日期：{w['start']} 至 {w['end'] or '今'}", f"- 状态：{w['state']}",
              f"- 说明：{w.get('note') or ''}", ""]
    n += ["## 受保护面", ""]
    for rule in c.get("protected", []):
        n += [f"### `{rule['path']}`", f"- 最低证据等级：{rule.get('min_tier')}",
              f"- 需要人批准：{'是' if rule.get('human', True) else '否'}", f"- 说明：{rule.get('note') or ''}", ""]
    n += ["## 影子规则", ""]
    for s_ in shadows:
        n += [f"### `{s_['id']}`{'（主规则）' if s_.get('primary') else ''}", f"- 规则：{s_['rule']}",
              f"- 指标：{s_.get('metric') or ''}", f"- 窗口：{s_['window']}，最少成熟 {s_.get('min_matured')} 个信号日",
              f"- 登记：{s_['ts'][:10]}，规则指纹 {s_.get('rule_sha')}",
              f"- 状态：{'未结' if s_['open'] else '已结 ' + str(s_.get('outcome') or '')}", f"- 备注：{s_.get('note') or ''}", ""]
    n += ["## 准入提议", ""]
    for x in state["admissions"]:
        n += [f"### `{x['id']}` {x['surface']}", f"- 内容：{x['summary']}", f"- 证据：{'、'.join(x.get('evidence') or [])}"
              f"（最好 {x.get('best_tier')}，要求 {x.get('required_tier')}）",
              f"- 决定：{x['decision']}{'，' + str(x.get('decided_by')) if x.get('decided_by') else ''}",
              f"- 理由：{x.get('reason') or '；'.join(x.get('reasons') or [])}", ""]
    if not state["admissions"]:
        n += ["（暂无）", ""]
    n += ["## 信号", ""]
    for sig in state["signals"]:
        n += [f"### `{sig['id']}` {sig['kind']}：{sig['name']}", f"- 时间：{sig['ts'][:10]}，{sig['by']}",
              f"- 说明：{sig.get('note') or ''}",
              f"- 状态：{'未处理' if sig['open'] else '已处理 ' + str(sig.get('resolution') or '')}", ""]
    if not state["signals"]:
        n += ["（暂无）", ""]
    (wiki / "nodes.md").write_text("\n".join(n) + "\n", encoding="utf-8")

    # trials
    t_lines = ["# 试验", "", head, "| 编号 | 日期 | 规则 | 类别 | 选定于 | 计分于 | 等级 | 效应 | t | 比较数 | 结论 | 备注 | 出处 |",
               "|---|---|---|---|---|---|---|---:|---:|---:|---|---|---|"]
    for t in trials:
        t_lines.append("| " + " | ".join(_cell(v) for v in (
            t["id"], t["ts"][:10], t["rule_id"], t["family"], t.get("selected_on"), t.get("scored_on"), t["tier"],
            t.get("effect"), t.get("t"), t.get("n_compared"), t["verdict"], t.get("note"), link(t.get("wiki")))) + " |")
    (wiki / "trials.md").write_text("\n".join(t_lines) + "\n", encoding="utf-8")

    # negatives
    neg = ["# 否决过的想法", "", head]
    for x in state["negatives"]:
        neg += [f"## `{x['id']}` {x['idea']}", f"- 原因：{x['reason']}", f"- 教训：{x.get('lesson') or ''}",
                f"- 相关试验：{'、'.join(x.get('trials') or []) or '无'}", f"- 出处：{link(x.get('wiki'))}",
                f"- 记录：{x['ts'][:10]}，{x['by']}", ""]
    (wiki / "negatives.md").write_text("\n".join(neg) + "\n", encoding="utf-8")

    # log
    log = ["# 问答日志", "", head]
    for e in state["episodes"]:
        log += [f"## [{e['ts'][:10]}] {e['id']} | {e['question']}", "", e["answer"], ""]
        log += [f"- 遗留：{item}" for item in e.get("open") or []]
        if e.get("trials"):
            log.append(f"- 试验：{'、'.join(e['trials'])}")
        if e.get("wiki"):
            log.append(f"- 出处：{link(e['wiki'])}")
        log.append("")
    (wiki / "log.md").write_text("\n".join(log) + "\n", encoding="utf-8")
    md = ["# 模型与模型审计", "", head,
          "审计规则见 `SKILL.md`「模型审计」。事实由项目脚本量出来再登记，工具只按固定规则判断。", ""]
    for m in state["models"]:
        md += [f"## `{m['name']}`（{ {'shipped': '上线', 'candidate': '候选', 'reference': '参照'}.get(m.get('role'), m.get('role')) }）",
               f"- 做法：{m.get('recipe') or ''}", f"- 做法指纹：{m.get('recipe_sha')}",
               f"- 各次训练的树数：{m.get('trees') or '未登记'}；市场状态特征的增益占比：{m.get('market_gain') if m.get('market_gain') is not None else '未登记'}",
               f"- 审计：{'通过' if not m['flags'] else str(len(m['flags'])) + ' 条问题'}"]
        md += [f"  - {text}" for text in m["flags"]]
        rows = [b for b in state["model_blocks"] if b["model"] == m["name"]]
        if rows:
            md += ["", "| 区块 | 和训练数据的关系 | 指标 | 数值 | 天数 | 分数来自 | 选股画像 |", "|---|---|---|---:|---:|---|---|"]
            for b in sorted(rows, key=lambda x: str(x["block"])):
                prof = "；".join(f"{k} {v:g}" for k, v in (b.get("profile") or {}).items())
                md.append(f"| {b['block']} | { {'oos': '样本外', 'fit': '拟合窗口', 'tune': '调参窗口'}.get(b.get('relation'), '') } | {_cell(b.get('metric'))} | "
                          f"{_cell(b.get('value'))} | {_cell(b.get('days'))} | {_cell(b.get('scored_by'))} | {prof} |")
        md.append("")
    if not state["models"]:
        md.append("（暂无）")
    if len(state["models"]) >= 2:
        md += ["## 放在一起看：往哪用力", ""] + diagnose_models(p) + [""]
    (wiki / "models.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (wiki / "playbooks.md").write_text(PLAYBOOKS, encoding="utf-8")


def cmd_status(p: Project, a) -> int:
    c = p.constitution()
    print(f"project: {c.get('project')}  root: {p.root}")
    print(f"database: {p.db_path}  wiki: {p.wiki_dir}")
    print("tiers (strongest first):", " > ".join(p.tiers()))
    print("protected surfaces:")
    for rule in c.get("protected", []):
        print(f"  {rule['path']:45s} min_tier={rule.get('min_tier')} human={rule.get('human', True)}")
    trials = p.read("trials")
    print("windows:")
    for w in p.windows().values():
        here = [t for t in trials if t.get("scored_on") == w["name"]]
        fam: dict[str, int] = {}
        for t in here:
            fam[t["family"]] = fam.get(t["family"], 0) + int(t.get("n_compared") or 1)
        detail = ", ".join(f"{k}: {v} rules (|t|>={bonferroni_t(v):.2f})" for k, v in fam.items())
        print(f"  {w['name']:28s} {w['start']}..{w['end'] or '':8s} {w['state']:9s} trials={len(here)} {detail}")
    open_shadows = [s for s in p.shadows().values() if s["open"]]
    print(f"open shadow rules: {len(open_shadows)}")
    for s in open_shadows:
        print(f"  {s['id']} {'primary' if s.get('primary') else 'secondary'} on {s['window']}: {s['rule']}")
    for w in {s["window"] for s in open_shadows}:
        if not any(s.get("primary") for s in open_shadows if s["window"] == w):
            print(f"  note: no primary rule named for {w}; scoring several rules there is a multiple comparison")
    pending = [x for x in p.admissions().values() if x["decision"] == "pending_human"]
    print(f"proposals waiting for a person: {len(pending)}")
    for x in pending:
        print(f"  {x['id']} {x['surface']}: {x['summary']}")
    print(f"trials: {len(trials)}  rejected ideas: {len(p.read('negatives'))}  episodes: {len(p.read('episodes'))}")
    problems = p.verify_chain()
    print("ledger chain:", "intact" if not problems else "; ".join(problems))
    return 0


def cmd_verify(p: Project, a) -> int:
    problems = p.verify_chain()
    print("intact" if not problems else "\n".join(problems))
    return 0 if not problems else 2


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        run = lambda *argv: main(["--project", str(root), *argv])  # noqa: E731
        assert run("init", "--name", "demo") == 0
        doc = json.loads((root / ".metarsi/constitution.json").read_text(encoding="utf-8"))
        doc["protected"].append({"path": "config/contract.json", "min_tier": "prospective", "human": True})
        doc["calendar"] = {"glob": "cal/*.txt", "horizon": 2}
        (root / "cal").mkdir()
        for i in range(5):
            (root / "cal" / f"{20260701 + i}.txt").write_text("", encoding="utf-8")
        (root / ".metarsi/constitution.json").write_text(json.dumps(doc), encoding="utf-8")
        run("window", "add", "--name", "dev", "--start", "20250101", "--end", "20251231", "--state", "open")
        run("window", "add", "--name", "hold", "--start", "20260101", "--end", "20260630", "--state", "open")
        run("window", "add", "--name", "future", "--start", "20260701", "--state", "reserved")
        assert decide_mode(Project(root))["mode"] == "learn"
        run("signal", "log", "--kind", "request", "--name", "improve the list")
        d = decide_mode(Project(root))
        assert (d["mode"], d["stage"]) == ("evolve", "holdout"), d
        run("signal", "resolve", "--id", "G0001", "--note", "done")
        assert decide_mode(Project(root))["mode"] == "learn"
        assert run("tick") == 0
        assert run("trial", "log", "--rule-id", "r1", "--family", "f", "--selected-on", "dev", "--scored-on", "dev",
                   "--t", "5.0", "--verdict", "pass") == 0
        assert run("trial", "log", "--rule-id", "r1", "--family", "f", "--selected-on", "dev", "--scored-on", "hold",
                   "--t", "0.4", "--verdict", "fail") == 0
        p = Project(root)
        tiers = [t["tier"] for t in p.read("trials")]
        assert tiers == ["in_sample", "holdout_once"], tiers
        assert p.windows()["hold"]["state"] == "consumed"
        assert p.tier_of("empirical", "dev", "hold", "f", None) == "reused_holdout"
        assert run("check", "--read", "20260601..20260715") == 2
        assert run("check", "--read", "20260101..20260630") == 0
        assert run("check", "--write", "config/contract.json") == 2
        try:
            run("trial", "log", "--rule-id", "r2", "--family", "f", "--selected-on", "dev", "--scored-on", "future", "--verdict", "pass")
            raise AssertionError("reserved window was scored without a shadow rule")
        except SystemExit:
            pass
        run("shadow", "add", "--rule", "keep top 10", "--metric", "ret", "--window", "future", "--min-matured", "60", "--primary")
        assert Project(root).matured(Project(root).windows()["future"]) == 3
        assert decide_mode(Project(root))["mode"] == "learn"
        for i in range(5, 70):
            (root / "cal" / f"{20260701 + i}.txt").write_text("", encoding="utf-8")
        d = decide_mode(Project(root))
        assert (d["mode"], d["stage"], d["target"]) == ("evolve", "verify", "S0001"), d
        assert run("check", "--read", "20260701..", "--shadow", "S0001", "--matured", "10") == 2
        assert run("check", "--read", "20260701..", "--shadow", "S0001", "--matured", "60") == 0
        assert run("propose", "--surface", "config/contract.json", "--summary", "x", "--evidence", "T0001") == 2
        run("trial", "log", "--rule-id", "r1", "--family", "f", "--selected-on", "dev", "--scored-on", "future",
            "--shadow", "S0001", "--t", "2.5", "--verdict", "pass")
        assert p.read("trials")[-1]["tier"] == "prospective"
        assert run("propose", "--surface", "config/contract.json", "--summary", "x", "--evidence", "T0003") == 0
        assert p.admissions()["P0002"]["decision"] == "pending_human"
        try:
            run("decide", "--id", "P0002", "--approve")
            raise AssertionError("agent approved its own proposal")
        except SystemExit:
            pass
        assert run("decide", "--id", "P0002", "--approve", "--by", "owner", "--reason", "ok") == 0
        assert run("check", "--write", "config/contract.json") == 0
        run("model", "register", "--name", "shipped", "--role", "shipped", "--recipe", "anchor + residual, early stopping", "--trees", "2,39,1,247")
        run("model", "block", "--name", "shipped", "--block", "2025H1", "--relation", "oos", "--value", "2.4", "--scored-by", "folds", "--fit-days", "38",
            "--profile", "ma20_up=0.98", "--profile", "ma20_up_market=0.38")
        flags = model_flags(Project(root), Project(root).models()["shipped"])
        assert len(flags) >= 5, flags
        run("model", "register", "--name", "clean", "--recipe", "one recipe, fixed trees", "--trees", "300,300,300", "--market-gain", "0.1")
        for i, v in enumerate((1.0, 0.5, -0.2)):
            run("model", "block", "--name", "clean", "--block", f"b{i}", "--relation", "oos", "--value", str(v), "--fit-days", "250")
        assert model_flags(Project(root), Project(root).models()["clean"]) == []
        run("model", "register", "--name", "fading", "--recipe", "fixed", "--trees", "300,300", "--market-gain", "0.0")
        for i, v in enumerate((2.0, 1.5, -0.5, -1.0)):
            run("model", "block", "--name", "fading", "--block", f"b{i}", "--relation", "oos", "--value", str(v), "--fit-days", "250")
        assert any("前好后差" in f for f in model_flags(Project(root), Project(root).models()["fading"]))
        assert run("model", "audit") == 0
        assert run("model", "diagnose") == 0
        assert any("互补" in line or "一起失效" in line for line in diagnose_models(Project(root)))
        assert run("propose", "--surface", "config/contract.json", "--summary", "ship", "--evidence", "T0003", "--model", "shipped") == 2
        assert run("calibration") == 0
        assert run("verify-ledger") == 0
        for page in ("README.md", "graph.md", "nodes.md", "trials.md", "negatives.md", "models.md", "log.md", "playbooks.md"):
            assert (root / ".metarsi/wiki" / page).is_file(), page
        with closing(sqlite3.connect(root / ".metarsi/metarsi.db")) as con:
            assert con.execute("SELECT COUNT(*) FROM trials").fetchone()[0] == 3
            assert con.execute("SELECT tier FROM trials WHERE id = 'T0003'").fetchone()[0] == "prospective"
            con.execute("UPDATE events SET data = replace(data, '0.4', '4.0') WHERE ledger = 'trials'")
            con.commit()
        assert run("verify-ledger") == 2
    print("self-test passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=".")
    ap.add_argument("--by", default="agent", help="who is acting; a person's name for human decisions")
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    common = argparse.ArgumentParser(add_help=False)   # lets --by follow the subcommand too
    common.add_argument("--by", default=argparse.SUPPRESS)
    add = lambda name: sub.add_parser(name, parents=[common])  # noqa: E731

    s = add("init"); s.add_argument("--name"); s.set_defaults(fn=cmd_init)
    s = add("status"); s.set_defaults(fn=cmd_status)
    s = add("verify-ledger"); s.set_defaults(fn=cmd_verify)
    s = add("calibration"); s.set_defaults(fn=cmd_calibration)
    s = add("search"); s.add_argument("words", nargs="+"); s.set_defaults(fn=cmd_search)
    s = add("tick"); s.set_defaults(fn=cmd_tick)
    s = add("hook"); s.set_defaults(fn=cmd_hook)
    s = add("signal"); s.add_argument("action", choices=["log", "resolve", "list"])
    s.add_argument("--kind", choices=["request", "failure", "drift", "opportunity"]); s.add_argument("--name")
    s.add_argument("--value", type=float); s.add_argument("--note"); s.add_argument("--id"); s.set_defaults(fn=cmd_signal)

    s = add("window"); s.add_argument("action", choices=["add", "set", "list"])
    s.add_argument("--name"); s.add_argument("--start"); s.add_argument("--end")
    s.add_argument("--state", choices=["open", "consumed", "reserved"], default="open"); s.add_argument("--note")
    s.set_defaults(fn=cmd_window)

    s = add("trial"); s.add_argument("action", choices=["log"])
    s.add_argument("--rule-id", required=True); s.add_argument("--family", required=True); s.add_argument("--question")
    s.add_argument("--kind", choices=["empirical", "formal", "judge"], default="empirical")
    s.add_argument("--selected-on"); s.add_argument("--scored-on"); s.add_argument("--shadow")
    s.add_argument("--n-compared", default=1); s.add_argument("--metric"); s.add_argument("--effect", type=float)
    s.add_argument("--t", type=float); s.add_argument("--n-obs", type=int)
    s.add_argument("--verdict", choices=["pass", "fail", "inconclusive"], required=True)
    s.add_argument("--artifact", action="append"); s.add_argument("--wiki"); s.add_argument("--note")
    s.set_defaults(fn=cmd_trial)

    s = add("negative"); s.add_argument("action", choices=["add"])
    s.add_argument("--idea", required=True); s.add_argument("--reason", required=True); s.add_argument("--lesson")
    s.add_argument("--trial", action="append"); s.add_argument("--wiki"); s.set_defaults(fn=cmd_negative)

    s = add("shadow"); s.add_argument("action", choices=["add", "close", "list"])
    s.add_argument("--rule"); s.add_argument("--metric"); s.add_argument("--window"); s.add_argument("--min-matured", type=int, default=0)
    s.add_argument("--primary", action="store_true"); s.add_argument("--note")
    s.add_argument("--id"); s.add_argument("--outcome"); s.add_argument("--trial-id"); s.set_defaults(fn=cmd_shadow)

    s = add("check"); s.add_argument("--read"); s.add_argument("--write", action="append")
    s.add_argument("--shadow"); s.add_argument("--matured", type=int); s.set_defaults(fn=cmd_check)

    s = add("propose"); s.add_argument("--surface", required=True); s.add_argument("--summary", required=True)
    s.add_argument("--evidence", action="append"); s.add_argument("--check", action="append")
    s.add_argument("--model", help="a registered model the change would ship; its audit must be clean"); s.set_defaults(fn=cmd_propose)

    s = add("model"); s.add_argument("action", choices=["register", "block", "audit", "diagnose", "list"])
    s.add_argument("--name"); s.add_argument("--role", choices=["shipped", "candidate", "reference"], default="candidate")
    s.add_argument("--recipe"); s.add_argument("--trees"); s.add_argument("--market-gain", type=float); s.add_argument("--note")
    s.add_argument("--block"); s.add_argument("--relation", choices=["oos", "fit", "tune"]); s.add_argument("--metric-name")
    s.add_argument("--value", type=float); s.add_argument("--days", type=int); s.add_argument("--fit-days", type=int)
    s.add_argument("--scored-by"); s.add_argument("--profile", action="append"); s.set_defaults(fn=cmd_model)

    s = add("decide"); s.add_argument("--id", required=True)
    g = s.add_mutually_exclusive_group(required=True); g.add_argument("--approve", action="store_true"); g.add_argument("--reject", action="store_true")
    s.add_argument("--reason"); s.set_defaults(fn=cmd_decide)

    s = add("episode"); s.add_argument("action", choices=["log"])
    s.add_argument("--question", required=True); s.add_argument("--answer", required=True)
    s.add_argument("--open", action="append"); s.add_argument("--trial", action="append"); s.add_argument("--wiki")
    s.set_defaults(fn=cmd_episode)
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not a.cmd:
        ap.print_help()
        return 1
    project = Project(a.project)
    try:
        return a.fn(project, a)
    finally:
        if project.dirty and (project.dir / "constitution.json").exists():
            project.sync()


if __name__ == "__main__":
    raise SystemExit(main())
