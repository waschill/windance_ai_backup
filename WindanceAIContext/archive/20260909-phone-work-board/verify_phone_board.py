import importlib.util, sys
from fastapi import FastAPI
from fastapi.testclient import TestClient
path='/Users/herald/.hermes/plugins/windance-vega-desktop/dashboard/plugin_api.py'
spec=importlib.util.spec_from_file_location('phone_plugin',path)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
app=FastAPI();app.include_router(m.router,prefix='/api/plugins/windance-vega-desktop')
c=TestClient(app)
base='/api/plugins/windance-vega-desktop/work'
r=c.get(base);assert r.status_code==200,r.text
assert 'Windance Work' in r.text and '?task=' in r.text
assert r.headers['cache-control']=='no-store'
assert "frame-ancestors 'self'" in r.headers['content-security-policy']
r=c.get(base,params={'task':'490bc438-52aa-4a1b-bd3b-258a4ca19690'})
assert r.status_code==200 and 'completed' in r.text
assert 'href="'+base+'"' in r.text and 'href="/staff/tasks/board"' not in r.text
assert c.get(base,params={'task':'http://example.com'}).status_code==422
assert c.get(base,params={'task':'00000000-0000-0000-0000-000000000000'}).status_code==404
assert c.post(base).status_code==405
assert c.get('/api/plugins/windance-vega-desktop/health').json()['agent']=='Vega'
print('PASS: live ledger list/detail, return navigation, no-store/CSP, invalid ID, missing task, read-only and preserved health')

