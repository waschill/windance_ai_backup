"""Raw ASGI fragmented/slow/disconnected bodies; fixture ledger, no dispatch."""
import asyncio,hashlib,json,tempfile
from pathlib import Path
from diagnostic_job_api import create_app
from diagnostic_request_bounds import RequestBounds

async def main():
    with tempfile.TemporaryDirectory() as directory:
        app=create_app(Path(directory)/'jobs.db',{hashlib.sha256(b'fixture').hexdigest():'owner'})
        payload=json.dumps({'request_key':'one','kind':'email_payload_diagnosis','evidence_sha256':'a'*64}).encode()
        async def probe(chunks,headers=(),pause=0,disconnect=False):
            sent=[];items=iter(chunks)
            scope={'type':'http','asgi':{'version':'3.0'},'http_version':'1.1','method':'POST','scheme':'http','path':'/jobs','raw_path':b'/jobs','query_string':b'','root_path':'','headers':[(b'authorization',b'Bearer fixture'),(b'content-type',b'application/json'),*headers],'client':('127.0.0.1',1),'server':('fixture',80)}
            async def receive():
                if pause:await asyncio.sleep(pause)
                try:return next(items)
                except StopIteration:return {'type':'http.disconnect'}
            async def send(message):sent.append(message)
            # Short deadline only for the slow-input fixture; production default remains10s.
            target=RequestBounds(app,timeout_seconds=.01) if pause else app
            await target(scope,receive,send)
            return next((m['status'] for m in sent if m['type']=='http.response.start'),None),b''.join(m.get('body',b'') for m in sent)
        def message(body,more=False):return {'type':'http.request','body':body,'more_body':more}
        cases=[
            ([message(b'x'*4097)],(),413),
            ([message(b'x'*2048,True),message(b'x'*2049)],(),413),
            ([],[(b'content-length',b'4097')],413),
            ([message(payload)],[(b'content-length',b'1')],400),
            ([],[(b'content-length',b'1'),(b'content-length',b'1')],400),
            ([],[(b'content-length',b'-1')],400),
        ]
        for chunks,headers,expected in cases:
            status,body=await probe(chunks,headers);assert status==expected
            assert b'xxxx' not in body
        assert (await probe([message(payload)],pause=.05))[0]==408
        assert (await probe([message(payload[:20],True)]))[0] is None
        status,body=await probe([message(b'{"private":"PRIVATE_SENTINEL"}')])
        assert status==422 and b'PRIVATE_SENTINEL' not in body and b'private' not in body
        with app.state.ledger.connect() as c:assert c.execute('select count(*) from jobs').fetchone()[0]==0
        status,_=await probe([message(payload[:20],True),message(payload[20:])],[(b'content-length',str(len(payload)).encode())])
        assert status==200
        with app.state.ledger.connect() as c:assert c.execute('select count(*) from jobs').fetchone()[0]==1
        print(json.dumps({'passed':True,'rejected_stream_cases':8,'valid_fragmented_submission':True,'dispatch_calls':0,'production_changes':False}))
asyncio.run(main())
