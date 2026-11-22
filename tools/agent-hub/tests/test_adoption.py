"""Synthetic gates and a real loopback SDK/control transport."""

import asyncio
import hashlib
import json
import secrets
import socket

import pytest

from agent_hub.adoption import AdoptionService, AssetManifest, load_task_asset
from agent_hub.client import call_tool, call_tool_async
from agent_hub.evolution import EvolutionError, EvolutionLedger, WAITING_BASELINE_VERSION, WAITING_CANDIDATE_VERSION
from agent_hub.server import Grants, create_app, token_digest
from agent_hub.storage import Store


PROJECT = "pilot"
SCOPE = {"project_id": PROJECT, "tool": "codex", "tool_version": "pilot.1"}
TARGET = {"task_id": "task", "attempt_id": "attempt-a", "generation": "opaque-1"}
SKILL = "hub-alerts"
BASE = WAITING_BASELINE_VERSION
CANDIDATE = WAITING_CANDIDATE_VERSION


def sha(data):
    return hashlib.sha256(data).hexdigest()


def event(**updates):
    return {**TARGET, "event_id": "registered", "host": "computer-a", "host_installation_id": "install-a",
            "window_id": "window-a", "session_id": "session-a", "account": "team-seat",
            "tool": "codex", "tool_version": "pilot.1", "status": "running", "summary": "Fixture",
            **updates}


def write_grants(path, records):
    path.write_text(json.dumps({"grants": list(records)}))
    path.chmod(0o600)


def setup(tmp_path):
    store = Store(tmp_path / "hub.sqlite")
    ledger = EvolutionLedger(tmp_path / "fixture-evolution.sqlite", allow_fixture_promotion=True)
    ledger.register_baseline(SCOPE, SKILL, BASE, "fixture-operator")
    root = tmp_path / "fixed"
    assets, texts = [], {}
    for version, revision, body in ((BASE, "a"*40, "timeout = 300\n"), (CANDIDATE, "b"*40, "require_signal = true\n")):
        directory = root / revision / "harness"
        directory.mkdir(parents=True)
        text = body.encode("utf-8")
        (directory / "rule.toml").write_bytes(text)
        assets.append({"project": PROJECT, "task_id": TARGET["task_id"], "tool": "codex", "tool_version": "pilot.1",
                       "skill_id": SKILL, "version": version, "kind": "harness", "revision": revision,
                       "path": "harness/rule.toml", "sha256": sha(text), "size": len(text)})
        texts[version] = text
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"schema": 1, "assets": assets}))
    registry = AssetManifest(manifest, sha(manifest.read_bytes()), root=root)
    tokens = {key: secrets.token_urlsafe(32) for key in ("host", "human", "model", "other-host")}
    grants = {}
    for key, token in tokens.items():
        grants[key] = {"sha256": token_digest(token), "project": PROJECT, "subject": key,
                       "accounts": ["team-seat"]}
    grants["host"].update(scopes=["events:append", "evolution:source"], host="computer-a",
                          host_installation_id="install-a", tools=["codex"])
    grants["other-host"].update(scopes=grants["host"]["scopes"], host="computer-b",
                                host_installation_id="install-b", tools=["codex"])
    grants["human"].update(scopes=["tasks:read", "evolution:confirm"], evolution_hosts=["install-a"])
    grants["model"].update(scopes=["tasks:read", "chat:model"])
    path = tmp_path / "grants.json"
    write_grants(path, grants.values())
    store.report_step(PROJECT, "host", event())
    return store, ledger, registry, path, grants, tokens, texts


def publish(ledger, skill_id=SKILL, dependency=None):
    ledger.propose(SCOPE, skill_id, "trial", version=CANDIDATE, parent_version=BASE, development_id="dev",
                   heldout_id="holdout", actor="fixture-operator", evidence_kind="fixture")
    for split, name, size in (("development", "dev", 10), ("heldout", "holdout", 60)):
        cases = []
        for label in ("blocked", "clear"):
            for index in range(size):
                key = f"{name}-{label}-{index}"
                blocked = label == "blocked"
                cases.append({"evidence_id": key, "group_id": key, "label": label, "observable": True,
                              "quiet_ms": 300_000, "signal": "blocked" if blocked else None,
                              "signal_delay_ms": 1_000 if blocked else None, "trusted_current": blocked})
        if dependency and split == "heldout":
            cases[0]["wiki_dependency"] = dependency
        proof = ledger.evaluate(SCOPE, skill_id, "trial", split, name, cases, "fixture-operator")
    ledger.promote(SCOPE, skill_id, "trial", "fixture-operator", evaluation_digest=proof["evaluation_digest"])
    return proof["evaluation_digest"]


def test_wiki_withdrawal_survives_hub_restart_and_masks_only_dependent_trial(tmp_path):
    import sqlite3

    from agent_hub.wiki_sync import withdraw_wiki

    store, ledger, registry, path, grants, _, texts = setup(tmp_path)
    ledger.bind_wiki_database(store.path)
    service = AdoptionService(store, ledger, Grants(path), registry)
    service.request(grants["host"], "prepare_evolution_loading", PROJECT, target=TARGET, skill_id=SKILL)
    service.request(grants["host"], "report_loading", PROJECT, target=TARGET, skill_id=SKILL,
                    version=BASE, asset_sha256=sha(texts[BASE]), result="loaded")
    source_text = "# Fixture evidence\nMeasurable observation."
    store.report_step(PROJECT, "host", event(
        event_id="evidence", task_id="evidence-task", attempt_id="evidence-attempt",
        wiki={"entry_id": "evaluation-evidence", "version": "one",
              "path": "omx_wiki/evaluation-evidence.md", "body": source_text},
    ))
    dependency = {"entry_id": "evaluation-evidence", "version": "one", "sha256": sha(source_text.encode())}
    approved = publish(ledger, dependency=dependency)
    independent = "independent-alerts"
    ledger.register_baseline(SCOPE, independent, BASE, "fixture-operator")
    publish(ledger, independent)
    confirmation = dict(target=TARGET, skill_id=SKILL, version=CANDIDATE,
                        asset_sha256=sha(texts[CANDIDATE]), request_id="on-revoked-proof")
    service.request(grants["human"], "confirm_evolution_loading", PROJECT, **confirmation)
    service.request(grants["host"], "prepare_evolution_loading", PROJECT, target=TARGET,
                    skill_id=SKILL, request_id=confirmation["request_id"])

    # The wiki commits and the original service then disappears before any evolution access.
    withdraw_wiki(store, PROJECT, "host", dependency["entry_id"], "withdraw-proof")
    unbound = EvolutionLedger(ledger.path, allow_fixture_promotion=True)
    with pytest.raises(EvolutionError, match="authority is required"):
        unbound.get_status(SCOPE, SKILL)
    assert unbound.get_status(SCOPE, independent)["published_version"] == CANDIDATE
    restarted = EvolutionLedger(ledger.path, allow_fixture_promotion=True, wiki_database=store.path)
    with pytest.raises(EvolutionError, match="does not authorize"):
        restarted.promote(SCOPE, SKILL, "trial", "fixture-operator", evaluation_digest=approved)
    reopened = EvolutionLedger(ledger.path, allow_fixture_promotion=True, wiki_database=store.path)
    status = reopened.get_status(SCOPE, SKILL, candidate_id="trial")
    assert status["published_version"] == BASE and status["published_candidate_id"] is None
    assert status["assessment"]["state"] == "evidence_revoked"
    assert status["assessment"]["splits"] == {} and status["assessment"]["evaluation_digest"] is None
    assert dependency["entry_id"] not in json.dumps(status)
    candidates = {row["skill_id"]: row for row in reopened.list_status(PROJECT)["items"]}
    assert candidates[independent]["published_version"] == CANDIDATE
    assert candidates[SKILL]["state"] == "evidence_revoked" and "candidate_version" not in candidates[SKILL]

    read_denied = AdoptionService(store, reopened, Grants(path), registry)
    attempt_status = read_denied.status_for(grants["human"], PROJECT, **TARGET, skill_id=SKILL)
    assert attempt_status["loading_state"] == "evidence_revoked"
    assert attempt_status["loaded_version"] == BASE
    with pytest.raises(PermissionError, match="adoption_version_withdrawn"):
        read_denied.request(grants["human"], "confirm_evolution_loading", PROJECT, **confirmation)
    with pytest.raises(PermissionError, match="adoption_version_withdrawn"):
        read_denied.request(grants["host"], "prepare_evolution_loading", PROJECT, target=TARGET,
                            skill_id=SKILL, request_id=confirmation["request_id"])
    with pytest.raises(PermissionError, match="adoption_version_withdrawn"):
        read_denied.request(grants["host"], "report_loading", PROJECT, **confirmation, result="loaded")
    with sqlite3.connect(ledger.path) as db:
        assert db.execute("SELECT count(*) FROM evolution_audit WHERE action='wiki_evidence_withdrawn'").fetchone()[0] == 1


def test_grants_binding_and_manifest_are_rechecked(tmp_path):
    store, ledger, registry, path, grants, _, texts = setup(tmp_path)
    service = AdoptionService(store, ledger, Grants(path), registry)
    base = service.request(grants["host"], "prepare_evolution_loading", PROJECT, target=TARGET, skill_id=SKILL)
    assert "text" in base["asset"] and base["state"] == "retrieved"
    status = service.status_for(grants["human"], PROJECT, **TARGET, skill_id=SKILL)
    assert status["pinned_version"] == BASE and status["loaded_version"] is None
    with pytest.raises(PermissionError):
        service.request(grants["other-host"], "report_loading", PROJECT, target=TARGET, skill_id=SKILL,
                        version=BASE, asset_sha256=sha(texts[BASE]), result="loaded")
    with pytest.raises(PermissionError):
        service.request(grants["host"], "report_loading", PROJECT, target=TARGET, skill_id=SKILL,
                        version=BASE, asset_sha256="0" * 64, result="loaded")
    service.request(grants["host"], "report_loading", PROJECT, target=TARGET, skill_id=SKILL,
                    version=BASE, asset_sha256=sha(texts[BASE]), result="loaded")
    publish(ledger)
    confirmation = dict(target=TARGET, skill_id=SKILL, version=CANDIDATE, asset_sha256=sha(texts[CANDIDATE]),
                        request_id="version-confirmation")
    with pytest.raises(PermissionError):
        service.request(grants["model"], "confirm_evolution_loading", PROJECT, **confirmation)
    service.request(grants["human"], "confirm_evolution_loading", PROJECT, **confirmation)
    prepared = service.request(grants["host"], "prepare_evolution_loading", PROJECT, target=TARGET,
                               skill_id=SKILL, request_id="version-confirmation")
    assert prepared["dispatch"] is True
    write_grants(path, [grant for key, grant in grants.items() if key != "human"])
    with pytest.raises((PermissionError, ValueError)):
        service.request(grants["host"], "report_loading", PROJECT, **confirmation, result="loaded")
    write_grants(path, grants.values())
    store.report_step(PROJECT, "other-host", event(event_id="handoff", attempt_id="attempt-b",
                      previous_attempt_id=TARGET["attempt_id"], host="computer-b", host_installation_id="install-b"))
    with pytest.raises(PermissionError):
        service.request(grants["host"], "report_loading", PROJECT, **confirmation, result="loaded")


def test_fixed_catalog_asset_cannot_be_truncated_or_redirected(tmp_path):
    _, _, registry, _, _, _, _ = setup(tmp_path)
    manifest = registry.manifest_path
    data = json.loads(manifest.read_bytes())
    asset = data["assets"][0]
    asset["catalog_skill_id"] = "c" * 64
    asset["catalog_resource"] = "rule.toml"
    body = (registry.root / asset["revision"] / asset["path"]).read_bytes()
    captured = []

    def read_catalog(name, args):
        captured.append((name, args))
        return {**asset, "skill_id": asset["catalog_skill_id"], "truncated": False, "text": body.decode()}

    manifest.write_text(json.dumps(data))
    manifest_hash = sha(manifest.read_bytes())
    catalog = AssetManifest(manifest, manifest_hash, catalog=read_catalog)
    key = {**TARGET, "project": PROJECT, "tool": "codex", "tool_version": "pilot.1"}
    offered = catalog.find(key, SKILL, BASE)
    assert catalog.read(offered) == body.decode()
    assert captured[0] == ("read_resource", {"skill_id": "c" * 64, "path": "rule.toml", "revision": "a" * 40})
    catalog.catalog = lambda name, args: {**read_catalog(name, args), "truncated": True}
    with pytest.raises(ValueError, match="catalog_asset_mismatch"):
        catalog.read(offered)
    with pytest.raises(ValueError, match="asset_unavailable"):
        catalog.find({**key, "task_id": "other-task"}, SKILL, BASE)
    manifest.write_text("{}")
    with pytest.raises(ValueError, match="manifest_digest_mismatch"):
        catalog.find(key, SKILL, BASE)


def artifact_cohort(specification, dataset, count):
    def run(asset, task, run_id, passed):
        return {"asset_sha256": asset["sha256"], "revision": asset["revision"], "task_sha256": task,
                "verifier_sha256": specification["verifier_sha256"], "run_id": run_id,
                "result_sha256": sha(run_id.encode()), "passed": passed, "critical_failure": False,
                "effectful_violation": False, "duration_ms": 100}

    result = []
    for index in range(count * 2):
        key = f"{dataset}-{index}"
        task = sha(f"immutable task fixture {key}".encode())
        result.append({"evidence_id": key, "group_id": key, "task_sha256": task,
                       "parent_run": run(specification["parent"], task, key+"-old", index < count),
                       "candidate_run": run(specification["candidate"], task, key+"-new", True)})
    return result


def prepare_generic(tmp_path):
    store, ledger, registry, path, grants, _, _ = setup(tmp_path)
    skill_id = "engineer-review"
    assets = []
    document = json.loads(registry.manifest_path.read_bytes())
    for index in range(3):
        content = f"# Fixture skill revision {index}\n".encode()
        revision = str(index + 1) * 40
        asset = {"kind": "skill", "revision": revision, "path": "skills/fixture/SKILL.md", "sha256": sha(content)}
        file = registry.root / revision / asset["path"]
        file.parent.mkdir(parents=True)
        file.write_bytes(content)
        assets.append(asset)
        document["assets"].append({**asset, "project": PROJECT, "task_id": TARGET["task_id"],
                                   "tool": SCOPE["tool"], "tool_version": SCOPE["tool_version"],
                                   "skill_id": skill_id, "version": asset["sha256"], "size": len(content)})
    registry.manifest_path.write_text(json.dumps(document))
    fixed = AssetManifest(registry.manifest_path, sha(registry.manifest_path.read_bytes()), root=registry.root)
    ledger.register_baseline(SCOPE, skill_id, assets[0]["sha256"], "fixture-operator")
    return ledger, AdoptionService(store, ledger, Grants(path), fixed), grants, skill_id, assets


def propose_artifact(ledger, skill_id, trial, parent, candidate, *, evidence_kind="fixture"):
    specification = {"parent": parent, "candidate": candidate, "verifier_sha256": "f"*64}
    ledger.propose(SCOPE, skill_id, trial, version=candidate["sha256"], parent_version=parent["sha256"],
                   development_id=trial+"-dev", heldout_id=trial+"-hold", actor="fixture-operator",
                   evidence_kind=evidence_kind, evaluator="paired-artifact-v1", provenance=specification)
    return specification


def test_generic_asset_trials_can_load_two_successive_upgrades_and_rollback(tmp_path):
    ledger, service, grants, skill_id, assets = prepare_generic(tmp_path)
    applied = []

    def host(name, args):
        args = dict(args)
        return service.request(grants["host"], name, args.pop("project"), **args)

    def loader(target, asset, data):
        assert target["generation"] == TARGET["generation"]
        applied.append(data)
        return {"result": "loaded", "effective_sha256": sha(applied[-1])}

    first = load_task_asset(host, PROJECT, TARGET, skill_id, loader)
    assert first["actual_version"] == assets[0]["sha256"]
    proofs = []
    for index, (old, new) in enumerate(zip(assets, assets[1:])):
        trial = f"artifact-{index}"
        specification = propose_artifact(ledger, skill_id, trial, old, new)
        for split, cohort, count in (("development", trial+"-dev", 10), ("heldout", trial+"-hold", 60)):
            report = ledger.evaluate(SCOPE, skill_id, trial, split, cohort,
                                     artifact_cohort(specification, cohort, count), "fixture-operator")
        assert report["evaluator"] == "paired-artifact-v1" and report["evidence_kind"] == "fixture"
        proofs.append(report["evaluation_digest"])
        ledger.promote(SCOPE, skill_id, trial, "fixture-operator", evaluation_digest=proofs[-1])
        with pytest.raises(EvolutionError, match="provenance mismatch"):
            ledger.check_asset(SCOPE, skill_id, new["sha256"], {**new, "revision": "e"*40})
        confirmed = service.request(grants["human"], "confirm_evolution_loading", PROJECT,
                                    target=TARGET, skill_id=skill_id, request_id=trial,
                                    version=new["sha256"], asset_sha256=new["sha256"])
        assert confirmed["state"] == "confirmed"
        state = service.status_for(grants["human"], PROJECT, **TARGET, skill_id=skill_id)
        assert state["loaded_version"] == old["sha256"]
        loaded = load_task_asset(host, PROJECT, TARGET, skill_id, loader, request_id=trial)
        assert loaded["actual_version"] == new["sha256"]
    assert [sha(data) for data in applied] == [asset["sha256"] for asset in assets]
    with pytest.raises(EvolutionError, match="ancestor version requires rollback"):
        propose_artifact(ledger, skill_id, "ancestor", assets[2], assets[0])
    assert ledger.rollback(SCOPE, skill_id, assets[2]["sha256"], "fixture-operator")["published_version"] == assets[1]["sha256"]
    ledger.promote(SCOPE, skill_id, "artifact-1", "fixture-operator", evaluation_digest=proofs[-1])
    ledger.rollback(SCOPE, skill_id, assets[2]["sha256"], "fixture-operator")
    result = ledger.revoke_evidence(SCOPE, "artifact-0-hold-0", "fixture-operator")
    assert result["rolled_back"] == {skill_id: assets[0]["sha256"]}
    assert ledger.get_status(SCOPE, skill_id, candidate_id="artifact-1")["assessment"]["state"] == "evidence_revoked"


def test_artifact_evaluation_refuses_mutable_refs_mismatched_runs_and_weak_proof(tmp_path):
    ledger, _, _, skill_id, assets = prepare_generic(tmp_path)
    with pytest.raises(EvolutionError, match="full immutable revision"):
        propose_artifact(ledger, skill_id, "tag", assets[0], {**assets[1], "revision": "v0.2.80"})
    with pytest.raises(EvolutionError, match="active parent"):
        propose_artifact(ledger, skill_id, "wrong-parent", assets[1], assets[2])
    spec = propose_artifact(ledger, skill_id, "untrusted", assets[0], assets[1], evidence_kind="authorized")
    with pytest.raises(EvolutionError, match="could not be verified"):
        ledger.evaluate(SCOPE, skill_id, "untrusted", "development", "untrusted-dev",
                        artifact_cohort(spec, "untrusted-dev", 10), "fixture-operator")

    spec = propose_artifact(ledger, skill_id, "paired", assets[0], assets[1])
    for field, wrong in (("revision", "9"*40), ("task_sha256", "d"*64), ("verifier_sha256", "d"*64)):
        cases = artifact_cohort(spec, "paired-dev", 10)
        cases[0]["candidate_run"][field] = wrong
        with pytest.raises(EvolutionError, match="does not match"):
            ledger.evaluate(SCOPE, skill_id, "paired", "development", "paired-dev", cases, "fixture-operator")
    developmental = artifact_cohort(spec, "paired-dev", 10)
    ledger.evaluate(SCOPE, skill_id, "paired", "development", "paired-dev", developmental, "fixture-operator")
    insufficient = artifact_cohort(spec, "paired-hold", 59)
    report = ledger.evaluate(SCOPE, skill_id, "paired", "heldout", "paired-hold", insufficient, "fixture-operator")
    assert report["splits"]["heldout"]["verdict"] == "insufficient_evidence"
    with pytest.raises(EvolutionError, match="does not authorize"):
        ledger.promote(SCOPE, skill_id, "paired", "fixture-operator", evaluation_digest=report["evaluation_digest"])


def test_wire_confirmation_and_actual_loading_are_distinct(tmp_path):
    import uvicorn
    from websockets.asyncio.client import connect
    from websockets.exceptions import ConnectionClosed

    store, ledger, registry, auth, _, tokens, texts = setup(tmp_path)

    async def scenario():
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            authority = f"127.0.0.1:{listener.getsockname()[1]}"
            endpoint = f"http://{authority}/hub/mcp"
            origin = "http://localhost:6771"
            app = create_app(store, auth, hosts=[authority], origins=[origin], evolution=ledger,
                             feedback_enabled=True, assets=registry)
            server = uvicorn.Server(uvicorn.Config(app, log_level="critical", access_log=False, lifespan="on"))
            worker = asyncio.create_task(server.serve(sockets=[listener]))
            try:
                for _ in range(200):
                    if server.started:
                        break
                    if worker.done():
                        await worker
                    await asyncio.sleep(.02)
                assert server.started

                def source(name, params):
                    return call_tool(name, params, endpoint=endpoint, token=tokens["host"])

                async def control(name, token="human", **params):
                    async with connect(f"ws://{authority}/hub/feedback", origin=origin, proxy=None) as ws:
                        await ws.send(json.dumps({"op": name, "token": tokens[token], "params": {
                            "target": {"project": PROJECT, **TARGET}, "skill_id": SKILL, **params,
                        }}))
                        return json.loads(await ws.recv())["result"]

                loaded = []

                def verify_and_apply(target, asset, data):
                    assert target["attempt_id"] == TARGET["attempt_id"]
                    parsed = data.decode().strip()
                    assert parsed in ("timeout = 300", "require_signal = true")
                    loaded.append(parsed)
                    return {"result": "loaded", "effective_sha256": sha(data)}

                initial = await asyncio.to_thread(load_task_asset, source, PROJECT, TARGET, SKILL, verify_and_apply)
                assert initial["actual_version"] == BASE
                publish(ledger)
                preview = await control("evolution_preview")
                assert "text" not in preview["asset"] and preview["loaded_version"] == BASE
                with pytest.raises(ConnectionClosed):
                    await control("evolution_preview", token="model")
                confirmation = await control("evolution_confirm", version=CANDIDATE,
                                             asset_sha256=sha(texts[CANDIDATE]), request_id="host-upgrade")
                assert confirmation["state"] == "confirmed" and loaded == ["timeout = 300"]
                newer = await asyncio.to_thread(load_task_asset, source, PROJECT, TARGET, SKILL, verify_and_apply,
                                                request_id="host-upgrade")
                assert newer["actual_version"] == CANDIDATE
                status = await call_tool_async("get_evolution_status", {
                    "project": PROJECT, "tool": "codex", "tool_version": "pilot.1",
                    "skill_id": SKILL, **TARGET,
                }, endpoint=endpoint, token=tokens["human"])
                assert status["loaded_version"] == CANDIDATE and status["loading_state"] == "loaded"
                replay = await asyncio.to_thread(load_task_asset, source, PROJECT, TARGET, SKILL, verify_and_apply,
                                                 request_id="host-upgrade")
                assert replay["dispatch"] is False and loaded == ["timeout = 300", "require_signal = true"]
                with pytest.raises((ValueError, ExceptionGroup)) as rejected:
                    await call_tool_async("prepare_evolution_loading", {
                        "project": PROJECT, "target": TARGET, "skill_id": SKILL,
                    }, endpoint=endpoint, token=tokens["model"])
                def is_denied(error):
                    return isinstance(error, ValueError) and str(error) == "mcp_request_failed"

                failure = rejected.value
                assert failure.subgroup(is_denied) if isinstance(failure, ExceptionGroup) else is_denied(failure)
            finally:
                server.should_exit = True
                await asyncio.wait_for(worker, 10)

    asyncio.run(scenario())
