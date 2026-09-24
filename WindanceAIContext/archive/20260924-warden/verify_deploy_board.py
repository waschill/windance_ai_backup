"""Validate fixed read-only board, then replace only the inspected revision."""
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient

root=Path('/Users/herald/services/windance-supervisor')
staged=root/'plugin_api.staged.py'
live=Path('/Users/herald/.hermes/plugins/windance-vega-desktop/dashboard/plugin_api.py')
spec=importlib.util.spec_from_file_location('supervisor_board',staged)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
app=FastAPI(); app.include_router(module.router)
client=TestClient(app)
r=client.get('/work?view=supervisor')
assert r.status_code==200 and 'Windance Supervisor' in r.text and 'SAL' in r.text
assert r.headers['cache-control']=='no-store'
assert client.post('/work?view=supervisor').status_code==405
assert client.get('/work?task=../../etc/passwd').status_code==422
assert client.get('/health').json()['status']=='ok'
backup=root/'backups/initial/plugin_api.py'
backup.parent.mkdir(parents=True,exist_ok=True)
if not backup.exists(): shutil.copy2(live,backup)
assert live.read_bytes()==backup.read_bytes(), 'Concurrent plugin edit: stop'
shutil.copy2(staged,live)
print(json.dumps({'board_tests':5,'sha256':hashlib.sha256(live.read_bytes()).hexdigest()}))
