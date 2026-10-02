"""Staged POSIX supervisor for trusted fixed email workers, not an access sandbox."""
import json,os,selectors,subprocess,sys,time
from pathlib import Path

class WorkerUnconfirmed(RuntimeError):pass

def run(worker,payload,*,timeout=120,output_limit=1024*1024):
    if os.name!='posix':raise ValueError('POSIX worker required')
    if not 0<timeout<=180 or not 0<output_limit<=1024*1024:raise ValueError('Bounded worker settings required')
    raw=json.dumps(payload,allow_nan=False).encode()
    if len(raw)>65536:raise ValueError('Request exceeds bound')
    worker=Path(worker).resolve(strict=True)
    # Caller supplies an operator-controlled worker path, never a user request path.
    deadline=time.monotonic()+timeout;data=bytearray();sent=0
    process=subprocess.Popen([sys.executable,'-I',str(Path(__file__).resolve()),str(worker),str(output_limit),str(timeout),str(os.getpid())],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True)
    try:
        with selectors.DefaultSelector() as selector:
            for stream,event in ((process.stdin,selectors.EVENT_WRITE),(process.stdout,selectors.EVENT_READ)):
                os.set_blocking(stream.fileno(),False);selector.register(stream,event)
            while selector.get_map():
                remaining=deadline-time.monotonic()
                if remaining<=0:raise WorkerUnconfirmed('Email worker deadline exceeded; inspect durable outcomes before retrying')
                for key,event in selector.select(min(.05,remaining)):
                    if key.fileobj is process.stdin:
                        try:sent+=os.write(process.stdin.fileno(),raw[sent:sent+4096])
                        except BrokenPipeError:sent=len(raw)
                        if sent==len(raw):selector.unregister(process.stdin);process.stdin.close()
                    else:
                        part=os.read(process.stdout.fileno(),min(65536,output_limit-len(data)+1))
                        if not part:selector.unregister(process.stdout);process.stdout.close()
                        else:
                            data.extend(part)
                            if len(data)>output_limit:raise WorkerUnconfirmed('Email worker output exceeded bound')
            remaining=deadline-time.monotonic()
            if remaining<=0:raise WorkerUnconfirmed('Email worker deadline exceeded')
            try:code=process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:raise WorkerUnconfirmed('Email worker deadline exceeded') from None
        if code!=0:raise WorkerUnconfirmed('Email worker did not confirm completion; inspect durable outcomes')
        try:result=json.loads(data)
        except Exception:raise WorkerUnconfirmed('Email worker receipt unavailable') from None
        if not isinstance(result,dict):raise WorkerUnconfirmed('Email worker receipt invalid')
        return result
    finally:
        if process.poll() is None:process.kill()
        process.wait()
        for stream in (process.stdin,process.stdout):
            if not stream.closed:stream.close()

def child():
    import importlib.util,signal,threading
    worker=Path(sys.argv[1]).resolve(strict=True);limit=int(sys.argv[2])
    lifetime=float(sys.argv[3]);parent=int(sys.argv[4])
    if not 0<lifetime<=180:raise ValueError('Bounded child lifetime required')
    # Kernel wall timer survives the supervising process; no Python signal handler.
    signal.signal(signal.SIGALRM,signal.SIG_DFL)
    signal.setitimer(signal.ITIMER_REAL,lifetime)
    def check_parent():
        while True:
            if os.getppid()!=parent:os._exit(125)
            time.sleep(.05)
    if os.getppid()!=parent:os._exit(125)
    threading.Thread(target=check_parent,daemon=True).start()
    def guard(event,args):
        if event in {'subprocess.Popen','os.system','os.fork','os.forkpty','os.posix_spawn'}:
            raise RuntimeError('Child dispatch forbidden')
    sys.addaudithook(guard)
    raw=sys.stdin.buffer.read(65537)
    if len(raw)>65536:raise ValueError('Request exceeds bound')
    payload=json.loads(raw)
    sys.path.insert(0,str(worker.parent))
    spec=importlib.util.spec_from_file_location('bounded_email_worker',worker)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result=module.run(payload)
    encoded=json.dumps(result,allow_nan=False).encode()
    if len(encoded)>limit:raise ValueError('Receipt exceeds bound')
    sys.stdout.buffer.write(encoded);sys.stdout.buffer.flush()

if __name__=='__main__':child()
