"""Composed authenticated-source/processor recovery with real disposable child exits."""
import ast,asyncio,json,os,sqlite3,subprocess,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
from authenticated_message_ingress import Adapter,Intake
from memory_command_router import Processor
from harness_memory_policy import parse_remember_command,memory_looks_secret


def setup(database,phase='normal'):
    class Closing(sqlite3.Connection):
        def __exit__(self,*args):
            try:return super().__exit__(*args)
            finally:self.close()
        def commit(self):
            if phase=='before_fact_commit' and self.in_transaction:
                # Called at the real gateway/source transaction commit boundary.
                if self.execute('SELECT count(*) FROM owned_fact_requests').fetchone()[0]:os._exit(73)
            return super().commit()
    def connect():
        c=sqlite3.connect(database,factory=Closing);c.row_factory=sqlite3.Row;return c
    processor=Processor(connect,parse_remember_command,memory_looks_secret,'fixture-sal','fixture-credential',['william'])
    return connect,processor


def child(database,phase):
    connect,processor=setup(database,phase)
    if phase in {'after_fact_commit','after_answer_commit'}:
        original=processor.answer
        def terminate(mid,answer):
            if phase=='after_answer_commit':original(mid,answer)
            os._exit(74 if phase=='after_fact_commit' else 75)
        processor.answer=terminate
    processor.process_pending()


async def accept(connect,row,text):
    intake=Intake([Adapter('fixture-sal','fixture-credential',frozenset({'william'}),'max-imessage',False,'max-imessage:')],
                  connect,lambda value:True,initial_status=lambda value:'memory_pending')
    async def body():return {'owner':'william','source_id':'max-imessage:'+str(row),'message':text}
    response=await intake.handle(SimpleNamespace(headers={'Authorization':'Bearer fixture-credential'},json=body))
    assert response.status==202


def invoke(database,phase,expected=0):
    result=subprocess.run([sys.executable,__file__,'--child',str(database),phase],capture_output=True,text=True,timeout=20)
    assert result.returncode==expected,(phase,result.returncode)


def main():
    outcomes=[]
    for phase,exit_code in [('before_fact_commit',73),('after_fact_commit',74),('after_answer_commit',75)]:
        with tempfile.TemporaryDirectory(prefix='memory-route-recovery-') as directory:
            base=Path(directory);database=base/'manager.db'
            connect,processor=setup(database)
            source=Path('/Users/herald/services/vega-manager/manager.py').read_text()
            init=next(n for n in ast.parse(source).body if getattr(n,'name','')=='init')
            ns={'BASE':base,'connect':connect};exec(compile(ast.Module(body=[init],type_ignores=[]),'<actual-init>','exec'),ns);ns['init']()
            with connect() as c:Intake.install(c)
            processor.install()
            asyncio.run(accept(connect,1,'remember this: synthetic crash recovery preference'))
            invoke(database,phase,exit_code)
            with connect() as c:
                assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                assert c.execute('SELECT count(*) FROM authenticated_message_sources').fetchone()[0]==1
                assert c.execute('SELECT count(*) FROM owned_facts').fetchone()[0]==(0 if phase=='before_fact_commit' else 1)
                assert c.execute('SELECT status FROM messages').fetchone()[0]==('answered' if phase=='after_answer_commit' else 'memory_pending')
            invoke(database,'normal')
            with connect() as c:
                key,revision=c.execute('SELECT fact_key,revision FROM owned_facts').fetchone()
                assert revision==1 and c.execute('SELECT count(*) FROM owned_fact_requests').fetchone()[0]==1
                assert c.execute('SELECT status FROM messages').fetchone()[0]=='answered'
            asyncio.run(accept(connect,2,f'forget memory {key} revision 1'))
            invoke(database,'normal')
            # Snapshot after forgetting, then operate only on the independent cold copy.
            restored=base/'cold-restored.db'
            with connect() as origin,sqlite3.connect(restored) as copy:origin.backup(copy)
            with sqlite3.connect(restored) as copy:
                assert copy.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                copy.execute("UPDATE messages SET status='memory_pending' WHERE id='max-imessage:1'")
            invoke(restored,'normal')
            with sqlite3.connect(restored) as copy:
                assert copy.execute('SELECT revision,value,deleted FROM owned_facts').fetchone()==(2,None,1)
                assert copy.execute('SELECT count(*) FROM owned_fact_requests').fetchone()[0]==2
                assert 'newer revision' in copy.execute("SELECT answer FROM messages WHERE id='max-imessage:1'").fetchone()[0]
            outcomes.append({'exit_boundary':phase,'child_exit':exit_code,'fresh_process_recovery':True,
                             'cold_restore_preserves_forgetting':True,'old_retry_did_not_resurrect':True})
    print(json.dumps({'cases':outcomes,'actual_process_exit':True,'production_changes':False,
                      'model_calls':0,'dispatches':0,'sends':0,
                      'limits':'Synthetic sources; current consistent cold snapshot only; no sender or host-loss recovery'}))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--child':child(Path(sys.argv[2]),sys.argv[3])
    else:main()
