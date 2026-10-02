"""Read live caller source, exercise extracted main with synthetic endpoints only."""
import ast,contextlib,hashlib,io,json,pathlib,sys
p=pathlib.Path.home()/'services/agent-harness/gmail_sender_rule_sweep_notify.py'
raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='20c9295addda27835b6d6520556a2390b58146a6ed5d76dd8e60353b4aea566d'
t=ast.parse(raw);node=next(n for n in t.body if getattr(n,'name','')=='main')
code=compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'<actual-notifier-main>','exec')
def guard(event,args):
 if event in {'socket.connect','subprocess.Popen','os.system','os.fork','os.posix_spawn'}:raise RuntimeError('External effect denied')
sys.addaudithook(guard)
out=[]
for label,result,receipt in [('empty_result',{},{}),('failed_notice_receipt',{'notices':['Synthetic notice'],'errors':[]},{'ok':False,'delivered':False}),('uncertain_notice',{'notices':['Synthetic action outcome not confirmed'],'errors':[]},{'ok':False})]:
 calls=[]
 def fake(url,payload,timeout):
  calls.append({'url':url,'payload':payload,'timeout':timeout})
  return result if url=='fixture-sweep' else receipt
 env={'json':json,'post_json':fake,'HARNESS_SWEEP_URL':'fixture-sweep','NODE_RED_SEND_URL':'fixture-notice','PHONE':'fixture-recipient'}
 exec(code,env)
 with contextlib.redirect_stdout(io.StringIO()):status=env['main']()
 out.append({'case':label,'exit':status,'notice_calls':sum(c['url']=='fixture-notice' for c in calls),
             'sweep_timeout':calls[0]['timeout'],'unconfirmed_notice_has_auto_delete_heading':label=='uncertain_notice' and calls[-1]['payload']['message'].startswith('Gmail auto-delete notice:')})
assert all(x['exit']==0 for x in out)
print(json.dumps({'source_sha256':hashlib.sha256(raw).hexdigest(),'cases':out,'actual_main_synthetic_transport':True,'external_calls':0,'production_changes':False}))
