"""Staged local state machine, not an authorization or sender interface.

Only a trusted outbox owner may supply request IDs, store identity and baseline.
No method sends, retries, deletes history or resets an uncertain attempt.
"""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3


def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


class Journal:
    def __init__(self,path,*,create=False):
        self.path=Path(path)
        # Provisioning is explicit and separate from normal runtime recovery.
        if create:
            with self.path.open('xb'):
                pass
        self.uri=self.path.resolve().as_uri()+'?mode=rw'
        with self.transaction() as c:
            version=c.execute('PRAGMA user_version').fetchone()[0]
            if version==0:
                if not create:
                    raise ValueError('uninitialized_journal')
                if c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchone()[0]:
                    raise ValueError('unrecognized_journal')
                c.execute('CREATE TABLE requests(id TEXT PRIMARY KEY,payload_hash TEXT NOT NULL,count INTEGER NOT NULL)')
                c.execute('''CREATE TABLE chunks(request_id TEXT NOT NULL,idx INTEGER NOT NULL,body_hash TEXT NOT NULL,
                    state TEXT NOT NULL CHECK(state IN ('ready','attempting','submitted','delivered')),
                    store_id TEXT,boundary INTEGER,receipt_row INTEGER,
                    PRIMARY KEY(request_id,idx),UNIQUE(store_id,receipt_row),
                    FOREIGN KEY(request_id) REFERENCES requests(id))''')
                c.execute('PRAGMA user_version=1')
            elif version!=1:
                raise ValueError('unsupported_journal')

    @contextmanager
    def transaction(self):
        c=sqlite3.connect(self.uri,uri=True,timeout=2)
        try:
            c.execute('PRAGMA foreign_keys=ON')
            c.execute('PRAGMA synchronous=FULL')
            c.execute('PRAGMA fullfsync=ON')
            c.execute('BEGIN IMMEDIATE')
            yield c
            c.commit()
        except BaseException:
            c.rollback()
            raise
        finally:
            c.close()

    def register(self,request_id,recipient,chunks):
        if (type(request_id) is not str or not 1<=len(request_id)<=128 or
            type(recipient) is not str or not 1<=len(recipient)<=320 or
            type(chunks) is not list or not 1<=len(chunks)<=100 or
            any(type(s) is not str or not 1<=len(s)<=20000 for s in chunks)):
            raise ValueError('invalid_request')
        fingerprint=digest([recipient,chunks,'iMessage'])
        with self.transaction() as c:
            old=c.execute('SELECT payload_hash FROM requests WHERE id=?',(request_id,)).fetchone()
            if old:
                if old[0]!=fingerprint:raise ValueError('request_content_conflict')
                return 'existing'
            c.execute('INSERT INTO requests VALUES(?,?,?)',(request_id,fingerprint,len(chunks)))
            c.executemany('INSERT INTO chunks(request_id,idx,body_hash,state) VALUES(?,?,?,?)',
                          [(request_id,i,digest(s),'ready') for i,s in enumerate(chunks)])
            return 'registered'

    def begin(self,request_id,index,store_id,boundary):
        if (type(index) is not int or index<0 or type(boundary) is not int or not 0<=boundary<2**63 or
            type(store_id) is not str or not 1<=len(store_id)<=128):
            raise ValueError('invalid_attempt')
        with self.transaction() as c:
            row=c.execute('SELECT state FROM chunks WHERE request_id=? AND idx=?',(request_id,index)).fetchone()
            if not row:raise ValueError('unknown_chunk')
            if row[0]!='ready':return 'held_existing_attempt'
            if c.execute("SELECT count(*) FROM chunks WHERE request_id=? AND idx<? AND state!='delivered'",(request_id,index)).fetchone()[0]:
                return 'held_prior_chunk'
            previous=c.execute('SELECT store_id,receipt_row FROM chunks WHERE request_id=? AND idx<?',(request_id,index)).fetchall()
            if any(previous_store!=store_id or boundary<previous_row for previous_store,previous_row in previous):
                return 'held_boundary_regression'
            c.execute("UPDATE chunks SET state='attempting',store_id=?,boundary=? WHERE request_id=? AND idx=?",
                      (store_id,boundary,request_id,index))
            # Returned permission is valid only for this live call, never after restart.
            return 'attempt_committed'

    def submitted(self,request_id,index):
        with self.transaction() as c:
            c.execute("UPDATE chunks SET state='submitted' WHERE request_id=? AND idx=? AND state='attempting'",(request_id,index))

    def confirm(self,request_id,index,store_id,receipt):
        if (type(receipt) is not dict or set(receipt)!= {'status','evidence','message_rowid'} or
            receipt.get('status')!='delivered' or receipt.get('evidence')!='local_messages_flags' or
            type(receipt.get('message_rowid')) is not int):
            return 'held_unverified'
        rowid=receipt['message_rowid']
        with self.transaction() as c:
            row=c.execute('SELECT state,store_id,boundary,receipt_row FROM chunks WHERE request_id=? AND idx=?',(request_id,index)).fetchone()
            if not row or row[0]=='ready' or row[1]!=store_id or not row[2]<rowid<2**63:
                return 'held_correlation_mismatch'
            if row[0]=='delivered':return 'existing_receipt' if row[3]==rowid else 'held_receipt_conflict'
            if c.execute('SELECT 1 FROM chunks WHERE store_id=? AND receipt_row=?',(store_id,rowid)).fetchone():
                return 'held_row_already_claimed'
            c.execute("UPDATE chunks SET state='delivered',receipt_row=? WHERE request_id=? AND idx=?",(rowid,request_id,index))
            return 'receipt_committed'

    def status(self,request_id):
        with self.transaction() as c:
            rows=c.execute('SELECT state FROM chunks WHERE request_id=? ORDER BY idx',(request_id,)).fetchall()
            return {'status':'delivered' if rows and all(r[0]=='delivered' for r in rows) else 'unconfirmed',
                    'chunks':[r[0] for r in rows]}
