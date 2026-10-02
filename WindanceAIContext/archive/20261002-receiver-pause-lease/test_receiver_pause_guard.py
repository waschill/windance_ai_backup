"""Real signals only against this test's owned disposable child processes."""
import json,os,select,signal,subprocess,sys,tempfile,time
from pathlib import Path
from receiver_pause_guard import inspect
results=[]
with tempfile.TemporaryDirectory() as tmp:
    for case in ('resume','controller_loss','expiry','wrong_identity','guard_terminated'):
        marker=Path(tmp)/case
        worker=subprocess.Popen([sys.executable,'-B','-c',
            'import pathlib,time,sys\np=pathlib.Path(sys.argv[1])\nwhile True:\n p.write_text(str(time.time()))\n time.sleep(.03)',str(marker)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        guard=None
        try:
            end=time.monotonic()+2
            while not marker.exists() and time.monotonic()<end:time.sleep(.02)
            assert marker.exists()
            identity=inspect(worker.pid)[0]
            guard=subprocess.Popen([sys.executable,'-B',str(Path(__file__).with_name('receiver_pause_guard.py'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True)
            guard.stdin.write((json.dumps({'pid':worker.pid,'identity':'0'*64 if case=='wrong_identity' else identity,'seconds':.7})+'\n').encode());guard.stdin.flush()
            assert select.select([guard.stdout],[],[],3)[0]
            first=json.loads(guard.stdout.readline())
            if case=='wrong_identity':
                assert first['status']=='held';guard.wait(timeout=3);assert guard.returncode==20
                assert 'T' not in inspect(worker.pid)[1]
            else:
                assert first['status']=='paused' and 'T' in inspect(worker.pid)[1]
                saved=marker.read_bytes();time.sleep(.08);assert marker.read_bytes()==saved
                if case=='resume':guard.stdin.write(b'resume\n');guard.stdin.flush()
                elif case=='controller_loss':guard.stdin.close()
                elif case=='guard_terminated':guard.terminate()
                guard.wait(timeout=4);assert guard.returncode==(1 if case=='guard_terminated' else 0)
                end=time.monotonic()+1
                while marker.read_bytes()==saved and time.monotonic()<end:time.sleep(.02)
                assert marker.read_bytes()!=saved and 'T' not in inspect(worker.pid)[1]
            results.append(case)
        finally:
            # Cleanup owns these exact Popen handles, never production PIDs.
            if guard is not None:
                if guard.stdin and not guard.stdin.closed:guard.stdin.close()
                guard.wait(timeout=4)
                guard.stdout.close()
            os.kill(worker.pid,signal.SIGCONT);worker.terminate();worker.wait(timeout=3)
print(json.dumps({'status':'passed','cases':results,'production_processes_signaled':0,'real_sends':0}))
