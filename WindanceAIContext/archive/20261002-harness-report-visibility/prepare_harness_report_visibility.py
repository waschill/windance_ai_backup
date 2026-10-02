import ast,hashlib
from pathlib import Path
root=Path(__file__).parent/'caller-contract-private'
p=root/'harness_report_identity_candidate.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='c90d0efb23f2ae89bb6d6287499348e797d55047c0e9c2becfa1481d9c50ee5f'
source=p.read_text(encoding='utf-8')
old='return {**task, "handoff_notes": [dict(row) for row in notes]}'
new='''with db() as conn:
        delivery=conn.execute('SELECT status FROM staff_task_deliveries WHERE task_id=?',(task['id'],)).fetchone()
    from task_report_status import status as report_status
    observation=report_status(TASK_REPORT_JOURNAL,str(task['id'])+':william',delivery['status'] if delivery else None)
    return {**task, "handoff_notes": [dict(row) for row in notes], "william_report_delivery": observation}'''
assert source.count(old)==1;source=source.replace(old,new)
needle='    notes = task.get("handoff_notes") or []'
replacement='''    delivery=task.get('william_report_delivery',{})
    labels={'verified':'Receipt verified','unconfirmed':'Unconfirmed; original request retained',
            'pending':'Pending','legacy_recorded':'Legacy delivery record; receipt not independently verified',
            'legacy_unreconciled':'Legacy attempt needs reconciliation','history_unavailable':'Delivery history unavailable',
            'not_recorded':'No delivery record'}
    lines.append('William report: '+labels.get(delivery.get('state'),'Delivery status unavailable'))
'''+needle
assert source.count(needle)==1;source=source.replace(needle,replacement)
ast.parse(source)
target=root/'harness_report_identity_r2.py'
with target.open('x',encoding='utf-8',newline='') as f:f.write(source)
print('candidate_sha256='+hashlib.sha256(target.read_bytes()).hexdigest())
