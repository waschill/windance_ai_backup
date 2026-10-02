import hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
import keyed_outbox_admission as admission
from message_receipt_journal import Journal

payload={'to':'synthetic-owner','chunks':['synthetic'],'sms':False};key='synthetic'
name='key-'+hashlib.sha256(key.encode()).hexdigest()+'.json'
if sys.argv[1:2]==['--child']:
    root=Path(sys.argv[2]);phase=sys.argv[3];original=admission.atomic_durable
    def interrupted(path,value):
        if phase=='before_claim' and path.parent.name=='claims':os._exit(73)
        original(path,value)
        if (phase=='after_claim' and path.parent.name=='claims') or (phase=='after_queue' and path.parent.name=='queue'):os._exit(73)
    admission.atomic_durable=interrupted
    admission.admit(root,key,payload)
    raise AssertionError('crash not injected')

results=[]
with tempfile.TemporaryDirectory(prefix='windance-admission-crash-') as tmp:
    for phase in ('before_claim','after_claim','after_queue'):
        root=Path(tmp)/phase;root.mkdir()
        for folder in ('claims','queue','results'):(root/folder).mkdir()
        Journal(root/'journal.db',create=True)
        child=subprocess.run([sys.executable,'-B',__file__,'--child',str(root),phase],capture_output=True,timeout=3)
        assert child.returncode==73,(phase,child.returncode)
        before={str(p):p.read_bytes() for p in root.rglob('*.json')}
        result=admission.admit(root,key,payload)
        if phase=='after_claim':
            assert result=={'status':'unknown','reason':'claim_without_outcome'},result
            assert not list((root/'queue').glob('*.json'))
        else:
            assert result['status']=='pending',result
            assert len(list((root/'queue').glob('*.json')))==1
        if phase!='before_claim':assert before=={str(p):p.read_bytes() for p in root.rglob('*.json')}
        after={str(p):p.read_bytes() for p in root.rglob('*.json')}
        assert admission.admit(root,key,payload)==result
        assert after=={str(p):p.read_bytes() for p in root.rglob('*.json')}
        results.append({'case':phase,'status':result['status'],'queued_items':len(list((root/'queue').glob('*.json')))})
print(json.dumps({'status':'passed','cases':results,'sends':0,'power_loss_tested':False}))
