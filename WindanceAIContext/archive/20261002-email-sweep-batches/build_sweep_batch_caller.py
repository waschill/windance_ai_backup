import ast,hashlib
from pathlib import Path
p=Path('sweep-caller-private/candidate.private.py');s=p.read_text(encoding='utf-8');tree=ast.parse(s)
start=s.index('        required = ');end=s.index('        if result.get("status") == "held" or result["errors"]:',start)
s=s[:start]+'        from email_sweep_contract import validate\n        validate(result)\n'+s[end:]
s=s.replace('Gmail sender-rule results (review notices for uncertain outcomes):','Gmail sender-rule batch results (review notices for uncertain outcomes):')
s=s.replace('print(json.dumps({"status": "sweep_completed", "checked": result["checked"],','print(json.dumps({"status": "sweep_partial" if result.get("status")=="partial" else "sweep_completed", "coverage":result.get("coverage"), "checked": result["checked"],')
assert [ast.dump(n) for n in tree.body if getattr(n,'name','')!='main']==[ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','')!='main']
target=p.with_name('batch_candidate.private.py')
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
print('candidate_sha256='+hashlib.sha256(target.read_bytes()).hexdigest())
