"""Real subprocess termination with actual durable intent and fixture effects."""
import json,os,sqlite3,sys,tempfile,time
from contextlib import closing
from pathlib import Path
from email_process_deadline import run,WorkerUnconfirmed
stage=Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);worker=root/'worker.py';db=root/'fixture.db';pidfile=root/'pid';effect=root/'effect'
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
  Path(p['effect']).write_text('one synthetic effect')
  if p['mode']=='hang':time.sleep(5)
  return {'trashed':True,'id':'fixture'}
 return perform(connect,'william','fixture','trash',{},effect)
''')
    payload={'stage':str(stage),'db':str(db),'pid':str(pidfile),'effect':str(effect),'mode':'hang'}
    start=time.monotonic()
    try:run(worker,payload,timeout=.5);raise AssertionError('Deadline failed')
    except WorkerUnconfirmed:pass
    elapsed=time.monotonic()-start;assert elapsed<1.5 and effect.exists()
    pid=int(pidfile.read_text())
    try:os.kill(pid,0);raise AssertionError('Worker still alive')
    except ProcessLookupError:pass
    with closing(sqlite3.connect(db)) as c:assert c.execute('SELECT state FROM email_action_intents').fetchall()==[('unconfirmed',)]
    before=effect.stat().st_mtime_ns;payload['mode']='success'
    try:run(worker,payload,timeout=2);raise AssertionError('Unknown operation replayed')
    except WorkerUnconfirmed:pass
    assert effect.stat().st_mtime_ns==before
    # Oversized output fails closed and a spawned child is prohibited.
    for name,source in [('output',"def run(p):\n print('x'*20000)\n return {}\n"),
        ('dispatch',"import subprocess\ndef run(p):\n subprocess.run(['true'])\n return {}\n")]:
        worker.write_text(source)
        try:run(worker,{},timeout=2,output_limit=1024);raise AssertionError(name+' accepted')
        except WorkerUnconfirmed:pass
    # Output cap must not impose a process-wide file limit on the durable database.
    worker.write_text("from pathlib import Path\ndef run(p):\n Path(p['path']).write_bytes(b'x'*4096)\n return {'ok':True}\n")
    assert run(worker,{'path':str(root/'large-private-fixture')},timeout=2,output_limit=1024)=={'ok':True}
print(json.dumps({'timeout_seconds':round(elapsed,3),'exact_child_absent':True,'durable_intent':'unconfirmed',
    'retry_no_second_fixture_effect':True,'oversize_output_held':True,'python_child_dispatch_denied':True,
    'normal_receipt_pass':True,'real_mailbox_calls':0,'limits':'Trusted fixture worker only; no full Harness integration, native-code sandbox, host-failure recovery or real identity proof.'}))
