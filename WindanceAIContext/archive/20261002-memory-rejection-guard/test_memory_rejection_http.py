"""Actual candidate HTTP app, disposable data, intercepted outbound operations."""
import asyncio,importlib.util,json,os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
async def main():
 with tempfile.TemporaryDirectory(prefix='memory-rejection-http-') as directory:
  for key in ['DATA','CONFIG','LOG']:os.environ['AGENT_HARNESS_'+key+'_DIR']=directory
  os.environ['GOOGLE_WORKSPACE_CONFIG_DIR']=directory
  sys.path.insert(0,'/Users/herald/services/agent-harness')
  spec=importlib.util.spec_from_file_location('rejection_candidate',Path(__file__).with_name('harness-memory-guard-candidate.py'))
  h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;spec.loader.exec_module(h);h.startup()
  import httpx
  def forbidden(*args,**kwargs):raise AssertionError('Outbound operation forbidden')
  with patch.object(h.urllib.request,'urlopen',side_effect=forbidden),patch.object(h.subprocess,'run',side_effect=forbidden),patch.object(h,'model_reply',side_effect=forbidden),patch.object(h,'dispatch_staff_worker',side_effect=forbidden):
   async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app,client=('127.0.0.1',4567)),base_url='http://fixture') as client:
    for owner in ['William','Shawn']:
     response=await client.post('/message',json={'message':'remember this: password: SYNTHETIC_REJECTION_HTTP_MARKER','user':owner,'channel':'vega-internal','request_id':'fixture-'+owner})
     assert response.status_code==200,response.status_code
     assert response.json()['model']=='memory-guard'
     assert 'SYNTHETIC_REJECTION' not in response.text
  with h.db() as c:
   assert c.execute("SELECT count(*) FROM audit_log WHERE payload_json LIKE '%SYNTHETIC_REJECTION%'").fetchone()[0]==0
   assert c.execute("SELECT count(*) FROM audit_log WHERE event_type='memory_rejected_secret_like'").fetchone()[0]==2
   assert c.execute('SELECT count(*) FROM conversations').fetchone()[0]==0
  print(json.dumps({'actual_candidate_http_app':True,'owner_cases':2,'content_free_audit_verified':True,'no_conversation_rows':True,
   'outbound_operations_intercepted':True,'production_changes':False,'model_calls':0}))
asyncio.run(main())
