"""Three-way AST-checked source composition; never changes the live service."""
import ast,hashlib,json,shutil
from pathlib import Path
base=Path('caller-contract-private/harness.py');live=Path('email-rebase-input-private/agent_harness.py')
prior=Path('email-rule-provenance-private');root=Path('email-rebased-private')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='0a95a09f0ad1932b53d38130579411ac8679c99265e4dc8741b8fd171dce2ab0'
assert hashlib.sha256(live.read_bytes()).hexdigest()=='c2fa4c908a2ff5cdcc92d58da0ac5cf38534d800a235cbdf3bfcaed5341e3ef7'
raw=(prior/'manifest.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='8d8395964f47aa5b1d47da251cdc89307b36d3fbf5c78db07eaa2fb189c229d6'
manifest=json.loads(raw);assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
texts={'base':base.read_text(encoding='utf-8'),'live':live.read_text(encoding='utf-8'),'staged':(prior/'agent_harness.py').read_text(encoding='utf-8')}
def key(n):
    if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):return n.name
    if isinstance(n,ast.Assign):return 'assign:'+','.join(ast.unparse(t) for t in n.targets)
    if isinstance(n,ast.AnnAssign):return 'assign:'+ast.unparse(n.target)
    return ast.dump(n)
nodes={k:{key(n):n for n in ast.parse(s).body} for k,s in texts.items()}
maps={k:{name:ast.dump(n) for name,n in ns.items()} for k,ns in nodes.items()}
changed={name for name in set(maps['base'])|set(maps['live']) if maps['base'].get(name)!=maps['live'].get(name)}
assert changed=={'_deliver_staff_task_message','_deliver_staff_task_message_legacy','assign:TASK_REPORT_JOURNAL','render_task_handoff','task_handoff'}
assert all(maps['staged'].get(n)==maps['base'].get(n) or maps['staged'].get(n)==maps['live'].get(n) for n in changed)
def span(n):return min([n.lineno]+[d.lineno for d in getattr(n,'decorator_list',[])]),n.end_lineno
def segment(label,n):
    start,end=span(n);return ''.join(texts[label].splitlines(keepends=True)[start-1:end])
edits=[]
for name in changed:
    if name in nodes['staged']:
        start,end=span(nodes['staged'][name]);edits.append((start-1,end,segment('live',nodes['live'][name])))
addition='\n'.join(segment('live',nodes['live'][n]) for n in ('_deliver_staff_task_message_legacy','assign:TASK_REPORT_JOURNAL'))+'\n'
insertion=span(nodes['staged']['_deliver_staff_task_message'])[0]-1
edits.append((insertion,insertion,addition))
lines=texts['staged'].splitlines(keepends=True)
for start,end,replacement in sorted(edits,reverse=True):lines[start:end]=[replacement]
source=''.join(lines);after={key(n):ast.dump(n) for n in ast.parse(source).body}
expected=dict(maps['staged']);expected.update({n:maps['live'][n] for n in changed})
assert after==expected
root.mkdir()
for name in manifest:shutil.copyfile(prior/name,root/name)
(root/'agent_harness.py').write_text(source,encoding='utf-8',newline='\n')
helpers=['task_report_journal.py','task_report_status.py','daily_report_journal.py','receipt_report_transport.py','outbox_wire_protocol.py']
for name in helpers:
    assert name not in manifest
    shutil.copyfile(live.parent/name,root/name)
manifest={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in list(manifest)+helpers}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2));digest=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()
(root/'worker-policy.json').write_text(json.dumps({'manifest_sha256':digest}))
print(json.dumps({'main':manifest['agent_harness.py'],'manifest':digest,'sources':len(manifest),'live_changes_preserved':sorted(changed),'staged_changes_preserved':True,'deployment':False}))
