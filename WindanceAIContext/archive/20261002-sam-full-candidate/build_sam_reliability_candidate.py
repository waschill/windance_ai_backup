"""Private full-source SAM candidate; no imports/execution of production app."""
import ast,hashlib,json
from pathlib import Path
path=Path('/home/williamschilling/services/sam-schedule/sam_schedule.py')
raw=path.read_bytes();source=raw.decode()
assert hashlib.sha256(raw).hexdigest()=='824026967ab935b2563f0a77021668754fa5969f704e17e3619137a455643bc1'
tree=ast.parse(source);changed={'init_db','commit_day','post_completed_service_history'}
candidate=source
for node in tree.body:
    if getattr(node,'name','') not in changed:continue
    old=ast.get_source_segment(source,node);new=old
    if node.name=='init_db':
        new+='\n    from sam_history_intent import install as install_history_intents\n    with connect() as intent_db:\n        install_history_intents(intent_db)'
    elif node.name=='commit_day':
        anchor='    result = json_http("POST", f"{HERALD_BASE}/memory", memory_payload, timeout=45)'
        assert new.count(anchor)==1
        new=new.replace(anchor,anchor+'\n    if not isinstance(result, dict) or result.get("status") != "ok":\n        raise RuntimeError("Memory acknowledgment did not confirm success; local day remains uncommitted")')
    else:
        anchor='result = herald_odoo_horse_history(int(horse_id), service_type, date_key, details)'
        assert new.count(anchor)==1
        new=new.replace(anchor,'from sam_history_intent import perform as history_once\n                    result = history_once(connect, date_key, item["id"], int(horse_id), service_type, details, lambda: herald_odoo_horse_history(int(horse_id), service_type, date_key, details))')
    assert new!=old;candidate=candidate.replace(old,new)
after=ast.parse(candidate)
assert [ast.dump(n) for n in tree.body if getattr(n,'name','') not in changed]==[ast.dump(n) for n in after.body if getattr(n,'name','') not in changed]
root=Path('/home/williamschilling/backups/sam-reliability-candidate-20261002')
root.mkdir(parents=True,exist_ok=True,mode=0o700)
target=root/'sam_schedule.candidate.private.py';target.write_text(candidate);target.chmod(0o600)
print(json.dumps({'baseline_sha256':hashlib.sha256(raw).hexdigest(),'candidate_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                  'changed_functions':sorted(changed),'production_changes':False}))
