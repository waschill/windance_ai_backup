"""One-function replacement; private full source, no app import or execution."""
import ast,hashlib,json
from pathlib import Path
p=Path('/Users/herald/services/agent-harness/agent_harness.py');raw=p.read_bytes();s=raw.decode()
assert hashlib.sha256(raw).hexdigest()=='9865597bda4368784beac015dbcec712a271889395e9fcebf788c60b636774d4'
t=ast.parse(s);node=next(n for n in t.body if getattr(n,'name','')=='classify_email_autonomy')
old=ast.get_source_segment(s,node);start=old.index('        for row in parse_email_autonomy_decisions(raw):');end=old.index('    return decisions',start)
new=old[:start]+'''        from email_classification_contract import validated_chunk
        expected = {entry["index"] for entry in payload[start : start + 8]}
        decisions.update(validated_chunk(parse_email_autonomy_decisions(raw), expected))
'''+old[end:]
candidate=s.replace(old,new);after=ast.parse(candidate)
assert [ast.dump(n) for n in t.body if getattr(n,'name','')!='classify_email_autonomy']==[ast.dump(n) for n in after.body if getattr(n,'name','')!='classify_email_autonomy']
root=Path('/Users/herald/backups/email-classification-candidate-20261002');root.mkdir(mode=0o700,exist_ok=True)
target=root/'agent_harness.candidate.private.py';target.write_text(candidate);target.chmod(0o600)
print(json.dumps({'baseline_sha256':hashlib.sha256(raw).hexdigest(),'candidate_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'changed_function':'classify_email_autonomy','production_changes':False}))
