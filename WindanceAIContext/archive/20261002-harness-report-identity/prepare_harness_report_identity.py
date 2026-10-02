"""Build inert private Harness candidate from exact current source."""
import ast,hashlib
from pathlib import Path
root=Path(__file__).parent/'caller-contract-private'
source=root/'harness.py';text=source.read_text(encoding='utf-8')
assert hashlib.sha256(source.read_bytes()).hexdigest()=='0a95a09f0ad1932b53d38130579411ac8679c99265e4dc8741b8fd171dce2ab0'
wrapper=root/'windance_report_send.py'
assert hashlib.sha256(wrapper.read_bytes()).hexdigest()=='aacab51098b3cf89c4b8660e67f3958eff71b56e496ea91a526e629279515780'
recipients=[v.value for n in ast.walk(ast.parse(wrapper.read_text())) if isinstance(n,ast.Dict) for k,v in zip(n.keys,n.values) if isinstance(k,ast.Constant) and k.value=='to' and isinstance(v,ast.Constant)]
assert len(recipients)==1
node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='_deliver_staff_task_message')
lines=text.splitlines(keepends=True)
old=''.join(lines[node.lineno-1:node.end_lineno]).replace('def _deliver_staff_task_message(', 'def _deliver_staff_task_message_legacy(',1)
new='''
TASK_REPORT_JOURNAL=Path.home()/'.local/share/agent-harness/task-report-delivery.db'

def _deliver_staff_task_message(task: dict[str, Any], recipient: str, script: str) -> None:
    if recipient == 'shawn':
        return _deliver_staff_task_message_legacy(task,recipient,script)
    if recipient != 'william' or script != '/Users/herald/bin/windance_report_send.py':
        raise ValueError('unrecognized_report_route')
    from task_report_journal import run_task
    from receipt_report_transport import send_report
    task_id=str(task.get('id') or '')
    if not task_id or len(task_id)>400:raise ValueError('invalid_task_identity')
    def legacy_exists():
        with db() as conn:
            return conn.execute('SELECT 1 FROM staff_task_deliveries WHERE task_id=?',(task_id,)).fetchone() is not None
    def render():
        assignee=str(task.get('assignee') or 'Staff')
        title=str(task.get('title') or 'Staff task')
        outcome=str(task.get('status') or 'completed').upper()
        result=re.sub(r'(?m)^VERIFICATION_JSON:\\s*\\{[^\\n]+\\}\\s*','',str(task.get('result') or '')).strip()
        return f'{assignee} report — {title}\\n\\n{outcome}\\n{result}'
    result=run_task(TASK_REPORT_JOURNAL,task_id+':william',RECIPIENT_VALUE,render,legacy_exists,send_report)
    if result.get('status')!='verified':return
    with db() as conn:
        conn.execute('BEGIN IMMEDIATE')
        previous=conn.execute('SELECT status FROM staff_task_deliveries WHERE task_id=?',(task_id,)).fetchone()
        if previous and previous['status']=='delivered':return
        stamp=now()
        conn.execute("INSERT INTO staff_task_deliveries(task_id,transport,status,attempted_at,delivered_at,detail) VALUES(?,?,'delivered',?,?,?) ON CONFLICT(task_id) DO UPDATE SET status='delivered',delivered_at=excluded.delivered_at,detail=excluded.detail",
                     (task_id,'imessage-william',stamp,stamp,'independent local Messages receipt; original snapshot retained'))
        conn.commit()
    audit('staff_task_result_delivered',{'id':task_id,'transport':'imessage-william','evidence':'local_messages_flags'})

'''.replace('RECIPIENT_VALUE',repr(recipients[0]))
candidate=''.join(lines[:node.lineno-1])+old+'\n'+new+''.join(lines[node.end_lineno:])
ast.parse(candidate)
target=root/'harness_report_identity_candidate.py'
with target.open('x',encoding='utf-8',newline='') as f:f.write(candidate)
print('candidate_sha256='+hashlib.sha256(target.read_bytes()).hexdigest())
