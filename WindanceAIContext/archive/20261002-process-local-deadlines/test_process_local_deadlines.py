"""Aged parent and repeated deadlines: no cross-process clock subtraction."""
import json,subprocess,sys,tempfile,time
from pathlib import Path
from bounded_outbox_request import run_bounded

time.sleep(2)
samples=[]
with tempfile.TemporaryDirectory(prefix='windance-local-deadline-') as tmp:
    root=Path(tmp)
    for index in range(5):
        worker=root/('worker%d.py'%index)
        effect=root/('effect%d'%index)
        pidfile=root/('pid%d'%index)
        worker.write_text('import os,time\nfrom pathlib import Path\nPath(%r).write_text(str(os.getpid()))\ntime.sleep(.8)\nPath(%r).write_text("synthetic")\ntime.sleep(60)\n'%(str(pidfile),str(effect)))
        start=time.monotonic()
        result=run_bounded([sys.executable,str(worker)],seconds=.3)
        elapsed=time.monotonic()-start
        assert result=={'status':'uncertain','reason':'whole_request_deadline'},result
        assert elapsed<.65,elapsed
        assert pidfile.exists(),'worker never started'
        state=subprocess.run(['/bin/ps','-o','stat=','-p',pidfile.read_text()],capture_output=True,text=True,timeout=1).stdout.strip()
        assert not state or state.startswith('Z'),state
        time.sleep(.85)
        assert not effect.exists(),'late synthetic effect'
        samples.append({'elapsed_seconds':round(elapsed,4),'worker_stopped':True,'late_effect_absent':True})
print(json.dumps({'status':'passed','python':sys.version.split()[0],'samples':samples,'real_sends':0}))
