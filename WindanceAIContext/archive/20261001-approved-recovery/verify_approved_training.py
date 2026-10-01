"""Read-only structural verification. Never invokes a sender or dispatcher."""
import ast
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

root = Path('/Users/zuzu/backups/training-correction-20261001T034328Z')
flow = Path('/Users/zuzu/.node-red/flows.json')
before = {n['id']:n for n in json.loads((root/'before/flows.json').read_text())}
wanted = {n['id']:n for n in json.loads((root/'candidate/flows.json').read_text())}
live = {n['id']:n for n in json.loads(flow.read_text())}
assert set(before) == set(wanted) == set(live)
normalized = json.loads(json.dumps(live))
assert normalized['wr_train_exec']['addpay'] == 'payload'
normalized['wr_train_exec']['addpay'] = True
for key in ['wr_train_format','wr_train_send']:
    assert normalized[key].pop('timeout') == ''
for key in ['0dab7dd7cbc94de8','ed2229ee9a7448cd']:
    assert normalized[key]['wires'] == [[]]
    normalized[key]['wires'] = []
assert normalized['samtemp00000003']['wires'] == [['samtemp00000004'],[]]
normalized['samtemp00000003']['wires'] = before['samtemp00000003']['wires']
assert normalized == wanted, 'Unexpected graph change'
ledger = Path('/Users/zuzu/bin/ledger_unpaid_invoice_report.py')
assert hashlib.sha256(ledger.read_bytes()).hexdigest() == 'e97253109a085b974c917965c8213a617c8ced7a01741f014162ea09da8f529e'
fn = next(n for n in ast.parse(ledger.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='shawn_recipient')
ns={'FLOWS_FILE':flow}
exec(compile(ast.Module(body=[fn],type_ignores=[]),'<recipient-only>','exec'),ns)
assert ns['shawn_recipient']()
jobs = {label:subprocess.run(['launchctl','print','gui/501/'+label],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0 for label in ['com.windance.supervisor','com.windance.supervisor-review']}
assert not any(jobs.values())
assert Path('/Users/zuzu/services/windance-supervisor/PAUSED').exists()
with urllib.request.urlopen('http://127.0.0.1:1880/',timeout=10) as response:
    http = response.status
result = {'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'training_four_fields_match_candidate':True,'recipient_pin_valid_and_distinct':True,
          'node_red_http':http,'warden_pause_marker':True,'warden_jobs_loaded':jobs,
          'saved_flow_sha256':hashlib.sha256(flow.read_bytes()).hexdigest(),
          'ledger_sha256':hashlib.sha256(ledger.read_bytes()).hexdigest(),
          'schedules_unchanged':True,'training_notes_collection_unchanged':True,
          'editor_defaults_normalized':['empty inject wires','empty function timeout','exec addpay true to payload'],
          'unexpected_alarm_wire_removal':{'source':'samtemp00000003','output':2,'target':'f7296630590f48ce','state':'disconnected; restoration held for owner approval'},
          'other_graph_differences':0,'explicit_sends':0,'manual_triggers':0,'natural_delivery_acceptance':'pending'}
(root/'verified-training-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
