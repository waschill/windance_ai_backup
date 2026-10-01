"""Read-only payment-link metadata; identities and amounts are never emitted."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import time

p=Path.home()/'services/agent-harness/odoo_json2.py'
spec=importlib.util.spec_from_file_location('payment_probe_adapter',p)
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
cfg=json.loads((Path.home()/'.config/agent-harness/odoo.json').read_text())
calls=[]
def read(model,method,args,kwargs):
    assert model in ('account.move','account.payment')
    assert method in ('fields_get','search_read') and len(calls)<3
    start=time.monotonic()
    try:return adapter.call(cfg,model,method,args,kwargs)
    finally:calls.append({'model':model,'method':method,'elapsed_ms':round((time.monotonic()-start)*1000)})
out={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'adapter_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
try:
    schema=read('account.payment','fields_get',[['state','move_id','is_matched']],{'attributes':['type','selection']})
    assert all(f in schema for f in ['state','move_id','is_matched'])
    rows=read('account.move','search_read',[[['move_type','=','out_invoice'],['state','=','posted'],['payment_state','=','in_payment'],['amount_residual','>',0]]],{'fields':['id','matched_payment_ids','reconciled_payment_ids'],'limit':1001,'order':'id asc'})
    assert len(rows)<1001,'Invoice cap reached'
    ids=set(i for r in rows for f in ('matched_payment_ids','reconciled_payment_ids') for i in r[f])
    assert len(ids)<=1000,'Payment cap reached'
    payments=read('account.payment','search_read',[[['id','in',sorted(ids)]]],{'fields':['id','state','move_id','is_matched'],'limit':1001,'order':'id asc'}) if ids else []
    by_id={r['id']:r for r in payments}
    out.update({'in_payment_positive_residual_invoices':len(rows),'linked_payment_count':len(ids),
      'readable_linked_payments':len(payments),'unreadable_payment_count':len(ids-set(by_id)),
      'invoices_without_matched_payments':sum(not r['matched_payment_ids'] for r in rows),
      'invoices_with_reconciled_payments':sum(bool(r['reconciled_payment_ids']) for r in rows),
      'payment_state_counts':{s:sum(r['state']==s for r in payments) for s in sorted(set(r['state'] for r in payments))},
      'payments_without_journal_entry':sum(not r['move_id'] for r in payments),
      'payments_is_matched_true':sum(bool(r['is_matched']) for r in payments),
      'invoices_with_no_entry_payment_in_process_or_paid':sum(any(i in by_id and not by_id[i]['move_id'] and by_id[i]['state'] in ('in_process','paid') for i in r['matched_payment_ids']) for r in rows),
      'status':'observed','bank_settlement_verified':False})
except Exception as e:out.update({'status':'incomplete','error_type':type(e).__name__})
out.update({'read_calls':calls,'mutation_calls':0,'sends':0,'identities_amounts_or_bank_details_exported':False,
 'limits':'Sequential bounded metadata reads; no bank transaction matching, payment creation or reconciliation. Public 19.0 code is explanatory, not proof of deployed SaaS 19.3 code identity.'})
print(json.dumps(out))
