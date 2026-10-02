"""Actual SAL outbox functions, disposable directories, send_one intercepted."""
import ast
import __future__
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import uuid

sources={name:(Path('/Users/zuzu/bin')/name).read_text() for name in ['send_imessage_payload.py','imessage_outbox_daemon.py']}
class Crash(BaseException):pass
results=[]
for scenario in ['completed_retry','post_send_crash','post_receipt_crash','content_conflict','pre_queue_recovery','partial_chunk_failure']:
    with tempfile.TemporaryDirectory(prefix='windance-outbox-fixture-') as directory:
        root=Path(directory);queue=root/'queue';receipts=root/'results';attempts=[]
        n={'ROOT':root,'QUEUE':queue,'RESULTS':receipts,'Path':Path,'json':json,'hashlib':hashlib,'uuid':uuid,'os':os,'fcntl':fcntl,
           'log':lambda *args:None,'time':SimpleNamespace(sleep=lambda _:None)}
        for name,s in sources.items():
            wanted={'enqueue'} if name.startswith('send_') else {'atomic_json','hold_uncertain','handle'}
            nodes=[x for x in ast.parse(s).body if isinstance(x,ast.FunctionDef) and x.name in wanted]
            exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-outbox-functions>','exec',flags=__future__.annotations.compiler_flag),n)
        def send_one(recipient,text,sms):
            attempts.append(text)
            if scenario=='post_send_crash':raise Crash()
            if scenario=='partial_chunk_failure' and len(attempts)==2:raise RuntimeError('fixture uncertain failure')
        n['send_one']=send_one
        atomic=n['atomic_json']
        def atomic_json(path,value):
            atomic(path,value)
            if scenario=='post_receipt_crash' and path.parent==receipts:raise Crash()
        n['atomic_json']=atomic_json
        payload={'to':'fixture-recipient','chunks':['fixture-one']+(['fixture-two'] if scenario=='partial_chunk_failure' else []),'sms':False}
        result,retained=n['enqueue'](payload,'fixture-stable-key')
        queued=next(queue.glob('*.json'))
        if scenario=='content_conflict':
            try:n['enqueue']({**payload,'chunks':['different']},'fixture-stable-key')
            except ValueError:pass
            else:raise AssertionError('Content mismatch accepted')
            assert not attempts
        else:
            if scenario=='pre_queue_recovery':
                queued.unlink();n['enqueue'](payload,'fixture-stable-key');assert queued.exists()
            try:n['handle'](queued)
            except Crash:pass
            n['atomic_json']=atomic
            before=len(attempts)
            n['enqueue'](payload,'fixture-stable-key')
            if queued.exists():n['handle'](queued)
            assert len(attempts)==before, 'Uncertain or completed send repeated'
            receipt=json.loads(result.read_text())
            if scenario in {'post_send_crash','partial_chunk_failure'}:
                assert receipt['status']=='uncertain' and receipt['ok'] is False
                assert (root/'uncertain'/queued.name).exists()
            else:assert receipt['ok'] is True and not queued.exists()
        results.append({'scenario':scenario,'intercepted_send_attempts':len(attempts),'passed':True})
print(json.dumps({'source_sha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in sources.items()},
 'scenarios':results,'real_sends':0,'production_outbox_writes':0,
 'limits':'Process-level idempotency/uncertainty behavior only; no independent Messages transport delivery proof.'},indent=2))
