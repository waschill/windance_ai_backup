"""Run the actual private report wrapper with subprocess replaced; no SSH/send."""
import contextlib,hashlib,importlib.util,io,json,os,sys
from pathlib import Path
from types import SimpleNamespace

source=Path(sys.argv[1]);digest=hashlib.sha256(source.read_bytes()).hexdigest()
assert digest=='aacab51098b3cf89c4b8660e67f3958eff71b56e496ea91a526e629279515780'
spec=importlib.util.spec_from_file_location('actual_report_wrapper',source)
wrapper=importlib.util.module_from_spec(spec);spec.loader.exec_module(wrapper)
results=[]
cases=[('legacy',0,{'ok':True,'chunks':1},True),
       ('versioned',0,{'version':2,'ok':True,'status':'delivered','evidence':'local_messages_flags','chunks':1},True),
       ('new_verified_schema',0,{'status':'verified_delivery','independent_delivery_verified':True,'chunks':1},False),
       ('pending',10,{'status':'pending'},False),('invalid',0,{},False)]
original_stdin=sys.stdin;previous=os.environ.get('WINDANCE_DELIVERY_KEY')
os.environ['WINDANCE_DELIVERY_KEY']='synthetic-contract-key'
try:
    for case,code,receipt,expected in cases:
        calls=[]
        def run(command,**kwargs):
            assert command[0]=='/usr/bin/ssh' and kwargs['timeout']==80
            import base64
            payload=json.loads(base64.b64decode(command[-1]))
            assert payload['idempotency_key']=='synthetic-contract-key' and payload['text']=='synthetic report'
            calls.append(True)
            return SimpleNamespace(returncode=code,stdout=json.dumps(receipt),stderr='')
        wrapper.subprocess=SimpleNamespace(run=run)
        sys.stdin=io.StringIO('synthetic report')
        try:
            with contextlib.redirect_stdout(io.StringIO()):wrapper.main()
            accepted=True
        except RuntimeError:accepted=False
        assert accepted==expected,(case,accepted)
        assert len(calls)==1
        results.append({'case':case,'accepted':accepted})
finally:
    sys.stdin=original_stdin
    if previous is None:os.environ.pop('WINDANCE_DELIVERY_KEY',None)
    else:os.environ['WINDANCE_DELIVERY_KEY']=previous
print(json.dumps({'source_sha256':digest,'cases':results,'actual_ssh_calls':0,'real_sends':0}))
