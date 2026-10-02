"""Actual rollover transformed to accept one DB transaction; no production calls."""
import ast,concurrent.futures,contextlib,datetime as dt,hashlib,json,sqlite3,tempfile
from pathlib import Path
from typing import Any
from sam_rollover_receipt import SCHEMA,run_once,RolloverHeld
root=Path(__file__).parent/'sam-memory-r4-private'
source=(root/'sam_schedule.memory-r4.private.py').read_text(encoding='utf-8')
assert hashlib.sha256(source.encode()).hexdigest()=='db71ccb2da8f794ba21f0fb1cf74995890acf8bbb94c436b680dc76e630ee816'
names={'connect','init_db','effective_active_carryovers','record_missed_training','rollover_unfinished_training'}
nodes=[n for n in ast.parse(source).body if getattr(n,'name','') in names];assert len(nodes)==5
class TransactionBody(ast.NodeTransformer):
    def visit_Call(self,node):
        node=self.generic_visit(node)
        if isinstance(node.func,ast.Name) and node.func.id=='connect':return ast.Call(func=ast.Name(id='nullcontext',ctx=ast.Load()),args=[ast.Name(id='transaction_db',ctx=ast.Load())],keywords=[])
        if isinstance(node.func,ast.Name) and node.func.id=='record_missed_training':node.keywords.append(ast.keyword(arg='transaction_db',value=ast.Name(id='transaction_db',ctx=ast.Load())))
        return node
    def visit_Expr(self,node):
        if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='commit':return ast.Pass()
        return self.generic_visit(node)
for node in nodes:
    if node.name in ('record_missed_training','rollover_unfinished_training'):
        node.args.kwonlyargs.append(ast.arg(arg='transaction_db'));node.args.kw_defaults.append(None)
        TransactionBody().visit(node)
tree=ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[]))
class ClosingConnection(sqlite3.Connection):
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()
results=[]
for mode in ('normal','receipt_failure','callback_failure','concurrent','cold_retry','changed_input','corrupt_receipt'):
    with tempfile.TemporaryDirectory(prefix='sam-rollover-transaction-') as directory:
        folder=Path(directory)
        ns={'Any':Any,'sqlite3':sqlite3,'DATA_DIR':folder,'DB_PATH':folder/'sam.db','DEFAULT_TRAINERS':[],
            'dt':dt,'json':json,'now_iso':lambda:'fixture','ROLLOVER_UNFINISHED_TRAINING':True,'nullcontext':contextlib.nullcontext}
        exec(compile(tree,'<actual-transaction-rollover>','exec'),ns)
        # Ensure all actual extracted schema contexts close on Windows.
        def connect():
            c=sqlite3.connect(ns['DB_PATH'],timeout=10,factory=ClosingConnection);c.row_factory=sqlite3.Row;return c
        ns['connect']=connect
        import sys
        sys.path.insert(0,str(root))
        ns['init_db']()
        with connect() as c:c.executescript(SCHEMA)
        items=[{'horse_key':'fixture','horse_name':'SYNTHETIC','training_raw':'A','training_done':0,'odoo_schedule_row_id':1}]
        with connect() as c:
            ns['record_missed_training']('2098-12-31','2099-01-01',dict(items[0],training_raw='B'),'local_carried',{},transaction_db=c)
            if mode=='receipt_failure':c.execute("CREATE TRIGGER fail_receipt BEFORE INSERT ON sam_rollover_receipts BEGIN SELECT RAISE(ABORT,'synthetic receipt failure'); END")
        calls=[]
        def perform(c):
            calls.append(1)
            result=ns['rollover_unfinished_training']('2099-01-01',items,transaction_db=c)
            if mode=='callback_failure' and len(calls)==1:raise RuntimeError('synthetic interruption after effects')
            return result
        def run():return run_once(connect,'2099-01-01',items,perform)
        if mode in ('receipt_failure','callback_failure'):
            try:run();raise AssertionError('Failure injection missed')
            except (sqlite3.IntegrityError,RuntimeError):pass
            with connect() as c:
                assert c.execute('SELECT count(*) FROM missed_training').fetchone()[0]==1
                assert c.execute('SELECT target_date FROM missed_training').fetchone()[0]=='2099-01-01'
                assert c.execute('SELECT count(*) FROM sam_rollover_receipts').fetchone()[0]==0
                if mode=='receipt_failure':c.execute('DROP TRIGGER fail_receipt')
        if mode=='concurrent':
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:receipts=list(pool.map(lambda _:run(),range(6)))
            assert all(r==receipts[0] for r in receipts);result=receipts[0]
        else:result=run()
        if mode=='cold_retry':
            import shutil
            shutil.copy2(ns['DB_PATH'],folder/'restored.db');ns['DB_PATH']=folder/'restored.db'
        if mode=='changed_input':
            try:run_once(connect,'2099-01-01',[dict(items[0],training_raw='C')],perform);raise AssertionError('Changed input accepted')
            except RolloverHeld:pass
        elif mode=='corrupt_receipt':
            with connect() as c:c.execute("UPDATE sam_rollover_receipts SET result_json='{}'")
            try:run();raise AssertionError('Corrupt receipt accepted')
            except RolloverHeld:pass
        else:assert run()==result
        with connect() as c:
            assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            assert c.execute('SELECT count(*) FROM missed_training').fetchone()[0]==2
            assert c.execute("SELECT count(*) FROM missed_training WHERE target_date='2099-01-02'").fetchone()[0]==2
        assert len(calls)==(2 if mode in ('receipt_failure','callback_failure') else 1)
        assert len(result['carried'])==1 and len(result['moved'])==1
        results.append({'scenario':mode,'callback_attempts':len(calls),'new_carries':1,'existing_carries_moved':1,'passed':True})
print(json.dumps({'cases':results,'production_changes':False,'full_candidate_integrated':False,'limits':'AST refactor fixture; no full startup, power-loss or end-to-end commit certification'}))
