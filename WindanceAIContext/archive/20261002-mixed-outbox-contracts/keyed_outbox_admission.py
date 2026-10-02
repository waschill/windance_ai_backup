"""Staged trusted keyed admission. Never recovers claim-only history by replay."""
import fcntl,hashlib,json,os
from pathlib import Path
from keyed_outbox_status import lookup
from message_receipt_journal import Journal


def atomic_durable(path,value):
    temporary=path.with_suffix('.admitting')
    with temporary.open('w',encoding='utf-8') as stream:
        json.dump(value,stream,sort_keys=True,separators=(',',':'))
        stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)
    directory=os.open(str(path.parent),os.O_RDONLY)
    try:os.fsync(directory)
    finally:os.close(directory)


def admit(root,key,payload):
    root=Path(root)
    initial=lookup(root,key,payload)
    if initial!={'status':'unknown','reason':'claim_absent'}:return initial
    if payload['sms'] or any(s!=s.strip() for s in [payload['to']]+payload['chunks']):
        return {'status':'unavailable','reason':'unsupported_admission'}
    try:
        if not all((root/folder).is_dir() for folder in ('claims','queue','results')):
            return {'status':'unavailable','reason':'outbox_not_provisioned'}
        journal=Journal(root/'journal.db')  # Existing versioned history required; never create.
        request_id='key-'+hashlib.sha256(key.encode()).hexdigest();name=request_id+'.json'
        with (root/'claims'/(request_id+'.lock')).open('a') as lock:
            try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:return {'status':'unknown','reason':'admission_busy'}
            current=lookup(root,key,payload)
            if current!={'status':'unknown','reason':'claim_absent'}:return current
            # Orphaned effect records must not become a fresh admission.
            if (journal.status(request_id)['chunks'] or
                any((root/folder/name).exists() for folder in ('queue','results','inflight','uncertain'))):
                return {'status':'uncertain','reason':'orphaned_request_history'}
            body=json.dumps(payload,sort_keys=True,separators=(',',':'))
            atomic_durable(root/'claims'/name,{'content_sha256':hashlib.sha256(body.encode()).hexdigest(),'receipt_contract':2})
            atomic_durable(root/'queue'/name,dict(payload,_receipt_contract=2))
            return {'status':'pending','reason':'queued'}
    except Exception:
        return {'status':'unknown','reason':'admission_outcome_unknown'}
