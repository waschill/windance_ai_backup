"""Bounded read-only Odoo reconciliation; no financial records leave this process."""
from __future__ import annotations
import ast
import datetime as dt
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from typing import Any

home=Path.home()
source=home/'services/agent-harness/agent_harness.py'
adapter_path=source.with_name('odoo_json2.py')
spec=importlib.util.spec_from_file_location('invoice_probe_adapter',adapter_path)
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
cfg=json.loads((home/'.config/agent-harness/odoo.json').read_text())
candidate=Path(sys.argv[1]).read_text()
domain=[['move_type','=','out_invoice'],['state','=','posted'],['payment_state','in',['not_paid','partial']],['amount_residual','>',0]]
fields=['id','name','partner_id','invoice_date','invoice_date_due','amount_total','amount_residual','currency_id','payment_state']
calls=[]
def read(method,args,kwargs):
    assert method in {'search_count','search_read'} and len(calls)<3
    started=time.monotonic()
    try:return adapter.call(cfg,'account.move',method,args,kwargs)
    finally:calls.append({'method':method,'elapsed_ms':round((time.monotonic()-started)*1000)})

out={'at':dt.datetime.now(dt.timezone.utc).isoformat(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
     'adapter_sha256':hashlib.sha256(adapter_path.read_bytes()).hexdigest(),
     'candidate_sha256':hashlib.sha256(candidate.encode()).hexdigest(),'production_changed':False,
     'invoice_identities_amounts_and_bodies_exported':False,'mutation_calls':0,'sends':0}
try:
    count=read('search_count',[domain],{})
    rows=read('search_read',[domain],{'fields':fields,'limit':1000,'order':'invoice_date_due asc, invoice_date asc, name asc'})
    assert isinstance(rows,list)
    frozen=json.loads(json.dumps(rows))
    def stub(model,method,args,kwargs):
        assert model=='account.move' and method=='search_read' and args==[domain]
        assert kwargs['limit']==1000
        return json.loads(json.dumps(frozen))
    namespace={'odoo_execute_kw':stub,'dt':dt,'Any':Any}
    function=next(n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='odoo_unpaid_customer_invoices')
    exec(compile(ast.Module(body=[function],type_ignores=[]),'<live-function-only>','exec'),namespace)
    old_text,old_kind,old_source=namespace['odoo_unpaid_customer_invoices'](limit=1000)
    exec(compile(candidate,'<staged-function-only>','exec'),namespace)
    text,kind,origin=namespace['odoo_unpaid_customer_invoices'](limit=1000)
    totals={};currency_names={}
    for row in rows:
        key=row['currency_id'][0];currency_names[key]=row['currency_id'][1]
        totals[key]=totals.get(key,Decimal('0'))+Decimal(str(row['amount_residual']))
    def money(value,key):
        value=Decimal(str(value));places=max(2,-value.as_tuple().exponent)
        return f'{currency_names[key]} {value:,.{places}f}'
    detail_lines=text.splitlines()[2:2+len(rows)]
    def due_text(row):
        if not row.get('invoice_date_due'): return 'no due date'
        day=dt.date.fromisoformat(row['invoice_date_due'])
        return f'{day.month}/{day.day}/{day.year}'
    details_ok=len(detail_lines)==len(rows) and all(any(
        'Invoice '+str(row['name'])+', Invoice Total: '+money(row['amount_total'],row['currency_id'][0])+', Remaining: '+money(row['amount_residual'],row['currency_id'][0])+', Due '+due_text(row) in line
        for line in detail_lines) for row in rows)
    totals_ok=all(money(value,key) in text.splitlines()[0] for key,value in totals.items())
    out.update({'matching_count':count,'examined_rows':len(rows),'count_matches_snapshot':count==len(rows),
      'snapshot_capped':len(rows)>=1000,'currency_count':len(totals),
      'partial_invoice_count':sum(r['payment_state']=='partial' for r in rows),
      'candidate_kind':kind,'candidate_source':origin,'candidate_row_totals_and_identifiers_match':details_ok,
      'candidate_currency_totals_match':totals_ok,'live_function_kind':old_kind,
      'live_function_source':old_source,'live_function_omits_invoice_identifiers':bool(rows) and all(str(r['name']) not in old_text for r in rows),
      'candidate_deterministic_on_frozen_snapshot':namespace['odoo_unpaid_customer_invoices'](limit=1000)==(text,kind,origin)})
    # Different projection and broader domain also detect positive residuals
    # excluded by the production payment-state filter. No connector guard changes.
    broader_domain=[['move_type','=','out_invoice'],['state','=','posted'],['amount_residual','>',0]]
    comparison=read('search_read',[broader_domain],{'fields':['id','currency_id','amount_residual','payment_state'],'limit':1001,'order':'id asc'})
    grouped={}
    for row in comparison:
        key=row['currency_id'][0]
        grouped[key]=grouped.get(key,Decimal('0'))+Decimal(str(row['amount_residual']))
    out['independent_projection_ids_match']=set(r['id'] for r in comparison)==set(r['id'] for r in rows)
    out['independent_projection_totals_match']=grouped==totals
    out['broader_positive_residual_count']=len(comparison)
    out['broader_projection_capped']=len(comparison)>=1001
    out['excluded_payment_state_counts']={state:sum(r['payment_state']==state for r in comparison) for state in set(r['payment_state'] for r in comparison) if state not in ('not_paid','partial')}
    out['result']='pass' if kind=='deterministic' and details_ok and totals_ok and out['independent_projection_ids_match'] and out['independent_projection_totals_match'] and count==len(rows) and not out['snapshot_capped'] and not out['broader_projection_capped'] else 'incomplete'
except Exception as exc:out.update({'result':'incomplete','error_type':type(exc).__name__})
out['read_calls']=calls
out['limits']='Bounded sequential reads, not a transactional snapshot or delivery test. No report body/amount/customer/invoice identity persisted.'
print(json.dumps(out))
