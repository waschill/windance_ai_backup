"""Atomic internal selection claim; caller must authenticate and validate refs first."""
import hashlib,json,uuid
from contextlib import closing
SCHEMA='''CREATE TABLE IF NOT EXISTS email_approval_selections (
 approval_id TEXT PRIMARY KEY,selection_sha256 TEXT NOT NULL,
 selected_indexes_json TEXT NOT NULL,rejected_indexes_json TEXT NOT NULL,
 remaining_indexes_json TEXT NOT NULL,child_approval_id TEXT,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);'''
class SelectionHeld(RuntimeError):pass
def claim(connect,approval,selected,rejected,is_fresh,now):
    payload=json.loads(approval['payload_json'])
    items=payload.get('actions')
    if approval['action']!='gmail.batch' or not isinstance(items,list) or not 1<=len(items)<=50:raise ValueError('Bounded Gmail batch required')
    if any(not isinstance(x,dict) or not isinstance(x.get('action'),str) or not x['action'].startswith('gmail.') or x['action']=='gmail.batch' for x in items):raise ValueError('Flat Gmail batch required')
    if not isinstance(selected,list) or not isinstance(rejected,list):raise ValueError('Index lists required')
    indexes=selected+rejected
    if not indexes or any(type(i) is not int or not 0<=i<len(items) for i in indexes) or len(set(indexes))!=len(indexes):raise ValueError('Distinct bounded indexes required')
    selected=sorted(selected);rejected=sorted(rejected);remaining=[i for i in range(len(items)) if i not in indexes]
    fingerprint=hashlib.sha256(json.dumps([approval['id'],approval['action'],approval['payload_json'],selected,rejected],separators=(',',':')).encode()).hexdigest()
    child_id=str(uuid.uuid4()) if remaining else None
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT action,payload_json,status,requested_at FROM approvals WHERE id=?',(approval['id'],)).fetchone()
        if row is None or tuple(row)!=(approval['action'],approval['payload_json'],'pending',approval['requested_at']):raise SelectionHeld('Approval changed or was already claimed; reconcile existing state')
        if not is_fresh(approval):raise SelectionHeld('Approval expired before selection claim')
        c.execute('INSERT INTO email_approval_selections(approval_id,selection_sha256,selected_indexes_json,rejected_indexes_json,remaining_indexes_json,child_approval_id) VALUES(?,?,?,?,?,?)',(approval['id'],fingerprint,json.dumps(selected),json.dumps(rejected),json.dumps(remaining),child_id))
        if remaining:
            child=dict(payload);child['actions']=[items[i] for i in remaining]
            # Old display text is not safely remappable by substring matching.
            child['summary']=[]
            c.execute("INSERT INTO approvals(id,action,payload_json,status,requested_at) VALUES(?,'gmail.batch',?,'pending',?)",(child_id,json.dumps(child),approval['requested_at']))
        changed=c.execute('UPDATE approvals SET status=?,decided_at=?,decision_note=? WHERE id=? AND status=\'pending\'',('executing' if selected else 'rejected',now(),'Numbered selection claimed; see durable selection record',approval['id'])).rowcount
        if changed!=1:raise SelectionHeld('Selection claim changed')
        c.commit()
    return {'approval_id':approval['id'],'selected_actions':[items[i] for i in selected],'selected_indexes':selected,'remaining_count':len(remaining),'refused_count':len(rejected),'child_approval_id':child_id,'selection_sha256':fingerprint}
