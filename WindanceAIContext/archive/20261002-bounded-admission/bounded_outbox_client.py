"""Staged trusted keyed submission and read-only wait under one caller budget."""
import json,math,subprocess,sys,time
from pathlib import Path

ALLOWED={'verified_delivery','pending','uncertain','legacy_submission','conflict','unknown','unavailable'}


def submit_and_wait(root,key,payload,*,seconds=55):
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or not 0<seconds<=55:
        return {'status':'unavailable','reason':'invalid_wait_budget'}
    started=time.monotonic();child=None
    try:
        raw=json.dumps({'root':str(root),'key':key,'payload':payload}).encode()
        if len(raw)>2*1024*1024:raise ValueError('input_cap')
        child=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--worker'],
                               stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        remaining=seconds-(time.monotonic()-started)
        if remaining<=0:raise subprocess.TimeoutExpired('status',seconds)
        out,_=child.communicate(raw,timeout=remaining)
        if child.returncode or len(out)>4096:raise ValueError('status_worker_failed')
        result=json.loads(out)
        if type(result) is not dict or result.get('status') not in ALLOWED:raise ValueError('invalid_status')
        return result
    except subprocess.TimeoutExpired:
        return {'status':'unknown','reason':'status_wait_expired','retry_action':'query_same_request_only'}
    except Exception:
        return {'status':'unavailable','reason':'status_query_failed'}
    finally:
        if child is not None and child.poll() is None:
            child.kill();child.communicate(timeout=3)


def worker():
    from keyed_outbox_status import lookup
    raw=sys.stdin.buffer.read(2*1024*1024+1)
    if len(raw)>2*1024*1024:raise ValueError('input_cap')
    request=json.loads(raw)
    from keyed_outbox_admission import admit
    admitted=admit(request['root'],request['key'],request['payload'])
    if admitted.get('status')!='pending':
        print(json.dumps(admitted),flush=True);return
    while True:
        result=lookup(request['root'],request['key'],request['payload'])
        if result['status']!='pending':
            print(json.dumps(result),flush=True);return
        time.sleep(.1)


if __name__=='__main__':
    if sys.argv[1:]==['--worker']:
        try:worker()
        except Exception:raise SystemExit(1)
    else:raise SystemExit(2)

