"""Human confirmation ledger. This endpoint carries metadata and never dispatches text."""
import asyncio
import hashlib
import json
import re
import secrets
import time

TARGET = ("project","task_id","attempt_id","host_installation_id","window_id",
          "terminal_session_id","generation","journal_id","tool","role","account")
SCHEMA = """CREATE TABLE IF NOT EXISTS feedback_requests (
    nonce TEXT PRIMARY KEY, project TEXT NOT NULL, subject TEXT NOT NULL, grant_digest TEXT NOT NULL,
    task_id TEXT NOT NULL, attempt_id TEXT NOT NULL, target TEXT NOT NULL, intent TEXT NOT NULL,
    body_sha256 TEXT NOT NULL, state TEXT NOT NULL, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
    UNIQUE(project,subject,intent))"""


def _json(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))


def _target(value):
    if not isinstance(value,dict) or set(value)!=set(TARGET):
        raise ValueError("invalid_target")
    for key in TARGET:
        v=value[key]
        if not isinstance(v,str) or not 1<=len(v)<=256 or any(ord(c)<32 for c in v):
            raise ValueError("invalid_target")
    return {k:value[k] for k in TARGET}


def _allowed(grant,target,scope):
    return (grant.get("project")==target["project"] and scope in grant.get("scopes",[])
            and target["host_installation_id"] in grant.get("feedback_hosts",[])
            and target["account"] in grant.get("accounts",[]))


def _current_attempt(db,target):
    row=db.execute("""SELECT a.payload,a.last_seq,t.primary_attempt_id FROM task_attempts a
        JOIN task_current t ON t.project=a.project AND t.task_id=a.task_id
        WHERE a.project=? AND a.task_id=? AND a.attempt_id=?""",
        (target["project"],target["task_id"],target["attempt_id"])).fetchone()
    if not row: raise PermissionError()
    attempt=json.loads(row["payload"])
    if (target["role"]!="verify" and row["primary_attempt_id"]!=target["attempt_id"]
            or any(attempt.get(k, "primary" if k=="role" else None)!=target[k] for k in TARGET if k!="project")):
        raise PermissionError()
    return row["last_seq"]


def _public(row):
    return {"nonce": row["nonce"], "text_sha256":row["body_sha256"],
            "expires_at":row["expires_at"],"state":row["state"]}


class Confirmations:
    def __init__(self,store,grants):
        self.store,self.grants=store,grants
        with store._db(write=True) as db:
            db.execute(SCHEMA)
            db.execute("""CREATE INDEX IF NOT EXISTS feedback_pending
                ON feedback_requests(project,subject,task_id,attempt_id,state,created_at)""")

    def request(self,digest,action,body):
        allowed_fields={
            "pending":{"target"}, "confirm":{"target","text_sha256","baseline_seq"},
            "source_submit":{"target","text_sha256","nonce"}, "source_status":{"target","nonce"},
            "source_observed":{"target","nonce","observation"}}
        if action not in allowed_fields or not isinstance(body,dict) or set(body)!=allowed_fields[action]:
            raise ValueError("invalid_request")
        target=_target(body["target"])
        source=action.startswith("source_")
        with self.store._db(write=action!="pending" and action!="source_status") as db:
            grant=self.grants.resolve(digest,target["project"])
            scope="feedback:source" if source else "feedback:confirm"
            if not _allowed(grant,target,scope) or (not source and "tasks:read" not in grant["scopes"]):
                raise PermissionError()
            seq=_current_attempt(db,target)
            subject=grant['subject']
            encoded=_json(target)
            if action in {"pending","confirm"}:
                row=db.execute("""SELECT * FROM feedback_requests WHERE project=? AND subject=? AND
                    task_id=? AND attempt_id=? AND target=? AND (?='pending' OR state IN ('reserved','claimed'))
                    ORDER BY created_at DESC,rowid DESC LIMIT 1""",
                    (target["project"],subject,target["task_id"],target["attempt_id"],encoded,action)).fetchone()
                if row:
                    self._human(row,target)
                    return {**_public(row),"may_send":False}
                if action=="pending": return {}
                hashed=body.get("text_sha256")
                if not isinstance(hashed,str) or not re.fullmatch(r"[0-9a-f]{64}",hashed):
                    raise ValueError("invalid_digest")
                if type(body["baseline_seq"])!=int or body["baseline_seq"]!=seq:
                    raise ValueError("baseline_changed")
                intent=hashlib.sha256(_json([target,seq,hashed]).encode()).hexdigest()
                prior=db.execute("SELECT * FROM feedback_requests WHERE project=? AND subject=? AND intent=?",
                          (target["project"],subject,intent)).fetchone()
                if prior:
                    self._human(prior,target)
                    return {**_public(prior),"may_send":False}
                now=int(time.time())
                nonce=secrets.token_hex(24)
                db.execute("""INSERT INTO feedback_requests VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (nonce,target["project"],subject,digest,target["task_id"],target["attempt_id"],encoded,
                     intent,hashed,"reserved",now,now+120))
                return {"nonce":nonce,"text_sha256":hashed,"expires_at":now+120,"state":"reserved","may_send":True}
            nonce=body["nonce"]
            if not isinstance(nonce,str) or not re.fullmatch(r"[0-9a-f]{48}",nonce):
                raise ValueError("invalid_nonce")
            row=db.execute("SELECT * FROM feedback_requests WHERE nonce=? AND project=?",(nonce,target["project"])).fetchone()
            if not row or row["target"]!=encoded or (not source and row["subject"]!=subject):
                raise PermissionError()
            self._human(row,target)
            if action=="source_submit":
                if row["body_sha256"]!=body["text_sha256"] or row["state"]!="reserved" or time.time()>row["expires_at"]:
                    raise PermissionError()
                db.execute("UPDATE feedback_requests SET state='claimed' WHERE nonce=?",(nonce,))
                return {"authorized":True,"nonce":nonce}
            if action=="source_status":
                return {"authorized":True,"nonce":nonce}
            state=body["observation"]
            if state=="absent" and time.time()<=row["expires_at"]:
                return {"recorded":True,"nonce":nonce}
            if state not in {"accepted","absent"}: raise ValueError("invalid_observation")
            if state=="accepted" and row["state"] not in {"claimed","observed_accepted"}:
                raise PermissionError()
            if row["state"] in {"reserved","claimed"}:
                db.execute("UPDATE feedback_requests SET state=? WHERE nonce=?",("observed_"+state,nonce))
            return {"recorded":True,"nonce":nonce}

    def _human(self,row,target):
        original=self.grants.resolve(row["grant_digest"],target["project"])
        if (original.get("subject")!=row["subject"] or "tasks:read" not in original["scopes"]
                or not _allowed(original,target,"feedback:confirm")):
            raise PermissionError()


def feedback_route(store,grants,hosts,origins,adoption=None):
    from starlette.routing import WebSocketRoute
    from starlette.websockets import WebSocketDisconnect
    from .server import token_digest
    ledger=Confirmations(store,grants)
    async def handle(ws):
        if ws.headers.get('host') not in hosts or ws.headers.get('origin') not in origins:
            await ws.close(code=1008); return
        await ws.accept()
        try:
            raw=await asyncio.wait_for(ws.receive_text(),5)
            if len(raw.encode('utf-8'))>8192: raise ValueError()
            message=json.loads(raw)
            if not isinstance(message,dict) or set(message)!={'op','token','params'}: raise ValueError()
            digest=token_digest(message.pop('token'))
            target=message['params']['target']
            project=target['project']
            grant=grants.resolve(digest,project)
            if message['op'] in {'evolution_preview','evolution_confirm'}:
                if adoption is None or not {'evolution:confirm','tasks:read'}<=set(grant.get('scopes',[])):
                    raise PermissionError()
                args=dict(message['params'])
                expected={'target','skill_id'}
                if message['op']=='evolution_confirm':
                    expected.update({'version','asset_sha256','request_id'})
                if set(args)!=expected or set(target)!={'project','task_id','attempt_id','generation'}:
                    raise ValueError('invalid_evolution_arguments')
                args['target']={k:v for k,v in target.items() if k!='project'}
                operation='preview_evolution_loading' if message['op']=='evolution_preview' else 'confirm_evolution_loading'
                result=await asyncio.to_thread(adoption.request,grant,operation,project,**args)
            else:
                result=await asyncio.to_thread(ledger.request,digest,message['op'],message['params'])
                scope='feedback:source' if message['op'].startswith('source_') else 'feedback:confirm'
                if not _allowed(grant,target,scope): raise PermissionError()
            if grant!=grants.resolve(digest,project): raise PermissionError()
            await ws.send_json({'ok':True,'result':result})
            await ws.close()
        except WebSocketDisconnect:
            return
        except Exception:
            await ws.close(code=1008)
    return WebSocketRoute('/hub/feedback',handle)
