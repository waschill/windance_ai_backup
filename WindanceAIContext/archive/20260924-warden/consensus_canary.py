"""Real reviewers and launchd; only a disposable sleep job can be changed."""
import json
import os
import plistlib
import subprocess
import sys
import time
import uuid
from pathlib import Path
import remote_ops as ops
import review_gate as gate

root=Path(__file__).resolve().parent
label='com.windance.supervisor-consensus-canary'
domain=f'gui/{os.getuid()}'

def herald():
    ops.ROOT=root/'canary-state'
    ops.LABELS={'harness':label}
    def observe():
        state=ops.launch(label)
        return {'host':'HERALD','checks':{'harness':state['pid']>0},'harness':state,
                'purpose':'Installation canary: harness refers ONLY to the disposable '+label+' sleep job. No production process is targeted. The job is deliberately stopped and registered; start it once to verify the unanimous-review gate. Cleanup bootouts only this disposable label.'}
    ops.probe=observe
    phase=sys.argv[1]
    if phase=='prepare':
        if ops.launch(label)['loaded']: raise RuntimeError('Canary already exists')
        path=root/(label+'.plist')
        path.write_bytes(plistlib.dumps({'Label':label,'ProgramArguments':['/bin/sleep','180'],'RunAtLoad':False}))
        subprocess.run(['/bin/launchctl','bootstrap',domain,str(path)],check=True,capture_output=True)
        return gate.prepare(ops,'restart_harness','INC-20260924-'+uuid.uuid4().hex[:8],'HERALD:harness')
    if phase=='review': return gate.claude_review(ops,json.load(sys.stdin))
    if phase=='execute':
        receipt=gate.authorized_recovery(ops,sys.argv[2])
        for _ in range(20):
            after=observe()
            if after['checks']['harness']: break
            time.sleep(0.25)
        if not after['checks']['harness']: raise RuntimeError('Disposable service never became healthy')
        return {'receipt':receipt,'after':after,'production_services_changed':False}
    if phase=='cleanup':
        p=subprocess.run(['/bin/launchctl','bootout',domain+'/'+label],capture_output=True)
        return {'removed':not ops.launch(label)['loaded'],'exit_code':p.returncode}
    raise ValueError('Unknown canary phase')

def sal():
    def remote(args,payload=None,timeout=310):
        p=subprocess.run(['ssh','-o','BatchMode=yes','HERALD','/Users/herald/.hermes/hermes-agent/venv/bin/python',
                          '/Users/herald/services/windance-supervisor-consensus-stage/consensus_canary.py',*args],
                          input=None if payload is None else json.dumps(payload),capture_output=True,text=True,timeout=timeout)
        if p.returncode: raise RuntimeError('Canary remote phase failed: '+args[0]+' '+p.stderr[-1200:])
        return json.loads(p.stdout)
    receipt={}
    try:
        proposal=remote(['prepare'])
        sha=gate.digest(proposal)
        receipt['proposal_sha256']=sha
        codex=gate.codex_review(root,proposal)
        receipt['codex']=codex
        if codex['decision']!='approve': raise RuntimeError('Canary held by Codex')
        claude=remote(['review'],{'proposal_sha256':sha,'codex':codex})
        receipt['claude']=claude
        gate.validate_verdict(claude,proposal,'Claude')
        if claude['decision']!='approve': raise RuntimeError('Canary held by Claude')
        result=remote(['execute',sha])
        receipt['execution']=result
        if not result['receipt']['performed']: raise RuntimeError('Canary did not execute')
    finally:
        gate.save(root/'consensus-canary-receipt.json',receipt)
        try: receipt['cleanup']=remote(['cleanup'])
        except Exception as exc: receipt['cleanup']={'error':type(exc).__name__}
        finally: gate.save(root/'consensus-canary-receipt.json',receipt)
    if not receipt['cleanup'].get('removed'): raise RuntimeError('Canary cleanup requires operator attention')
    return receipt

if __name__=='__main__':
    print(json.dumps(herald() if Path.home().name=='herald' else sal()))
