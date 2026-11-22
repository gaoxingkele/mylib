"""Trusted central-to-supervisor delegation over the operator-configured MCP route."""
import asyncio

from .client import call_tool_async, check_endpoint
from .supervisor import EvidenceSupervisor, RemoteReadStore


def _projects(values):
    if (not isinstance(values, (list, tuple)) or not 1 <= len(values) <= 64
            or any(not isinstance(p, str) or not p.strip() or p == "*" or len(p.encode("utf-8")) > 256
                   for p in values) or len(set(values)) != len(values)):
        raise ValueError("invalid_project_set")
    return tuple(sorted(values))


def _statement(question):
    if not isinstance(question, str) or not 0 < len(question.strip()) <= 2000:
        raise ValueError("invalid_question")


def _epochs(values, projects):
    if (not isinstance(values, dict) or set(values) != set(projects)
            or any(type(epoch) is not int or epoch < 0 for epoch in values.values())):
        raise ValueError("invalid_evidence_epochs")


class RemoteSupervisor:
    """Central caller. Permissions and epoch checks in Domain wrap this operation."""

    def __init__(self, endpoint, projects, token, *, call=call_tool_async):
        check_endpoint(endpoint)
        self.endpoint = endpoint
        self.projects = frozenset(_projects(projects))
        if (not isinstance(token, str) or not 16 <= len(token) <= 4096
                or any(not 33 <= ord(ch) <= 126 for ch in token) or token in endpoint):
            raise ValueError("invalid_delegate_credential")
        self._token = token
        self._call = call

    async def __call__(self, project, args):
        if project not in self.projects:
            raise PermissionError("project_not_delegated")
        if not isinstance(args, dict) or set(args) - {"question", "task_id"}:
            raise ValueError("invalid_chat_arguments")
        _statement(args.get("question"))
        task = args.get("task_id", "")
        if not isinstance(task, str) or len(task) > 256 or self._token in task or self._token in args["question"]:
            raise ValueError("invalid_chat_arguments")
        return await self._call("chat", {"project": project, **args}, endpoint=self.endpoint, token=self._token)

    async def summarize_projects(self, question, projects, epochs, rows):
        _statement(question)
        if self._token in question:
            raise ValueError("credential_in_request")
        projects = _projects(projects)
        _epochs(epochs, projects)
        if not self.projects.issuperset(projects):
            raise PermissionError("project_not_delegated")
        refs = {(r["project"], r["event_id"], r.get("source", "")) for r in rows
                if isinstance(r, dict) and r.get("project") in projects and isinstance(r.get("event_id"), str)
                and isinstance(r.get("source", ""), str)}
        result = await self._call("infer_projects", {"projects": list(projects), "epochs": epochs, "question": question},
                                  endpoint=self.endpoint, token=self._token)
        if not isinstance(result, dict) or result.get("mode") not in {"model", "recent_events"}:
            raise ValueError("invalid_remote_answer")
        answer, evidence = result.get("answer"), result.get("evidence")
        if (not isinstance(answer, str) or not answer or len(answer.encode("utf-8")) > 65536
                or self._token in answer or not isinstance(evidence, list) or len(evidence) > 1280
                or (result["mode"] == "model" and not evidence)):
            raise ValueError("invalid_remote_answer")
        checked = []
        for ref in evidence:
            if not isinstance(ref, dict):
                raise ValueError("unbound_evidence")
            key = ref.get("project"), ref.get("event_id"), ref.get("source", "")
            if not all(isinstance(s, str) for s in key) or key not in refs:
                raise ValueError("unbound_evidence")
            checked.append(dict(project=key[0], event_id=key[1], source=key[2]))
        return {"answer": answer, "evidence": checked, "mode": result["mode"]}


async def infer_projects_authorized(grants, digest, supervisor, projects, epochs, question):
    """US service-only MCP tool: obtain current facts from central's read-only MCP."""
    _statement(question)
    projects = _projects(projects)
    _epochs(epochs, projects)
    if not isinstance(supervisor, EvidenceSupervisor) or not isinstance(supervisor.store, RemoteReadStore):
        raise PermissionError("remote_evidence_required")
    source = supervisor.store
    if not all(source.covers(p) for p in projects):
        raise PermissionError("project_not_delegated")

    required = {"tasks:read", "chat:model", "chat:delegate"}
    def read_grants():
        values = [grants.resolve(digest, project) for project in projects]
        if any(not required.issubset(grant.get("scopes", [])) for grant in values):
            raise PermissionError("delegate_scope_required")
        return values

    original = read_grants()
    limit = asyncio.Semaphore(6)
    async def read(project, fn):
        async with limit:
            return await asyncio.to_thread(fn, project)

    async def recheck():
        if read_grants() != original:
            raise PermissionError("delegation_changed")
        current = await asyncio.gather(*(read(p, source.privacy_epoch) for p in projects))
        if any(epoch != epochs[p] for p, epoch in zip(projects, current)):
            raise PermissionError("source_withdrawn")
        if read_grants() != original:
            raise PermissionError("delegation_changed")

    await recheck()
    pages = await asyncio.gather(*(read(p, source.list_tasks) for p in projects))
    rows = []
    for project, page in zip(projects, pages):
        facts = page.get("tasks")
        if (not isinstance(facts, list) or len(facts) > 20
                or any(not isinstance(row, dict) or row.get("project", project) != project for row in facts)):
            raise ValueError("invalid_project_evidence")
        rows.extend(dict(row, project=project) for row in facts)
    await recheck()
    result = await supervisor.summarize_authorized(question, rows)
    await recheck()
    return result


def project_token_env(values, environment):
    """Parse repeated PROJECT=ENV_NAME arguments. Model and reader secrets stay local."""
    result = {}
    for item in values or ():
        if not isinstance(item, str) or item.count("=") != 1:
            raise ValueError("expected_project_environment_binding")
        project, variable = item.split("=", 1)
        _projects([project])
        if (not variable.isascii() or not variable.isidentifier() or project in result
                or not environment.get(variable)):
            raise ValueError("invalid_project_environment_binding")
        result[project] = environment[variable]
    if len(result) > 64:
        raise ValueError("invalid_project_set")
    return result
