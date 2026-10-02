"""Actual candidate manager handlers in disposable SQLite, no external effects."""
import asyncio,importlib.util,json,os,tempfile,time
from pathlib import Path

async def main():
 with tempfile.TemporaryDirectory(prefix='manager-bounds-') as directory:
  os.environ['VEGA_MANAGER_DATA']=directory
  spec=importlib.util.spec_from_file_location('candidate',Path(__file__).with_name('manager-candidate.py'))
  m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.init()
  assert m.BASE==Path(directory)
  requests=[];replies={}
  async def fake_http(path,payload=None,*args,**kwargs):
   assert payload is None,'No resubmission or mutation allowed'
   requests.append(path);return replies[path.rsplit('/',1)[-1]]
  async def forbidden(*args,**kwargs):raise AssertionError('No send')
  m.http=fake_http;m.send=forbidden
  with m.connect() as c:
   for identifier in ('uncertain','interrupted','completed','failed'):
    c.execute('INSERT INTO messages(id,request,channel,session,status,answer,created,updated,notify,receipt,owner) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
      (identifier,'synthetic','fixture','fixture','submitted','',time.time(),time.time(),0,None,'William'))
    replies[identifier]={'current_status':'execution_uncertain' if identifier=='uncertain' else identifier,'result_summary':'synthetic result'}
  await m.process_messages()
  with m.connect() as c:
   rows={r['id']:dict(r) for r in c.execute('SELECT * FROM messages')}
  assert {key:r['status'] for key,r in rows.items()}=={'uncertain':'execution_uncertain','interrupted':'interrupted','completed':'answered','failed':'failed'}
  assert 'unconfirmed' in rows['uncertain']['answer'] and rows['uncertain']['receipt'] is None
  # notify=true on uncertainty must not enter the completed/failed delivery path.
  with m.connect() as c:c.execute('UPDATE messages SET notify=1 WHERE id=?',('uncertain',))
  requests.clear();m.init();await m.process_messages()
  assert requests==['/v1/jobs/uncertain']
  # Reconciliation accepts only a later bridge result, never a local retry.
  with m.connect() as c:c.execute('UPDATE messages SET notify=0 WHERE id=?',('uncertain',))
  replies['uncertain']={'current_status':'interrupted'}
  await m.process_messages()
  with m.connect() as c:
   assert c.execute('SELECT status FROM messages WHERE id=?',('uncertain',)).fetchone()[0]=='interrupted'
   assert c.execute('SELECT COUNT(*) FROM projects').fetchone()[0]==0
  print(json.dumps({'actual_function':'process_messages','disposable_sqlite':True,'status_mapping_passed':True,'uncertain_notify_withheld':True,'repeated_status_read_without_resubmit':True,'later_terminal_receipt_accepted':True,'production_changes':False,'sends':0,'model_calls':0}))
asyncio.run(main())
