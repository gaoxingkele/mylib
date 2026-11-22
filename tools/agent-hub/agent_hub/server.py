"""Agent Hub MCP and the read-only cockpit bridge. Run behind a trusted TLS proxy."""
import argparse
import asyncio
from contextvars import ContextVar
from datetime import datetime
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import secrets

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.responses import JSONResponse
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocketDisconnect

from .client import call_tool_async
from .storage import Store


_identity = ContextVar('agent_hub_principal', default=None)
READ_TOOLS = {'search_task_events', 'list_tasks', 'get_wiki_entry', 'get_evidence_epoch', 'get_task_status', 'get_usage_overview',
              'chat', 'search_skills', 'read_skill', 'list_evolution', 'get_evolution_status'}
FIELDS = {
    'prepare_evolution_loading': {'target','skill_id','request_id'},
    'report_loading': {'target','skill_id','version','asset_sha256','result','request_id'},
    'sync_wiki': {'revision'}, 'withdraw_wiki': {'entry_id','request_id'},
    'get_evidence_epoch': set(),
    'report_step': {'event'}, 'claim_usage_job': {'account', 'worker', 'idle_after_seconds'},
    'record_usage_snapshot': {'account', 'snapshot'}, 'search_task_events': {'query', 'limit'},
    'get_task_status': {'task_id'}, 'list_tasks': {'status','limit','before'}, 'get_wiki_entry': {'entry_id','version'},
    'get_usage_overview': set(), 'chat': {'question', 'task_id'},
    'search_skills': {'query', 'limit'}, 'read_skill': {'skill_id', 'revision'},
    'list_evolution': {'limit'}, 'get_evolution_status': {'tool', 'tool_version', 'skill_id', 'task_id', 'attempt_id', 'generation', 'candidate_id'},
}
WRITE_SCOPES = {
    'sync_wiki': 'wiki:write', 'withdraw_wiki': 'wiki:withdraw',
    'report_step': 'events:append', 'claim_usage_job': 'usage:collect',
    'record_usage_snapshot': 'usage:collect', 'prepare_evolution_loading': 'evolution:source',
    'report_loading': 'evolution:source',
}


class AccessDenied(ValueError):
    pass


class Grants:
    def __init__(self, path):
        self.path = Path(path)
        self.records()

    def records(self):
        if os.name == 'posix' and self.path.stat().st_mode & 0o077:
            raise ValueError('private_auth_file_required')
        records = json.loads(self.path.read_text(encoding='utf-8-sig'))['grants']
        if not isinstance(records, list):
            raise ValueError('invalid_auth_configuration')
        bindings = set()
        for grant in records:
            if (not isinstance(grant, dict) or not re.fullmatch(r'[0-9a-f]{64}', str(grant.get('sha256', '')))
                    or not isinstance(grant.get('subject'), str) or not grant['subject'].strip()
                    or not isinstance(grant.get('project'), str) or not grant['project'].strip() or grant['project'] == '*'):
                raise ValueError('invalid_grant')
            for field in ('scopes', 'accounts', 'tools', 'feedback_hosts', 'evolution_hosts'):
                values = grant.get(field, [])
                if not isinstance(values, list) or any(not isinstance(v, str) or not v for v in values):
                    raise ValueError('invalid_grant_list')
            if not isinstance(grant.get('shared_pools', {}), dict):
                raise ValueError('invalid_pool_map')
            for account, pools in grant.get('shared_pools', {}).items():
                if (account not in grant.get('accounts', []) or not isinstance(pools, dict)
                        or any(not isinstance(key, str) or not key or not isinstance(v, str) or not v for key, v in pools.items())):
                    raise ValueError('invalid_pool_map')
            binding = (grant['sha256'], grant['project'])
            if binding in bindings:
                raise ValueError('duplicate_grant')
            bindings.add(binding)
        return records

    def resolve(self, digest, project=None):
        if digest is None:
            raise AccessDenied('authentication_required')
        for grant in self.records():
            if (secrets.compare_digest(grant['sha256'], digest)
                    and (project is None or project == grant['project'])):
                return grant
        raise AccessDenied('access_denied')

    def projects(self, digest, scope='tasks:read'):
        return sorted({g['project'] for g in self.records() if digest and secrets.compare_digest(g['sha256'], digest)
                       and scope in g['scopes'] and 'tasks:read' in g['scopes']})


def token_digest(token):
    if not isinstance(token, str) or not 16 <= len(token) <= 4096 or not token.isascii():
        raise AccessDenied('authentication_required')
    return hashlib.sha256(token.encode()).hexdigest()


def shared_usage(rows, grants):
    """Combine only explicitly bound pools, retaining per-project freshness and visibility."""
    mappings = {g['project']: g.get('shared_pools', {}) for g in grants}
    groups = {}
    for row in rows:
        project, account, pool = row['project'], row['account'], row['pool']
        binding = mappings[project].get(account, {}).get(pool)
        key = ('shared', binding) if binding else ('local', project, account, pool)
        if key not in groups:
            groups[key] = dict(row, projects=[project])
            continue
        current = groups[key]
        current['projects'] = sorted(set(current['projects']) | {project})
        for field in ('latest', 'last_success'):
            latest, incoming = current.get(field), row.get(field)
            if incoming and (not latest or datetime.fromisoformat(incoming['observed_at'].replace('Z', '+00:00')) >
                             datetime.fromisoformat(latest['observed_at'].replace('Z', '+00:00'))):
                current[field] = incoming
                if field == 'latest':
                    current.update(project=project, account=account, pool=pool)
    return list(groups.values())


def usage_question(question):
    text = question.casefold()
    return any(word in text for word in ('额度', '配额', '余量', '剩余', '重置时间', 'quota', 'weekly limit', 'remaining capacity'))


def usage_answer(overview):
    lines, refs = [], []
    freshness = {'fresh':'已更新', 'stale':'数据过期', 'period_ended':'上个周期已结束',
                 'missing':'待查询', 'query_failed':'最近查询失败'}
    for group in overview['recommendations']:
        best = group['accounts'][0]
        lines.append(f"{group['provider']} · {group['pool_class']} 优先可用账号 {best['account']}（剩余 {best['remaining']} {group['unit']}）。")
    for row in overview['accounts']:
        quota = row['capacity']
        week = next((w for w in quota['windows'] if w['period'] == 'weekly'), None)
        value = f"{week['remaining']} {week['unit']}" if week and week.get('remaining') is not None else '未知'
        reset = week.get('reset_at') if week else None
        lines.append(f"{row['account']} · {row['pool']}：本周剩余 {value}，重置 {reset or '未知'}，{freshness.get(quota['freshness'], '待核对')}。")
        sample = row.get('latest') or {}
        if sample.get('snapshot_id'):
            refs.append(f"{row.get('project','')}/quota/{sample['snapshot_id']}")
    return {'answer':'\n'.join(lines) or '当前可查看的账号尚无额度观测。', 'mode':'usage_records', 'evidence':refs}


class Domain:
    def __init__(self, store, grants, catalog=None, supervisor=None, evolution=None, adoption=None):
        self.store, self.grants = store, grants
        self.catalog, self.supervisor = catalog, supervisor
        self.evolution = evolution
        self.adoption = adoption

    async def invoke(self, digest, name, project, args):
        if project == '*':
            return await self.overview(digest, name, args)
        grant = self.grants.resolve(digest, project)
        epoch = await self.privacy_epoch(project) if name in READ_TOOLS else None
        result = await self.dispatch(grant, name, project, args)
        if self.grants.resolve(digest, project) != grant:
            raise AccessDenied('grant_changed')
        if epoch is not None and await self.privacy_epoch(project) != epoch:
            raise AccessDenied('source_withdrawn')
        return result

    async def privacy_epoch(self, project):
        if not isinstance(self.store, Store):
            return None
        from .wiki_sync import privacy_epoch
        return await asyncio.to_thread(privacy_epoch, self.store, project)

    async def overview(self, digest, name, args):
        collections = {'list_tasks': 'tasks', 'search_task_events': 'events', 'get_usage_overview': 'accounts',
                       'list_evolution': 'items', 'chat': 'tasks'}
        if name not in collections or not isinstance(args, dict) or set(args) - FIELDS[name]:
            raise AccessDenied('select_one_project')
        if name == 'chat' and isinstance(args.get('question'), str) and usage_question(args['question']):
            if not 0 < len(args['question']) <= 2000 or args.get('task_id'):
                raise ValueError('invalid_global_question')
            return usage_answer(await self.overview(digest, 'get_usage_overview', {}))
        projects = self.grants.projects(digest, 'usage:read' if name == 'get_usage_overview' else 'tasks:read')
        if not projects or len(projects) > 64:
            raise AccessDenied('select_one_project')
        original_grants = [self.grants.resolve(digest, project) for project in projects]
        epochs = [await self.privacy_epoch(project) for project in projects]
        limit = args.get('limit', 50)
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError('invalid_limit')
        if args.get('before') or (name == 'chat' and args.get('task_id')):
            raise ValueError('select_one_project')
        rows = []
        field = collections[name]
        partial = False
        for project in projects:
            if name == 'chat':
                question = args.get('question')
                if not isinstance(question, str) or not 0 < len(question.strip()) <= 2000:
                    raise ValueError('invalid_question')
                result = await self.invoke(digest, 'list_tasks', project, {'limit': 20})
            else:
                result = await self.invoke(digest, name, project, args)
            rows.extend(dict(row, project=project) for row in result[field])
            partial |= bool(result.get('next_before'))
        if name in {'list_tasks', 'search_task_events', 'chat'}:
            rows.sort(key=lambda row: row.get('seq', 0), reverse=True)
        if name == 'get_usage_overview':
            rows = shared_usage(rows, original_grants)
        model_result = None
        if (name == 'chat' and (hasattr(self.supervisor, 'summarize_authorized') or hasattr(self.supervisor, 'summarize_projects'))
                and set(projects) <= set(getattr(self.supervisor, 'projects', projects))
                and all('chat:model' in grant['scopes'] for grant in original_grants)):
            if (original_grants != [self.grants.resolve(digest, p) for p in projects]
                    or epochs != [await self.privacy_epoch(p) for p in projects]):
                raise AccessDenied('source_or_grant_changed')
            if hasattr(self.supervisor, 'summarize_projects'):
                model_result = await self.supervisor.summarize_projects(args['question'], projects, dict(zip(projects, epochs)), rows)
            else:
                model_result = await self.supervisor.summarize_authorized(args['question'], rows)
        if self.grants.projects(digest, 'usage:read' if name == 'get_usage_overview' else 'tasks:read') != projects:
            raise AccessDenied('grant_changed')
        if original_grants != [self.grants.resolve(digest, project) for project in projects]:
            raise AccessDenied('grant_changed')
        if epochs != [await self.privacy_epoch(project) for project in projects]:
            raise AccessDenied('source_withdrawn')
        if model_result is not None:
            refs = model_result['evidence']
            return {**model_result, 'evidence_refs':refs, 'evidence':[f"{ref['project']}/{ref['event_id']}" for ref in refs]}
        if name == 'chat':
            rows = rows[:8]
            return {'answer': '\n'.join(f"[{row['project']}] {str(row['summary'])[:320]}" for row in rows) or '暂无授权范围内的任务事件。',
                    'mode':'recent_events', 'evidence':[f"{r['project']}/{r['event_id']}" for r in rows],
                    'evidence_refs': [{'project':r['project'],'event_id':r['event_id']} for r in rows]}
        if name == 'get_usage_overview':
            from .capacity import capacity_overview
            if len(rows) > 1024:
                raise ValueError('select_one_project')
            return {**capacity_overview(rows), 'partial': False}
        return {field: rows[:limit], 'next_before': None, 'partial': partial or len(rows) > limit}

    async def dispatch(self, grant, name, project, args):
        if not isinstance(project, str) or not project or name not in FIELDS or not isinstance(args, dict) or set(args) - FIELDS[name]:
            raise ValueError('invalid_arguments')
        scope = WRITE_SCOPES.get(name, 'usage:read' if name == 'get_usage_overview' else 'tasks:read')
        if scope not in grant['scopes']:
            raise AccessDenied('access_denied')
        accounts = grant.get('accounts', [])
        if name in {'prepare_evolution_loading','report_loading'}:
            if self.adoption is None:
                raise ValueError('evolution_unconfigured')
            return await asyncio.to_thread(self.adoption.request, grant, name, project, **args)
        if name == 'get_evidence_epoch':
            epoch = await self.privacy_epoch(project)
            if epoch is None:
                raise ValueError('evidence_source_unavailable')
            return {'epoch': epoch}
        if name in {'sync_wiki', 'withdraw_wiki'}:
            from .wiki_sync import sync_wiki, withdraw_wiki
            function = sync_wiki if name == 'sync_wiki' else withdraw_wiki
            return await asyncio.to_thread(function, self.store, project, grant['subject'], **args)
        if name == 'report_step':
            event = args['event']
            if (not isinstance(event, dict) or event.get('account') not in accounts
                    or event.get('host') != grant.get('host') or not grant.get('host')
                    or event.get('host_installation_id') != grant.get('host_installation_id')
                    or event.get('tool') not in grant.get('tools', [])):
                raise AccessDenied('source_binding_mismatch')
            return await asyncio.to_thread(self.store.report_step, project, grant['subject'], event)
        if name in {'claim_usage_job', 'record_usage_snapshot'}:
            if args.get('account') not in accounts:
                raise AccessDenied('account_scope_denied')
            if name == 'claim_usage_job':
                if args.get('worker') != grant['subject']:
                    raise AccessDenied('worker_binding_mismatch')
                cadence = args.get('idle_after_seconds')
                options = {'idle_after_seconds': cadence} if cadence is not None else {}
                result = await asyncio.to_thread(self.store.claim_usage_job, project, args['account'], grant['subject'], **options)
                return result or {}
            return await asyncio.to_thread(self.store.record_usage_snapshot, project, args['account'], args['snapshot'])
        if name == 'get_usage_overview':
            from .capacity import capacity_overview
            overview = await asyncio.to_thread(self.store.get_usage_overview, project)
            return capacity_overview([dict(row, project=project) for row in overview['accounts'] if row['account'] in accounts])
        if name in {'search_task_events', 'get_task_status', 'list_tasks', 'get_wiki_entry'}:
            return await asyncio.to_thread(getattr(self.store, name), project, **args)
        if name in {'list_evolution', 'get_evolution_status'}:
            if self.evolution is None:
                raise ValueError('evolution_unconfigured')
            if name == 'list_evolution':
                return await asyncio.to_thread(self.evolution.list_status, project, **args)
            values = dict(args)
            scope = dict(project_id=project, tool=values.pop('tool'), tool_version=values.pop('tool_version'))
            task_id = values.pop('task_id', None)
            if task_id or values.get('attempt_id') or values.get('generation'):
                if not task_id or not values.get('attempt_id') or values.get('generation') is None or not self.adoption:
                    raise ValueError('exact_attempt_required')
                return await asyncio.to_thread(self.adoption.status_for, grant, project, task_id=task_id, **values)
            return await asyncio.to_thread(self.evolution.get_status, scope, **values)
        if name in {'search_skills', 'read_skill'}:
            if self.catalog is None:
                raise ValueError('catalog_unconfigured')
            result = await self.catalog(name, args)
            if name == 'search_skills':
                return {'skills': [dict(row, id=row.get('id') or row.get('skill_id'), title=row.get('name'), revision=result.get('revision'))
                                   for row in result.get('items', [])]}
            return result
        question = args.get('question')
        if not isinstance(question, str) or not 0 < len(question.strip()) <= 2000:
            raise ValueError('invalid_question')
        if usage_question(question):
            overview = await self.dispatch(grant, 'get_usage_overview', project, {})
            return usage_answer(overview)
        if self.supervisor and 'chat:model' in grant['scopes']:
            return await self.supervisor(project, args)
        if args.get('task_id'):
            task = await asyncio.to_thread(self.store.get_task_status, project, args['task_id'])
            rows = task['attempts'][:8]
        else:
            current = await asyncio.to_thread(self.store.list_tasks, project, limit=8)
            rows = current['tasks']
        return {'answer': '\n'.join(str(row.get('summary', ''))[:360] for row in rows) or '暂无匹配的任务事件。',
                'evidence': [row['event_id'] for row in rows], 'mode': 'recent_events'}


class HttpAuth:
    def __init__(self, app, grants):
        self.app, self.grants = app, grants

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = [v for k, v in scope['headers'] if k.lower() == b'authorization']
        try:
            if len(headers) != 1 or not headers[0].startswith(b'Bearer '):
                raise AccessDenied()
            digest = token_digest(headers[0][7:].decode('ascii'))
            self.grants.resolve(digest)
        except (ValueError, OSError, KeyError):
            return await JSONResponse({'error': 'unauthorized'}, status_code=401)(scope, receive, send)
        marker = _identity.set(digest)
        try:
            return await self.app(scope, receive, send)
        finally:
            _identity.reset(marker)


def create_app(store, auth_file, *, hosts, origins=(), catalog=None, supervisor=None, evolution=None, feedback_enabled=False,
               assets=None):
    grants = Grants(auth_file)
    adoption = None
    if evolution is not None and isinstance(store, Store):
        evolution.bind_wiki_database(store.path)
    if assets is not None:
        from .adoption import AdoptionService
        if evolution is None:
            raise ValueError('evolution_ledger_required')
        adoption = AdoptionService(store, evolution, grants, assets)
    domain = Domain(store, grants, catalog, supervisor, evolution, adoption)
    server = FastMCP('mylib Agent Hub', stateless_http=True, json_response=True,
                     streamable_http_path='/hub/mcp', log_level='CRITICAL', max_request_body_size=131072,
                     transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True,
                         allowed_hosts=list(hosts), allowed_origins=list(origins)))

    async def invoke(name, project, args):
        try:
            return await domain.invoke(_identity.get(), name, project, args)
        except AccessDenied:
            raise ValueError('access_denied') from None
        except Exception:
            raise ValueError('operation_failed') from None

    @server.tool()
    async def report_step(project: str, event: dict) -> dict:
        return await invoke('report_step', project, {'event': event})

    @server.tool()
    async def get_evidence_epoch(project: str) -> dict:
        return await invoke('get_evidence_epoch', project, {})

    @server.tool()
    async def prepare_evolution_loading(project: str, target: dict, skill_id: str, request_id: str | None = None) -> dict:
        return await invoke('prepare_evolution_loading', project, dict(target=target, skill_id=skill_id, request_id=request_id))

    @server.tool()
    async def report_loading(project: str, target: dict, skill_id: str, version: str, asset_sha256: str,
                             result: str, request_id: str | None = None) -> dict:
        return await invoke('report_loading', project, dict(target=target, skill_id=skill_id, version=version,
                            asset_sha256=asset_sha256, result=result, request_id=request_id))

    @server.tool()
    async def sync_wiki(project: str, revision: dict) -> dict:
        return await invoke('sync_wiki', project, {'revision': revision})

    @server.tool()
    async def withdraw_wiki(project: str, entry_id: str, request_id: str) -> dict:
        return await invoke('withdraw_wiki', project, {'entry_id': entry_id, 'request_id': request_id})

    @server.tool()
    async def search_task_events(project: str, query: str = '', limit: int = 50) -> dict:
        return await invoke('search_task_events', project, {'query': query, 'limit': limit})

    @server.tool()
    async def list_tasks(project: str, status: str | None = None, limit: int = 50, before: int | None = None) -> dict:
        return await invoke('list_tasks', project, {'status': status, 'limit': limit, 'before': before})

    @server.tool()
    async def get_wiki_entry(project: str, entry_id: str, version: str | None = None) -> dict:
        return await invoke('get_wiki_entry', project, {'entry_id': entry_id, 'version': version})

    @server.tool()
    async def get_task_status(project: str, task_id: str) -> dict:
        return await invoke('get_task_status', project, {'task_id': task_id})

    @server.tool()
    async def get_usage_overview(project: str) -> dict:
        return await invoke('get_usage_overview', project, {})

    @server.tool()
    async def claim_usage_job(project: str, account: str, worker: str, idle_after_seconds: int | None = None) -> dict:
        return await invoke('claim_usage_job', project, dict(account=account, worker=worker, idle_after_seconds=idle_after_seconds))

    @server.tool()
    async def record_usage_snapshot(project: str, account: str, snapshot: dict) -> dict:
        return await invoke('record_usage_snapshot', project, {'account': account, 'snapshot': snapshot})

    @server.tool()
    async def infer_projects(projects: list[str], epochs: dict[str, int], question: str) -> dict:
        from .remote_supervisor import infer_projects_authorized
        try:
            return await infer_projects_authorized(grants, _identity.get(), domain.supervisor, projects, epochs, question)
        except Exception:
            raise ValueError('inference_unavailable') from None

    @server.tool()
    async def chat(project: str, question: str, task_id: str = '') -> dict:
        return await invoke('chat', project, {'question': question, 'task_id': task_id})

    @server.tool()
    async def list_evolution(project: str, limit: int = 50) -> dict:
        return await invoke('list_evolution', project, {'limit': limit})

    @server.tool()
    async def get_evolution_status(project: str, tool: str, tool_version: str, skill_id: str,
                                   attempt_id: str | None = None, generation: str | int | None = None,
                                   candidate_id: str | None = None, task_id: str | None = None) -> dict:
        return await invoke('get_evolution_status', project, dict(tool=tool, tool_version=tool_version, skill_id=skill_id,
                            attempt_id=attempt_id, generation=generation, candidate_id=candidate_id, task_id=task_id))

    @server.tool()
    async def search_skills(project: str, query: str, limit: int = 10) -> dict:
        return await invoke('search_skills', project, {'query': query, 'limit': limit})

    @server.tool()
    async def read_skill(project: str, skill_id: str, revision: str | None = None) -> dict:
        return await invoke('read_skill', project, {'skill_id': skill_id, 'revision': revision})

    async def viewer(ws):
        if ws.headers.get('origin') not in origins or ws.headers.get('host') not in hosts:
            await ws.close(code=1008)
            return
        await ws.accept()
        try:
            hello = await asyncio.wait_for(ws.receive_json(), 8)
            if not isinstance(hello, dict) or hello.get('op') != 'hello' or not isinstance(hello.get('project'), str):
                raise ValueError('invalid_hello')
            project = hello['project']
            digest = token_digest(hello.pop('token', None))
            projects = grants.projects(digest)
            if not projects or (project != '*' and project not in projects):
                raise AccessDenied()
            view_grants = [grants.resolve(digest, p) for p in projects]
            initial_epochs = [await domain.privacy_epoch(p) for p in projects]
            await ws.send_json({'op': 'ready', 'project': project, 'projects': projects})
            while True:
                if projects != grants.projects(digest) or view_grants != [grants.resolve(digest, p) for p in projects]:
                    raise AccessDenied('grant_changed')
                if initial_epochs != [await domain.privacy_epoch(p) for p in projects]:
                    raise AccessDenied('source_withdrawn')
                try:
                    msg = await asyncio.wait_for(ws.receive_json(), 5)
                except asyncio.TimeoutError:
                    continue
                if not isinstance(msg, dict) or msg.get('op') != 'request' or msg.get('tool') not in READ_TOOLS:
                    raise ValueError('invalid_request')
                req = msg.get('id')
                if not isinstance(req, (int, str)) or len(str(req)) > 128:
                    raise ValueError('invalid_request_id')
                try:
                    selected = msg.get('project', project)
                    if selected != '*' and selected not in projects:
                        raise AccessDenied('access_denied')
                    result = await domain.invoke(digest, msg['tool'], selected, msg.get('arguments', {}))
                    await ws.send_json({'op': 'response', 'id': req, 'ok': True, 'result': result})
                except AccessDenied:
                    raise
                except Exception:
                    await ws.send_json({'op': 'response', 'id': req, 'ok': False, 'error': 'operation_failed'})
        except WebSocketDisconnect:
            return
        except (ValueError, OSError, TypeError, KeyError, TimeoutError):
            await ws.close(code=1008)

    app = server.streamable_http_app()
    app.router.routes.append(WebSocketRoute('/hub/view', viewer))
    if feedback_enabled:
        from .feedback import feedback_route
        options = {'adoption': adoption} if adoption is not None else {}
        app.router.routes.append(feedback_route(store, grants, hosts, origins, **options))
    return HttpAuth(app, grants)


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--auth-file', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8822)
    parser.add_argument('--allowed-host', action='append', default=[])
    parser.add_argument('--allowed-origin', action='append', default=[])
    parser.add_argument('--catalog-endpoint')
    parser.add_argument('--enable-feedback', action='store_true', help='Enable user-confirmed pilot delivery receipts')
    parser.add_argument('--evolution-database', type=Path)
    parser.add_argument('--asset-manifest', type=Path)
    parser.add_argument('--asset-manifest-sha256')
    parser.add_argument('--asset-root', type=Path)
    parser.add_argument('--model-endpoint')
    parser.add_argument('--model')
    parser.add_argument('--model-evidence-endpoint', help='Read-only central MCP for a separate supervisor host')
    parser.add_argument('--model-project', help='Single authorized upstream project for remote evidence')
    parser.add_argument('--supervisor-mcp', help='Private remote Agent Hub MCP running the supervisor')
    parser.add_argument('--supervisor-project', action='append', default=[], help='Project explicitly permitted to use that supervisor')
    parser.add_argument('--model-project-token-env', action='append', default=[], metavar='PROJECT=ENV',
                        help='Map each remote evidence project to its own read credential environment variable')
    args = parser.parse_args()
    logging.getLogger('mcp').setLevel(logging.CRITICAL)
    catalog_token = os.environ.get('MYLIB_HUB_CATALOG_TOKEN', '')
    if args.catalog_endpoint and not catalog_token:
        parser.error('--catalog-endpoint requires MYLIB_HUB_CATALOG_TOKEN')

    async def catalog(name, params):
        return await call_tool_async(name, params, endpoint=args.catalog_endpoint, token=catalog_token)

    store = Store(args.database)
    evolution = None
    if args.evolution_database:
        if args.evolution_database.resolve() == args.database.resolve():
            parser.error('Use a separate evolution state file')
        from .evolution import EvolutionLedger
        evolution = EvolutionLedger(args.evolution_database, wiki_database=store.path)
    supervisor = None
    assets = None
    if args.asset_manifest or args.asset_manifest_sha256 or args.asset_root:
        from .adoption import AssetManifest
        if not args.asset_manifest or not args.asset_manifest_sha256 or evolution is None:
            parser.error('A pinned asset manifest requires its SHA-256 and an evolution ledger')
        def read_catalog(name, values):
            return asyncio.run(catalog(name, values))
        assets = AssetManifest(args.asset_manifest, args.asset_manifest_sha256, root=args.asset_root,
                               catalog=read_catalog if args.catalog_endpoint else None)
    if args.supervisor_mcp or args.supervisor_project:
        upstream_token = os.environ.get('MYLIB_HUB_SUPERVISOR_TOKEN', '')
        if not args.supervisor_mcp or not args.supervisor_project or not upstream_token:
            parser.error('Remote supervisor requires --supervisor-mcp, --supervisor-project and MYLIB_HUB_SUPERVISOR_TOKEN')

        from .remote_supervisor import RemoteSupervisor
        supervisor = RemoteSupervisor(args.supervisor_mcp, args.supervisor_project, upstream_token)

    if args.model_endpoint or args.model or args.model_evidence_endpoint or args.model_project or args.model_project_token_env:
        if supervisor is not None:
            parser.error('Choose a provider or a remote supervisor for this service instance')
        from .supervisor import EvidenceSupervisor, RemoteReadStore
        api_key = os.environ.get('MYLIB_HUB_MODEL_KEY', '')
        if not args.model_endpoint or not args.model or not api_key:
            parser.error('Supply --model-endpoint, --model and MYLIB_HUB_MODEL_KEY')
        evidence = store
        if args.model_evidence_endpoint or args.model_project or args.model_project_token_env:
            project_tokens = {}
            if args.model_project:
                project_tokens[args.model_project] = os.environ.get('MYLIB_HUB_EVIDENCE_TOKEN', '')
            for spec in args.model_project_token_env:
                project, sep, var = spec.partition('=')
                if not sep or not project or project in project_tokens or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', var):
                    parser.error('Invalid or duplicate project credential mapping')
                project_tokens[project] = os.environ.get(var, '')
            if not args.model_evidence_endpoint or not project_tokens or not all(project_tokens.values()):
                parser.error('Remote evidence requires an endpoint and a read credential for each selected project')
            evidence = RemoteReadStore(args.model_evidence_endpoint, project_tokens)
        supervisor = EvidenceSupervisor(evidence, endpoint=args.model_endpoint, model=args.model, api_key=api_key)
    hosts = [f'127.0.0.1:{args.port}', f'localhost:{args.port}', *args.allowed_host]
    app = create_app(store, args.auth_file, hosts=hosts, origins=args.allowed_origin, evolution=evolution,
                     supervisor=supervisor, catalog=catalog if args.catalog_endpoint else None,
                     feedback_enabled=args.enable_feedback, assets=assets)
    uvicorn.run(app, host='127.0.0.1', port=args.port, access_log=False, proxy_headers=False,
                limit_concurrency=32, ws_max_size=131072, server_header=False)


if __name__ == '__main__':
    main()
