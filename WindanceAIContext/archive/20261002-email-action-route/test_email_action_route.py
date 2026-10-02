"""Actual API payload creation -> durable approval -> item journal, synthetic effects."""
import ast, datetime as dt, hashlib, json, os, sqlite3, sys, tempfile, uuid
from pathlib import Path
from typing import Any
from pydantic import BaseModel
from fastapi import Header, HTTPException

root=Path(sys.argv[1]); sys.path.insert(0,str(root))
manifest=json.loads((root/'manifest.json').read_text())
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
names={'db','ClosingConnection','seed_memories','GmailActionIn','request_gmail_action',
       'request_approval','approve_pending','find_pending_approval','execute_approved_action',
       'audit','redacted_payload'}
nodes=[n for n in ast.parse((root/'agent_harness.candidate.private.py').read_text()).body if getattr(n,'name','') in names]
assert len(nodes)==len(names)
for n in nodes:
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)): n.decorator_list=[]
results=[]
for mode in ('normal','lost_response'):
    with tempfile.TemporaryDirectory() as folder:
        effects=[]
        def trash(mid):
            effects.append(mid)
            if mode=='lost_response': raise TimeoutError('PRIVATE_PROVIDER_SENTINEL')
            return {'trashed':True,'id':mid}
        ns=dict(Any=Any,BaseModel=BaseModel,Header=Header,HTTPException=HTTPException,
                sqlite3=sqlite3,os=os,DB_FILE=Path(folder)/'fixture.db',ensure_dirs=lambda:None,
                dt=dt,uuid=uuid,json=json,now=lambda:dt.datetime.now(dt.UTC).isoformat(),
                require_token=lambda _:None,require_william_mailbox=lambda:None,
                require_payload=lambda p,k:p[k],gmail_delete_message=trash,
                approval_is_fresh=lambda _:True,GMAIL_APPROVAL_EXPIRE_MINUTES=10)
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-route-chain>','exec'),ns)
        request=ns['GmailActionIn'](action='trash',message_id='synthetic-message')
        created=ns['request_gmail_action'](request,authorization='synthetic-auth')
        assert created['status']=='pending' and effects==[]
        replies=[ns['approve_pending'](created['id']),ns['approve_pending'](created['id'])]
        assert effects==['synthetic-message'],f'Expected one effect, got {len(effects)}'
        assert 'PRIVATE_PROVIDER_SENTINEL' not in repr(replies)
        with ns['db']() as c:
            state=c.execute('SELECT status FROM approvals').fetchone()[0]
            item=c.execute('SELECT state FROM email_approved_item_intents').fetchone()[0]
        assert state==('executed' if mode=='normal' else 'uncertain')
        assert item==('confirmed' if mode=='normal' else 'unconfirmed')
        results.append({'case':mode,'approval':state,'item':item,'synthetic_effects':len(effects)})
print(json.dumps({'candidate_sha256':manifest['agent_harness.candidate.private.py'],'cases':results,
                  'limits':'Direct route function, not HTTP transport. Authentication/freshness intercepted; mailbox primitive synthetic.'}))
