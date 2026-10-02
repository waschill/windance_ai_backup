import hashlib,json,sqlite3,uuid
from contextlib import contextmanager
from pathlib import Path

class JobError(Exception):
    def __init__(self,status_code,detail):
        self.status_code=status_code;self.detail=detail
        super().__init__(detail)

class Ledger:
    def __init__(self,path):
        self.path=Path(path)
        with self.connect() as c:
            c.executescript('''CREATE TABLE IF NOT EXISTS jobs(
              id TEXT PRIMARY KEY,owner TEXT NOT NULL,request_key TEXT NOT NULL,
              request_hash TEXT NOT NULL,state TEXT NOT NULL,payload TEXT NOT NULL,
              UNIQUE(owner,request_key));
              CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY,job_id TEXT NOT NULL,state TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS results(job_id TEXT PRIMARY KEY,receipt_json TEXT NOT NULL);''')
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
                if prior['request_hash']!=digest:raise JobError(409,'Request key already binds different evidence')
                return {'id':prior['id'],'state':prior['state'],'reused':True}
            key=uuid.uuid4().hex
            c.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?)',(key,owner,body.request_key,digest,'queued',payload))
            c.execute('INSERT INTO events(job_id,state) VALUES(?,?)',(key,'queued'))
            return {'id':key,'state':'queued','reused':False}
    def read(self,owner,key):
        with self.connect() as c:
            row=c.execute('SELECT id,state FROM jobs WHERE owner=? AND id=?',(owner,key)).fetchone()
            if not row:raise JobError(404,'Job not found')
            events=[dict(r) for r in c.execute('SELECT seq,state FROM events WHERE job_id=? ORDER BY seq',(key,))]
            return {**dict(row),'events':events,'worker_liveness':'not_observed'}
    def cancel(self,owner,key):
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT state FROM jobs WHERE owner=? AND id=?',(owner,key)).fetchone()
            if not row:raise JobError(404,'Job not found')
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
    def request(self,key):
        with self.connect() as c:
            row=c.execute('SELECT payload,state FROM jobs WHERE id=?',(key,)).fetchone()
            if not row:raise JobError(404,'Job not found')
            return json.loads(row['payload']),row['state']
    def finish(self,key,receipt):
        encoded=json.dumps(receipt,sort_keys=True,separators=(',',':'))
        if len(encoded)>65536:raise JobError(409,'Receipt exceeds bound')
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT state,payload FROM jobs WHERE id=?',(key,)).fetchone()
            if not row or row['state'] not in ('running','cancel_requested'):raise JobError(409,'No active claim')
            request=json.loads(row['payload'])
            if receipt.get('job_id')!=key or receipt.get('evidence_sha256')!=request['evidence_sha256'] or receipt.get('worker_stopped') is not True:raise JobError(409,'Receipt identity mismatch')
            if receipt.get('outcome')!='completed':raise JobError(409,'Completion evidence required')
            # A cancel request is not a claim that completion could not race it.
            c.execute('INSERT INTO results VALUES(?,?)',(key,encoded))
            c.execute("UPDATE jobs SET state='completed' WHERE id=?",(key,))
            c.execute("INSERT INTO events(job_id,state) VALUES(?,'completed')",(key,))
    def result(self,owner,key):
        self.read(owner,key)
        with self.connect() as c:
            row=c.execute('SELECT receipt_json FROM results WHERE job_id=?',(key,)).fetchone()
            if not row:raise JobError(409,'No verified result available')
            return json.loads(row[0])
