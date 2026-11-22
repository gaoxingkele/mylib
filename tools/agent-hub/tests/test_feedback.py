import asyncio
import concurrent.futures
import hashlib
import json
import secrets
import socket
from contextlib import closing

import pytest
from agent_hub.backup import backup
from agent_hub.feedback import Confirmations
from agent_hub.server import AccessDenied, Grants, create_app, token_digest
from agent_hub.storage import Store


def scenario(tmp_path):
    store=Store(tmp_path/'hub.sqlite3')
    target=dict(project='review',task_id='t',attempt_id='a',host_installation_id='host-install',
                window_id='w',terminal_session_id='s',generation='g',journal_id='j',tool='codex',
                role='primary',account='acct')
    event={k:v for k,v in target.items() if k!='project'}
    event.update(host='host-A',event_id='e1',status='reported',summary='Synthetic result.')
    rec=store.report_step('review','host-hook',event)
    tokens={who:secrets.token_urlsafe(32) for who in ('human','phone','source','read','other')}
    rows=[]
    for who,scopes in [('human',['tasks:read','feedback:confirm']),('phone',['tasks:read','feedback:confirm']),
                       ('source',['feedback:source']),('read',['tasks:read']),('other',['tasks:read','feedback:confirm'])]:
        rows.append({'sha256':token_digest(tokens[who]),'project':'review','subject':'alice' if who in ('human','phone') else who,
                     'accounts':['acct'],'feedback_hosts':['host-install'],'scopes':scopes})
    path=tmp_path/'grants.json'; path.write_text(json.dumps({'grants':rows}));path.chmod(0o600)
    args={'target':target,'baseline_seq':rec['seq'],'text_sha256':hashlib.sha256(b'test').hexdigest()}
    return store,path,tokens,target,args,rows


def test_two_clients_share_nonce_without_duplicate_dispatch_and_keep_across_backup(tmp_path):
    import sqlite3
    store,path,tokens,target,args,rows=scenario(tmp_path)
    service=Confirmations(store,Grants(path))
    def call(actor,op,params):return service.request(token_digest(tokens[actor]),op,params)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda who:call(who,'confirm',args),['human','phone']))
    assert sum(r['may_send'] for r in responses)==1
    nonce=responses[0]['nonce']
    assert responses[1]['nonce']==nonce
    assert call('other','pending',{'target':target})=={}
    same={'target':target,'nonce':nonce}
    claim={**same,'text_sha256':args['text_sha256']}
    with pytest.raises(PermissionError):call('source','source_submit',{**claim,'text_sha256':'0'*64})
    assert call('source','source_submit',claim)['authorized']
    with pytest.raises(PermissionError):call('source','source_submit',claim)
    assert call('phone','pending',{'target':target})['state']=='claimed'
    assert call('source','source_status',same)['authorized']
    with pytest.raises(PermissionError):call('phone','source_observed',{**same,'observation':'accepted'})
    assert call('source','source_observed',{**same,'observation':'accepted'})['recorded']
    assert not call('human','confirm',args)['may_send']
    assert call('phone','pending',{'target':target})['state']=='observed_accepted'
    dest=tmp_path/'backup'
    backup(store.path,dest)
    with closing(sqlite3.connect(dest/'snapshot.sqlite3')) as db:
        assert db.execute("SELECT nonce,state FROM feedback_requests").fetchall()==[(nonce,'observed_accepted')]
    with pytest.raises((PermissionError, AccessDenied)):call('read','pending',{'target':target})
    original='human' if responses[0]['may_send'] else 'phone'
    path.write_text(json.dumps({'grants':[r for r in rows if r['sha256']!=token_digest(tokens[original])]}))
    with pytest.raises((PermissionError, AccessDenied)):call('source','source_status',same)
    with pytest.raises((PermissionError, AccessDenied)):call('phone','pending',{'target':target})


def test_source_refuses_when_handoff_occurs_after_user_confirmation(tmp_path):
    store,path,tokens,target,args,_rows=scenario(tmp_path)
    service=Confirmations(store,Grants(path))
    rec=service.request(token_digest(tokens['human']),'confirm',args)
    fields={k:v for k,v in target.items() if k!='project'}
    store.report_step('review','second',dict(fields,event_id='e2',attempt_id='b',
        previous_attempt_id='a',status='running',summary='handoff'))
    with pytest.raises(PermissionError):
        service.request(token_digest(tokens['source']),'source_submit',
                        {'target':target,'nonce':rec['nonce'],'text_sha256':args['text_sha256']})


def test_dedicated_websocket_requires_exact_origin_and_human_scope(tmp_path):
    import uvicorn
    from websockets.asyncio.client import connect
    from websockets.exceptions import ConnectionClosed, InvalidStatus
    async def run():
        store,path,tokens,target,args,_rows=scenario(tmp_path)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0))
            host=f'127.0.0.1:{sock.getsockname()[1]}'
            app=create_app(store,path,hosts=[host],origins=['http://localhost:6771'],feedback_enabled=True)
            server=uvicorn.Server(uvicorn.Config(app,log_level='critical',access_log=False))
            job=asyncio.create_task(server.serve(sockets=[sock]))
            try:
                for _ in range(150):
                    if server.started:break
                    await asyncio.sleep(.02)
                async def call(who,op,params):
                    async with connect(f'ws://{host}/hub/feedback',origin='http://localhost:6771',proxy=None) as ws:
                        await ws.send(json.dumps({'op':op,'token':tokens[who],'params':params}))
                        return json.loads(await ws.recv())['result']
                with pytest.raises(InvalidStatus):
                    async with connect(f'ws://{host}/hub/feedback',origin='https://wrong.example',proxy=None):
                        pass
                with pytest.raises(ConnectionClosed):await call('read','confirm',args)
                rec=await call('human','confirm',args)
                assert rec['may_send'] is True
                assert (await call('phone','pending',{'target':target}))['nonce']==rec['nonce']
            finally:
                server.should_exit=True
                await asyncio.wait_for(job,10)
    asyncio.run(run())
