"""Suspend supervisor; verify the worker's independent kernel timer terminates it."""
import json,os,signal,subprocess,sys,tempfile,time
from pathlib import Path
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);worker=root/'worker.py';pidfile=root/'pid';late=root/'late'
    worker.write_text("import os,time\nfrom pathlib import Path\ndef run(p):\n Path(p['pid']).write_text(str(os.getpid()))\n time.sleep(8)\n Path(p['late']).write_text('unexpected')\n return {}\n")
    outer=root/'parent.py'
    outer.write_text("import sys,json\nsys.path.insert(0,sys.argv[1])\nfrom email_process_deadline import run\nrun(sys.argv[2],json.loads(sys.argv[3]),timeout=.4)\n")
    p=subprocess.Popen([sys.executable,'-I',str(outer),str(Path(__file__).parent),str(worker),json.dumps({'pid':str(pidfile),'late':str(late)})],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        end=time.monotonic()+2
        while not pidfile.exists() and time.monotonic()<end:time.sleep(.01)
        assert pidfile.exists() and p.poll() is None
        pid=int(pidfile.read_text());os.kill(p.pid,signal.SIGSTOP);start=time.monotonic();state=''
        while time.monotonic()-start<2:
            state=subprocess.run(['/bin/ps','-p',str(pid),'-o','state='],capture_output=True,text=True,timeout=1).stdout.strip()
            if not state or state.startswith('Z'):break
            time.sleep(.02)
        assert not state or state.startswith('Z'),state
        assert not late.exists()
        elapsed=time.monotonic()-start
        os.kill(p.pid,signal.SIGCONT);p.wait(timeout=2)
        print(json.dumps({'supervisor_was_suspended':True,'worker_terminal_without_supervisor':True,
            'observed_seconds':round(elapsed,3),'late_effect_absent':True,'real_mailbox_calls':0}))
    finally:
        if p.poll() is None:os.kill(p.pid,signal.SIGCONT);p.kill();p.wait()
