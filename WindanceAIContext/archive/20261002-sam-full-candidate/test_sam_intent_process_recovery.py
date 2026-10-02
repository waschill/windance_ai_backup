"""Real disposable child exits/concurrency; remote effect is an fsynced fixture line."""
import json,os,sqlite3,subprocess,sys,tempfile,time
from pathlib import Path
import sam_history_intent as journal


def invoke(directory,mode):
    directory=Path(directory);database=directory/'intent.db'
    class Connection(sqlite3.Connection):
        def commit(self):
            super().commit()
            if mode=='after_confirmation' and self.execute("SELECT count(*) FROM sam_history_intents WHERE state='confirmed'").fetchone()[0]:
                os._exit(72)
    def connect():return sqlite3.connect(database,factory=Connection,timeout=5)
    def effect():
        if mode=='before_send':os._exit(70)
        if mode=='concurrent_first':
            (directory/'ready').write_text('ready')
            deadline=time.monotonic()+8
            while not (directory/'release').exists():
                if time.monotonic()>deadline:raise TimeoutError('fixture release missing')
                time.sleep(.02)
        with (directory/'effects').open('a') as f:
            f.write('synthetic-create\n');f.flush();os.fsync(f.fileno())
        if mode=='after_send':os._exit(71)
        return {'status':'ok','record_id':123}
    try:
        result=journal.perform(connect,'2099-01-01',1,1,'Farrier','synthetic service',effect)
        assert result=={'status':'ok','record_id':123}
        print('confirmed')
    except journal.Unconfirmed:print('held')


def command(directory,mode):return [sys.executable,__file__,'--child',str(directory),mode]
def run(directory,mode,expected=0):
    result=subprocess.run(command(directory,mode),capture_output=True,text=True,timeout=15)
    assert result.returncode==expected,(mode,result.returncode)
    return result.stdout.strip()
def count(directory):
    path=Path(directory)/'effects'
    return len(path.read_text().splitlines()) if path.exists() else 0
def initialize(directory):
    with sqlite3.connect(Path(directory)/'intent.db') as c:journal.install(c)


def main():
    outcomes=[]
    for mode,exit_code in [('before_send',70),('after_send',71),('after_confirmation',72)]:
        with tempfile.TemporaryDirectory(prefix='sam-intent-process-') as path:
            root=Path(path);initialize(root)
            run(root,mode,exit_code)
            expected='confirmed' if mode=='after_confirmation' else 'held'
            assert run(root,'retry')==expected
            assert count(root)==(0 if mode=='before_send' else 1)
            restored=root/'restored';restored.mkdir()
            with sqlite3.connect(root/'intent.db') as origin,sqlite3.connect(restored/'intent.db') as target:origin.backup(target)
            with sqlite3.connect(restored/'intent.db') as c:assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            assert run(restored,'retry')==expected and count(restored)==0
            outcomes.append({'exit_boundary':mode,'state_after_restart':expected,'synthetic_creates':count(root),'cold_copy_no_new_effect':True})
    with tempfile.TemporaryDirectory(prefix='sam-intent-concurrency-') as path:
        root=Path(path);initialize(root)
        first=subprocess.Popen(command(root,'concurrent_first'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            deadline=time.monotonic()+8
            while not (root/'ready').exists():
                assert first.poll() is None
                if time.monotonic()>deadline:raise TimeoutError('fixture first attempt not ready')
                time.sleep(.02)
            assert run(root,'concurrent_second')=='held'
            (root/'release').write_text('release')
            stdout,stderr=first.communicate(timeout=10)
            assert first.returncode==0 and stdout.strip()=='confirmed' and count(root)==1
        finally:
            if first.poll() is None:first.kill();first.wait(timeout=5)
    print(json.dumps({'cases':outcomes,'competing_process_held_without_second_create':True,
                      'production_changes':False,'actual_odoo_calls':0,'model_calls':0,
                      'limits':'Fixture effect only; current consistent snapshot; no older-backup reconciliation or full SAM lifecycle'}))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--child':invoke(sys.argv[2],sys.argv[3])
    else:main()
