"""Scoped offline alert evaluation and version receipts for Agent Hub.

The service must authenticate the actor, check operator or host permissions,
and verify current attempt identity before dispatching a confirmed load.
"""

import hashlib
import json
import math
import re
import sqlite3
import time
from contextlib import closing, contextmanager
from pathlib import Path


_EVALUATOR = "waiting-v1"
_ARTIFACT_EVALUATOR = "paired-artifact-v1"
_QUIET_MS = 300_000
_MAX_CASES = 2_000
_SPLITS = {"development": 10, "heldout": 60}
_TERMINAL_SIGNALS = {"blocked", "waiting", "limited"}
_RECEIPT_RESULTS = {"loaded", "pending_restart", "failed"}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS evolution_mode (
    id INTEGER PRIMARY KEY CHECK (id = 1), fixture INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS evolution_items (
    scope TEXT, skill TEXT, baseline TEXT NOT NULL, active TEXT NOT NULL,
    active_candidate TEXT,
    PRIMARY KEY (scope, skill)
);
CREATE TABLE IF NOT EXISTS evolution_candidates (
    scope TEXT, skill TEXT, id TEXT, version TEXT NOT NULL, parent TEXT NOT NULL,
    kind TEXT NOT NULL, development_id TEXT NOT NULL, heldout_id TEXT NOT NULL,
    PRIMARY KEY (scope, skill, id)
);
CREATE TABLE IF NOT EXISTS evolution_evaluations (
    scope TEXT, skill TEXT, id TEXT, split TEXT, dataset TEXT NOT NULL,
    digest TEXT NOT NULL, scores TEXT NOT NULL,
    PRIMARY KEY (scope, skill, id, split)
);
CREATE TABLE IF NOT EXISTS evolution_trial_specs (
    scope TEXT, skill TEXT, id TEXT, specification TEXT NOT NULL,
    PRIMARY KEY (scope,skill,id)
);
CREATE TABLE IF NOT EXISTS evolution_release_links (
    scope TEXT, skill TEXT, id TEXT, parent_id TEXT,
    PRIMARY KEY (scope,skill,id)
);
CREATE TABLE IF NOT EXISTS evolution_invalidated_releases (
    scope TEXT, skill TEXT, id TEXT, PRIMARY KEY (scope,skill,id)
);
CREATE TABLE IF NOT EXISTS evolution_exposure (
    scope TEXT, skill TEXT, kind TEXT, unit TEXT, split TEXT, dataset TEXT NOT NULL,
    PRIMARY KEY (scope, skill, kind, unit)
);
CREATE TABLE IF NOT EXISTS evolution_revocations (
    scope TEXT, evidence TEXT, PRIMARY KEY (scope, evidence)
);
CREATE TABLE IF NOT EXISTS evolution_wiki_dependencies (
    project TEXT NOT NULL, scope TEXT NOT NULL, skill TEXT NOT NULL, evidence TEXT NOT NULL,
    entry TEXT NOT NULL, revision TEXT NOT NULL, body_sha256 TEXT NOT NULL,
    withdrawn INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(scope,skill,evidence)
);
CREATE INDEX IF NOT EXISTS evolution_wiki_by_project
    ON evolution_wiki_dependencies(project,withdrawn);
CREATE TABLE IF NOT EXISTS evolution_attempts (
    scope TEXT, skill TEXT, attempt TEXT, generation INTEGER,
    pinned TEXT NOT NULL, loaded TEXT, PRIMARY KEY (scope, skill, attempt, generation)
);
CREATE TABLE IF NOT EXISTS evolution_load_requests (
    request TEXT PRIMARY KEY, scope TEXT NOT NULL, skill TEXT NOT NULL, attempt TEXT NOT NULL,
    generation INTEGER NOT NULL, version TEXT NOT NULL, actor TEXT NOT NULL,
    expires REAL NOT NULL, state TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evolution_audit (
    seq INTEGER PRIMARY KEY, scope TEXT, skill TEXT, actor TEXT NOT NULL,
    action TEXT NOT NULL, payload TEXT NOT NULL, at REAL NOT NULL
);
"""


class EvolutionError(ValueError):
    """A request that failed the evaluation or version protocol."""


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


WAITING_BASELINE_VERSION = _digest([_EVALUATOR, "quiet_timeout", _QUIET_MS])
WAITING_CANDIDATE_VERSION = _digest([_EVALUATOR, "trusted_signal_only"])


def _identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[\w][\w./:@+-]{0,127}", value):
        raise EvolutionError("invalid identifier")
    return value


def _version(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
        raise EvolutionError("invalid version digest")
    return value


def _uint(value, limit=2**31 - 1):
    if type(value) is not int or not 0 <= value <= limit:
        raise EvolutionError("invalid nonnegative integer")
    return value


def _scope(value):
    names = ("project_id", "tool", "tool_version")
    if not isinstance(value, dict) or set(value) != set(names):
        raise EvolutionError("invalid scope")
    return _json([_identifier(value[name]) for name in names])


def _wiki_reference(value):
    if not isinstance(value, dict) or set(value) != {"entry_id", "version", "sha256"}:
        raise EvolutionError("invalid wiki evidence dependency")
    for name in ("entry_id", "version"):
        text = value[name]
        if not isinstance(text, str) or not 0 < len(text) <= 256 or not text.isprintable():
            raise EvolutionError("invalid wiki evidence reference")
    return value["entry_id"], value["version"], _version(value["sha256"])


def _asset_provenance(value):
    fields = {"kind", "revision", "path", "sha256"}
    if not isinstance(value, dict) or set(value) != fields:
        raise EvolutionError("invalid asset provenance")
    revision = value["revision"]
    if not isinstance(revision, str) or not re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", revision):
        raise EvolutionError("asset must name a full immutable revision")
    path = value["path"]
    if (not isinstance(path, str) or not 0 < len(path) <= 256 or not path.isprintable()
            or chr(92) in path or ":" in path or any(part in {"", ".", ".."} for part in path.split("/"))):
        raise EvolutionError("invalid asset path")
    kind = value["kind"]
    if kind not in ("skill", "harness"):
        raise EvolutionError("invalid asset kind")
    suffixes = (".md",) if kind == "skill" else (".md", ".toml", ".json", ".txt")
    if not path.lower().endswith(suffixes):
        raise EvolutionError("unsupported asset file type")
    _version(value["sha256"])
    return value


def _trial_spec(evaluator, provenance, parent, version):
    if evaluator == _EVALUATOR:
        if (parent, version) != (WAITING_BASELINE_VERSION, WAITING_CANDIDATE_VERSION) or provenance is not None:
            raise EvolutionError("waiting-v1 can only evaluate the fixed policy pair")
        return None
    if evaluator != _ARTIFACT_EVALUATOR or not isinstance(provenance, dict) or set(provenance) != {
        "parent", "candidate", "verifier_sha256",
    }:
        raise EvolutionError("invalid artifact evaluator specification")
    old = _asset_provenance(provenance["parent"])
    new = _asset_provenance(provenance["candidate"])
    if (old["sha256"], new["sha256"]) != (parent, version) or old["kind"] != new["kind"] or parent == version:
        raise EvolutionError("artifact versions or kinds do not match the trial")
    return {"parent": old, "candidate": new, "verifier_sha256": _version(provenance["verifier_sha256"])}


def waiting_alert(version, *, observable, quiet_ms, signal, trusted_current):
    """Return the state of the exact policy version exercised by offline tests."""
    if version not in (WAITING_BASELINE_VERSION, WAITING_CANDIDATE_VERSION):
        raise EvolutionError("unknown waiting policy version")
    if not observable:
        return "unknown"
    if trusted_current and signal in _TERMINAL_SIGNALS:
        return signal
    if version == WAITING_BASELINE_VERSION and quiet_ms >= _QUIET_MS:
        return "blocked"
    return "observing"


def _score_case(case):
    fields = {
        "evidence_id", "group_id", "label", "observable", "quiet_ms",
        "signal", "signal_delay_ms", "trusted_current",
    }
    if not isinstance(case, dict) or not fields <= case.keys() or case.keys() - fields - {"wiki_dependency"}:
        raise EvolutionError("invalid evaluation case")
    if "wiki_dependency" in case:
        _wiki_reference(case["wiki_dependency"])
    label = case["label"]
    signal = case["signal"]
    if not isinstance(label, str) or label not in _TERMINAL_SIGNALS | {"clear"}:
        raise EvolutionError("unknown observation or label")
    if signal is not None and (not isinstance(signal, str) or signal not in _TERMINAL_SIGNALS):
        raise EvolutionError("unknown observation or label")
    if type(case["observable"]) is not bool or type(case["trusted_current"]) is not bool:
        raise EvolutionError("invalid observation flags")
    quiet_ms = _uint(case["quiet_ms"])
    signal_delay = case["signal_delay_ms"]
    if signal is None:
        if signal_delay is not None or case["trusted_current"]:
            raise EvolutionError("empty signal has metadata")
    else:
        _uint(signal_delay)
    confirmed = signal if case["observable"] and case["trusted_current"] else None
    quiet = case["observable"] and quiet_ms >= _QUIET_MS
    observation = {key: case[key] for key in ("observable", "quiet_ms", "signal", "trusted_current")}
    candidate = waiting_alert(WAITING_CANDIDATE_VERSION, **observation)
    parent = waiting_alert(WAITING_BASELINE_VERSION, **observation)
    parent_delay = signal_delay if parent == "blocked" and confirmed else _QUIET_MS
    if quiet and parent == "blocked":
        parent_delay = min(parent_delay, _QUIET_MS)
    return {
        "evidence": _digest(_identifier(case["evidence_id"])),
        "group": _digest(_identifier(case["group_id"])),
        "label": label,
        "parent": parent,
        "candidate": candidate,
        "parent_delay": parent_delay if parent == "blocked" else None,
        "candidate_delay": signal_delay if candidate == "blocked" else None,
        "beacon": quiet and confirmed is None,
    }


def _artifact_run(value, asset, task, verifier):
    fields = {
        "run_id", "revision", "asset_sha256", "task_sha256", "verifier_sha256", "result_sha256",
        "passed", "critical_failure", "effectful_violation", "duration_ms",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise EvolutionError("invalid paired task run")
    if (value["revision"], value["asset_sha256"], value["task_sha256"], value["verifier_sha256"]) != (
        asset["revision"], asset["sha256"], task, verifier,
    ):
        raise EvolutionError("paired task input, verifier or asset does not match")
    outcome = [value[name] for name in ("passed", "critical_failure", "effectful_violation")]
    if any(type(flag) is not bool for flag in outcome) or (outcome[0] and any(outcome[1:])):
        raise EvolutionError("invalid paired task outcome")
    _version(value["result_sha256"])
    _uint(value["duration_ms"])
    _identifier(value["run_id"])
    return value


def _score_artifact_case(case, specification):
    fields = {"evidence_id", "group_id", "task_sha256", "parent_run", "candidate_run"}
    if not isinstance(case, dict) or not fields <= case.keys() or case.keys() - fields - {"wiki_dependency"}:
        raise EvolutionError("invalid paired artifact case")
    if "wiki_dependency" in case:
        _wiki_reference(case["wiki_dependency"])
    task = _version(case["task_sha256"])
    verify = specification["verifier_sha256"]
    parent = _artifact_run(case["parent_run"], specification["parent"], task, verify)
    child = _artifact_run(case["candidate_run"], specification["candidate"], task, verify)
    if parent["run_id"] == child["run_id"]:
        raise EvolutionError("paired task needs independently executed runs")
    return {
        "evidence": _digest(_identifier(case["evidence_id"])),
        "group": _digest(_identifier(case["group_id"])), "task": task,
        "runs": [_digest(parent["run_id"]), _digest(child["run_id"])],
        "parent_passed": parent["passed"], "candidate_passed": child["passed"],
        "new_critical": child["critical_failure"] and not parent["critical_failure"],
        "candidate_violation": child["effectful_violation"],
        "parent_ms": parent["duration_ms"], "candidate_ms": child["duration_ms"],
    }


def _p95(values):
    return sorted(values)[math.ceil(len(values) * 0.95) - 1] if values else None


def _paired_p(fixed, added):
    discordant = fixed + added
    return sum(math.comb(discordant, count) for count in range(fixed, discordant + 1)) / 2**discordant


def _assessment(scores, split):
    blockers = [row for row in scores if row["label"] == "blocked"]
    clear = [row for row in scores if row["label"] != "blocked"]
    fixed = sum(row["parent"] == "blocked" and row["candidate"] != "blocked" for row in clear)
    added = sum(row["parent"] != "blocked" and row["candidate"] == "blocked" for row in clear)
    introduced_misses = sum(
        row["parent"] == "blocked" and row["candidate"] != "blocked" for row in blockers
    )
    unsupported = sum(
        row["candidate"] in _TERMINAL_SIGNALS and row["candidate"] != row["label"]
        for row in scores
    )
    paired_p = _paired_p(fixed, added)
    benefit = (fixed - added) / len(clear) if clear else 0
    shared = [
        row for row in blockers if row["parent"] == "blocked" and row["candidate"] == "blocked"
    ]
    latency = (
        _p95([row["candidate_delay"] for row in shared])
        - _p95([row["parent_delay"] for row in shared])
        if shared else None
    )
    # A fully unobserved blocker does not get counted as a successful safety trial.
    parent_detected = sum(row["parent"] == "blocked" for row in blockers)
    if introduced_misses or unsupported or (latency is not None and latency > 5_000):
        result = "rejected"
    elif min(parent_detected, len(clear)) < _SPLITS[split]:
        result = "insufficient_evidence"
    elif any(row["beacon"] for row in scores) and benefit >= 0.05 and paired_p <= 0.05:
        result = "passed"
    else:
        result = "insufficient_evidence"
    return {
        "verdict": result, "groups": len(scores), "blocked_groups": len(blockers),
        "nonblocked_groups": len(clear), "parent_detected_blocked_groups": parent_detected,
        "candidate_detected_blocked_groups": sum(row["candidate"] == "blocked" for row in blockers),
        "fixed_false_alerts": fixed, "added_false_alerts": added,
        "added_blocked_misses": introduced_misses, "unsupported_conclusions": unsupported,
        "paired_p": paired_p, "false_alert_rate_reduction": benefit,
        "blocked_p95_delay_change_ms": latency,
    }


def _artifact_assessment(rows, split):
    passed = sum(row["parent_passed"] for row in rows)
    improved = sum(row["candidate_passed"] and not row["parent_passed"] for row in rows)
    regressed = sum(row["parent_passed"] and not row["candidate_passed"] for row in rows)
    critical = sum(row["new_critical"] for row in rows)
    violations = sum(row["candidate_violation"] for row in rows)
    delta = (improved - regressed) / len(rows) if rows else 0
    p_value = _paired_p(improved, regressed)
    latency = _p95([row["candidate_ms"] for row in rows]) - _p95([row["parent_ms"] for row in rows]) if rows else None
    # Improvement cannot trade away known passing tasks or approval boundaries.
    if regressed or critical or violations or (latency is not None and latency > 5_000):
        verdict = "rejected"
    elif min(passed, len(rows) - passed) >= _SPLITS[split] and delta >= 0.05 and p_value <= 0.05:
        verdict = "passed"
    else:
        verdict = "insufficient_evidence"
    return {
        "verdict": verdict, "groups": len(rows), "parent_passed_groups": passed,
        "improved_groups": improved, "regressed_groups": regressed,
        "new_critical_failures": critical, "candidate_effectful_violations": violations,
        "passed_rate_improvement": delta, "paired_p": p_value, "p95_delay_change_ms": latency,
    }


class EvolutionLedger:
    """Serialize scope changes in SQLite and record host loading separately.

    verify_evidence(scope, case) is a trusted local verifier for authorized
    data and must validate the label, independent group and evidence. With
    verify_evidence omitted, only explicitly enabled fixtures can be promoted.
    """

    def __init__(self, path, *, verify_evidence=None, allow_fixture_promotion=False, clock=time.time,
                 wiki_database=None):
        if type(allow_fixture_promotion) is not bool:
            raise EvolutionError("invalid ledger mode")
        self.path = path
        self.verify_evidence = verify_evidence
        self.fixture_promotion = allow_fixture_promotion
        self.clock = clock
        self.wiki_database = None
        if wiki_database is not None:
            self.bind_wiki_database(wiki_database)
        db = sqlite3.connect(path)
        try:
            db.executescript(_SCHEMA)
            with db:
                db.execute("INSERT OR IGNORE INTO evolution_mode VALUES(1,?)", (allow_fixture_promotion,))
                if db.execute("SELECT fixture FROM evolution_mode").fetchone()[0] != allow_fixture_promotion:
                    raise EvolutionError("fixture and ordinary ledgers must use separate databases")
        finally:
            db.close()

    def bind_wiki_database(self, path):
        authority = Path(path).resolve()
        if authority == Path(self.path).resolve() or (
            self.wiki_database is not None and self.wiki_database != authority
        ):
            raise EvolutionError("wiki evidence authority conflicts with this ledger")
        self.wiki_database = authority

    @contextmanager
    def _wiki_authority(self):
        if self.wiki_database is None:
            raise EvolutionError("wiki evidence authority is required")
        try:
            with closing(sqlite3.connect(self.wiki_database.as_uri() + "?mode=ro", uri=True)) as authority:
                authority.execute("BEGIN")
                yield authority
        except (sqlite3.Error, OSError):
            raise EvolutionError("wiki evidence authority unavailable") from None

    @staticmethod
    def _wiki_withdrawn(authority, project, entry):
        return authority.execute(
            "SELECT 1 FROM wiki_withdrawals WHERE project=? AND entry_id=?", (project, entry)
        ).fetchone() is not None

    @staticmethod
    def _has_wiki_tombstones(authority):
        return authority.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='wiki_withdrawals'"
        ).fetchone() is not None

    @staticmethod
    def _verify_wiki_revision(authority, project, entry, revision, digest):
        row = authority.execute(
            "SELECT digest FROM wiki_entry_versions WHERE project=? AND entry_id=? AND version=?",
            (project, entry, revision),
        ).fetchone()
        if row is None or row[0] != digest:
            raise EvolutionError("wiki evidence unavailable or changed")

    def _reconcile_wiki(self, db, project, wiki_item):
        selection = " AND scope=? AND skill=?" if wiki_item is not None else ""
        dependencies = db.execute(
            "SELECT scope,skill,evidence,entry,revision,body_sha256 FROM evolution_wiki_dependencies "
            "WHERE project=? AND withdrawn=0" + selection, (project, *(wiki_item or ())),
        ).fetchall()
        if not dependencies:
            return
        scopes = set()
        with self._wiki_authority() as authority:
            tombstones = self._has_wiki_tombstones(authority)
            for scope, skill, evidence, entry, revision, digest in dependencies:
                if tombstones and self._wiki_withdrawn(authority, project, entry):
                    db.execute("UPDATE evolution_wiki_dependencies SET withdrawn=1 "
                               "WHERE scope=? AND skill=? AND evidence=?", (scope, skill, evidence))
                    self._audit(db, (scope, skill), "wiki-reconcile", "wiki_evidence_withdrawn", {"evidence": evidence})
                    scopes.add(scope)
                else:
                    self._verify_wiki_revision(authority, project, entry, revision, digest)
        for scope in scopes:
            self._recheck_publications(db, scope, "wiki-reconcile")

    @contextmanager
    def _transaction(self, *, write=True, project=None, wiki_item=None):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        try:
            db.execute("BEGIN IMMEDIATE" if write or project is not None else "BEGIN")
            if project is not None:
                self._reconcile_wiki(db, project, wiki_item)
            db.execute("SAVEPOINT evolution_operation")
            try:
                yield db
            except BaseException:
                # Keep independently observed withdrawals even if the request is forbidden.
                db.execute("ROLLBACK TO evolution_operation")
                raise
            finally:
                db.execute("RELEASE evolution_operation")
                db.commit()
        finally:
            db.close()

    def _audit(self, db, key, actor, action, payload):
        db.execute(
            "INSERT INTO evolution_audit(scope,skill,actor,action,payload,at) VALUES(?,?,?,?,?,?)",
            (*key, _identifier(actor), action, _json(payload), self.clock()),
        )

    @staticmethod
    def _item(db, key):
        item = db.execute("SELECT * FROM evolution_items WHERE scope=? AND skill=?", key).fetchone()
        if item is None:
            raise EvolutionError("baseline not registered")
        return item

    @staticmethod
    def _candidate(db, key, candidate_id):
        row = db.execute("SELECT * FROM evolution_candidates WHERE scope=? AND skill=? AND id=?",
                         (*key, _identifier(candidate_id))).fetchone()
        if row is None:
            raise EvolutionError("unknown candidate")
        return row

    @staticmethod
    def _specification(db, key, candidate_id):
        row = db.execute("SELECT specification FROM evolution_trial_specs WHERE scope=? AND skill=? AND id=?",
                         (*key, candidate_id)).fetchone()
        return json.loads(row[0]) if row else None

    @staticmethod
    def _key(scope, skill_id):
        return _scope(scope), _identifier(skill_id)

    def register_baseline(self, scope, skill_id, version, actor):
        key = self._key(scope, skill_id)
        version = _version(version)
        with self._transaction() as db:
            cursor = db.execute("INSERT OR IGNORE INTO evolution_items VALUES(?,?,?,?,NULL)",
                                (*key, version, version))
            if cursor.rowcount:
                self._audit(db, key, actor, "register_baseline", {"version": version})
            elif self._item(db, key)["baseline"] != version:
                raise EvolutionError("different baseline already registered")
            return {"baseline_version": version}

    def propose(self, scope, skill_id, candidate_id, *, version, parent_version,
                development_id, heldout_id, actor, evidence_kind="authorized",
                evaluator=_EVALUATOR, provenance=None):
        key = self._key(scope, skill_id)
        candidate_id = _identifier(candidate_id)
        version, parent = _version(version), _version(parent_version)
        development, heldout = _identifier(development_id), _identifier(heldout_id)
        specification = _trial_spec(evaluator, provenance, parent, version)
        if development == heldout or evidence_kind not in ("authorized", "fixture"):
            raise EvolutionError("invalid candidate specification")
        with self._transaction(project=scope["project_id"], wiki_item=key) as db:
            row = db.execute("SELECT * FROM evolution_candidates WHERE scope=? AND skill=? AND id=?",
                             (*key, candidate_id)).fetchone()
            values = (*key, candidate_id, version, parent, evidence_kind, development, heldout)
            if row:
                if tuple(row) != values or self._specification(db, key, candidate_id) != specification:
                    raise EvolutionError("candidate identifier conflict")
                return {"candidate_id": candidate_id}
            item = self._item(db, key)
            if parent != item["active"]:
                raise EvolutionError("candidate must extend the active parent")
            lineage = self._release_chain(db, key, item)
            if version == item["baseline"] or any(approved["version"] == version for approved in lineage):
                raise EvolutionError("an ancestor version requires rollback")
            active_spec = self._specification(db, key, item["active_candidate"])
            if active_spec is not None and (specification is None or active_spec["candidate"] != specification["parent"]):
                raise EvolutionError("candidate parent artifact provenance changed")
            db.execute("INSERT INTO evolution_candidates VALUES(?,?,?,?,?,?,?,?)", values)
            if specification is not None:
                db.execute("INSERT INTO evolution_trial_specs VALUES(?,?,?,?)",
                           (*key, candidate_id, _json(specification)))
            self._audit(db, key, actor, "propose", {"id": candidate_id, "version": version, "evaluator": evaluator})
            return {"candidate_id": candidate_id}

    @staticmethod
    def _seen(db, key, kind, unit):
        return db.execute("SELECT split,dataset FROM evolution_exposure "
                          "WHERE scope=? AND skill=? AND kind=? AND unit=?", (*key, kind, unit)).fetchone()

    def _reports(self, db, key, candidate):
        reports = {}
        digests = {}
        specification = self._specification(db, key, candidate["id"])
        evaluator = _ARTIFACT_EVALUATOR if specification else _EVALUATOR
        assess = _artifact_assessment if specification else _assessment
        unavailable = {"evaluator": evaluator, "evidence_kind": candidate["kind"],
                       "state": "evidence_revoked", "splits": {}, "evaluation_digest": None}
        if db.execute("SELECT 1 FROM evolution_invalidated_releases WHERE scope=? AND skill=? AND id=?",
                      (*key, candidate["id"])).fetchone():
            return unavailable
        revoked = {row[0] for row in db.execute(
            "SELECT evidence FROM evolution_revocations WHERE scope=?", (key[0],))}
        wiki_withdrawals = {row[0] for row in db.execute(
            "SELECT evidence FROM evolution_wiki_dependencies WHERE scope=? AND skill=? AND withdrawn=1", key)}
        for row in db.execute("SELECT split,digest,scores FROM evolution_evaluations "
                              "WHERE scope=? AND skill=? AND id=?", (*key, candidate["id"])):
            scores = json.loads(row["scores"])
            if any(score["evidence"] in wiki_withdrawals for score in scores):
                return unavailable
            remaining = [score for score in scores if score["evidence"] not in revoked]
            result = assess(remaining, row["split"])
            result["evidence_revoked"] = len(remaining) != len(scores)
            reports[row["split"]] = result
            digests[row["split"]] = _digest([row["digest"], [score["evidence"] for score in remaining]])
        proof = [evaluator, tuple(candidate), digests]
        if specification is not None:
            proof.append(specification)
        return {
            "evaluator": evaluator, "evidence_kind": candidate["kind"],
            "splits": reports,
            "evaluation_digest": _digest(proof),
        }

    @staticmethod
    def _passes(reports):
        return all(reports["splits"].get(split, {}).get("verdict") == "passed" for split in _SPLITS)

    def _register_wiki_dependencies(self, db, key, project, cases):
        new = []
        for case in cases:
            evidence = _digest(case["evidence_id"])
            row = db.execute("SELECT entry,revision,body_sha256,withdrawn FROM evolution_wiki_dependencies "
                             "WHERE scope=? AND skill=? AND evidence=?", (*key, evidence)).fetchone()
            reference = _wiki_reference(case["wiki_dependency"]) if "wiki_dependency" in case else None
            if row:
                if row["withdrawn"] or tuple(row)[:3] != reference:
                    raise EvolutionError("wiki evidence dependency withdrawn or changed")
            elif reference:
                if self._seen(db, key, "evidence", evidence):
                    raise EvolutionError("prior evidence binding changed")
                new.append((evidence, reference))
        if not new:
            return
        with self._wiki_authority() as authority:
            tombstones = self._has_wiki_tombstones(authority)
            for evidence, reference in new:
                if tombstones and self._wiki_withdrawn(authority, project, reference[0]):
                    raise EvolutionError("wiki evidence was withdrawn")
                self._verify_wiki_revision(authority, project, *reference)
                db.execute("INSERT INTO evolution_wiki_dependencies VALUES(?,?,?,?,?,?,?,0)",
                           (project, *key, evidence, *reference))

    def evaluate(self, scope, skill_id, candidate_id, split, dataset_id, cases, actor):
        key = self._key(scope, skill_id)
        if split not in tuple(_SPLITS) or not isinstance(cases, list) or not 0 < len(cases) <= _MAX_CASES:
            raise EvolutionError("invalid split or case count")
        with self._transaction(write=False, project=scope["project_id"], wiki_item=key) as db:
            candidate = self._candidate(db, key, candidate_id)
            specification = self._specification(db, key, candidate_id)
        scores = (
            [_score_artifact_case(case, specification) for case in cases] if specification else
            [_score_case(case) for case in cases]
        )
        scores.sort(key=lambda row: row["evidence"])
        kinds = ("evidence", "group", "task") if specification else ("evidence", "group")
        units = [(field, row[field]) for row in scores for field in kinds]
        if specification:
            units.extend(("run", run) for row in scores for run in row["runs"])
        if len(set(units)) != len(units):
            raise EvolutionError("repeat evidence, run, task or group within the split")
        payload_digest = _digest(sorted(cases, key=lambda case: case["evidence_id"]))
        if candidate["kind"] == "authorized":
            if self.verify_evidence is None or any(self.verify_evidence(scope, case) is not True for case in cases):
                raise EvolutionError("authorized evidence could not be verified")
        with self._transaction(project=scope["project_id"], wiki_item=key) as db:
            candidate = self._candidate(db, key, candidate_id)
            if dataset_id != candidate[f"{split}_id"]:
                raise EvolutionError("dataset differs from preregistration")
            existing = db.execute("SELECT digest FROM evolution_evaluations WHERE "
                                  "scope=? AND skill=? AND id=? AND split=?", (*key, candidate_id, split)).fetchone()
            if existing:
                if existing["digest"] != payload_digest:
                    raise EvolutionError("split already evaluated with different evidence")
                return self._reports(db, key, candidate)
            if split == "heldout":
                development = self._reports(db, key, candidate)["splits"].get("development", {})
                if development.get("verdict") != "passed":
                    raise EvolutionError("passing development assessment required")
            self._register_wiki_dependencies(db, key, scope["project_id"], cases)
            units.append(("dataset", _digest(dataset_id)))
            for kind, unit in units:
                exposed = self._seen(db, key, kind, unit)
                if exposed and (split == "heldout" or exposed["split"] == "heldout"):
                    raise EvolutionError("heldout evidence overlaps a prior assessment")
                if kind == "evidence" and db.execute("SELECT 1 FROM evolution_revocations "
                                                     "WHERE scope=? AND evidence=?", (key[0], unit)).fetchone():
                    raise EvolutionError("evaluation evidence was revoked")
                db.execute("INSERT OR IGNORE INTO evolution_exposure VALUES(?,?,?,?,?,?)",
                           (*key, kind, unit, split, dataset_id))
            db.execute("INSERT INTO evolution_evaluations VALUES(?,?,?,?,?,?,?)",
                       (*key, candidate_id, split, dataset_id, payload_digest, _json(scores)))
            evaluator = _ARTIFACT_EVALUATOR if specification else _EVALUATOR
            self._audit(db, key, actor, "evaluate", {"id": candidate_id, "split": split, "evaluator": evaluator})
            return self._reports(db, key, candidate)

    def promote(self, scope, skill_id, candidate_id, actor, *, evaluation_digest):
        key = self._key(scope, skill_id)
        with self._transaction(project=scope["project_id"], wiki_item=key) as db:
            item = self._item(db, key)
            candidate = self._candidate(db, key, candidate_id)
            report = self._reports(db, key, candidate)
            if report["evaluation_digest"] != _version(evaluation_digest) or not self._passes(report):
                raise EvolutionError("current evaluation does not authorize promotion")
            if candidate["kind"] == "fixture" and not self.fixture_promotion:
                raise EvolutionError("fixture evidence cannot authorize promotion")
            if candidate["kind"] == "authorized" and self.fixture_promotion:
                raise EvolutionError("authorized evidence cannot publish from a fixture ledger")
            if item["active_candidate"] == candidate_id:
                return {"published_version": item["active"], "evidence_kind": candidate["kind"]}
            if item["active"] != candidate["parent"]:
                raise EvolutionError("candidate parent is no longer active")
            lineage = self._release_chain(db, key, item)
            if (candidate["version"] == item["baseline"] or
                    any(approved["version"] == candidate["version"] for approved in lineage)):
                raise EvolutionError("an ancestor version requires rollback")
            parent_id = item["active_candidate"]
            specification = self._specification(db, key, candidate_id)
            active_spec = self._specification(db, key, parent_id)
            if active_spec is not None and (specification is None or active_spec["candidate"] != specification["parent"]):
                raise EvolutionError("active parent artifact no longer matches trial")
            prior_link = db.execute("SELECT parent_id FROM evolution_release_links WHERE scope=? AND skill=? AND id=?",
                                    (*key, candidate_id)).fetchone()
            if prior_link and prior_link[0] != parent_id:
                raise EvolutionError("previously promoted trial had a different parent approval")
            if not prior_link:
                db.execute("INSERT INTO evolution_release_links VALUES(?,?,?,?)", (*key, candidate_id, parent_id))
            self._set_active(db, key, item["active"], candidate["version"], actor, "promote",
                             candidate_id=candidate_id, details={"evaluation_digest": evaluation_digest})
            return {"published_version": candidate["version"], "evidence_kind": candidate["kind"]}

    def _set_active(self, db, key, previous, version, actor, action, *, candidate_id=None, details=None):
        db.execute("UPDATE evolution_items SET active=?,active_candidate=? WHERE scope=? AND skill=?",
                   (version, candidate_id, *key))
        db.execute("UPDATE evolution_load_requests SET state='expired' WHERE scope=? AND skill=? "
                   "AND state='confirmed'", key)
        self._audit(db, key, actor, action,
                    {"from": previous, "to": version, "candidate_id": candidate_id, **(details or {})})

    def rollback(self, scope, skill_id, expected_version, actor):
        key = self._key(scope, skill_id)
        with self._transaction(project=scope["project_id"], wiki_item=key) as db:
            item = self._item(db, key)
            current = item["active"]
            if current != _version(expected_version):
                raise EvolutionError("active version changed")
            if item["active_candidate"] is None:
                raise EvolutionError("baseline has no parent")
            chain = self._release_chain(db, key, item)
            version, parent_id = self._supported_release(db, key, item, chain[:-1], actor)
            self._set_active(db, key, current, version, actor, "rollback", candidate_id=parent_id)
            return {"published_version": version}

    def revoke_evidence(self, scope, evidence_id, actor):
        scope_id = _scope(scope)
        evidence = _digest(_identifier(evidence_id))
        with self._transaction(project=scope["project_id"]) as db:
            inserted = db.execute("INSERT OR IGNORE INTO evolution_revocations VALUES(?,?)",
                                  (scope_id, evidence))
            if inserted.rowcount:
                self._audit(db, (scope_id, None), actor, "revoke_evidence", {"evidence": evidence})
            return {"rolled_back": self._recheck_publications(db, scope_id, actor)}

    def _recheck_publications(self, db, scope_id, actor):
        changed = {}
        for item in db.execute("SELECT * FROM evolution_items WHERE scope=?", (scope_id,)).fetchall():
            key = scope_id, item["skill"]
            # Parent links are inserted before descendant approvals. Include inactive descendants
            # so a rollback or a restart cannot hide their dependence on an invalidated proof.
            links = db.execute("SELECT id,parent_id FROM evolution_release_links WHERE scope=? AND skill=? "
                               "AND parent_id IS NOT NULL ORDER BY rowid", key).fetchall()
            for child_id, parent_id in links:
                parent = self._candidate(db, key, parent_id)
                if not self._passes(self._reports(db, key, parent)):
                    self._invalidate_release(db, key, child_id, actor)
            if item["active_candidate"] is None:
                continue
            chain = self._release_chain(db, key, item)
            version, candidate_id = self._supported_release(db, key, item, chain, actor)
            if version != item["active"]:
                self._set_active(db, key, item["active"], version, actor, "evidence_rollback",
                                 candidate_id=candidate_id)
                changed[item["skill"]] = version
        return changed

    def _invalidate_release(self, db, key, candidate_id, actor):
        cursor = db.execute("INSERT OR IGNORE INTO evolution_invalidated_releases VALUES(?,?,?)",
                            (*key, candidate_id))
        if cursor.rowcount:
            self._audit(db, key, actor, "invalidate_release", {"candidate_id": candidate_id})

    def _release_chain(self, db, key, item):
        newest_first = []
        seen = set()
        candidate_id, expected = item["active_candidate"], item["active"]
        while candidate_id is not None:
            candidate = self._candidate(db, key, candidate_id)
            if candidate_id in seen or candidate["version"] != expected:
                raise EvolutionError("release lineage is inconsistent")
            seen.add(candidate_id)
            newest_first.append(candidate)
            link = db.execute("SELECT parent_id FROM evolution_release_links WHERE scope=? AND skill=? AND id=?",
                              (*key, candidate_id)).fetchone()
            candidate_id = link[0] if link else None  # Legacy waiting-v1 releases only extend the baseline.
            expected = candidate["parent"]
        if expected != item["baseline"]:
            raise EvolutionError("release lineage is missing its baseline")
        return newest_first[::-1]

    def _supported_release(self, db, key, item, chain, actor):
        version, candidate_id = item["baseline"], None
        broken = False
        for candidate in chain:
            if broken:
                self._invalidate_release(db, key, candidate["id"], actor)
            elif not self._passes(self._reports(db, key, candidate)):
                broken = True
            else:
                version, candidate_id = candidate["version"], candidate["id"]
        return version, candidate_id

    def check_asset(self, scope, skill_id, version, asset):
        """Bind a served artifact to its active approved provenance."""
        key = self._key(scope, skill_id)
        _version(version)
        with self._transaction(write=False, project=scope["project_id"], wiki_item=key) as db:
            item = self._item(db, key)
            if version != item["active"]:
                raise EvolutionError("asset version is not published")
            specification = self._specification(db, key, item["active_candidate"])
            if specification:
                if any(asset.get(name) != value for name, value in specification["candidate"].items()):
                    raise EvolutionError("published artifact provenance mismatch")
            elif version not in (WAITING_BASELINE_VERSION, WAITING_CANDIDATE_VERSION):
                if asset.get("sha256") != version:
                    raise EvolutionError("baseline artifact digest mismatch")

    @staticmethod
    def _attempt_key(key, attempt_id, generation):
        return *key, _identifier(attempt_id), _uint(generation)

    @staticmethod
    def _attempt(db, key):
        row = db.execute("SELECT * FROM evolution_attempts WHERE scope=? AND skill=? AND attempt=? "
                         "AND generation=?", key).fetchone()
        if row is None:
            raise EvolutionError("attempt is not pinned")
        return row

    @staticmethod
    def _withdrawn_version(db, key, version, published):
        if version is None or version == published:
            return False
        if db.execute(
            """SELECT 1 FROM evolution_candidates c JOIN evolution_invalidated_releases i
               ON (c.scope,c.skill,c.id)=(i.scope,i.skill,i.id)
               WHERE c.scope=? AND c.skill=? AND c.version=? LIMIT 1""", (*key, version),
        ).fetchone():
            return True
        return db.execute(
            """SELECT 1 FROM evolution_candidates c
               JOIN evolution_evaluations e ON (c.scope,c.skill,c.id)=(e.scope,e.skill,e.id)
               JOIN json_each(e.scores) score
               JOIN evolution_wiki_dependencies w ON (w.scope,w.skill)=(c.scope,c.skill)
                    AND w.evidence=json_extract(score.value,'$.evidence') AND w.withdrawn=1
               WHERE c.scope=? AND c.skill=? AND c.version=? LIMIT 1""", (*key, version),
        ).fetchone() is not None

    def pin_attempt(self, scope, skill_id, attempt_id, generation, actor):
        key = self._attempt_key(self._key(scope, skill_id), attempt_id, generation)
        with self._transaction(project=scope["project_id"], wiki_item=key[:2]) as db:
            active = self._item(db, key[:2])["active"]
            previous = db.execute("SELECT * FROM evolution_attempts WHERE scope=? AND skill=? AND attempt=? "
                                  "ORDER BY generation DESC LIMIT 1", key[:3]).fetchone()
            if previous and previous["generation"] > generation:
                raise EvolutionError("stale attempt generation")
            pinned = (previous["loaded"] or previous["pinned"]) if previous else active
            if self._withdrawn_version(db, key[:2], pinned, active):
                raise EvolutionError("pinned version evidence was withdrawn")
            inserted = db.execute("INSERT OR IGNORE INTO evolution_attempts VALUES(?,?,?,?,?,NULL)",
                                  (*key, pinned))
            if inserted.rowcount:
                self._audit(db, key[:2], actor, "pin_attempt",
                            {"attempt_id": attempt_id, "generation": generation, "version": pinned})
            return {"pinned_version": self._attempt(db, key)["pinned"]}

    def _current_attempt(self, db, key):
        attempt = self._attempt(db, key)
        latest = db.execute("SELECT MAX(generation) FROM evolution_attempts WHERE scope=? AND skill=? AND attempt=?",
                            key[:3]).fetchone()[0]
        if latest != key[3]:
            raise EvolutionError("stale attempt generation")
        return attempt

    def _request(self, db, key, request_id, version):
        request = db.execute("SELECT * FROM evolution_load_requests WHERE request=?",
                             (_identifier(request_id),)).fetchone()
        if request and tuple(request)[1:6] != (*key, version):
            raise EvolutionError("load request target or version changed")
        return request

    def confirm_loading(self, scope, skill_id, attempt_id, generation, version, request_id, actor,
                        *, ttl_seconds=300):
        key = self._attempt_key(self._key(scope, skill_id), attempt_id, generation)
        _version(version)
        _identifier(actor)
        if not 0 < _uint(ttl_seconds, 900):
            raise EvolutionError("invalid confirmation lifetime")
        with self._transaction(project=scope["project_id"], wiki_item=key[:2]) as db:
            attempt = self._current_attempt(db, key)
            active = self._item(db, key[:2])["active"]
            if self._withdrawn_version(db, key[:2], version, active):
                raise EvolutionError("target version evidence was withdrawn")
            request = self._request(db, key, request_id, version)
            if request:
                if request["actor"] != actor:
                    raise EvolutionError("load confirmation actor changed")
                return {"request_id": request_id, "state": request["state"]}
            if version != active or version == attempt["loaded"]:
                raise EvolutionError("target version is not an available change")
            db.execute("UPDATE evolution_load_requests SET state='expired' WHERE scope=? AND skill=? "
                       "AND attempt=? AND generation=? AND state='confirmed' AND expires<=?", (*key, self.clock()))
            if db.execute("SELECT 1 FROM evolution_load_requests WHERE scope=? AND skill=? AND attempt=? "
                          "AND generation=? AND state IN ('confirmed','dispatched','pending_restart')", key).fetchone():
                raise EvolutionError("load request already in progress")
            db.execute("INSERT INTO evolution_load_requests VALUES(?,?,?,?,?,?,?,?,'confirmed')",
                       (request_id, *key, version, actor, self.clock() + ttl_seconds))
            self._audit(db, key[:2], actor, "confirm_loading", {"request_id": request_id})
            return {"request_id": request_id, "state": "confirmed"}

    def authorize_loading(self, scope, skill_id, attempt_id, generation, version, request_id, actor):
        key = self._attempt_key(self._key(scope, skill_id), attempt_id, generation)
        _version(version)
        with self._transaction(project=scope["project_id"], wiki_item=key[:2]) as db:
            self._current_attempt(db, key)
            request = self._request(db, key, request_id, version)
            active = self._item(db, key[:2])["active"]
            if self._withdrawn_version(db, key[:2], version, active):
                return {"dispatch": False, "state": "evidence_revoked"}
            if request is None or request["state"] != "confirmed":
                return {"dispatch": False, "state": request["state"] if request else "unknown"}
            if self.clock() >= request["expires"] or active != version:
                db.execute("UPDATE evolution_load_requests SET state='expired' WHERE request=?", (request_id,))
                self._audit(db, key[:2], actor, "expire_load", {"request_id": request_id})
                return {"dispatch": False, "state": "expired"}
            db.execute("UPDATE evolution_load_requests SET state='dispatched' WHERE request=?", (request_id,))
            self._audit(db, key[:2], actor, "authorize_loading", {"request_id": request_id})
            return {"dispatch": True, "state": "dispatched"}

    def record_loading(self, scope, skill_id, attempt_id, generation, version, actor,
                       *, request_id=None, result="loaded"):
        key = self._attempt_key(self._key(scope, skill_id), attempt_id, generation)
        _version(version)
        if not isinstance(result, str) or result not in _RECEIPT_RESULTS:
            raise EvolutionError("invalid host loading result")
        with self._transaction(project=scope["project_id"], wiki_item=key[:2]) as db:
            active = self._item(db, key[:2])["active"]
            if self._withdrawn_version(db, key[:2], version, active):
                raise EvolutionError("load receipt version evidence was withdrawn")
            attempt = self._current_attempt(db, key)
            if request_id is None:
                if result != "loaded" or version != attempt["pinned"]:
                    raise EvolutionError("startup receipt does not match pinned version")
                if attempt["loaded"] is not None:
                    return {"actual_version": attempt["loaded"], "replayed": True}
            else:
                request = self._request(db, key, request_id, version)
                if request is None:
                    raise EvolutionError("load was not authorized")
                if request["state"] == result or (request["state"] == "loaded" and result == "pending_restart"):
                    return {"actual_version": attempt["loaded"], "replayed": True}
                if request["state"] not in {"dispatched", "pending_restart"}:
                    raise EvolutionError("load receipt conflicts with current state")
                db.execute("UPDATE evolution_load_requests SET state=? WHERE request=?", (result, request_id))
            if result == "loaded":
                db.execute("UPDATE evolution_attempts SET loaded=? WHERE scope=? AND skill=? AND attempt=? "
                           "AND generation=?", (version, *key))
            self._audit(db, key[:2], actor, "record_loading", {
                "attempt_id": attempt_id, "generation": generation, "version": version,
                "request_id": request_id, "result": result,
            })
            return {"actual_version": version if result == "loaded" else attempt["loaded"], "replayed": False}

    def get_status(self, scope, skill_id, *, attempt_id=None, generation=None, candidate_id=None):
        key = self._key(scope, skill_id)
        with self._transaction(write=False, project=scope["project_id"], wiki_item=key) as db:
            item = self._item(db, key)
            active = item["active"]
            assessment = self._reports(db, key, self._candidate(db, key, candidate_id)) if candidate_id else None
            pinned = loaded = None
            state = "unknown"
            if attempt_id is not None or generation is not None:
                attempt_key = self._attempt_key(key, attempt_id, generation)
                attempt = self._current_attempt(db, attempt_key)
                pinned, loaded = attempt["pinned"], attempt["loaded"]
                state = "loaded" if loaded else "unknown"
                request = db.execute("SELECT state,expires,version FROM evolution_load_requests WHERE "
                                     "scope=? AND skill=? AND attempt=? AND generation=? ORDER BY rowid DESC LIMIT 1",
                                     attempt_key).fetchone()
                if request:
                    state = request["state"]
                    if state == "confirmed" and self.clock() >= request["expires"]:
                        state = "expired"
                    if self._withdrawn_version(db, key, request["version"], active):
                        state = "evidence_revoked"
                if self._withdrawn_version(db, key, pinned, active):
                    pinned, state = None, "evidence_revoked"
                if self._withdrawn_version(db, key, loaded, active):
                    loaded, state = None, "evidence_revoked"
            return {
                "published_version": active, "pinned_version": pinned, "loaded_version": loaded,
                "has_update": loaded is not None and active != loaded, "loading_state": state,
                "published_candidate_id": item["active_candidate"], "assessment": assessment,
            }

    def list_status(self, project_id, limit=50):
        project_id = _identifier(project_id)
        if not 0 < _uint(limit, 50):
            raise EvolutionError("invalid evolution list limit")
        with self._transaction(write=False, project=project_id) as db:
            rows = db.execute(
                """SELECT item.*, COALESCE(item.active_candidate, (
                       SELECT candidate.id FROM evolution_candidates candidate
                       WHERE candidate.scope=item.scope AND candidate.skill=item.skill
                       ORDER BY candidate.rowid DESC LIMIT 1
                   )) AS shown_candidate FROM evolution_items item
                   WHERE json_extract(item.scope, '$[0]')=?
                   ORDER BY item.scope, item.skill LIMIT ?""",
                (project_id, limit),
            )
            items = []
            for row in rows:
                _, tool, tool_version = json.loads(row["scope"])
                candidate_id = row["shown_candidate"]
                item = {"tool": tool, "tool_version": tool_version, "skill_id": row["skill"],
                        "published_version": row["active"], "candidate_id": candidate_id,
                        "state": "baseline", "evidence_revoked": False}
                if candidate_id:
                    key = row["scope"], row["skill"]
                    candidate = self._candidate(db, key, candidate_id)
                    report = self._reports(db, key, candidate)
                    splits = report["splits"]
                    verdicts = {split["verdict"] for split in splits.values()}
                    if report.get("state") == "evidence_revoked":
                        item.update(state="evidence_revoked", evidence_revoked=True)
                        items.append(item)
                        continue
                    item.update(candidate_version=candidate["version"], evidence_kind=candidate["kind"],
                                evidence_revoked=any(split["evidence_revoked"] for split in splits.values()))
                    if row["active_candidate"]:
                        item["state"] = "published"
                    elif "rejected" in verdicts:
                        item["state"] = "rejected"
                    elif self._passes(report):
                        item["state"] = "verified"
                    elif "insufficient_evidence" in verdicts:
                        item["state"] = "insufficient_evidence"
                    else:
                        item["state"] = "under_review"
                items.append(item)
            return {"items": items}


def _read_operator_json(path):
    with open(path, "rb") as handle:
        payload = handle.read(2_000_001)
    if len(payload) > 2_000_000:
        raise EvolutionError("operator input exceeds size limit")
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise EvolutionError("operator input must be a JSON object")
    return value


def _operator_verifier(path, arguments):
    manifest = _read_operator_json(path)
    required = {"scope", "candidate_id", "dataset_id", "reviewer", "case_sha256"}
    if set(manifest) != required or not isinstance(manifest["case_sha256"], dict):
        raise EvolutionError("invalid authorized evidence manifest")
    for name in ("scope", "candidate_id", "dataset_id"):
        if manifest[name] != arguments.get(name):
            raise EvolutionError("evidence manifest is for a different evaluation")
    _scope(manifest["scope"])
    _identifier(manifest["reviewer"])
    digests = manifest["case_sha256"]
    for evidence_id, digest in digests.items():
        _identifier(evidence_id)
        _version(digest)
    if set(digests) != {case.get("evidence_id") for case in arguments.get("cases", [])}:
        raise EvolutionError("evidence manifest does not contain the exact evaluation cohort")

    def verify(scope, case):
        return scope == manifest["scope"] and digests.get(case["evidence_id"]) == _digest(case)

    return verify


def main():
    """Run only human-operated ledger commands from the service owner account."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--actor")
    parser.add_argument("--fixture-sandbox", action="store_true")
    parser.add_argument("--approved-evidence")
    parser.add_argument("--wiki-database", help="current authoritative Hub task and wiki database")
    reads = {"get_status", "list_status"}
    writes = {"register_baseline", "propose", "evaluate", "promote", "rollback", "revoke_evidence"}
    parser.add_argument("operation", choices=sorted(reads | writes))
    parser.add_argument("arguments", help="JSON file whose keys match the ledger method arguments")
    options = parser.parse_args()
    try:
        arguments = _read_operator_json(options.arguments)
        if "actor" in arguments:
            raise EvolutionError("provide actor via --actor")
        if options.operation in writes:
            arguments["actor"] = _identifier(options.actor)
        verifier = None
        if options.approved_evidence:
            if options.operation != "evaluate" or options.fixture_sandbox:
                raise EvolutionError("approved evidence is for ordinary evaluation only")
            verifier = _operator_verifier(options.approved_evidence, arguments)
        ledger = EvolutionLedger(options.db, verify_evidence=verifier,
                                 allow_fixture_promotion=options.fixture_sandbox,
                                 wiki_database=options.wiki_database)
        result = getattr(ledger, options.operation)(**arguments)
    except (OSError, sqlite3.Error, ValueError, TypeError, AttributeError) as error:
        parser.exit(2, f"evolution: {error}\n")
    print(_json(result))


if __name__ == "__main__":
    main()
