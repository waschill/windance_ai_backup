"""Real child process exits and shared SQLite claims with synthetic effects only."""
import json,os,sqlite3,subprocess,sys,tempfile,time
from contextlib import closing
from pathlib import Path
from email_action_intent import install,perform,OutcomeHeld
if len(sys.argv)>1:
 root=Path(sys.argv[1]);mode=sys.argv[2]
 def connect():return sqlite3.connect(root/'fixture.db',timeout=5)
 def callback():
  if mode=='before':os._exit(70)
  with (root/'synthetic-effects.txt').open('a') as f:f.write('draft\n');f.flush();os.fsync(f.fileno())
  if mode=='after':os._exit(71)
  if mode=='wait':
   (root/'ready').write_text('ready')
   deadline=time.monotonic()+10
   while not (root/'release').exists():
    if time.monotonic()>deadline:raise TimeoutError('fixture release deadline')
    time.sleep(.02)
  return {'draft_created':True,'id':'fixture-draft'}
 try:
  result=perform(connect,'william','fixture-message','draft',{'intent':'synthetic'},callback)
  if mode=='confirmed':os._exit(72)
  print(json.dumps({'confirmed':result['id']=='fixture-draft'}))
 except OutcomeHeld:print(json.dumps({'held':True}))
 sys.exit(0)
results=[]
with tempfile.TemporaryDirectory(prefix='email-intent-crash-') as folder:
 for mode in ['before','after','confirmed','wait']:
  root=Path(folder)/mode;root.mkdir()
  with closing(sqlite3.connect(root/'fixture.db')) as c:install(c)
  args=[sys.executable,__file__,str(root)]
  if mode=='wait':
   child=subprocess.Popen(args+[mode],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   deadline=time.monotonic()+10
   while not (root/'ready').exists():
    assert child.poll() is None and time.monotonic()<deadline
    time.sleep(.02)
   second=subprocess.run(args+['retry'],capture_output=True,text=True,check=True);assert json.loads(second.stdout)=={'held':True}
   (root/'release').write_text('release');out,err=child.communicate(timeout=10);assert child.returncode==0 and json.loads(out)=={'confirmed':True}
  else:
   first=subprocess.run(args+[mode],capture_output=True,text=True);assert first.returncode=={'before':70,'after':71,'confirmed':72}[mode]
  retry=subprocess.run(args+['retry'],capture_output=True,text=True,check=True)
  expected={'held':True} if mode in ['before','after'] else {'confirmed':True};assert json.loads(retry.stdout)==expected
  effects=(root/'synthetic-effects.txt').read_text().splitlines() if (root/'synthetic-effects.txt').exists() else []
  assert len(effects)==(0 if mode=='before' else 1)
  with closing(sqlite3.connect(root/'fixture.db')) as c:assert c.execute('PRAGMA integrity_check').fetchone()==('ok',)
  results.append({'case':mode,'synthetic_effects':len(effects),'restart':expected})
print(json.dumps({'cases':results,'real_process_exits':3,'competing_process_test':True,'actual_mailbox_calls':0,'production_changes':False}))
