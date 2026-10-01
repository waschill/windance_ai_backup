"""Real HTTP handler, disposable DB/config and denied external effects."""
import asyncio
import json
import os
import sys
import tempfile
from unittest.mock import patch

with tempfile.TemporaryDirectory(prefix='windance-owner-isolation-') as temp:
    for name in ['DATA','LOG','CONFIG']:
        os.environ['AGENT_HARNESS_'+name+'_DIR']=temp
    os.environ['GOOGLE_WORKSPACE_CONFIG_DIR']=temp
    sys.path.insert(0,'/Users/herald/services/agent-harness')
    import agent_harness as h
    import httpx
    calls=[]
    approval_refs=[]
    def synthetic_mailbox():
        calls.append('william-mailbox')
        return 'SYNTHETIC_WILLIAM_PRIVATE_MAIL', 'deterministic', 'synthetic-william-email'
    def synthetic_approval(*args):
        approval_refs.append([a.get('message_id') for a in args[1].get('actions',[])])
        return 'synthetic-approval'
    def denied(*args,**kwargs):
        raise AssertionError('External effects forbidden in owner isolation test')
    async def main():
        h.startup()
        h.save_email_report_refs('synthetic-william-report',[(1,'test',{'id':'synthetic-william-message','from':'sender@example.test','subject':'synthetic'})])
        results=[]
        with patch.object(h.urllib.request,'urlopen',side_effect=denied),patch.object(h.subprocess,'run',side_effect=denied),patch.object(h,'dispatch_staff_worker',side_effect=denied),patch.object(h,'model_reply',side_effect=denied),patch.object(h,'summarize_email_for_william',side_effect=synthetic_mailbox),patch.object(h,'request_approval',side_effect=synthetic_approval):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=h.app,client=('127.0.0.1',4567)),base_url='http://test') as c:
                for owner in ['William','Shawn']:
                    start=len(calls)
                    approval_start=len(approval_refs)
                    r=await c.post('/message',json={'user':owner,'channel':'vega-internal','message':'delete 1','request_id':'synthetic-owner-'+owner.lower()})
                    d=r.json()
                    results.append({'owner':owner,'http':r.status_code,'provider':d.get('provider'),'model':d.get('model'),'william_mailbox_handler_called':len(calls)>start,'william_reference_approval_prepared':any('synthetic-william-message' in refs for refs in approval_refs[approval_start:]),'synthetic_private_result_returned':'SYNTHETIC_WILLIAM_PRIVATE_MAIL' in d.get('reply','')})
        print(json.dumps({'test':'isolated internal email owner boundary','results':results,'production_modified':False,'real_mailbox_reads':0,'sends':0}))
    asyncio.run(main())


