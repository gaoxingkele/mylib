"""Opt-in transfer of approved artifacts to authenticated task hosts."""

import hashlib
import json
from pathlib import Path, PurePosixPath
import re

from .evolution import EvolutionError


_MAX_ASSET = 64 * 1024
_MAX_MANIFEST = 256 * 1024
_DIGEST = re.compile(r"[a-f0-9]{64}")
_REVISION = re.compile(r"(?:[a-f0-9]{40}|[a-f0-9]{64})")
_HUMAN_OPS = {"preview_evolution_loading", "confirm_evolution_loading"}
_SOURCE_OPS = {"prepare_evolution_loading", "report_loading"}
_FROZEN_ASSET_FIELDS = {
    "project", "task_id", "tool", "tool_version", "skill_id", "version", "kind",
    "revision", "path", "sha256", "size",
}
_ASSET_VIEW = ("version", "kind", "revision", "path", "sha256", "size")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS adoption_confirmations (
    request_id TEXT PRIMARY KEY, binding TEXT NOT NULL, skill_id TEXT NOT NULL,
    version TEXT NOT NULL, asset_sha256 TEXT NOT NULL, confirmer TEXT NOT NULL,
    grant_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS adoption_transfers (
    binding TEXT, skill_id TEXT, request_id TEXT,
    version TEXT NOT NULL, asset_sha256 TEXT NOT NULL,
    PRIMARY KEY (binding, skill_id, request_id)
);
"""


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _tag(value):
    if not isinstance(value, str) or not 0 < len(value) <= 256 or not value.isprintable():
        raise ValueError("invalid_adoption_identifier")
    return value


def _hash(value, pattern=_DIGEST):
    if not isinstance(value, str) or not pattern.fullmatch(value):
        raise ValueError("invalid_adoption_digest")
    return value


def _relative(value):
    path = PurePosixPath(_tag(value))
    if path.is_absolute() or ":" in value or chr(92) in value or any(
        part in {"", ".", ".."} for part in value.split("/")
    ):
        raise ValueError("invalid_adoption_path")
    return path


def _read(path, limit):
    with path.open("rb") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise ValueError("adoption_file_too_large")
    return data


def _asset_view(asset):
    return {key: asset[key] for key in _ASSET_VIEW}


class AssetManifest:
    """Hash-pinned, operator-provided mapping for approved, task-scoped text."""

    def __init__(self, manifest_path, expected_sha256, *, root=None, catalog=None):
        self.manifest_path = Path(manifest_path)
        if not self.manifest_path.is_absolute():
            raise ValueError("absolute_adoption_manifest_required")
        self.expected_sha256 = _hash(expected_sha256)
        self.root = Path(root).resolve(strict=True) if root is not None else None
        self.catalog = catalog
        self.manifest = self._load()

    def _load(self):
        data = _read(self.manifest_path, _MAX_MANIFEST)
        if _sha(data) != self.expected_sha256:
            raise ValueError("adoption_manifest_digest_mismatch")
        document = json.loads(data)
        if (not isinstance(document, dict) or set(document) != {"schema", "assets"}
                or type(document["schema"]) is not int or document["schema"] != 1
                or not isinstance(document["assets"], list) or len(document["assets"]) > 256):
            raise ValueError("invalid_adoption_manifest")
        index = {}
        for asset in document["assets"]:
            optional = {"catalog_skill_id", "catalog_resource"}
            if (not isinstance(asset, dict) or not _FROZEN_ASSET_FIELDS <= asset.keys()
                    or asset.keys() - _FROZEN_ASSET_FIELDS - optional):
                raise ValueError("invalid_adoption_asset")
            for field in ("project", "task_id", "tool", "tool_version", "skill_id"):
                _tag(asset[field])
            _hash(asset["version"])
            _hash(asset["revision"], _REVISION)
            _hash(asset["sha256"])
            kind, size = asset["kind"], asset["size"]
            path = _relative(asset["path"])
            suffixes = (".md",) if kind == "skill" else (".md", ".txt", ".json", ".toml")
            if (kind not in ("skill", "harness") or path.suffix.lower() not in suffixes
                    or type(size) is not int or not 0 < size <= _MAX_ASSET):
                raise ValueError("invalid_adoption_text_asset")
            if "catalog_skill_id" in asset:
                _hash(asset["catalog_skill_id"])
            if "catalog_resource" in asset:
                if "catalog_skill_id" not in asset:
                    raise ValueError("adoption_resource_without_skill")
                _relative(asset["catalog_resource"])
            key = tuple(asset[field] for field in ("project", "task_id", "tool", "tool_version", "skill_id", "version"))
            if key in index:
                raise ValueError("duplicate_adoption_asset")
            index[key] = asset
        return index

    def find(self, target, skill_id, version):
        if _sha(_read(self.manifest_path, _MAX_MANIFEST)) != self.expected_sha256:
            raise ValueError("adoption_manifest_digest_mismatch")
        key = tuple(target[field] for field in ("project", "task_id", "tool", "tool_version"))
        asset = self.manifest.get((*key, _tag(skill_id), _hash(version)))
        if asset is None:
            raise ValueError("adoption_asset_unavailable")
        return asset

    def read(self, asset):
        if "catalog_skill_id" in asset:
            if self.catalog is None:
                raise ValueError("adoption_catalog_unavailable")
            args = {"skill_id": asset["catalog_skill_id"], "revision": asset["revision"]}
            operation = "read_skill"
            if "catalog_resource" in asset:
                operation = "read_resource"
                args["path"] = asset["catalog_resource"]
            record = self.catalog(operation, args)
            if (not isinstance(record, dict) or record.get("truncated") is not False
                    or not isinstance(record.get("text"), str) or record.get("encoding", "utf-8") != "utf-8"
                    or record.get("skill_id") != asset["catalog_skill_id"]
                    or any(record.get(key) != asset[key] for key in ("revision", "path", "sha256", "size"))):
                raise ValueError("adoption_catalog_asset_mismatch")
            data = record["text"].encode("utf-8")
        else:
            if self.root is None:
                raise ValueError("adoption_asset_root_unavailable")
            release = self.root / asset["revision"]
            resolved = (release / Path(*_relative(asset["path"]).parts)).resolve(strict=True)
            if release.is_symlink() or not resolved.is_relative_to(release):
                raise ValueError("adoption_asset_escaped_root")
            data = _read(resolved, _MAX_ASSET)
        if len(data) != asset["size"] or _sha(data) != asset["sha256"] or b"\x00" in data:
            raise ValueError("adoption_asset_digest_mismatch")
        return data.decode("utf-8")


def _target(value):
    if not isinstance(value, dict) or set(value) != {"task_id", "attempt_id", "generation"}:
        raise ValueError("invalid_adoption_target")
    _tag(value["task_id"])
    _tag(value["attempt_id"])
    generation = value["generation"]
    if type(generation) is int and 0 <= generation < 2**63:
        return value
    _tag(generation)
    return value


def _scope(current):
    return {"project_id": current["project"], "tool": current["tool"], "tool_version": current["tool_version"]}


def _binding(current):
    return _sha(_json(current).encode())


def _public_target(current):
    return {key: value for key, value in current.items() if key not in {"source", "account", "session_id"}}


def _load_key(current, skill_id):
    # Opaque generations are already bound into the identity digest.
    return _scope(current), skill_id, _binding(current), 0


def _current(db, project, target):
    row = db.execute(
        """SELECT a.payload,a.source,a.role,t.primary_attempt_id FROM task_attempts a
           JOIN task_current t ON (a.project,a.task_id)=(t.project,t.task_id)
           WHERE a.project=? AND a.task_id=? AND a.attempt_id=?""",
        (project, target["task_id"], target["attempt_id"]),
    ).fetchone()
    if row is None or (row["role"] != "verify" and row["primary_attempt_id"] != target["attempt_id"]):
        raise PermissionError("adoption_attempt_inactive")
    attempt = json.loads(row["payload"])
    if attempt.get("generation") != target["generation"] or type(attempt.get("generation")) is not type(target["generation"]):
        raise PermissionError("adoption_generation_changed")
    names = ("host", "host_installation_id", "window_id", "tool", "tool_version", "account", "session_id")
    return {**target, "project": project, "source": row["source"], "role": row["role"],
            **{key: _tag(attempt.get(key)) for key in names}}


def _allowed(grant, current, kind):
    scopes = grant.get("scopes", ())
    if grant.get("project") != current["project"] or current["account"] not in grant.get("accounts", ()):
        return False
    if kind == "source":
        return ("evolution:source" in scopes and grant.get("subject") == current["source"]
                and grant.get("host") == current["host"]
                and grant.get("host_installation_id") == current["host_installation_id"]
                and current["tool"] in grant.get("tools", ()))
    return ("evolution:confirm" in scopes and "tasks:read" in scopes
            and current["host_installation_id"] in grant.get("evolution_hosts", ()))


class AdoptionService:
    """Persist read permits separately from actual host loading receipts."""

    def __init__(self, store, ledger, grants, assets):
        self.store, self.ledger, self.grants, self.assets = store, ledger, grants, assets
        with store._db(write=True) as db:
            for statement in _SCHEMA.split(";"):
                if statement.strip():
                    db.execute(statement)

    def _authorize(self, grant, current, kind):
        if not _allowed(grant, current, kind):
            raise PermissionError("adoption_grant_denied")
        if self.grants.resolve(grant["sha256"], current["project"]) != grant:
            raise PermissionError("adoption_grant_changed")

    def _original_confirmation(self, db, current, skill_id, request_id):
        row = db.execute("SELECT * FROM adoption_confirmations WHERE request_id=?", (_tag(request_id),)).fetchone()
        if row is None or (row["binding"], row["skill_id"]) != (_binding(current), skill_id):
            raise PermissionError("adoption_confirmation_missing")
        human = self.grants.resolve(row["grant_sha256"], current["project"])
        self._authorize(human, current, "human")
        if human["subject"] != row["confirmer"]:
            raise PermissionError("adoption_confirmation_changed")
        return row

    def _describe(self, current, skill_id):
        scope, skill_id, attempt, generation = _load_key(current, skill_id)
        status = self.ledger.get_status(scope, skill_id)
        asset = self._approved_asset(current, skill_id, status["published_version"])
        try:
            loaded = self.ledger.get_status(scope, skill_id, attempt_id=attempt, generation=generation)["loaded_version"]
        except EvolutionError as error:
            if str(error) != "attempt is not pinned":
                raise
            loaded = None
        return asset, loaded

    def _approved_asset(self, current, skill_id, version):
        asset = self.assets.find(current, skill_id, version)
        self.ledger.check_asset(_scope(current), skill_id, version, asset)
        return asset

    def request(self, grant, operation, project, *, target, skill_id, version=None, asset_sha256=None,
                request_id=None, result=None):
        target = _target(target)
        skill_id = _tag(skill_id)
        if operation not in _HUMAN_OPS | _SOURCE_OPS:
            raise ValueError("unknown_adoption_operation")
        if operation == "prepare_evolution_loading":
            return self._prepare(grant, project, target, skill_id, request_id)
        with self.store._db(write=operation != "preview_evolution_loading") as db:
            current = _current(db, project, target)
            self._authorize(grant, current, "human" if operation in _HUMAN_OPS else "source")
            if operation == "report_loading":
                return self._report(db, grant, current, skill_id, version, asset_sha256, request_id, result)
            if operation == "confirm_evolution_loading":
                return self._confirm(db, grant, current, skill_id, version, asset_sha256, request_id)
            asset, loaded = self._describe(current, skill_id)
            return {"state": "preview", "target": _public_target(current), "skill_id": skill_id,
                    "asset": _asset_view(asset), "loaded_version": loaded}

    def _confirm(self, db, grant, current, skill_id, version, asset_sha256, request_id):
        _hash(version)
        _hash(asset_sha256)
        _tag(request_id)
        key = _load_key(current, skill_id)
        prior = db.execute("SELECT * FROM adoption_confirmations WHERE request_id=?", (request_id,)).fetchone()
        expected = (request_id, _binding(current), skill_id, version, asset_sha256, grant["subject"], grant["sha256"])
        if prior and tuple(prior) != expected:
            raise PermissionError("adoption_confirmation_conflict")
        if prior:
            if self.ledger.get_status(key[0], skill_id)["published_version"] != version:
                raise PermissionError("adoption_version_withdrawn")
            asset = self._approved_asset(current, skill_id, version)
        else:
            asset, _ = self._describe(current, skill_id)
        if (asset["version"], asset["sha256"]) != (version, asset_sha256):
            raise PermissionError("adoption_preview_changed")
        status = self.ledger.confirm_loading(*key, version, request_id, grant["subject"])
        if not prior:
            db.execute("INSERT INTO adoption_confirmations VALUES(?,?,?,?,?,?,?)", expected)
        return {**status, "target": _public_target(current), "skill_id": skill_id, "asset": _asset_view(asset)}

    def _prepare(self, grant, project, target, skill_id, request_id):
        with self.store._db(write=True) as db:
            current = _current(db, project, target)
            self._authorize(grant, current, "source")
            key = _load_key(current, skill_id)
            if request_id is None:
                pinned = self.ledger.pin_attempt(*key, grant["subject"])
                version = pinned["pinned_version"]
                expected_sha = None
            else:
                consent = self._original_confirmation(db, current, skill_id, request_id)
                version, expected_sha = consent["version"], consent["asset_sha256"]
            if self.ledger.get_status(key[0], skill_id)["published_version"] != version:
                raise PermissionError("adoption_version_withdrawn")
            asset = self._approved_asset(current, skill_id, version)
            if expected_sha is not None and expected_sha != asset["sha256"]:
                raise PermissionError("adoption_preview_changed")
        text = self.assets.read(asset)
        with self.store._db(write=True) as db:
            fresh = _current(db, project, target)
            if fresh != current:
                raise PermissionError("adoption_target_changed")
            self._authorize(grant, fresh, "source")
            if self.ledger.get_status(key[0], skill_id)["published_version"] != version:
                raise PermissionError("adoption_version_withdrawn")
            if self._approved_asset(fresh, skill_id, version) != asset:
                raise PermissionError("adoption_target_changed")
            if request_id is not None:
                self._original_confirmation(db, fresh, skill_id, request_id)
                permission = self.ledger.authorize_loading(*key, version, request_id, grant["subject"])
                if not permission["dispatch"]:
                    return {"state": permission["state"], "request_id": request_id, "dispatch": False}
            db.execute("INSERT OR IGNORE INTO adoption_transfers VALUES(?,?,?,?,?)",
                       (_binding(current), skill_id, request_id or "", version, asset["sha256"]))
            return {"state": "retrieved", "target": _public_target(current), "skill_id": skill_id,
                    "request_id": request_id, "dispatch": True, "asset": {**_asset_view(asset), "text": text}}

    def _report(self, db, grant, current, skill_id, version, asset_sha256, request_id, result):
        _hash(version)
        _hash(asset_sha256)
        if request_id is not None:
            self._original_confirmation(db, current, skill_id, request_id)
        transfer = db.execute("SELECT version,asset_sha256 FROM adoption_transfers WHERE "
                              "binding=? AND skill_id=? AND request_id=?",
                              (_binding(current), skill_id, request_id or "")).fetchone()
        if transfer is None or tuple(transfer) != (version, asset_sha256):
            raise PermissionError("adoption_asset_receipt_mismatch")
        key = _load_key(current, skill_id)
        if self.ledger.get_status(key[0], skill_id)["published_version"] != version:
            raise PermissionError("adoption_version_withdrawn")
        asset = self._approved_asset(current, skill_id, version)
        if asset["sha256"] != asset_sha256:
            raise PermissionError("adoption_asset_receipt_mismatch")
        receipt = self.ledger.record_loading(*key, version, grant["subject"], request_id=request_id, result=result)
        return {**receipt, "state": result, "version": version, "asset_sha256": asset_sha256}

    def status_for(self, grant, project, *, task_id, attempt_id, generation, skill_id, candidate_id=None):
        target = _target({"task_id": task_id, "attempt_id": attempt_id, "generation": generation})
        with self.store._db() as db:
            current = _current(db, project, target)
            if (grant.get("project") != project or "tasks:read" not in grant.get("scopes", ())
                    or self.grants.resolve(grant["sha256"], project) != grant):
                raise PermissionError("adoption_read_denied")
            scope, skill_id, attempt, generation = _load_key(current, skill_id)
            try:
                status = self.ledger.get_status(scope, skill_id, attempt_id=attempt, generation=generation,
                                                candidate_id=candidate_id)
            except EvolutionError as error:
                if str(error) != "attempt is not pinned":
                    raise
                status = self.ledger.get_status(scope, skill_id, candidate_id=candidate_id)
            return {**status, "tool": scope["tool"], "tool_version": scope["tool_version"],
                    "target": _public_target(current)}


def load_task_asset(call, project, target, skill_id, loader, *, request_id=None):
    """The authorized host supplies a typed loader for its specific runtime.

    The loader verifies the real applied bytes and returns its observation.
    A read, staged file or missing receipt does not imply effective loading.
    """
    arguments = {"project": project, "target": _target(target), "skill_id": _tag(skill_id),
                 "request_id": request_id}
    offer = call("prepare_evolution_loading", arguments)
    if offer.get("dispatch") is not True:
        return offer
    asset = offer.get("asset")
    if not isinstance(asset, dict) or not isinstance(asset.get("text"), str):
        raise ValueError("adoption_host_invalid_asset")
    data = asset["text"].encode("utf-8")
    if len(data) != asset.get("size") or len(data) > _MAX_ASSET or _sha(data) != asset.get("sha256"):
        raise ValueError("adoption_host_asset_digest_mismatch")
    public = offer.get("target")
    if (offer.get("request_id") != request_id or offer.get("skill_id") != skill_id
            or not isinstance(public, dict) or public.get("project") != project
            or any(public.get(key) != value or type(public.get(key)) is not type(value)
                   for key, value in target.items())):
        raise PermissionError("adoption_host_target_mismatch")
    observation = loader(public, _asset_view(asset), data)
    if not isinstance(observation, dict) or observation.get("result") not in ("loaded", "pending_restart", "failed"):
        raise ValueError("adoption_host_invalid_observation")
    result = observation["result"]
    if result == "loaded" and observation.get("effective_sha256") != asset["sha256"]:
        raise ValueError("adoption_host_effective_hash_mismatch")
    return call("report_loading", {**arguments, "version": asset["version"],
                                  "asset_sha256": asset["sha256"], "result": result})
