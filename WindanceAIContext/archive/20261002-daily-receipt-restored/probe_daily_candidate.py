import contextlib,importlib.util,io,json,os,sys
from pathlib import Path
source=Path(sys.argv[1]);sys.path.insert(0,str(source.parent))
def guard(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect','socket.bind','socket.sendto'):raise AssertionError('outbound denied')
 if event=='sqlite3.connect':assert 'mode=ro' in os.fsdecode(args[0]),'non-readonly database'
 if event=='open' and not isinstance(args[0],int):assert not ((args[2] or 0)&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)),'write denied'
sys.addaudithook(guard)
spec=importlib.util.spec_from_file_location('daily_no_send_probe',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
before=m.DELIVERY_JOURNAL.exists();output=io.StringIO();sys.argv=[str(source),'--dry-run']
with contextlib.redirect_stdout(output):code=m.main()
text=output.getvalue();assert code==0 and m.DELIVERY_JOURNAL.exists()==before
print(json.dumps({'dry_run_exit':code,'report_available':not text.startswith('Sentinel router review BLOCKED:'),'report_characters':len(text),'journal_created':False,'outbound_and_writes_blocked':True,'report_content_output':False}))
