import ast,contextlib,io,json
from pathlib import Path
tree=ast.parse(Path('sweep-caller-private/batch_candidate.private.py').read_text(encoding='utf-8'))
scope={'json':json,'HARNESS_SWEEP_URL':'fixture-sweep','NODE_RED_SEND_URL':'fixture-notice','PHONE':'fixture-owner'}
node=next(n for n in tree.body if getattr(n,'name','')=='main')
exec(compile(ast.Module(body=[node],type_ignores=[]),'<fixture>','exec'),scope)
coverage={'version':1,'rules_visited':8,'rules_total':181,'message_cap':20,'has_more':True,'cursor_advanced':True}
base={'rules':181,'checked':0,'deleted':0,'kept':0,'notices':[],'errors':[],'status':'partial','coverage':coverage}
cases=[(base,0,'sweep_partial'),(dict(base,coverage=None),1,'outcome_unconfirmed'),(dict(base,coverage=dict(coverage,rules_visited=9)),1,'outcome_unconfirmed'),(dict(base,status=None),1,'outcome_unconfirmed'),(dict(base,coverage=dict(coverage,cursor_advanced=1)),1,'outcome_unconfirmed')]
for receipt,expected,state in cases:
    calls=[]
    def transport(url,*args,**kw):calls.append(url);return receipt
    scope['post_json']=transport;out=io.StringIO()
    with contextlib.redirect_stdout(out):code=scope['main']()
    assert code==expected and json.loads(out.getvalue())['status']==state and calls==['fixture-sweep']
print(json.dumps({'status':'passed','partial_not_completed':True,'malformed_coverage_rejected':4,'real_sends':0}))
