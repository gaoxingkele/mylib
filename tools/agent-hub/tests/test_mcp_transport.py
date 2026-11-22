"""Real SDK and cockpit connections against a loopback-only, ephemeral server."""
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import json
import secrets
import socket

import pytest

from agent_hub.client import call_tool_async
from agent_hub.server import create_app, shared_usage, token_digest
from agent_hub.storage import Store


@asynccontextmanager
async def pilot(tmp_path):
    import uvicorn
    tokens = {label: secrets.token_urlsafe(32) for label in ('reader', 'hook', 'usage')}
    grants = [{'sha256': token_digest(token), 'project': 'demo', 'subject': label,
               'scopes': {'reader':['tasks:read','usage:read'], 'hook':['events:append'], 'usage':['usage:collect']}[label],
               'accounts':['fixture'], 'host':'host-A', 'tools':['codex']}
              for label, token in tokens.items()]
    grants.append({**grants[0], 'project':'second-project'})
    for label, tool in [('B','claude'), ('C','grok')]:
        tokens[label] = secrets.token_urlsafe(32)
        grants.append(dict(sha256=token_digest(tokens[label]),subject=label,project='demo',scopes=['events:append'],
                           host='host-'+label,tools=[tool],accounts=['fixture']))
    auth = tmp_path / 'auth.json'
    auth.write_text(json.dumps({'grants': grants}))
    auth.chmod(0o600)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
        authority = f'127.0.0.1:{port}'
        app = create_app(Store(tmp_path / 'sandbox.db'), auth, hosts=[authority], origins=['http://localhost:6771'])
        service = uvicorn.Server(uvicorn.Config(app, log_level='critical', access_log=False, lifespan='on'))
        task = asyncio.create_task(service.serve(sockets=[listener]))
        try:
            for _ in range(200):
                if service.started:
                    break
                if task.done():
                    await task
                await asyncio.sleep(.02)
            assert service.started
            yield authority, tokens, auth
        finally:
            service.should_exit = True
            await asyncio.wait_for(task, 10)


def test_mcp_end_to_end_and_websocket_revocation(tmp_path):
    from websockets.asyncio.client import connect
    from websockets.exceptions import ConnectionClosed

    async def scenario():
        async with pilot(tmp_path) as (host, tokens, auth):
            async def call(name, who, **args):
                return await call_tool_async(name, {'project':'demo', **args}, endpoint=f'http://{host}/hub/mcp', token=tokens[who])

            body = '# Test evidence\nA verified result.'
            event = dict(event_id='e1', task_id='task', attempt_id='first', account='fixture', host='host-A',
                         tool='codex', status='completed', summary='A verified result',
                         wiki=dict(entry_id='note',version='1',path='omx_wiki/note.md',body=body))
            receipt = await call('report_step','hook',event=event)
            assert receipt == await call('report_step','hook',event=event)
            assert receipt['seq'] > 0
            with pytest.raises(Exception):
                await call('report_step','reader',event=event)
            with pytest.raises(Exception):
                await call('search_task_events','reader',project='unrelated')
            assert (await call('list_tasks','reader'))['tasks'][0]['task_id'] == 'task'
            assert (await call('get_wiki_entry','reader',entry_id='note',version='1'))['body'] == body
            job = await call('claim_usage_job','usage',account='fixture',worker='usage')
            assert job['event_id'] == 'e1'
            now = datetime.now(timezone.utc)
            snapshot = dict(job_id=job['job_id'], lease_token=job['lease_token'], status='ok',
                            observed_at=now.isoformat(), pool='plan',
                            windows=[dict(period='weekly',unit='percent',remaining=30,reset_at=(now+timedelta(days=3)).isoformat())])
            await call('record_usage_snapshot','usage',account='fixture',snapshot=snapshot)
            assert (await call('get_usage_overview','reader'))['accounts'][0]['account'] == 'fixture'
            quota_answer = await call('chat','reader',project='*',question='本周额度还剩多少？')
            assert quota_answer['mode'] == 'usage_records'
            assert '30 percent' in quota_answer['answer'] and quota_answer['evidence'] == ['demo/quota/1']
            async with connect(f'ws://{host}/hub/view', origin='http://localhost:6771',proxy=None) as ws:
                await ws.send(json.dumps({'op':'hello','project':'demo','token':tokens['reader']}))
                ready = json.loads(await ws.recv())
                assert ready['op'] == 'ready' and ready['projects'] == ['demo', 'second-project']
                await ws.send(json.dumps({'op':'request','id':'global','project':'*','tool':'list_tasks','arguments':{}}))
                assert json.loads(await ws.recv())['result']['tasks'][0]['project'] == 'demo'
                await ws.send(json.dumps({'op':'request','id':1,'tool':'chat','arguments':{'question':'status?'}}))
                answer = json.loads(await ws.recv())
                assert answer['result']['evidence'] == ['e1']
                auth.write_text('{"grants":[]}')
                await ws.send(json.dumps({'op':'request','id':2,'tool':'list_tasks','arguments':{}}))
                with pytest.raises(ConnectionClosed) as exc:
                    await ws.recv()
                assert exc.value.rcvd.code == 1008
    asyncio.run(scenario())


def test_shared_pool_requires_admin_binding_and_uses_latest_valid_observation():
    old = {'status':'ok', 'observed_at':'2026-11-21T11:00:00+08:00'}
    failure = {'status':'rate_limited', 'observed_at':'2026-11-21T04:00:00Z'}
    rows = [{'project':'left','account':'work','pool':'plan','latest':old,'last_success':old},
            {'project':'right','account':'work','pool':'plan','latest':failure,'last_success':None}]
    grants = [{'project':'left'}, {'project':'right'}]
    assert len(shared_usage(rows, grants)) == 2
    for grant in grants:
        grant['shared_pools'] = {'work': {'plan':'issuer/subscription-1'}}
    combined, = shared_usage(rows, grants)
    assert combined['projects'] == ['left','right']
    assert combined['latest'] == failure and combined['last_success'] == old


def test_hook_wiki_handoff_and_parallel_verification_over_real_mcp(tmp_path):
    from agent_hub.hooks import HookQueue
    from agent_hub.client import call_tool

    async def scenario():
        async with pilot(tmp_path) as (host, tokens, _):
            endpoint = f'http://{host}/hub/mcp'
            async def submit(label, node, tool, phase, **binding):
                root = tmp_path / node
                root.mkdir(exist_ok=True)
                config = dict(project_root=str(root),state_dir=str(tmp_path / ('queue-'+node)),project='demo',
                              host='host-'+node,window='Same title',generation='1',tool=tool,account='fixture',
                              task_id='repair',attempt_id=node,artifact='revision-a',**binding)
                queue = HookQueue(config)
                message = dict(step_id='step-'+phase,summary=f'{node}: {phase}',status=phase)
                if binding.get('role') == 'verify':
                    message['verdict'] = 'pass'
                eid = queue.enqueue(message, manual=True)
                assert queue.status()['pending'] == 1
                def send(name, args):
                    return call_tool(name, args, endpoint=endpoint, token=tokens[label])
                assert await asyncio.to_thread(queue.flush, send) == 1
                doc = await call_tool_async('get_wiki_entry',dict(project='demo',entry_id=eid,version='1'),
                                            endpoint=endpoint,token=tokens['reader'])
                assert (root / doc['path']).read_bytes().decode('utf8') == doc['body']
                return queue, send

            first, sender = await submit('hook','A','codex','quota_limited')
            await submit('B','B','claude','completed',previous_attempt_id='A')
            await submit('C','C','grok','completed',role='verify')
            first.enqueue(dict(step_id='late',summary='old attempt went offline',status='blocked'),manual=True)
            assert await asyncio.to_thread(first.flush, sender) == 1
            status = await call_tool_async('get_task_status',dict(project='demo',task_id='repair'),endpoint=endpoint,token=tokens['reader'])
            assert status['primary_attempt_id'] == 'B'
            assert status['verification_status'] == 'passed'
            assert {attempt['attempt_id'] for attempt in status['attempts']} == {'A','B','C'}
    asyncio.run(scenario())
