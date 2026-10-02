"""Keep group identity alive until the external guardian cleans it."""
import json,os,subprocess,sys,time

if __name__=='__main__':
    assert os.getpid()==os.getpgrp()
    raw=sys.stdin.buffer.readline(65537)
    assert len(raw)<=65536
    command=json.loads(raw)
    assert type(command) is list and command and all(type(x) is str for x in command)
    child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL,close_fds=True)
    code=child.wait()
    print(json.dumps({'returncode':code}),flush=True)
    while True:time.sleep(60)
