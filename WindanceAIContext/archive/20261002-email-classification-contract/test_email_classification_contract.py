"""Run real classifier and parser with synthetic model responses, no mailbox."""
import ast,hashlib,json,re
from pathlib import Path
from typing import Any
def row(i,decision='escalate'):return {'index':i,'decision':decision,'category':'fixture','reason':'synthetic decision','draft_intent':'synthetic reply'}
base=Path('/Users/herald/services/agent-harness/agent_harness.py')
candidate=Path('/Users/herald/backups/email-classification-candidate-20261002/agent_harness.candidate.private.py')
cases={
 'valid':[[row(i) for i in range(1,9)],[row(9,'draft')]],
 'cross_batch':[[row(i) for i in range(1,9)],[row(1,'automatic')]],
 'duplicate':[[row(i) for i in range(1,9)]+[row(1,'automatic')],[row(9)]],
 'missing':[[row(i) for i in range(1,8)],[row(9)]],
 'boolean_index':[[row(True)]+[row(i) for i in range(2,9)],[row(9)]],
 'string_index':[[row('1')]+[row(i) for i in range(2,9)],[row(9)]],
 'false_reason':[[dict(row(1),reason=None)]+[row(i) for i in range(2,9)],[row(9)]],
 'unknown_decision':[[row(1,'send')]+[row(i) for i in range(2,9)],[row(9)]],
 'truncated':['[broken',[row(9)]]}
results=[]
for version,path in [('baseline',base),('candidate',candidate)]:
 s=path.read_text();nodes=[n for n in ast.parse(s).body if getattr(n,'name','') in ['classify_email_autonomy','parse_email_autonomy_decisions']]
 for case,responses in cases.items():
  calls=[]
  def model(*args):
   reply=responses[len(calls)];calls.append(1)
   return (reply if isinstance(reply,str) else json.dumps(reply),'fixture','fixture')
  ns={'Any':Any,'json':json,'re':re,'model_reply':model}
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual-classifier>','exec'),ns)
  decisions=ns['classify_email_autonomy']([{'from':'fixture@example.invalid','subject':'synthetic'} for _ in range(9)])
  assert len(calls)==2
  if version=='candidate':
   if case=='valid':assert set(decisions)==set(range(1,10)) and decisions[9]['decision']=='draft'
   elif case=='cross_batch':assert set(decisions)==set(range(1,9)) and decisions[1]['decision']=='escalate'
   else:assert set(decisions)=={9}
  if version=='baseline' and case in ['cross_batch','duplicate']:assert decisions[1]['decision']=='automatic'
  results.append({'version':version,'case':case,'accepted_indexes':sorted(decisions),'first_decision':decisions.get(1,{}).get('decision'),'synthetic_model_responses':len(calls)})
print(json.dumps({'cases':results,'candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'actual_model_calls':0,'mailbox_actions':0,'production_changes':False,'limits':'Deterministic response validation only; classifier semantic quality, authenticated intake and live email acceptance remain open'}))
