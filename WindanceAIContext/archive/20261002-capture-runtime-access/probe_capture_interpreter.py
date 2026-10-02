"""Run pinned count-only reader under each interpreter; no content or sends."""
import hashlib,importlib.util,json,subprocess,sys,time
from pathlib import Path
source=Path('/Users/herald/services/capture-review-reminder/capture_review_reminder.py')
if sys.argv[1:2]==['--child']:
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='763a096d0a61319ea4c732ae24119b2f642adc847570585c7fa6f05802753900'
    spec=importlib.util.spec_from_file_location('actual_capture_reader',source)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    allowed=f'file:{m.DB}?mode=ro'
    def guard(event,args):
        if event=='sqlite3.connect':
            target=args[0].decode('utf-8') if isinstance(args[0],bytes) else args[0]
            if target!=allowed:raise RuntimeError('unexpected_database')
        if event=='subprocess.Popen' or event in ('os.system','os.posix_spawn') or event.startswith('socket.'):
            raise RuntimeError('external_effect_blocked')
    sys.addaudithook(guard)
    started=time.monotonic()
    try:
        value=m.active_count();assert type(value) is int and value>=0
        print(json.dumps({'status':'readable','count':value,'seconds':round(time.monotonic()-started,4)}))
    except Exception as e:print(json.dumps({'status':'unavailable','error_type':type(e).__name__,'seconds':round(time.monotonic()-started,4)}))
else:
    values=[]
    for interpreter in ('/usr/bin/python3','/Users/herald/.hermes/hermes-agent/venv/bin/python'):
        result=subprocess.run([interpreter,'-B',__file__,'--child'],capture_output=True,text=True,timeout=15)
        if result.returncode:values.append({'interpreter':interpreter,'status':'probe_failed','exit':result.returncode});continue
        value=json.loads(result.stdout);value.pop('count',None);value['interpreter']=interpreter;values.append(value)
    print(json.dumps({'results':values,'capture_content_read':False,'real_sends':0,'production_changed':False}))
