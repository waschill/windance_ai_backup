import ast,hashlib,shutil
from pathlib import Path
p=Path('sweep-caller-private/effects_candidate.private.py')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='37a1fa9ef0cec98ed4a23ae56fdc92e42de2f6d35f1960163a8b52d29cf082e1'
s=p.read_text(encoding='utf-8').replace('"effects":result.get("effects"),','"effects":result.get("effects"), "accounting_reconciled":result.get("accounting_reconciled",0),')
ast.parse(s);target=p.with_name('provenance_candidate.private.py')
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
shutil.copyfile('email-rule-provenance-private/email_sweep_contract.py','email_sweep_contract.py')
print('caller_sha256='+hashlib.sha256(target.read_bytes()).hexdigest())
