import ast,hashlib,json,shutil
from pathlib import Path
prior=Path('email-bounded-sweep-private');root=Path('email-exchange-budget-private')
raw=(prior/'manifest.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='d9dd9a97324d7ee1bbc5d1758a5670a78c54d35332cdaa8626fbc46bbf12e1ec'
manifest=json.loads(raw)
assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
root.mkdir()
for name in manifest:shutil.copyfile(prior/name,root/name)
shutil.copyfile('gmail_exchange_budget.py',root/'gmail_exchange_budget.py')
p=root/'gmail_single_attempt_transport.py';s=p.read_text()
needle="        if not self._allowed(url,refresh):raise TransportUnconfirmed('Provider destination refused')"
assert s.count(needle)==1
s=s.replace(needle,needle+'\n        from gmail_exchange_budget import charge_exchange\n        charge_exchange()')
ast.parse(s);p.write_text(s,encoding='utf-8',newline='\n')
p=root/'email_fixed_worker.py';s=p.read_text()
needle="    return call(SimpleNamespace(user=payload['owner']))"
assert s.count(needle)==1
s=s.replace(needle,"    from gmail_exchange_budget import exchange_budget\n    with exchange_budget(256):\n        return call(SimpleNamespace(user=payload['owner']))")
ast.parse(s);p.write_text(s,encoding='utf-8',newline='\n')
manifest={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in list(manifest)+['gmail_exchange_budget.py']}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2))
digest=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()
(root/'worker-policy.json').write_text(json.dumps({'manifest_sha256':digest}))
print(json.dumps({'main_unchanged':manifest['agent_harness.py'],'manifest':digest,'files':len(manifest),'deployment':False}))
