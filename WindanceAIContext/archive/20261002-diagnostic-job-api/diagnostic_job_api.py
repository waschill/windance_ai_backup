"""Staged authenticated job ledger. No scheduler or execution route is enabled."""
import hashlib,hmac,json,re,sqlite3,uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Literal
from fastapi import FastAPI,Header,HTTPException
from pydantic import BaseModel,ConfigDict,Field

class Submission(BaseModel):
    model_config=ConfigDict(extra='forbid')
    request_key:str=Field(min_length=1,max_length=128,pattern=r'^[A-Za-z0-9_.:-]+$')
    kind:Literal['email_payload_diagnosis']
    evidence_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')

class Ledger:
    def __init__(self,path):
        self.path=Path(path)
        with self.connect() as c:
            c.executescript('''CREATE TABLE IF NOT EXISTS jobs(
              id TEXT PRIMARY KEY,owner TEXT NOT NULL,request_key TEXT NOT NULL,
              request_hash TEXT NOT NULL,state TEXT NOT NULL,payload TEXT NOT NULL,
              UNIQUE(owner,request_key));
              CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY,job_id TEXT NOT NULL,state TEXT NOT NULL);''')
    @contextmanager
    def connect(self):
        c=sqlite3.connect(self.path,timeout=1);c.row_factory=sqlite3.Row
        try:
            with c:yield c
        finally:c.close()
    def submit(self,owner,body):
        payload=json.dumps(body.model_dump(),sort_keys=True,separators=(',',':'))
        digest=hashlib.sha256(payload.encode()).hexdigest()
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            prior=c.execute('SELECT * FROM jobs WHERE owner=? AND request_key=?',(owner,body.request_key)).fetchone()
            if prior:
                if prior['request_hash']!=digest:raise HTTPException(409,'Request key already binds different evidence')
                return {'id':prior['id'],'state':prior['state'],'reused':True}
            key=uuid.uuid4().hex
            c.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?)',(key,owner,body.request_key,digest,'queued',payload))
            c.execute('INSERT INTO events(job_id,state) VALUES(?,?)',(key,'queued'))
            return {'id':key,'state':'queued','reused':False}
    def read(self,owner,key):
        with self.connect() as c:
            row=c.execute('SELECT id,state FROM jobs WHERE owner=? AND id=?',(owner,key)).fetchone()
            if not row:raise HTTPException(404,'Job not found')
            events=[dict(r) for r in c.execute('SELECT seq,state FROM events WHERE job_id=? ORDER BY seq',(key,))]
            return {**dict(row),'events':events,'worker_liveness':'not_observed'}
    def cancel(self,owner,key):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT state FROM jobs WHERE owner=? AND id=?',(owner,key)).fetchone()
            if not row:raise HTTPException(404,'Job not found')
            state=row['state']
            new='cancelled' if state=='queued' else 'cancel_requested' if state=='running' else state
            if state!=new:
                c.execute('UPDATE jobs SET state=? WHERE id=?',(new,key))
                c.execute('INSERT INTO events(job_id,state) VALUES(?,?)',(key,new))
            return {'id':key,'state':new,'worker_stopped':new=='cancelled'}
    def claim(self,key):
        """Internal one-way claim; no automatic requeue for lost worker evidence."""
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            changed=c.execute("UPDATE jobs SET state='running' WHERE id=? AND state='queued'",(key,)).rowcount
            if changed:c.execute('INSERT INTO events(job_id,state) VALUES(?,?)',(key,'running'))
            return changed==1

def create_app(database,credential_principals):
    # Server-owned mapping of SHA256(token) -> principal; request body never selects it.
    principals=dict(credential_principals)
    if not principals or any(not re.fullmatch('[0-9a-f]{64}',k) or not isinstance(v,str) or not v.strip() for k,v in principals.items()):
        raise ValueError('Explicit nonempty credential/principal configuration required')
    ledger=Ledger(database);app=FastAPI();app.state.ledger=ledger
    def owner(header):
        if not isinstance(header,str) or not header.startswith('Bearer ') or len(header)>512:raise HTTPException(401,'Authentication required')
        candidate=hashlib.sha256(header[7:].encode()).hexdigest()
        for digest,principal in principals.items():
            if hmac.compare_digest(digest,candidate):return principal
        raise HTTPException(401,'Authentication required')
    @app.post('/jobs')
    def submit(body:Submission,authorization:str|None=Header(default=None)):
        return ledger.submit(owner(authorization),body)
    @app.get('/jobs/{key}')
    def status(key:str,authorization:str|None=Header(default=None)):
        return ledger.read(owner(authorization),key)
    @app.post('/jobs/{key}/cancel')
    def cancel(key:str,authorization:str|None=Header(default=None)):
        return ledger.cancel(owner(authorization),key)
    @app.get('/jobs/{key}/result')
    def result(key:str,authorization:str|None=Header(default=None)):
        ledger.read(owner(authorization),key)
        raise HTTPException(409,'No verified result; execution adapter is not enabled')
    return app
