"""SAL only: prepare private candidate and verify cold rollback; never install."""
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import tempfile

os.umask(0o077)
stage = Path('/Users/zuzu/services/agentic-training-isolation-20261001')
root = Path('/Users/zuzu/backups') / ('training-correction-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
root.mkdir(mode=0o700)
before = root/'before'; before.mkdir()
candidate = root/'candidate'; candidate.mkdir()
flow = Path('/Users/zuzu/.node-red/flows.json')
ledger = Path('/Users/zuzu/bin/ledger_unpaid_invoice_report.py')
sources = [flow, ledger, Path('/Users/zuzu/bin/send_shawn_report_payload.py'), Path('/Users/zuzu/bin/send_imessage_payload.py')]
digest = lambda data: hashlib.sha256(data).hexdigest()
manifest = []
for source in sources:
    data = source.read_bytes()
    target = before/source.name
    target.write_bytes(data)
    assert target.read_bytes() == data
    manifest.append({'source':str(source),'backup':str(target),'sha256':digest(data),'mode':source.stat().st_mode & 0o777})
assert digest(flow.read_bytes()) == '41228c501266b0f4061b40c328ea297cb1ce07d43c6a625bff101ef71d746702', 'Flow drift: stop'
packet = json.loads((stage/'training-candidate/node-changes.json').read_text())
nodes = json.loads((before/'flows.json').read_bytes())
original = {n['id']:dict(n) for n in nodes}
changes = packet['changes']
assert set(changes) == {'wr_train_format','wr_train_send','wr_train_exec','wr_train_eod_memory_format'}
for node in nodes:
    if node['id'] in changes:
        node.update(changes[node['id']])
assert {n['id'] for n in nodes if n != original[n['id']]} == set(changes)
(candidate/'flows.json').write_text(json.dumps(nodes,ensure_ascii=False,indent=4)+'\n')
source = (before/ledger.name).read_text()
tree = ast.parse(source)
matches = [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='shawn_recipient']
assert len(matches)==1
old = matches[0]
replacement = (stage/'invoice-candidate/recipient_function.py').read_text().strip()
lines = source.splitlines(keepends=True)
updated = ''.join(lines[:old.lineno-1]) + replacement + '\n' + ''.join(lines[old.end_lineno:])
new_tree = ast.parse(updated)
without = lambda t: ast.dump(ast.Module(body=[n for n in t.body if not(isinstance(n,ast.FunctionDef) and n.name=='shawn_recipient')],type_ignores=[]),include_attributes=False)
assert without(tree)==without(new_tree), 'Unexpected source change'
compile(updated, '<staged-ledger>', 'exec')
(candidate/ledger.name).write_text(updated)
restored = []
with tempfile.TemporaryDirectory(prefix='training-cold-restore-') as temporary:
    for entry in manifest:
        source = Path(entry['backup'])
        target = Path(temporary)/source.name
        target.write_bytes(source.read_bytes())
        assert digest(target.read_bytes())==entry['sha256']
        if target.suffix=='.json': json.loads(target.read_text())
        else: ast.parse(target.read_text())
        restored.append(source.name)
# A concurrent edit invalidates this receipt; never overwrite it.
assert all(digest(Path(e['source']).read_bytes())==e['sha256'] for e in manifest)
receipt = {'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'private_root':str(root),
           'status':'STAGED_NOT_INSTALLED','manifest':manifest,'cold_restores':restored,
           'candidate_hashes':{p.name:digest(p.read_bytes()) for p in candidate.iterdir()},
           'changed_flow_nodes':sorted(changes),'changed_python_function':'shawn_recipient',
           'other_python_ast_unchanged':True,'live_sources_unchanged':True,
           'secrets_and_private_recipient_pin_copied':False,'services_started':0,'messages_sent':0}
(root/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
