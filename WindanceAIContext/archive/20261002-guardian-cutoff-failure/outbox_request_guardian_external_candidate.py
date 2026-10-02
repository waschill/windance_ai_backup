"""Guardian outside the worker's dedicated process group."""
import json,math,os,select,signal,subprocess,sys,time
from pathlib import Path
worker=None

def finish(result):
    if worker is not None:
        try:os.killpg(worker.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        worker.wait(timeout=2)
    print(json.dumps(result),flush=True)
    raise SystemExit(0)

def main():
    global worker
    raw=sys.stdin.buffer.readline(65537)
    if len(raw)>65536:raise ValueError('command_cap')
    request=json.loads(raw);command=request['command'];deadline=request['deadline']
    if (type(command) is not list or not command or any(type(x) is not str for x in command)
        or type(deadline) not in (int,float) or not math.isfinite(deadline) or not 0<deadline-time.monotonic()<=600):
        raise ValueError('invalid_request')
    if select.select([sys.stdin],[],[],0)[0] and not os.read(sys.stdin.fileno(),1):
        finish({'status':'uncertain','reason':'request_parent_gone'})
    worker=subprocess.Popen([sys.executable,'-B',str(Path(__file__).with_name('outbox_group_worker.py'))],
                            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                            start_new_session=True,close_fds=True)
    worker.stdin.write(json.dumps(command).encode()+b'\n');worker.stdin.close()
    while True:
        if time.monotonic()>=deadline:finish({'status':'uncertain','reason':'whole_request_deadline'})
        ready=select.select([sys.stdin,worker.stdout],[],[],min(0.05,max(0,deadline-time.monotonic())))[0]
        if sys.stdin in ready:
            os.read(sys.stdin.fileno(),1)
            finish({'status':'uncertain','reason':'request_parent_gone'})
        if worker.stdout in ready:
            raw=worker.stdout.readline(4097)
            if len(raw)>4096:raise ValueError('worker_result_cap')
            result=json.loads(raw)
            if set(result)!= {'returncode'} or type(result['returncode']) is not int:raise ValueError('worker_result')
            finish({'status':'process_exited','returncode':result['returncode']})

if __name__=='__main__':
    try:main()
    except Exception:finish({'status':'unavailable','reason':'request_supervision_failed'})
