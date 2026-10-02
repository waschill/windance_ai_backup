"""Function-only private staging on the selected host. No deployment."""
import ast,hashlib,json,sys
from pathlib import Path

host=sys.argv[1]
if host=='HERALD':
    live=Path('/Users/herald/services/agent-harness/agent_harness.py')
    stage=Path('/Users/herald/services/invoice-format-20261002')
    function='odoo_unpaid_customer_invoices';replacement='invoice_function.py'
    expected='db8a435907a2fb49796818a17b29334874b1919d6a03640901a22b6b12ea8195'
elif host=='SAL':
    live=Path('/Users/zuzu/bin/ledger_unpaid_invoice_report.py')
    stage=Path('/Users/zuzu/backups/invoice-format-candidate-20261002')
    function='get_report';replacement='sender_function.py'
    expected='e97253109a085b974c917965c8213a617c8ced7a01741f014162ea09da8f529e'
else:raise ValueError('Unexpected host')
raw=live.read_bytes();assert hashlib.sha256(raw).hexdigest()==expected
source=raw.decode();tree=ast.parse(source)
matches=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==function]
assert len(matches)==1
old=ast.get_source_segment(source,matches[0]);new=(stage/replacement).read_text().strip()
newtree=ast.parse(new);assert len(newtree.body)==1 and newtree.body[0].name==function
assert source.count(old)==1
candidate=source.replace(old,new,1)
before=[ast.dump(n,include_attributes=False) for n in tree.body if n is not matches[0]]
after=[ast.dump(n,include_attributes=False) for n in ast.parse(candidate).body if not(isinstance(n,ast.FunctionDef) and n.name==function)]
assert before==after
(stage/'original.private.py').write_bytes(raw)
(stage/'candidate.private.py').write_text(candidate)
for p in [stage/'original.private.py',stage/'candidate.private.py']:p.chmod(0o600)
receipt={'host':host,'baseline_sha256':expected,'candidate_sha256':hashlib.sha256(candidate.encode()).hexdigest(),
 'changed_function':function,'all_other_ast_nodes_unchanged':True,'production_bytes_unchanged':live.read_bytes()==raw}
(stage/'rebase-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
