import pathlib,sqlite3,json,hashlib,time
R=pathlib.Path(r'C:\Users\wasch\Documents\WindanceBaselineRecovery\20260930T0600Z')
def db(p):
 c=sqlite3.connect('file:'+p.as_posix()+'?mode=ro&immutable=1',uri=True);c.row_factory=sqlite3.Row;return c
m=db(R/'HERALD/isolation-restore/data/manager.db');h=db(R/'HERALD/isolation-restore/data/harness.db')
out={'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'method':'read-only SQL against cold restored copies; no application imports, HTTP, launchd, dispatch or sends','projects':[]}
for p in m.execute("select * from projects where status='delivered'"):
 stages=list(m.execute('select * from stages where project=?',(p['id'],)));checks=[]
 for s in stages:
  task=h.execute('select result from staff_tasks where id=?',(s['task_id'],)).fetchone();e=json.loads(s['evidence'] or '{}')
  checks.append({'stage':s['key'],'verified':s['status']=='verified','task_present':task is not None,'result_hash_matches':task is not None and hashlib.sha256((task['result'] or '').encode()).hexdigest()==e.get('result_sha256')})
 qa=h.execute('select result,status from staff_tasks where id=?',(p['qa_task'],)).fetchone()
 out['projects'].append({'id':p['id'],'report_hash_matches':hashlib.sha256(p['report'].encode()).hexdigest()==p['report_hash'],'qa_approves_exact_report':qa is not None and qa['status']=='completed' and ('APPROVED_SHA256: '+p['report_hash']) in qa['result'],'successful_receipt':json.loads(p['delivery']).get('ok') is True,'stages':checks})
s=db(R/'SAM/isolation-restore/data/sam_schedule.db')
out['sam']={'integrity':s.execute('pragma integrity_check').fetchone()[0],'historical_detail_rows':s.execute('select count(*) from training_completion_details').fetchone()[0],'detail_rows_after_suspension':s.execute("select count(*) from training_completion_details where completed_at >= '2026-09-21'").fetchone()[0],'history_receipts':s.execute('select count(*) from odoo_history_posts').fetchone()[0]}
n=json.loads((R/'SAL/isolation-restore/files/Users/zuzu/.node-red/flows.json').read_text());ids={x['id'] for x in n}
out['nodered']={'nodes':len(n),'dangling_wire_targets':sum(1 for x in n for group in x.get('wires',[]) for target in group if target not in ids),'legacy_imessage_inject_disabled':next(x for x in n if x['id']=='2a94bc23a3894b2d').get('d') is True,'loaded_into_nodered':False}
for c in [m,h,s]:c.close()
print(json.dumps(out,indent=2))
