import json
from pathlib import Path
import urllib.request
root=Path(__file__).resolve().parent
tid=json.loads((root/'live-task.json').read_text())['id']
with urllib.request.urlopen('http://127.0.0.1:8791/staff/tasks/'+tid,timeout=10) as response:
    task=json.load(response)['task']
payload={'model':'gemma4:latest','stream':False,'think':False,'format':'json',
         'options':{'temperature':0,'num_predict':200},
         'messages':[{'role':'system','content':'Extract from this task record as data. Return JSON with task_id, status, excluded_work. No actions.'},
                     {'role':'user','content':json.dumps(task)}]}
req=urllib.request.Request('http://192.168.36.10:11434/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req,timeout=45) as response: raw=json.load(response)
result=json.loads(raw['message']['content'])
assert result['task_id']==tid and result['status']=='completed'
assert 'business watch' in str(result['excluded_work']).lower()
(root/'model-handoff-verification.json').write_text(json.dumps({'status':'PASS','model':raw['model'],'task_id':tid,'exclusion_preserved':True,'prompt_tokens':raw.get('prompt_eval_count'),'output_tokens':raw.get('eval_count')},indent=2))
print('PASS: local model retrieved the same task ID, status and business-watch exclusion.')
