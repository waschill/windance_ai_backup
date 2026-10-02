"""Parent death and normal leader exit leave no running same-group descendants."""
import json,os,subprocess,sys,tempfile,time
from pathlib import Path
from bounded_outbox_request import run_bounded


def not_running(pid):
    value=subprocess.run(['/bin/ps','-o','stat=','-p',str(pid)],capture_output=True,text=True,timeout=1)
    return not value.stdout.strip() or value.stdout.strip().startswith('Z')


if sys.argv[1:2]==['--parent']:
    run_bounded([sys.executable,sys.argv[2]],seconds=30)
else:
    results=[]
    with tempfile.TemporaryDirectory(prefix='windance-guardian-lifecycle-') as tmp:
        for case in ('normal_exit','parent_death'):
            root=Path(tmp)/case;root.mkdir()
            grandchild=root/'grandchild.py'
            grandchild.write_text("import os,time\nfrom pathlib import Path\nr=Path(__file__).parent\n(r/'descendant.pid').write_text(str(os.getpid()))\ntime.sleep(2)\n(r/'late_effect').write_text('synthetic')\ntime.sleep(60)\n")
            worker=root/'worker.py'
            worker.write_text("import os,subprocess,sys,time\nfrom pathlib import Path\nr=Path(__file__).parent\n(r/'worker.pid').write_text(str(os.getpid()))\nsubprocess.Popen([sys.executable,str(r/'grandchild.py')])\nwhile not (r/'descendant.pid').exists():time.sleep(0.01)\n"+('time.sleep(60)\n' if case=='parent_death' else ''))
            if case=='normal_exit':
                result=run_bounded([sys.executable,str(worker)],seconds=5)
                assert result=={'status':'process_exited','returncode':0},result
            else:
                parent=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--parent',str(worker)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                deadline=time.monotonic()+3
                while not (root/'descendant.pid').exists():
                    assert parent.poll() is None and time.monotonic()<deadline
                    time.sleep(0.02)
                parent.kill();parent.wait(timeout=2)
            pids=[int((root/name).read_text()) for name in ('worker.pid','descendant.pid')]
            deadline=time.monotonic()+2
            while not all(not_running(pid) for pid in pids):
                assert time.monotonic()<deadline,(case,'survivor')
                time.sleep(0.05)
            time.sleep(2.1)
            assert not (root/'late_effect').exists()
            results.append({'case':case,'workers_not_running':True,'late_effect_absent':True})
    print(json.dumps({'status':'passed','cases':results,'escaped_sessions_tested':False,'real_sends':0}))
