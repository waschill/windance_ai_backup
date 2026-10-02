"""Staged atomic provenance/receipt seam. No HTTP server or production credentials."""
import hashlib
import json
import owned_fact_store as store


def apply_fact_request(resolver, connection, authorization, *, event_id, owner,
                       channel, scope, kind, key, value, expected_revision=0, delete=False,
                       provenance=None, _joined_transaction=False):
    if not isinstance(event_id,str) or not event_id.strip() or len(event_id)>200:
        raise ValueError('Stable source event ID required')
    bound=resolver.bind(authorization,owner=owner,channel=channel,scope=scope,
                       operation='delete' if delete else 'write',source_ref=event_id)
    payload={'owner':bound.owner,'channel':bound.channel,'scope':bound.scope,
             'kind':kind,'key':key,'value':value,'expected_revision':expected_revision,'delete':delete}
    if provenance is not None:payload['provenance']=provenance
    fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    source_ref='owned-request:'+json.dumps([bound.issuer,event_id],separators=(',',':'))
    with store.transaction(connection,join_existing=_joined_transaction):
        previous=connection.execute('SELECT payload_sha256,receipt_json FROM owned_fact_requests WHERE issuer=? AND event_id=?',
                                    (bound.issuer,event_id)).fetchone()
        if previous:
            if previous[0]!=fingerprint:raise store.Conflict('Source event ID reused for different content')
            receipt=json.loads(previous[1])
            current=connection.execute('''SELECT revision FROM owned_facts WHERE owner=? AND scope=? AND kind=? AND fact_key=?''',
                                       (bound.owner,bound.scope,kind,key)).fetchone()
            return {**receipt,'replayed':True,'superseded':current is None or current[0]!=receipt['revision']}
        result=store.write(connection,bound.owner,bound.owner,bound.scope,kind,key,value,source_ref,
                           expected_revision,delete=delete,_joined_transaction=True)
        # Never retain raw fact values in a replay receipt; deletion must not
        # leave a duplicate value in this ledger or replay an obsolete answer.
        receipt={'owner':bound.owner,'scope':bound.scope,'kind':kind,'key':key,
                 'revision':result['revision'],'deleted':result['deleted'],'source_ref':source_ref}
        connection.execute('''INSERT INTO owned_fact_requests
          (issuer,event_id,owner,channel,scope,operation,payload_sha256,receipt_json)
          VALUES(?,?,?,?,?,?,?,?)''',(bound.issuer,event_id,bound.owner,bound.channel,bound.scope,bound.operation,
                                    fingerprint,json.dumps(receipt,sort_keys=True)))
    return {**receipt,'replayed':False,'superseded':False}
