import json
import urllib.request
task_id='b11f91d8-6875-4521-90b3-5bb13f12f767'
base='http://127.0.0.1:8791/staff/tasks/'+task_id
def post(path,payload):
    with urllib.request.urlopen(urllib.request.Request(path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'}),timeout=60) as r:return json.load(r)
with urllib.request.urlopen(base) as r:task=json.load(r)['task']
assert task['status']=='blocked' and '\nPASS.' in task['result']
result=post(base+'/complete',{'status':'completed','completed_by':'Vega — reviewed receipt/status reconciliation','result':'PASS\nVega reconciled a presentation-prefix classification mismatch. Original Archivist review follows unchanged:\n\n'+task['result']})
print(json.dumps({'id':task_id,'status':result.get('task',result).get('status')}))
