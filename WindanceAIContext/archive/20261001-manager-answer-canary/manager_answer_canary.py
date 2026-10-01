"""One synthetic no-notification request; poll same ID, never resubmit uncertain work."""
import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import urllib.request

MID='STACK-RECOVERY-CANARY-20261001T2313Z'
BASE='http://127.0.0.1:8797'
ROOT=Path('/Users/herald/backups/manager-recovery-20261001T2305Z')
DB=Path('/Users/herald/.local/share/vega-manager/manager.db')
def request(path,payload=None):
 data=None if payload is None else json.dumps(payload).encode()
 req=urllib.request.Request(BASE+path,data=data,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=10) as r:return json.load(r)
def counts():
 c=sqlite3.connect('file:'+str(DB)+'?mode=ro',uri=True)
 try:return {t:c.execute('select count(*) from '+t).fetchone()[0] for t in ['projects','stages']}
 finally:c.close()
before=counts()
with urllib.request.urlopen('http://127.0.0.1:8793/health',timeout=5) as r:health=json.load(r)
assert health['active']==0 and health['queued']==0
payload={'id':MID,'owner':'William','channel':'recovery-canary','session':'stack-recovery-synthetic-20261001','notify':False,
 'message':'Synthetic service recovery check. Reply with exactly WINDANCE_RECOVERY_OK_20261001. Do not use tools, access files, create projects, assign staff, send notifications or perform any other action. This is not a business request.'}
try:
 prior=request('/messages/'+MID)
 assert prior['request']==payload['message'] and prior['notify']==0
except urllib.error.HTTPError as e:
 if e.code!=404:raise
 prior=request('/messages',payload)
 assert prior['id']==MID and prior['notify']==0
print(json.dumps({'accepted_id':MID,'notify':False,'status':prior['status']}),flush=True)
start=time.monotonic();row=prior
while row['status'] in ['queued','submitted'] and time.monotonic()-start<120:
 time.sleep(3);row=request('/messages/'+MID)
timed_out=row['status'] in ['queued','submitted']
if timed_out:
 request('/messages/'+MID+'/interrupt',{})
 for _ in range(10):
  time.sleep(2);row=request('/messages/'+MID)
  if row['status'] not in ['queued','submitted']:break
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'request_id':MID,'status':row['status'],'notify':row['notify'],'receipt_absent':row['receipt'] is None,'exact_reply':row.get('answer','').strip()=='WINDANCE_RECOVERY_OK_20261001','answer_sha256':hashlib.sha256((row.get('answer') or '').encode()).hexdigest(),'elapsed_seconds':round(row['updated']-row['created'],2),'project_stage_counts_unchanged':counts()==before,'timeout_interrupt_requested':timed_out,'no_retry_submissions':True,'production_model_route_unchanged':True,'model_call_attempts':1}
(ROOT/'answer-canary-receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
