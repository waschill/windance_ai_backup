"""Internal per-item execution record; no route, credentials or retry reset."""
import hashlib,json
from contextlib import closing
from email_approval_lineage import resolve
from email_mailbox_admission import SCHEMA as ADMISSION_SCHEMA,claim as claim_mailbox,release as release_mailbox
SCHEMA='''CREATE TABLE IF NOT EXISTS email_approved_item_intents (
 root_approval_id TEXT NOT NULL,root_item_index INTEGER NOT NULL,
 action_sha256 TEXT NOT NULL,state TEXT NOT NULL CHECK(state IN ('unconfirmed','confirmed')),
 receipt_json TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,confirmed_at TEXT,
 PRIMARY KEY(root_approval_id,root_item_index));'''
SCHEMA+=ADMISSION_SCHEMA
class ItemHeld(RuntimeError):pass
def perform(connect,approval_id,item_index,execute,validate_receipt):
    if type(item_index) is not int or not 0<=item_index<50:raise ValueError('Bounded item index required')
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT action,payload_json,status FROM approvals WHERE id=?',(approval_id,)).fetchone()
        if not row or not row[0].startswith('gmail.') or row[2]!='executing':raise ItemHeld('Current executing Gmail claim required')
        payload=json.loads(row[1])
        if not isinstance(payload,dict) or 'action' in payload:raise ItemHeld('Invalid approval payload')
        batch=row[0]=='gmail.batch'
        items=payload.get('actions') if batch else [{'action':row[0],**payload}]
        if not isinstance(items,list) or not 1<=len(items)<=50 or item_index>=len(items):raise ItemHeld('Invalid claimed batch')
        item=items[item_index]
        if not isinstance(item,dict) or not isinstance(item.get('action'),str) or not item['action'].startswith('gmail.') or item['action']=='gmail.batch':raise ItemHeld('Flat Gmail item required')
        selection=c.execute('SELECT selected_indexes_json,rejected_indexes_json,selection_sha256 FROM email_approval_selections WHERE approval_id=?',(approval_id,)).fetchone()
        if selection:
            selected,rejected=json.loads(selection[0]),json.loads(selection[1])
            fingerprint=hashlib.sha256(json.dumps([approval_id,row[0],row[1],selected,rejected],separators=(',',':')).encode()).hexdigest()
            if fingerprint!=selection[2] or item_index not in selected:raise ItemHeld('Item selection changed or was not authorized')
        # Reuse this transaction; application connectors may initialize schema.
        digest=hashlib.sha256(json.dumps(item,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        if batch:identity=resolve(connect,approval_id,item_index,connection=c)
        else:
            if selection:raise ItemHeld('Unexpected selection evidence on single action')
            identity={'root_approval_id':approval_id,'root_item_index':0,'action_sha256':digest}
        if digest!=identity['action_sha256']:raise ItemHeld('Claimed action changed')
        key=(identity['root_approval_id'],identity['root_item_index'])
        reservation='approved:'+hashlib.sha256(json.dumps(key,separators=(',',':')).encode()).hexdigest()
        prior=c.execute('SELECT action_sha256,state,receipt_json FROM email_approved_item_intents WHERE root_approval_id=? AND root_item_index=?',key).fetchone()
        if prior:
            if prior[0]!=digest or prior[1]!='confirmed':raise ItemHeld('Earlier item outcome needs reconciliation')
            return json.loads(prior[2])
        claim_mailbox(c,reservation)
        c.execute("INSERT INTO email_approved_item_intents(root_approval_id,root_item_index,action_sha256,state) VALUES(?,?,?,'unconfirmed')",(*key,digest));c.commit()
    try:
        result=execute(item)
        receipt=validate_receipt(item,result)
        if not isinstance(receipt,dict) or not receipt:raise ValueError('Validated minimal receipt required')
        encoded=json.dumps(receipt,sort_keys=True,separators=(',',':'),allow_nan=False)
        if len(encoded.encode())>16384:raise ValueError('Receipt exceeds bound')
        with closing(connect()) as c:
            c.execute('BEGIN IMMEDIATE')
            changed=c.execute("UPDATE email_approved_item_intents SET state='confirmed',receipt_json=?,confirmed_at=CURRENT_TIMESTAMP WHERE root_approval_id=? AND root_item_index=? AND action_sha256=? AND state='unconfirmed'",(encoded,*key,digest)).rowcount
            if changed!=1:raise ItemHeld('Item receipt changed')
            release_mailbox(c,reservation)
            c.commit()
        return receipt
    except Exception:
        raise ItemHeld('Approved item outcome unconfirmed; reconcile before another attempt') from None
