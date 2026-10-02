"""Staged SAL receipt worker. Request content travels over stdin, never argv/logs."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

WHEEL_HASH='499920d4cb8bec8fd9d9cdd4c6312765eb418c398c10371ab1c9c0051104d278'
FAIL={'status':'unavailable','reason':'bounded_observation_failed'}


def observe_bounded(database,recipient,text,boundary,wheel):
    child=None
    try:
        payload=json.dumps({'database':str(Path(database).resolve()),'recipient':recipient,
                            'text':text,'boundary':boundary},ensure_ascii=False).encode('utf-8')
        if len(payload)>262144:return dict(FAIL)
        child=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--worker',str(Path(wheel).resolve())],
                               stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        deadline=time.monotonic()+15
        first=True
        while True:
            if time.monotonic()>=deadline:raise TimeoutError()
            try:
                stdout,stderr=child.communicate(input=payload if first else None,timeout=0.05)
                break
            except subprocess.TimeoutExpired:
                first=False
                sample=subprocess.run(['/bin/ps','-o','rss=','-p',str(child.pid)],capture_output=True,timeout=1)
                if sample.returncode==0:
                    if int(sample.stdout.strip())>256*1024:raise MemoryError()
                elif child.poll() is None:raise RuntimeError()
        if child.returncode or len(stdout)>4096:return dict(FAIL)
        result=json.loads(stdout)
        if type(result) is not dict:return dict(FAIL)
        if result.get('status')=='delivered':
            if (set(result)!= {'status','evidence','message_rowid'} or result['evidence']!='local_messages_flags'
                or type(result['message_rowid']) is not int or result['message_rowid']<=boundary):return dict(FAIL)
        elif (set(result)!= {'status','reason'} or result.get('status') not in ('unavailable','unconfirmed','ambiguous')
              or result.get('reason') not in REASONS):return dict(FAIL)
        return result
    except Exception:
        return dict(FAIL)
    finally:
        if child is not None and child.poll() is None:
            child.kill()
            child.communicate(timeout=2)


REASONS={'invalid_correlation_input','candidate_limit_exceeded','candidate_content_unverifiable',
         'no_exact_direct_message','multiple_exact_messages','message_error_recorded',
         'delivery_flags_incomplete','receipt_store_unavailable','bounded_observation_failed'}


def worker(wheel):
    import os
    import resource
    import signal
    resource.setrlimit(resource.RLIMIT_CPU,(5,5))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    signal.alarm(10)
    assert hashlib.sha256(wheel.read_bytes()).hexdigest()==WHEEL_HASH
    sys.path.insert(0,str(wheel))
    from messages_attributed_receipt import observe
    raw=sys.stdin.buffer.read(262145)
    if len(raw)>262144:return dict(FAIL)
    request=json.loads(raw)
    if type(request) is not dict or set(request)!= {'database','recipient','text','boundary'}:return dict(FAIL)
    database=Path(request['database']).resolve()
    uri=database.as_uri()+'?mode=ro'
    def guard(event,args):
        if event in ('subprocess.Popen','os.system','os.posix_spawn') or event.startswith('socket.'):
            raise PermissionError('effect_denied')
        if event=='sqlite3.connect' and args[0] not in (uri,uri.encode('utf-8')):
            raise PermissionError('unexpected_database')
        if event=='open':
            mode,flags=args[1:3]
            write_flags=os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND
            if (isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&write_flags):
                raise PermissionError('write_denied')
    sys.addaudithook(guard)
    return observe(database,request['recipient'],request['text'],request['boundary'])


if __name__=='__main__':
    try:
        if sys.argv[1:2]!=['--worker']:raise ValueError()
        result=worker(Path(sys.argv[2]))
    except Exception:
        result=dict(FAIL)
    print(json.dumps(result))
