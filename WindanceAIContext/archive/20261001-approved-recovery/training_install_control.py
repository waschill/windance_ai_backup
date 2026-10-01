"""SAL maintenance control for the recipient dependency only; no sends/restarts."""
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path('/Users/zuzu/backups/training-correction-20261001T034328Z')
receipt = json.loads((root/'receipt.json').read_text())
digest = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cli = ['/usr/bin/python3','/Users/zuzu/services/windance-supervisor/supervisor.py']
mode = sys.argv[1] if len(sys.argv)>1 else 'preflight'
assert mode in ('preflight','install','rollback')
target = Path('/Users/zuzu/bin/ledger_unpaid_invoice_report.py')
entry = next(e for e in receipt['manifest'] if e['source']==str(target))
if mode == 'preflight':
    for e in receipt['manifest']:
        assert digest(Path(e['source']))==e['sha256'], 'Live source drift'
    src = (root/'candidate'/target.name).read_text()
    node = next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='shawn_recipient')
    namespace = {'FLOWS_FILE':Path('/Users/zuzu/.node-red/flows.json')}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<recipient-only>','exec'),namespace)
    assert namespace['shawn_recipient']()
    state = json.loads(subprocess.check_output(cli+['status']))
    print(json.dumps({'preflight':'pass','recipient_pin_valid_and_not_william':True,
                      'warden_paused':state.get('paused'),
                      'incidents':[{'id':i.get('id'),'status':i.get('status')} for i in state.get('incidents',[])],
                      'live_sources_unchanged':True}))
else:
    assert Path('/Users/zuzu/services/windance-supervisor/PAUSED').exists(), 'Maintenance pause required'
    if mode == 'install':
        live_nodes = {n['id']: n for n in json.loads(Path('/Users/zuzu/.node-red/flows.json').read_text())}
        observed_nodes = {n['id']: n for n in json.loads((root/'after-first-ui-deploy.json').read_text())}
        candidate_nodes = {n['id']: n for n in json.loads((root/'candidate/flows.json').read_text())}
        assert live_nodes == observed_nodes, 'Live graph drift since verified UI deployment'
        for node_id, field in [('wr_train_format','func'),('wr_train_send','func'),
                               ('wr_train_eod_memory_format','func'),('wr_train_exec','command')]:
            assert live_nodes[node_id][field] == candidate_nodes[node_id][field], 'Training component mismatch'
        assert live_nodes['wr_train_exec']['addpay'] == 'payload'
        # The editor normalized defaults and removed an unrelated cross-tab alarm
        # wire. Its separate restoration is held for owner approval. Do not alter it.
        for label in ('com.windance.supervisor','com.windance.supervisor-review'):
            assert subprocess.run(['launchctl','print','gui/501/'+label],stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL).returncode != 0, 'Warden job unexpectedly loaded'
    expected = entry['sha256'] if mode=='install' else receipt['candidate_hashes'][target.name]
    assert digest(target)==expected, 'Concurrent source change'
    source = root/('candidate' if mode=='install' else 'before')/target.name
    wanted = receipt['candidate_hashes'][target.name] if mode=='install' else entry['sha256']
    assert digest(source)==wanted
    temporary = target.with_name(target.name+'.training-correction-tmp')
    assert not temporary.exists(), 'Staged install already present'
    temporary.write_bytes(source.read_bytes());temporary.chmod(entry['mode']);os.replace(temporary,target)
    assert digest(target)==wanted
    result = {'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':mode,
              'target':str(target),'sha256':wanted,'services_restarted':0,'messages_sent':0,
              'coordinated_training_fields_verified':mode=='install',
              'separate_alarm_link_repair':'held_for_owner_approval' if mode=='install' else 'unchanged'}
    (root/(mode+'-receipt.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
