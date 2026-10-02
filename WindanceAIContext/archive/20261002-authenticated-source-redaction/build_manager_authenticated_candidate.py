"""Private full manager candidate, rebased with exact source hash and AST preservation."""
import ast,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
live=Path('/Users/herald/services/vega-manager/manager.py')
raw=live.read_bytes();source=raw.decode()
assert hashlib.sha256(raw).hexdigest()=='0ad87dcebb5844736ca218101ded61ce15c525c0042222f3f9e90d319f5445d5'
tree=ast.parse(source)
node=next(n for n in tree.body if getattr(n,'name','')=='app')
old=ast.get_source_segment(source,node)
new=old.replace('    return a',
    '    from manager_authenticated_routes import attach, make_content_policy\n'
    '    from harness_memory_policy import parse_remember_command, memory_looks_secret, redact_approval_auth_word, redact_level8_code\n'
    '    sanitize = lambda text: redact_approval_auth_word(redact_level8_code(text))\n'
    '    attach(a,connect,make_content_policy(parse_remember_command,memory_looks_secret,sanitize),sanitize)\n'
    '    return a')
assert new!=old
candidate=source.replace(old,new)
after=ast.parse(candidate)
assert [ast.dump(n) for n in tree.body if n is not node]==[ast.dump(n) for n in after.body if getattr(n,'name','')!='app']
target=root/'manager-authenticated-candidate.private.py';target.write_text(candidate);target.chmod(0o600)
h=Path('/Users/herald/services/agent-harness/agent_harness.py')
hs=h.read_text();ht=ast.parse(hs)
functions=[n for n in ht.body if getattr(n,'name','') in {'parse_remember_command','memory_looks_secret','redact_approval_auth_word','redact_level8_code'}]
assert len(functions)==4
policy='"""Exact installed Harness policy functions frozen for staged integration."""\nimport re\n\n'+'\n\n'.join(ast.get_source_segment(hs,n) for n in functions)+'\n'
(root/'harness_memory_policy.py').write_text(policy)
print(json.dumps({'manager_source_sha256':hashlib.sha256(raw).hexdigest(),
 'candidate_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
 'harness_source_sha256':hashlib.sha256(h.read_bytes()).hexdigest(),
 'policy_sha256':hashlib.sha256(policy.encode()).hexdigest(),'only_changed_function':'app','production_changes':False}))
