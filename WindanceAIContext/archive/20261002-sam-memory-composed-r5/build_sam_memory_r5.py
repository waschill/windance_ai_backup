"""Compose private r5 from exact r4; no live installation or remote execution."""
import ast,copy,hashlib,json,shutil
from pathlib import Path
prior=Path('sam-memory-r4-private');root=Path('sam-memory-r5-private')
m=json.loads((prior/'memory-r4-manifest.json').read_text())
assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in m.items())
assert m['sam_schedule.memory-r4.private.py']=='db71ccb2da8f794ba21f0fb1cf74995890acf8bbb94c436b680dc76e630ee816'
s=(prior/'sam_schedule.memory-r4.private.py').read_text(encoding='utf-8');before=ast.parse(s)
def function(name):return ast.get_source_segment(s,next(n for n in ast.parse(s).body if getattr(n,'name','')==name))
old=function('init_db');s=s.replace(old,old+'\n    from sam_rollover_receipt import SCHEMA as rollover_schema\n    with connect() as rollover_db:\n        rollover_db.executescript(rollover_schema)')
old=function('get_schedule')
new=old.replace('def get_schedule(date: str | None = None)', 'def get_schedule(date: str | None = None, *, transaction_db=None)')
new=new.replace('    date_key, day_name, _ = selected_date(date)','    from contextlib import nullcontext\n    date_key, day_name, _ = selected_date(date)')
assert new.count('with connect() as db:')==1
new=new.replace('with connect() as db:','with (nullcontext(transaction_db) if transaction_db is not None else connect()) as db:')
s=s.replace(old,new)
# Preserve public functions for other callers; add explicit-transaction clones.
class TransactionBody(ast.NodeTransformer):
    def visit_Call(self,node):
        node=self.generic_visit(node)
        if isinstance(node.func,ast.Name) and node.func.id=='connect':return ast.Call(func=ast.Name(id='nullcontext',ctx=ast.Load()),args=[ast.Name(id='transaction_db',ctx=ast.Load())],keywords=[])
        if isinstance(node.func,ast.Name) and node.func.id=='record_missed_training':
            node.func.id='_record_missed_training_in_transaction';node.keywords.append(ast.keyword(arg='transaction_db',value=ast.Name(id='transaction_db',ctx=ast.Load())))
        return node
    def visit_Expr(self,node):
        if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='commit':return ast.Pass()
        return self.generic_visit(node)
clones=[]
for name in ('record_missed_training','rollover_unfinished_training'):
    node=copy.deepcopy(next(n for n in before.body if getattr(n,'name','')==name))
    node.name='_'+name+'_in_transaction';node.args.kwonlyargs.append(ast.arg(arg='transaction_db'));node.args.kw_defaults.append(None)
    TransactionBody().visit(node);node.body.insert(0,ast.ImportFrom(module='contextlib',names=[ast.alias(name='nullcontext')],level=0))
    clones.append(ast.unparse(ast.fix_missing_locations(node)))
old=function('post_completed_service_history')
anchor='skipped.append({"horse": item.get("horse_name"), "service": service_type, "history_id": history_receipt["odoo_history_id"]})'
assert old.count(anchor)==1
s=s.replace(old,old.replace(anchor,anchor.replace('"history_id":','"details": details, "history_id":')))
old=function('commit_day');new=old.replace('    schedule = get_schedule(date)','''    from sam_source_guard import source_token, finalize, SourceChanged
    with connect() as source_db:
        source_db.execute("BEGIN")
        schedule = get_schedule(date, transaction_db=source_db)
        base_token = source_token(source_db, schedule["date"], include_carries=False)
        initial_token = source_token(source_db, schedule["date"])
        initial_details = {row["item_id"]: dict(row) for row in source_db.execute("SELECT * FROM training_completion_details WHERE date=?", (schedule["date"],))}''',1)
a=new.index('    detail_inputs = []');b=new.index('    prepared = begin',a)
new=new[:a]+'    commit_inputs = {"date": date_key, "day_name": schedule["day_name"], "base_token": base_token}\n'+new[b:]
new=new.replace('        rollover_result = rollover_unfinished_training(date_key, items)','''        from sam_rollover_receipt import run_once as rollover_once
        def perform_rollover(db):
            if source_token(db, date_key) != initial_token:
                raise SourceChanged("Source changed before rollover; retain original commit binding")
            value = _rollover_unfinished_training_in_transaction(date_key, items, transaction_db=db)
            value["_source_token"] = source_token(db, date_key)
            return value
        rollover_result = rollover_once(connect, date_key, {"base_token": base_token}, perform_rollover)''',1)
# Renderer reads details from the same initial snapshot as schedule items.
a=new.index('                    with connect() as detail_db:');b=new.index('                    if detail:',a)
new=new[:a]+'                    detail = initial_details.get(item["id"])\n'+new[b:]
new=new.replace('        if history_result["posted"]:', '        confirmed_history = sorted(history_result["posted"] + history_result["already_posted"], key=lambda entry: entry["history_id"])\n        if confirmed_history:')
new=new.replace('"Odoo horse history entries created:"','"Confirmed Odoo horse history entries:"').replace('for entry in history_result["posted"]:', 'for entry in confirmed_history:')
anchor='f"- Carried to {rollover_result[\'to_date\']}: {len(rollover_result[\'carried\'])}",'
assert anchor in new
new=new.replace(anchor,anchor+'\n                    f"- Existing carries moved: {len(rollover_result[\'moved\'])}",')
a=new.index('    with connect() as db:',new.index('    result = post_sam_business_memory'))
b=new.index('    log_event(',a)
new=new[:a]+'    finalize(connect, date_key, rollover_result["_source_token"], result, now_iso())\n'+new[b:]
s=s.replace(old,new)
main=next(n for n in ast.parse(s).body if isinstance(n,ast.If) and '__name__' in ast.unparse(n.test))
lines=s.splitlines(keepends=True);lines.insert(main.lineno-1,'\n\n'+'\n\n'.join(clones)+'\n\n');s=''.join(lines)
after=ast.parse(s);changed={'init_db','get_schedule','post_completed_service_history','commit_day','_record_missed_training_in_transaction','_rollover_unfinished_training_in_transaction'}
assert [ast.dump(n) for n in before.body if getattr(n,'name','') not in changed]==[ast.dump(n) for n in after.body if getattr(n,'name','') not in changed]
compile(s,'<sam-memory-r5>','exec');root.mkdir()
(root/'sam_schedule.memory-r5.private.py').write_text(s,encoding='utf-8',newline='\n')
for name in m:
    if name!='sam_schedule.memory-r4.private.py':shutil.copy2(prior/name,root/name)
for name in ('sam_rollover_receipt.py','sam_source_guard.py'):shutil.copy2(name,root/name)
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
(root/'memory-r5-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest))
