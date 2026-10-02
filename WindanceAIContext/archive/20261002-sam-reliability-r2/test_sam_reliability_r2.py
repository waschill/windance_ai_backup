"""Full composed commit path against real candidate schema and fake remotes."""
import ast,hashlib,io,json,sqlite3,sys,tempfile,urllib.request
from pathlib import Path
from types import SimpleNamespace
from typing import Any
root=Path('/home/williamschilling/backups/sam-reliability-r2-20261002')
manifest=json.loads((root/'manifest.json').read_text())
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in manifest.items())
sys.path.insert(0,str(root))
source=(root/'sam_schedule.candidate.private.py').read_text()
names={'connect','init_db','commit_day','post_completed_service_history','json_http'}
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in names];assert len(nodes)==5
results=[]
for mode in ['normal','memory_error','history_lost','clear_lost_new_need','clear_false','clear_receipt_failure_new_need']:
 with tempfile.TemporaryDirectory(prefix='sam-r2-') as directory:
  folder=Path(directory);creates=[];clears=[];posts=[];remote={'need':True}
  def history(*args):
   creates.append(1)
   if mode=='history_lost':raise TimeoutError('synthetic lost history acknowledgment')
   return {'status':'ok','record_id':123}
  def clear(model,record,values):
   clears.append(1)
   if mode=='clear_false':return {'status':'ok','result':False,'model':model,'record_id':record,'fields':list(values)}
   remote['need']=False
   if mode=='clear_lost_new_need':raise TimeoutError('synthetic lost clear acknowledgment')
   return {'status':'ok','result':True,'model':model,'record_id':record,'fields':list(values)}
  def http(request,timeout):
   posts.append(1)
   return io.BytesIO(json.dumps({'status':'error' if mode=='memory_error' and len(posts)==1 else 'ok'}).encode())
  ns={'Any':Any,'sqlite3':sqlite3,'DATA_DIR':folder,'DB_PATH':folder/'fixture.db','DEFAULT_TRAINERS':[],
      'now_iso':lambda:'fixture','json':json,'HERALD_BASE':'http://fixture.invalid',
      'urllib':SimpleNamespace(request=SimpleNamespace(Request=urllib.request.Request,urlopen=http)),
      'rollover_unfinished_training':lambda *a:{'enabled':False},'herald_odoo_horse_history':history,
      'herald_odoo_write':clear,'log_event':lambda *a,**k:None}
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'<r2-composed>','exec'),ns);ns['init_db']()
  with ns['connect']() as c:
   c.execute("INSERT INTO schedule_days(date,day_name) VALUES('2099-01-01','fixture')")
   if mode=='clear_receipt_failure_new_need':c.execute("CREATE TRIGGER receipt_failure BEFORE INSERT ON odoo_service_clear_posts BEGIN SELECT RAISE(ABORT,'fixture receipt failure'); END")
   c.commit()
  def schedule(date):
   with ns['connect']() as c:day=dict(c.execute('SELECT * FROM schedule_days').fetchone())
   return {'date':'2099-01-01','day_name':'fixture','day':day,'items':[{'id':'fixture-text-id','odoo_horse_id':1,'horse_name':'SYNTHETIC','farrier_text':'synthetic service','farrier_done':1}]}
  ns['get_schedule']=schedule;errors=[]
  for attempt in range(2):
   try:ns['commit_day']('2099-01-01');errors.append(False)
   except RuntimeError:errors.append(True)
   if attempt==0 and 'new_need' in mode:remote['need']=True
   if attempt==0 and mode=='clear_receipt_failure_new_need':
    with ns['connect']() as c:c.execute('DROP TRIGGER receipt_failure')
  ns['init_db']()
  with ns['connect']() as c:
   committed=bool(c.execute('SELECT committed FROM schedule_days').fetchone()[0])
   assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  assert len(creates)==1 and len(clears)<=1
  held=mode in ['history_lost','clear_lost_new_need','clear_false']
  assert committed!=held
  if held:assert errors==[True,True] and not posts
  if 'new_need' in mode:assert remote['need']
  if mode=='memory_error':assert len(posts)==2 and errors==[True,False]
  results.append({'scenario':mode,'simulated_history_creates':len(creates),'simulated_clears':len(clears),'memory_attempts':len(posts),'committed':committed,'new_need_preserved':remote['need'] if 'new_need' in mode else None})
print(json.dumps({'candidate_files_sha256':manifest,'cases':results,'production_changes':False,'actual_remote_calls':0,'limits':'Synthetic remotes; no proof of first-clear version safety, authoritative reconciliation, pre-cutover ambiguity or deployment readiness'}))
