"""Staged read-only keyed lookup. Never enqueue, delete receipts or clear holds."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3


def read_json(path):
    if path.stat().st_size>2*1024*1024:raise ValueError('oversize')
    value=json.loads(path.read_text(encoding='utf-8'))
    if type(value) is not dict:raise ValueError('invalid')
    return value


def lookup(root,key,payload):
    if (type(key) is not str or not key.strip() or len(key)>512 or type(payload) is not dict or
        set(payload)!= {'to','chunks','sms'} or type(payload['to']) is not str or not payload['to'] or
        type(payload['chunks']) is not list or not payload['chunks'] or len(payload['chunks'])>100 or
        any(type(s) is not str or not s or len(s)>20000 for s in payload['chunks']) or type(payload['sms']) is not bool):
        return {'status':'unavailable','reason':'invalid_lookup'}
    root=Path(root)
    request_id='key-'+hashlib.sha256(key.encode()).hexdigest()
    name=request_id+'.json'
    expected=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    try:
        claim_path=root/'claims'/name
        if not claim_path.exists():return {'status':'unknown','reason':'claim_absent'}
        if read_json(claim_path).get('content_sha256')!=expected:
            return {'status':'conflict','reason':'request_content_mismatch'}
        result_path=root/'results'/name
        if result_path.exists():
            result=read_json(result_path)
            if result.get('status')=='uncertain':return {'status':'uncertain','reason':'held_for_reconciliation'}
            if result.get('ok') is True and 'version' not in result:
                return {'status':'legacy_submission','independent_delivery_verified':False}
            if (result.get('version')!=2 or result.get('ok') is not True or result.get('status')!='delivered' or
                result.get('evidence')!='local_messages_flags' or type(result.get('chunks')) is not int or
                result['chunks']!=len(payload['chunks']) or payload['sms']):
                return {'status':'unavailable','reason':'unrecognized_receipt'}
            # A versioned file alone is insufficient. Require matching saved journal.
            path=(root/'journal.db').resolve()
            with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=2)) as c:
                c.execute('PRAGMA query_only=ON');c.execute('BEGIN')
                operations=[0]
                def budget():
                    operations[0]+=1
                    return int(operations[0]>100)
                c.set_progress_handler(budget,1000)
                if c.execute('PRAGMA user_version').fetchone()[0]!=3:raise ValueError('journal_version')
                fingerprint=hashlib.sha256(json.dumps([payload['to'],payload['chunks'],'iMessage'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
                request=c.execute('SELECT payload_hash,count FROM requests WHERE id=?',(request_id,)).fetchone()
                if request!=(fingerprint,len(payload['chunks'])):raise ValueError('journal_identity')
                rows=c.execute('SELECT idx,state,store_id,boundary,receipt_row,CASE WHEN length(checkpoint_json)<=4096 THEN checkpoint_json ELSE NULL END FROM chunks WHERE request_id=? ORDER BY idx LIMIT 101',(request_id,)).fetchall()
                if len(rows)!=len(payload['chunks']):raise ValueError('journal_count')
                for idx,row in enumerate(rows):
                    index,state,store_id,boundary,receipt_row,snapshot_json=row
                    if index!=idx or state!='delivered' or not store_id or type(boundary) is not int or type(receipt_row) is not int or receipt_row<=boundary:
                        raise ValueError('journal_evidence')
                    snapshot=json.loads(snapshot_json)
                    if snapshot.get('status')!='captured' or snapshot.get('store_id')!=store_id or snapshot.get('boundary')!=boundary:
                        raise ValueError('journal_checkpoint')
            return {'status':'verified_delivery','independent_delivery_verified':True,'chunks':len(rows)}
        if (root/'uncertain'/name).exists() or (root/'inflight'/name).exists():
            return {'status':'uncertain','reason':'attempt_or_quarantine_present'}
        if (root/'queue'/name).exists():return {'status':'pending','reason':'queued'}
        return {'status':'unknown','reason':'claim_without_outcome'}
    except (OSError,ValueError,sqlite3.Error,TypeError):
        return {'status':'unavailable','reason':'status_evidence_unavailable'}
