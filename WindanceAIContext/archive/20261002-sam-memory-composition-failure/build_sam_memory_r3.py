"""Compose only private staged source; require pinned predecessor manifest."""
import ast,hashlib,json,shutil
from pathlib import Path
root=Path('sam-memory-r3-private');m=json.loads((root/'manifest.json').read_text())
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==v for n,v in m.items())
p=root/'sam_schedule.candidate.private.py';s=p.read_text(encoding='utf-8');before=ast.parse(s)
assert hashlib.sha256(p.read_bytes()).hexdigest()=='8e994992c402091aaef103e75bf9596c0d595c6e86c877d7852bba4df1b2aac9'
for node in before.body:
    if getattr(node,'name','')=='init_db':
        old=ast.get_source_segment(s,node)
        s=s.replace(old,old+'\n    from sam_memory_client import SCHEMA as memory_schema\n    with connect() as memory_db:\n        memory_db.executescript(memory_schema)')
    elif getattr(node,'name','')=='commit_day':
        old=ast.get_source_segment(s,node);anchor='result = json_http("POST", f"{HERALD_BASE}/memory", memory_payload, timeout=45)'
        assert old.count(anchor)==1
        s=s.replace(old,old.replace(anchor,'result = post_sam_business_memory(memory_payload)'))
helper='''
def post_sam_business_memory(payload):
    from sam_memory_client import submit
    from sam_memory_transport import send
    import os
    endpoint = os.environ.get("SAM_BUSINESS_MEMORY_URL", "")
    credential_path = os.environ.get("SAM_BUSINESS_MEMORY_CREDENTIAL_FILE", "")
    if not endpoint or not credential_path:
        raise RuntimeError("Dedicated business memory endpoint and credential file must be configured")
    return submit(connect, payload, lambda envelope: send(endpoint, credential_path, envelope))
'''
# Insert before main execution so the helper exists during application startup.
main=next((n for n in ast.parse(s).body if isinstance(n,ast.If) and '__name__' in ast.unparse(n.test)),None)
assert main is not None
lines=s.splitlines(keepends=True);lines.insert(main.lineno-1,helper+'\n');s=''.join(lines)
after=ast.parse(s);changed={'init_db','commit_day','post_sam_business_memory'}
assert [ast.dump(n) for n in before.body if getattr(n,'name','') not in changed]==[ast.dump(n) for n in after.body if getattr(n,'name','') not in changed]
compile(s,'<sam-memory-r3>','exec')
out=root/'sam_schedule.memory-r3.private.py';assert not out.exists();out.write_text(s,encoding='utf-8',newline='\n')
for n in ('sam_memory_client.py','sam_memory_transport.py'):shutil.copy2(n,root/n)
names=['sam_schedule.memory-r3.private.py','sam_history_intent.py','sam_clear_intent.py','sam_memory_client.py','sam_memory_transport.py']
manifest={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in names}
(root/'memory-r3-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'candidate':str(out),'manifest':manifest,'production_changes':False}))
