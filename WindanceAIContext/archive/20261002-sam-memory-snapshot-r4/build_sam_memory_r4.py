"""Compose private r4 from pinned failed r3; preserve the failed artifact."""
import ast,hashlib,json,shutil
from pathlib import Path
prior=Path('sam-memory-r3-private');root=Path('sam-memory-r4-private')
m=json.loads((prior/'memory-r3-manifest.json').read_text())
assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in m.items())
assert m['sam_schedule.memory-r3.private.py']=='a9288a5549ea50491caf771cfad67a818b442cbe27460d492cbbd8036fa58377'
s=(prior/'sam_schedule.memory-r3.private.py').read_text(encoding='utf-8');before=ast.parse(s)
init=next(n for n in before.body if getattr(n,'name','')=='init_db')
old=ast.get_source_segment(s,init)
s=s.replace(old,old+'\n    from sam_commit_snapshot import SCHEMA as snapshot_schema\n    with connect() as snapshot_db:\n        snapshot_db.executescript(snapshot_schema)')
node=next(n for n in ast.parse(s).body if getattr(n,'name','')=='commit_day');old=ast.get_source_segment(s,node)
start=old.index('    items = schedule["items"]');end=old.index('    result = post_sam_business_memory(memory_payload)')
render=old[start:end]
prefix='''    import os
    from sam_commit_snapshot import begin, freeze
    if not os.environ.get("SAM_BUSINESS_MEMORY_URL") or not os.environ.get("SAM_BUSINESS_MEMORY_CREDENTIAL_FILE"):
        raise RuntimeError("Dedicated business memory configuration required before commit effects")
    detail_inputs = []
    with connect() as detail_db:
        for item in schedule["items"]:
            if item.get("training_raw") and item.get("training_done"):
                detail = detail_db.execute("SELECT category,subcategory,note,stars FROM training_completion_details WHERE item_id=?", (item["id"],)).fetchone()
                detail_inputs.append([item["id"], list(detail) if detail else None])
    commit_inputs = {"date": date_key, "day_name": schedule["day_name"], "items": schedule["items"], "training_details": detail_inputs}
    prepared = begin(connect, date_key, commit_inputs)
    if prepared is None:
'''
suffix='''        prepared = freeze(connect, date_key, commit_inputs, {"memory_payload": memory_payload, "completed": completed, "totals": totals, "rollover": rollover_result, "history": history_result, "auto": auto})
    memory_payload = prepared["memory_payload"]
    completed, totals = prepared["completed"], prepared["totals"]
    rollover_result, history_result = prepared["rollover"], prepared["history"]
    auto = prepared["auto"]
'''
new=old[:start]+prefix+''.join('    '+line if line.strip() else line for line in render.splitlines(keepends=True))+suffix+old[end:]
s=s.replace(old,new);after=ast.parse(s)
assert [ast.dump(n) for n in before.body if getattr(n,'name','') not in {'init_db','commit_day'}]==[ast.dump(n) for n in after.body if getattr(n,'name','') not in {'init_db','commit_day'}]
compile(s,'<sam-memory-r4>','exec');root.mkdir()
(root/'sam_schedule.memory-r4.private.py').write_text(s,encoding='utf-8',newline='\n')
for name in m:
    if name!='sam_schedule.memory-r3.private.py':shutil.copy2(prior/name,root/name)
shutil.copy2('sam_commit_snapshot.py',root/'sam_commit_snapshot.py')
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
(root/'memory-r4-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest))
