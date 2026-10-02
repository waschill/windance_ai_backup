"""Stage manager status propagation; does not install or run the service."""
import ast,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
source=Path('/Users/herald/services/vega-manager/manager.py').read_bytes().decode()
assert hashlib.sha256(source.encode()).hexdigest()=='1d2c67417ca4080158db8e5c9840b5c602523856bfc7551ad0f2c8276a4c7a83'
tree=ast.parse(source);node=next(n for n in tree.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='process_messages')
old=ast.get_source_segment(source,node);new=old.replace("status IN ('queued','submitted')", "status IN ('queued','submitted','execution_uncertain')")
new=new.replace("{'completed','failed','interrupted'}", "{'completed','failed','interrupted','execution_uncertain'}")
new=new.replace("'failed':'failed'}", "'failed':'failed','execution_uncertain':'execution_uncertain'}")
new=new.replace("answer=result.get('result_summary') or", "answer=('Execution stop is unconfirmed. Accepted work is preserved; conflicting work is held for reconciliation.' if state=='execution_uncertain' else result.get('result_summary')) or")
assert new!=old
source=source.replace(old,new)
after=ast.parse(source)
assert [ast.dump(n,include_attributes=False) for n in tree.body if n is not node]==[ast.dump(n,include_attributes=False) for n in after.body if not isinstance(n,ast.AsyncFunctionDef) or n.name!='process_messages']
target=root/'manager-candidate.py';target.write_text(source);target.chmod(0o600)
print(json.dumps({'manager_candidate_sha256':hashlib.sha256(source.encode()).hexdigest(),'only_changed_function':'process_messages','production_changed':False}))
