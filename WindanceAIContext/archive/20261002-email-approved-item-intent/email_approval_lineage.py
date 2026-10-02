"""Read-only provenance resolution for atomic batch remainder records."""
import hashlib,json
from contextlib import closing
class LineageHeld(RuntimeError):pass
def resolve(connect,approval_id,item_index):
    if not isinstance(approval_id,str) or not approval_id or type(item_index) is not int or item_index<0:raise ValueError('Approval item identity required')
    with closing(connect()) as c:
        c.execute('BEGIN')
        seen=set();current=approval_id;index=item_index
        for depth in range(51):
            if current in seen:raise LineageHeld('Approval lineage cycle')
            seen.add(current)
            row=c.execute('SELECT action,payload_json,requested_at FROM approvals WHERE id=?',(current,)).fetchone()
            if not row or row[0]!='gmail.batch':raise LineageHeld('Missing batch evidence')
            try:payload=json.loads(row[1]);items=payload['actions']
            except (ValueError,KeyError,TypeError):raise LineageHeld('Invalid batch evidence') from None
            if not isinstance(items,list) or not 1<=len(items)<=50 or index>=len(items):raise LineageHeld('Invalid batch item position')
            parents=c.execute('SELECT approval_id,selection_sha256,selected_indexes_json,rejected_indexes_json,remaining_indexes_json FROM email_approval_selections WHERE child_approval_id=? LIMIT 2',(current,)).fetchall()
            if not parents:
                return {'root_approval_id':current,'root_item_index':index,'action_sha256':hashlib.sha256(json.dumps(items[index],sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest(),'lineage_depth':depth}
            if len(parents)!=1:raise LineageHeld('Ambiguous approval lineage')
            parent=parents[0]
            original=c.execute('SELECT action,payload_json,requested_at FROM approvals WHERE id=?',(parent[0],)).fetchone()
            if not original or original[0]!='gmail.batch':raise LineageHeld('Missing original approval')
            try:
                original_payload=json.loads(original[1]);original_items=original_payload['actions']
                selected,rejected,remaining=[json.loads(v) for v in parent[2:5]]
            except (ValueError,KeyError,TypeError):raise LineageHeld('Invalid lineage evidence') from None
            if not isinstance(original_items,list) or not 1<=len(original_items)<=50 or any(not isinstance(v,list) for v in [selected,rejected,remaining]):raise LineageHeld('Invalid lineage partition')
            all_indexes=selected+rejected+remaining
            if any(type(i) is not int for i in all_indexes) or sorted(all_indexes)!=list(range(len(original_items))) or any(v!=sorted(v) for v in [selected,rejected,remaining]):raise LineageHeld('Invalid lineage partition')
            digest=hashlib.sha256(json.dumps([parent[0],original[0],original[1],selected,rejected],separators=(',',':')).encode()).hexdigest()
            if digest!=parent[1] or items!=[original_items[i] for i in remaining] or row[2]!=original[2] or payload.get('_expires_at')!=original_payload.get('_expires_at'):raise LineageHeld('Approval lineage changed')
            current=parent[0];index=remaining[index]
        raise LineageHeld('Approval lineage exceeds bound')
