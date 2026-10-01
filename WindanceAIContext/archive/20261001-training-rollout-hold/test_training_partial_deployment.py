"""SAL: actual saved resolver/adapter functions, fake paths and sender only."""
from __future__ import annotations
import ast
import base64
import contextlib
import io
import json
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

root=Path('/Users/zuzu/backups/training-correction-20261001T034328Z')
def extract(path,name,namespace):
    tree=ast.parse(path.read_text())
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<isolated-'+name+'>','exec'),namespace)
    return namespace[name]
results=[]
with tempfile.TemporaryDirectory(prefix='training-transition-isolation-') as temporary:
    home=Path(temporary)
    pin=home/'.config/windance-recipients/shawn-email.json';pin.parent.mkdir(parents=True)
    pin.write_text(json.dumps({'recipient':'+12025550123'}))
    flows=home/'flows.json'
    staged_nodes={n['id']:n for n in json.loads((root/'candidate/flows.json').read_text())}
    before_nodes={n['id']:n for n in json.loads((root/'before/flows.json').read_text())}
    assert staged_nodes['wr_train_exec']['command']=='/usr/bin/python3 /Users/zuzu/bin/send_shawn_report_payload.py'
    assert before_nodes['wr_train_exec']['command']=='/usr/bin/python3 /Users/zuzu/bin/send_william_imessage_payload.py'
    # Use the actual staged formatter; only the owner comparison is synthetic.
    flows.write_text(json.dumps([staged_nodes['wr_train_format'],
        {'id':'wr_brief_format','func':'msg.recipient = "+12025550124";'}]))
    old_ns={'FLOWS_FILE':flows,'json':json,'re':re,'Path':Path}
    new_ns={'FLOWS_FILE':flows}
    old=extract(root/'before/ledger_unpaid_invoice_report.py','shawn_recipient',old_ns)
    new=extract(root/'candidate/ledger_unpaid_invoice_report.py','shawn_recipient',new_ns)
    calls=[]
    def fake_run(argv,**kwargs):
        assert argv[:2]==['/usr/bin/python3','/Users/zuzu/bin/send_imessage_payload.py']
        calls.append(json.loads(base64.b64decode(argv[2])))
        return SimpleNamespace(returncode=0,stdout='{"ok":true,"synthetic":true}')
    ns={'base64':base64,'json':json,'sys':SimpleNamespace(argv=['synthetic',base64.b64encode(b'Synthetic schedule').decode(),'training-Shawn-2026-09-30']),
        'subprocess':SimpleNamespace(run=fake_run),'shawn_recipient':old}
    adapter=extract(root/'before/send_shawn_report_payload.py','main',ns)
    with patch('pathlib.Path.home',return_value=home),contextlib.redirect_stdout(io.StringIO()):
        try:adapter()
        except RuntimeError:pass
        else:raise AssertionError('Incomplete flow-first deployment reached sender')
        assert calls==[]
        results.append('new flow plus old resolver withholds before sender')
        ns['shawn_recipient']=new
        assert adapter()==0
        assert len(calls)==1 and calls[0]['to']=='+12025550123'
        assert calls[0]['idempotency_key']=='training-Shawn-2026-09-30'
        assert calls[0]['text']=='Synthetic schedule'
        results.append('matched resolver and adapter preserve recipient text and stable key')
        calls.clear();pin.write_text(json.dumps({'recipient':'+12025550124'}))
        try:adapter()
        except RuntimeError:pass
        else:raise AssertionError('Owner mismatch accepted')
        assert calls==[]
        results.append('owner mismatch withholds before sender')
        pin.unlink()
        try:adapter()
        except RuntimeError:pass
        else:raise AssertionError('Missing pin accepted')
        assert calls==[]
        results.append('missing configuration withholds before sender')
print(json.dumps({'passed':results,'actual_sends':0,'production_changes':0,
    'real_adapter_subprocess_called':False,'private_pin_accessed':False,
    'limit':'Tests argument/resolver transition only; no Node-RED deployment, scheduling race, network or Messages receipt exercised.'}))
