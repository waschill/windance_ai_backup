import asyncio
import importlib.util
import json
import urllib.request
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

def request(path,payload=None):
    req=urllib.request.Request('http://127.0.0.1:8791'+path,data=json.dumps(payload).encode() if payload is not None else None,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)

async def main():
    params=StdioServerParameters(command='/Users/herald/services/google-workspace-mcp/.venv/bin/python',args=['/Users/herald/services/herald-staff-mcp/herald_staff_mcp.py'])
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            names={t.name for t in (await session.list_tools()).tools}
            assert {'capture_idea','list_ideas','review_idea'} <= names
            note='I would also like to create an Idea Board where I can send you some random thoughts and ideas that would not be for immediate implementation. At the end of the day or week, compile those ideas/notes into a suggested implementation plan.'
            result=await session.call_tool('capture_idea',{'text':note})
            assert not result.isError, result
            data=json.loads(result.content[0].text)
            idea_id=data['id']
            for state in ['archived','active','discussion']:
                result=await session.call_tool('review_idea',{'idea_id':idea_id,'state':state,'reason':'Workflow setup verification: preserved William\'s original request; evaluate first digest on 2026-09-25.'})
                assert not result.isError, result
            result=await session.call_tool('list_ideas',{'state':'discussion'})
            assert note in str(result)
    # Verify the actual deployed protected plugin renderer and malicious-text escaping.
    spec=importlib.util.spec_from_file_location('plugin','/Users/herald/.hermes/plugins/windance-vega-desktop/dashboard/plugin_api.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    body=module.idea_board().body.decode()
    assert idea_id in body and 'Idea Board' in body
    assert 'Idea Board' in module.work_board().body.decode()
    original=module.urllib.request.urlopen
    import io
    module.urllib.request.urlopen=lambda *a,**kw:io.BytesIO(json.dumps({'items':[{'id':'test','state':'active','original_text':'<script>alert(1)</script>','history':[]}]}).encode())
    try:
        test=module.idea_board().body.decode()
        assert '<script>' not in test and '&lt;script&gt;' in test
    finally:module.urllib.request.urlopen=original
    assert request('/decision-logs')=={'items':[]}
    print(json.dumps({'mcp_tools_verified':sorted(names),'idea_id':idea_id,'archive_restore_preserved_text':True,'final_state':'discussion','deployed_board_rendered':True,'html_escaping':True,'decision_log_read':True}))

asyncio.run(main())
