import contextlib,datetime,importlib.util,io,json,sys
from pathlib import Path
import receipt_report_transport

source=Path(sys.argv[1]);spec=importlib.util.spec_from_file_location('sentinel_candidate',source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
results=[]
original_deliver=m.deliver
for case in ('verified','uncertain','generation_failure','dry_run'):
    calls=[]
    def report(minutes):
        if case=='generation_failure':raise ValueError('synthetic')
        return 'Router is all clear'
    def deliver(message):
        calls.append(message)
        if case=='uncertain':raise RuntimeError('uncertain')
    m.report=report;m.deliver=deliver;m.log=lambda message:None
    original_argv=sys.argv;sys.argv=['sentinel']+(['--dry-run'] if case=='dry_run' else [])
    try:
        with contextlib.redirect_stdout(io.StringIO()):code=m.main()
    finally:sys.argv=original_argv
    assert len(calls)==(0 if case=='dry_run' else 1),(case,len(calls))
    assert code==(1 if case in ('uncertain','generation_failure') else 0)
    results.append({'case':case,'delivery_attempts':len(calls),'exit_code':code})
keys=[]
def send(recipient,message,key,**kwargs):keys.append(key);return {'ok':True}
receipt_report_transport.send_report=send
original_deliver('Router is all clear');original_deliver('synthetic changed report')
assert len(keys)==2 and keys[0]==keys[1] and keys[0].startswith('sentinel-router:')
print(json.dumps({'status':'passed','cases':results,'same_day_changed_body_same_key':True,'real_sends':0}))
