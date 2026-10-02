"""Stage stable reminder identity and honest submission wording, without sending."""
import ast,hashlib,json
from pathlib import Path
p=Path('capture-reminder-private/original.private.py');s=p.read_text(encoding='utf-8')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='763a096d0a61319ea4c732ae24119b2f642adc847570585c7fa6f05802753900'
t=ast.parse(s);node=next(n for n in t.body if getattr(n,'name','')=='main');old=ast.get_source_segment(s,node)
helper='''def capture_delivery_key(moment=None) -> str:
    import datetime
    from zoneinfo import ZoneInfo
    current = moment or datetime.datetime.now(datetime.timezone.utc)
    if current.tzinfo is None:
        raise ValueError("Timezone-aware reminder time required")
    day = current.astimezone(ZoneInfo("America/Denver")).date().isoformat()
    return "capture-review:william:" + day
'''
new=old.replace('    completed = subprocess.run(','''    import os
    sender_environment = dict(os.environ)
    sender_environment["WINDANCE_DELIVERY_KEY"] = capture_delivery_key()
    completed = subprocess.run(''',1)
new=new.replace('timeout=90,','timeout=90, env=sender_environment,')
if 'env=sender_environment' not in new:new=new.replace('timeout=90)', 'timeout=90, env=sender_environment)')
assert 'env=sender_environment' in new
for n in ast.walk(ast.parse(new)):
 if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and getattr(n.value.func,'id','')=='print' and n.value.args and isinstance(n.value.args[0],ast.JoinedStr):
  segment=ast.get_source_segment(new,n)
  if 'Sent Capture Inbox' in segment:
   new=new.replace(segment,'print(json.dumps({"status": "submitted", "independent_delivery_verified": False, "active_items": count}))')
assert 'Sent Capture Inbox reminder' not in new
s=s.replace(old,helper+'\n\n'+new);after=ast.parse(s)
changed={'main','capture_delivery_key'}
assert [ast.dump(n) for n in t.body if getattr(n,'name','') not in changed]==[ast.dump(n) for n in after.body if getattr(n,'name','') not in changed]
out=p.with_name('candidate.private.py');out.write_text(s,encoding='utf-8',newline='\n')
print(json.dumps({'candidate_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'unrelated_ast_preserved':True,'installed':False}))
