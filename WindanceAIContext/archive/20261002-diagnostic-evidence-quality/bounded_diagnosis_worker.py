"""Fixed deterministic diagnostic worker; no executable instructions from evidence."""
import errno,json,socket,sys,time,re
from pathlib import Path

mode=sys.argv[1]
if mode in ('timeout','cancel'):
    while True: time.sleep(0.1)
assert mode=='diagnose'
e=json.loads(Path('/evidence/failure.json').read_text())
required={'approval_action','payload_argument_names','journal_rejects_payload_action','before_synthetic_effects','after_synthetic_effects','before_sha256','after_sha256'}
valid=(isinstance(e,dict) and set(e)==required
       and isinstance(e['payload_argument_names'],list)
       and len(e['payload_argument_names'])<=50
       and all(isinstance(n,str) and len(n)<=128 for n in e['payload_argument_names'])
       and type(e['before_synthetic_effects']) is int and type(e['after_synthetic_effects']) is int
       and all(isinstance(e[n],str) and re.fullmatch('[0-9a-f]{64}',e[n]) for n in ('before_sha256','after_sha256'))
       and e['before_sha256']!=e['after_sha256'])
supported=(valid and e['approval_action']=='gmail.delete' and 'action' in e['payload_argument_names']
           and e['journal_rejects_payload_action'] is True
           and e['before_synthetic_effects']==0 and e['after_synthetic_effects']==1)
try:
    Path('/evidence/forbidden-write').write_text('probe')
    raise AssertionError('Evidence mount unexpectedly writable')
except OSError as exc:
    assert exc.errno in (errno.EROFS,errno.EACCES)
try:
    Path('/forbidden-write').write_text('probe')
    raise AssertionError('Root filesystem unexpectedly writable')
except OSError as exc:
    assert exc.errno in (errno.EROFS,errno.EACCES)
assert set(p.name for p in Path('/sys/class/net').iterdir())=={'lo'}
# No network request is attempted; loopback-only namespace is checked locally.
print(json.dumps({'status':'diagnosed' if supported else 'insufficient_evidence',
 'cause':'Route payload includes reserved action field rejected by journal' if supported else None,
 'repair_proposal':'Exclude the routing action from argument payload; retain authoritative approval action' if supported else None,
 'rollback':'Retain predecessor stage and manifest; no production repair performed' if supported else None,
 'evidence':e,'barriers':{'evidence_write_denied':True,'root_write_denied':True,'network_interfaces':['lo']},
 'limits':'One deterministic known failure; no general diagnosis, live caller authentication or provider validation.'}))
