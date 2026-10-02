"""Crash the real supervisor after durable fixture effect; verify orphan termination."""
import json,os,signal,sqlite3,subprocess,sys,tempfile,time
from contextlib import closing
from pathlib import Path
stage=Path(sys.argv[1]).resolve();supervisor=Path(__file__).with_name('email_process_deadline.py')
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);worker=root/'worker.py';pidfile=root/'worker.pid';db=root/'fixture.db';effect=root/'effect'
    worker.write_text('''import os,sys,time,sqlite3
from pathlib import Path
from contextlib import closing
def run(p):
 sys.path.insert(0,p['stage'])
 from email_action_intent import install,perform
 Path(p['pid']).write_text(str(os.getpid()))
 def connect():return sqlite3.connect(p['db'])
 with closing(connect()) as c:install(c)
 def effect():
  Path(p['effect']).write_text('one effect')
  time.sleep(8)
  Path(p['late']).write_text('must not happen')
  return {'trashed':True,'id':'fixture'}
 return perform(connect,'william','fixture','trash',{},effect)
''')
    outer=root/'supervisor.py'
    outer.write_text('''import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from email_process_deadline import run
run(sys.argv[2],json.loads(sys.argv[3]),timeout=2)
''')
    late=root/'late';payload={'stage':str(stage),'db':str(db),'pid':str(pidfile),'effect':str(effect),'late':str(late)}
    process=subprocess.Popen([sys.executable,'-I',str(outer),str(supervisor.parent),str(worker),json.dumps(payload)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    child=None
    try:
        end=time.monotonic()+3
        while not effect.exists() and time.monotonic()<end:time.sleep(.01)
        assert effect.exists() and process.poll() is None
        child=int(pidfile.read_text());process.kill();process.wait(timeout=2);start=time.monotonic()
        state=''
        while time.monotonic()-start<3:
            observation=subprocess.run(['/bin/ps','-p',str(child),'-o','state='],capture_output=True,text=True,timeout=1)
            state=observation.stdout.strip()
            if not state or state.startswith('Z'):break
            time.sleep(.02)
        assert not state or state.startswith('Z'),state
        assert not late.exists()
        with closing(sqlite3.connect(db)) as c:assert c.execute('SELECT state FROM email_action_intents').fetchall()==[('unconfirmed',)]
        print(json.dumps({'supervisor_killed':True,'child_terminal_state':'absent' if not state else 'zombie-not-executing',
            'termination_observed_seconds':round(time.monotonic()-start,3),'late_effect_absent':True,'intent':'unconfirmed',
            'real_mailbox_calls':0,'limits':'Trusted Python worker on HERALD; no full Harness/identity/host power-loss acceptance.'}))
    finally:
        if process.poll() is None:process.kill();process.wait()
        if child:
            try:os.kill(child,signal.SIGKILL)
            except ProcessLookupError:pass
