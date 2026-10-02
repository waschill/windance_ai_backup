"""Short-lived POSIX receiver pause lease. No launchctl, send, or deployment."""
import hashlib,json,os,select,signal,subprocess,sys,time

def interrupted(signum,frame):raise RuntimeError('guard_interrupted')

def inspect(pid):
    result=subprocess.run(['/bin/ps','-p',str(pid),'-o','lstart=','-o','command='],capture_output=True,timeout=1)
    if result.returncode!=0 or not result.stdout.strip():return None
    state=subprocess.run(['/bin/ps','-p',str(pid),'-o','stat='],capture_output=True,timeout=1)
    if state.returncode!=0:return None
    return hashlib.sha256(result.stdout.strip()).hexdigest(),state.stdout.decode().strip()

def main():
    request=json.loads(sys.stdin.buffer.readline(4097))
    assert set(request)=={'pid','identity','seconds'}
    pid=request['pid'];expected=request['identity'];seconds=request['seconds']
    assert type(pid) is int and pid>1 and pid!=os.getpid()
    assert type(expected) is str and len(expected)==64
    assert type(seconds) in (int,float) and 0<seconds<=15
    before=inspect(pid)
    if before is None or before[0]!=expected or 'T' in before[1]:
        print(json.dumps({'status':'held','reason':'process_identity_or_state'}),flush=True);return 20
    paused=False;deadline=time.monotonic()+seconds
    try:
        paused=True;os.kill(pid,signal.SIGSTOP)
        check=inspect(pid)
        if check is None or check[0]!=expected or 'T' not in check[1]:raise RuntimeError('pause_not_verified')
        print(json.dumps({'status':'paused','pid':pid,'lease_seconds':seconds}),flush=True)
        reason='lease_expired'
        while time.monotonic()<deadline:
            ready,_,_=select.select([sys.stdin],[],[],min(.1,max(0,deadline-time.monotonic())))
            if ready:
                line=sys.stdin.buffer.readline(128)
                reason='controller_gone' if not line else 'resume_requested'
                break
        print(json.dumps({'status':'releasing','reason':reason}),flush=True)
    finally:
        # A service manager may already have removed this exact process.
        # Never signal a PID whose observed start/command identity changed.
        if paused:
            current=inspect(pid)
            if current is not None and current[0]==expected:
                os.kill(pid,signal.SIGCONT)
                print(json.dumps({'status':'resumed'}),flush=True)
            else:print(json.dumps({'status':'original_process_absent'}),flush=True)
    return 0

if __name__=='__main__':
    signal.signal(signal.SIGTERM,interrupted)
    signal.signal(signal.SIGINT,interrupted)
    try:raise SystemExit(main())
    except Exception:raise SystemExit(1)
