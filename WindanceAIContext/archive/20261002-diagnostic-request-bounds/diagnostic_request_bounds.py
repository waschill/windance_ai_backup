"""Bound request streams before JSON parsing; no body content in errors."""
import asyncio
from starlette.responses import JSONResponse

class RequestBounds:
    def __init__(self, app, max_bytes=4096, timeout_seconds=10):
        self.app=app; self.max_bytes=max_bytes; self.timeout_seconds=timeout_seconds

    async def __call__(self, scope, receive, send):
        if scope['type']!='http':
            return await self.app(scope,receive,send)
        async def reject(code,detail):
            await JSONResponse({'detail':detail},status_code=code)(scope,receive,send)
        lengths=[v for k,v in scope.get('headers',[]) if k.lower()==b'content-length']
        if len(lengths)>1 or (lengths and (not lengths[0].isdigit() or len(lengths[0])>10)):
            return await reject(400,'Invalid request length')
        declared=int(lengths[0]) if lengths else None
        if declared is not None and declared>self.max_bytes:
            return await reject(413,'Request exceeds bound')
        body=bytearray()
        deadline=asyncio.get_running_loop().time()+self.timeout_seconds
        while True:
            remaining=deadline-asyncio.get_running_loop().time()
            if remaining<=0:return await reject(408,'Request body timeout')
            try:message=await asyncio.wait_for(receive(),remaining)
            except asyncio.TimeoutError:return await reject(408,'Request body timeout')
            if message['type']=='http.disconnect':return
            if message['type']!='http.request':return await reject(400,'Invalid request stream')
            chunk=message.get('body',b'')
            if len(chunk)>self.max_bytes-len(body):return await reject(413,'Request exceeds bound')
            body.extend(chunk)
            if not message.get('more_body',False):break
        if declared is not None and declared!=len(body):return await reject(400,'Request length mismatch')
        delivered=False
        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered=True
                return {'type':'http.request','body':bytes(body),'more_body':False}
            return await receive()
        await self.app(scope,bounded_receive,send)
