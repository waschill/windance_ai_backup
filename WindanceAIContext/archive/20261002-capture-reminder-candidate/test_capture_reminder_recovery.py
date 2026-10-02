"""Candidate reminder and actual SAL enqueue with synthetic private directories only."""
from __future__ import annotations
import __future__,argparse,ast,contextlib,datetime,fcntl,hashlib,io,json,os,sqlite3,sys,tempfile,uuid
from pathlib import Path
from types import SimpleNamespace
candidate=Path(sys.argv[1]);raw=candidate.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='f354d1412c5abc30f1cab1eee9ece4ec71a1bbf7fc13baf11083840822cb5368'
source=Path.home()/'bin/send_imessage_payload.py';saved=source.read_bytes()
assert hashlib.sha256(saved).hexdigest()=='382b55125c3ed2d606ce6fc41be5deb4640cac884610bff8822a5f47c0e1f74f'
def functions(raw,names,env):
 tree=ast.parse(raw);nodes=[n for n in tree.body if getattr(n,'name','') in names]
 exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'<fixture>', 'exec',flags=__future__.annotations.compiler_flag),env)
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);db=root/'captures.db';c=sqlite3.connect(db);c.execute('CREATE TABLE captures(state TEXT)');c.execute("INSERT INTO captures VALUES('active')");c.commit();c.close()
 queue=root/'queue';results=root/'results';env={'Path':Path,'json':json,'os':os,'uuid':uuid,'hashlib':hashlib,'fcntl':fcntl,'ROOT':root,'QUEUE':queue,'RESULTS':results}
 functions(saved,{'enqueue'},env)
 calls=[]
 def intercepted(args,**kw):
  key=kw['env']['WINDANCE_DELIVERY_KEY'];calls.append(key)
  path,retained=env['enqueue']({'to':'synthetic','chunks':[kw['input']],'sms':False},key)
  if (root/'uncertain'/path.name).exists():raise TimeoutError('Synthetic unresolved receipt')
  return SimpleNamespace(stdout=json.dumps({'ok':True,'transport':'imessage','receipt':{'ok':True}}))
 h={'argparse':argparse,'sqlite3':sqlite3,'Path':Path,'DB':db,'json':json,'subprocess':SimpleNamespace(run=intercepted)}
 functions(raw,{'active_count','capture_delivery_key','main'},h)
 original_key=h['capture_delivery_key']
 assert original_key(datetime.datetime(2026,10,2,5,59,tzinfo=datetime.timezone.utc)).endswith('2026-10-01')
 assert original_key(datetime.datetime(2026,10,2,6,0,tzinfo=datetime.timezone.utc)).endswith('2026-10-02')
 h['capture_delivery_key']=lambda:original_key(datetime.datetime(2026,10,2,12,tzinfo=datetime.timezone.utc))
 oldargv=sys.argv;sys.argv=['fixture']
 try:
  def invoke():
   b=io.StringIO()
   with contextlib.redirect_stdout(b):status=h['main']()
   return status,b.getvalue()
  one=invoke();two=invoke();assert one[0]==two[0]==0 and calls[0]==calls[1] and len(list(queue.glob('*.json')))==1
  assert json.loads(one[1])['independent_delivery_verified'] is False
  c=sqlite3.connect(db);c.execute("INSERT INTO captures VALUES('active')");c.commit();c.close()
  try:invoke();raise AssertionError('Changed payload accepted')
  except ValueError as exc:assert str(exc)=='idempotency key reused with different content'
  assert len(list(queue.glob('*.json')))==1
  sys.argv=['fixture','--dry-run'];before=len(calls);assert invoke()[0]==0 and len(calls)==before
  c=sqlite3.connect(db);c.execute('DELETE FROM captures');c.commit();c.close();sys.argv=['fixture'];assert invoke()[0]==0 and len(calls)==before
  c=sqlite3.connect(db);c.execute("INSERT INTO captures VALUES('active')");c.commit();c.close()
  uncertain=root/'uncertain';uncertain.mkdir();q=next(queue.glob('*.json'));q.replace(uncertain/q.name)
  for _ in range(2):
   try:invoke();raise AssertionError('Uncertain receipt accepted')
   except TimeoutError:pass
  assert not list(queue.glob('*.json')) and len(list(uncertain.glob('*.json')))==1
 finally:sys.argv=oldargv
print(json.dumps({'same_day_same_key_one_queue_item':True,'changed_count_same_day_held':True,'uncertain_receipt_retry_no_requeue':True,'mountain_date_boundary_verified':True,'dry_run_and_empty_no_sender':True,'submission_not_delivery_claim':True,'real_sends':0,'production_changes':False,
 'limits':'Synthetic intercepted sender receipt and actual enqueue only; independent delivery, process crash and full sender chain not proved.'}))
