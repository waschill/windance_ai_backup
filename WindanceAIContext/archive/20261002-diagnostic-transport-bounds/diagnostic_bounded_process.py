"""Operator-only bounded transport capture. Local stop is not remote job cancellation."""
import os,selectors,signal,subprocess,time

def capture(args,*,timeout,max_stdout,max_stderr=4096):
    process=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    output=bytearray();error=bytearray();deadline=time.monotonic()+timeout
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout,selectors.EVENT_READ,(output,max_stdout))
            selector.register(process.stderr,selectors.EVENT_READ,(error,max_stderr))
            while selector.get_map():
                remaining=deadline-time.monotonic()
                if remaining<=0:raise RuntimeError('Diagnostic transport deadline exceeded; outcome unconfirmed')
                for key,_ in selector.select(min(remaining,.1)):
                    target,limit=key.data
                    chunk=os.read(key.fileobj.fileno(),min(4096,limit-len(target)+1))
                    if not chunk:
                        selector.unregister(key.fileobj);continue
                    if len(target)+len(chunk)>limit:raise RuntimeError('Diagnostic transport output exceeds bound; outcome unconfirmed')
                    target.extend(chunk)
            remaining=deadline-time.monotonic()
            if remaining<=0:raise RuntimeError('Diagnostic transport deadline exceeded; outcome unconfirmed')
            try:code=process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:raise RuntimeError('Diagnostic transport deadline exceeded; outcome unconfirmed') from None
            if code:raise RuntimeError('Diagnostic transport failed; outcome unconfirmed')
            try:return output.decode('utf-8')
            except UnicodeDecodeError:raise RuntimeError('Invalid diagnostic transport encoding; outcome unconfirmed') from None
    finally:
        # Kill only this local transport group. Never claim remote worker termination.
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        process.wait()
        process.stdout.close();process.stderr.close()
