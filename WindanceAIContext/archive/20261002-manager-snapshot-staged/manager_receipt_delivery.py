"""Manager-private immutable delivery snapshots in its existing state table."""
import copy,hashlib,json
RECEIPT={'ok':True,'transport':'imessage','chunks':1,'receipt':{'version':2,'ok':True,'status':'delivered','evidence':'local_messages_flags','chunks':1}}

def deliver(connect,recipient,text,key,transport):
    for value,limit in ((recipient,320),(text,20000),(key,500)):
        if type(value) is not str or not value.strip() or len(value)>limit:raise ValueError('invalid_delivery')
    wire_key='vega-manager:'+key
    state_key='receipt-v2:'+hashlib.sha256(wire_key.encode()).hexdigest()
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        row=c.execute('SELECT value FROM state WHERE key=?',(state_key,)).fetchone()
        if row is None:
            saved={'version':2,'wire_key':wire_key,'recipient':recipient.strip(),'body':text.strip(),'phase':'attempting'}
            encoded=json.dumps(saved,sort_keys=True)
            c.execute('INSERT INTO state(key,value) VALUES(?,?)',(state_key,encoded));c.commit()
            mode='submit'
        else:
            saved=json.loads(row[0])
            if (type(saved) is not dict or set(saved)!={'version','wire_key','recipient','body','phase'} or
                type(saved['version']) is not int or saved['version']!=2 or saved['wire_key']!=wire_key or
                saved['recipient']!=recipient.strip() or type(saved['body']) is not str or not saved['body'] or
                len(saved['body'])>20000 or saved['phase'] not in ('attempting','verified')):
                raise ValueError('delivery_snapshot_invalid')
            if saved['phase']=='verified':return copy.deepcopy(RECEIPT)
            mode='query'
            encoded=row[0]
    result=transport(saved['recipient'],saved['body'],wire_key,mode=mode)
    if result!=RECEIPT:raise RuntimeError('independent_delivery_unconfirmed')
    saved['phase']='verified'
    with connect() as c:
        c.execute('BEGIN IMMEDIATE')
        verified=json.dumps(saved,sort_keys=True)
        changed=c.execute('UPDATE state SET value=? WHERE key=? AND value=?',(verified,state_key,encoded)).rowcount
        if changed!=1:
            row=c.execute('SELECT value FROM state WHERE key=?',(state_key,)).fetchone()
            if row is None or row[0]!=verified:raise RuntimeError('delivery_snapshot_changed')
        c.commit()
    return copy.deepcopy(RECEIPT)
