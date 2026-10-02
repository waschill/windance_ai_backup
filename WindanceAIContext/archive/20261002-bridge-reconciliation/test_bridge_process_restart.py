"""Start actual candidate HTTP child twice with only fake read-only RPC transport."""
import json,os,socket,subprocess,tempfile,time,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parent
def available_port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
with tempfile.TemporaryDirectory(prefix='bridge-restart-fixture-') as directory:
 work=Path(directory);data=work/'data';data.mkdir();token=work/'token';token.write_text('synthetic-only')
 trace=work/'rpc.trace';threadfile=work/'thread.json'
 state={'version':1,'threads':{},'tasks':{'fixture':{'task_id':'fixture','manager_v2':True,'current_status':'running',
  'requested_by':'William','session':'fixture','original_request':'synthetic','acceptance_receipt':{'thread_id':'thread','turn_id':'turn'}}}}
 (data/'state.json').write_text(json.dumps(state))
 def run(expected):
  port=available_port();env=os.environ.copy();env.update(WINDANCE_CODEX_BRIDGE_PORT=str(port),WINDANCE_CODEX_DATA_DIR=str(data),
   WINDANCE_CODEX_BRIDGE_SECRET_FILE=str(token),WINDANCE_CODEX_APP_SERVER='fixture:no-network',FIXTURE_THREAD=str(threadfile),FIXTURE_RPC_TRACE=str(trace))
  child=subprocess.Popen(['/Users/herald/.local/bin/node','--import',str(root/'fixture_bridge_websocket.mjs'),str(root/'server-candidate.mjs')],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  try:
   deadline=time.monotonic()+8;found=None
   while time.monotonic()<deadline:
    assert child.poll() is None,'Test child exited'
    try:
     req=urllib.request.Request(f'http://127.0.0.1:{port}/v1/jobs/fixture',headers={'Authorization':'Bearer synthetic-only'})
     with urllib.request.urlopen(req,timeout=1) as response:found=json.load(response)
     if found['current_status']==expected and trace.exists() and 'thread/read' in trace.read_text():break
    except OSError:pass
    time.sleep(.03)
   assert found and found['current_status']==expected
   saved=json.loads((data/'state.json').read_text())['tasks']['fixture']
   assert saved['current_status']==expected
   return found
  finally:
   child.terminate()
   try:child.wait(timeout=3)
   except subprocess.TimeoutExpired:child.kill();child.wait(timeout=3)
   child.stderr.close()
 thread={'id':'thread','status':{'type':'active'},'turns':[{'id':'turn','status':'inProgress','items':[]}]}
 threadfile.write_text(json.dumps(thread));first=run('execution_uncertain')
 assert first['acceptance_receipt']==state['tasks']['fixture']['acceptance_receipt']
 thread['status']={'type':'notLoaded'};thread['turns'][0].update(status='completed',items=[{'type':'agentMessage','phase':'final_answer','text':'fixture final'}])
 threadfile.write_text(json.dumps(thread));trace.write_text('');second=run('completed')
 assert second['result_summary']=='fixture final' and second['verification_evidence']['source']=='thread/read'
 assert set(trace.read_text().splitlines())<={'initialize','initialized','thread/read'}
 print(json.dumps({'actual_candidate_process_starts':2,'restart_running_persisted_uncertain':True,'active_remote_remains_held':True,
  'exact_terminal_reconciled_after_restart':True,'authenticated_http_status_verified':True,'final_result_preserved':True,
  'rpc_methods':['initialize','initialized','thread/read'],'model_calls':0,'production_changes':False,'synthetic_rpc_only':True}))
