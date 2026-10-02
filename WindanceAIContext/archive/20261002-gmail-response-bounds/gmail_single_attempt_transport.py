"""Staged Gmail transport: no API replay, redirects or raw provider error bodies."""
from types import SimpleNamespace
from urllib.parse import urlsplit
import httpx,httplib2,zlib,time
class TransportUnconfirmed(RuntimeError):pass
class GmailTransport:
    def __init__(self,credentials,*,allow_loopback=False,read_timeout=15,response_limit=16*1024*1024,exchange_timeout=30):
        if not 0<read_timeout<=15:raise ValueError('Bounded read timeout required')
        if not 0<response_limit<=16*1024*1024 or not 0<exchange_timeout<=30:raise ValueError('Bounded response settings required')
        self.credentials=credentials;self.allow_loopback=allow_loopback
        self.read_timeout=read_timeout
        self.response_limit=response_limit;self.exchange_timeout=exchange_timeout
    def close(self):pass  # Each exchange owns and closes its connection pool.
    def _allowed(self,url,refresh=False):
        parsed=urlsplit(url)
        if parsed.username or parsed.password or parsed.fragment:return False
        if self.allow_loopback and parsed.scheme=='http' and parsed.hostname=='127.0.0.1':return True
        if parsed.scheme!='https' or parsed.port not in (None,443):return False
        if refresh:return parsed.hostname=='oauth2.googleapis.com' and parsed.path=='/token'
        return parsed.hostname in ('gmail.googleapis.com','www.googleapis.com') and parsed.path.startswith(('/gmail/v1/','/upload/gmail/v1/'))
    def _exchange(self,url,method,body,headers,*,refresh=False):
        if not self._allowed(url,refresh):raise TransportUnconfirmed('Provider destination refused')
        try:
            deadline=time.monotonic()+self.exchange_timeout
            headers={k:v for k,v in (headers or {}).items() if k.lower()!='accept-encoding'}
            headers['Accept-Encoding']='gzip, identity'
            with httpx.Client(transport=httpx.HTTPTransport(retries=0,trust_env=False),
                    timeout=httpx.Timeout(self.read_timeout,connect=min(5,self.read_timeout)),
                    follow_redirects=False,trust_env=False) as client, client.stream(method,url,content=body,headers=headers,follow_redirects=False) as response:
                if 300<=response.status_code<400:raise TransportUnconfirmed('Provider redirect refused; outcome unconfirmed')
                encoding=response.headers.get('content-encoding','identity').strip().lower()
                if encoding not in ('identity','gzip'):raise TransportUnconfirmed('Provider response encoding refused')
                decoder=zlib.decompressobj(16+zlib.MAX_WBITS) if encoding=='gzip' else None
                chunks=[];size=0;wire_size=0
                for raw in response.iter_raw():
                    if time.monotonic()>deadline:raise TransportUnconfirmed('Provider response deadline exceeded; outcome unconfirmed')
                    wire_size+=len(raw)
                    if wire_size>self.response_limit:raise TransportUnconfirmed('Provider response exceeds bound; outcome unconfirmed')
                    part=decoder.decompress(raw,self.response_limit-size+1) if decoder else raw
                    size+=len(part)
                    if size>self.response_limit:raise TransportUnconfirmed('Provider response exceeds bound; outcome unconfirmed')
                    chunks.append(part)
                if time.monotonic()>deadline:raise TransportUnconfirmed('Provider response deadline exceeded; outcome unconfirmed')
                if decoder and (not decoder.eof or decoder.unused_data or decoder.unconsumed_tail):raise TransportUnconfirmed('Provider compressed response incomplete or ambiguous')
                data=b''.join(chunks)
                values=dict(response.headers)
                # Return decoded content without the old compressed size/encoding.
                values.pop('content-encoding',None);values.pop('transfer-encoding',None)
                values['content-length']=str(len(data))
                return response.status_code,values,data
        except TransportUnconfirmed:raise
        except Exception:raise TransportUnconfirmed('Provider response unavailable; retain operation for reconciliation') from None
    def request(self,uri,method='GET',body=None,headers=None,**kwargs):
        if not self._allowed(uri):raise TransportUnconfirmed('Provider destination refused')
        request_headers=dict(headers or {});refresh_count=0
        def refresh(url,method='GET',body=None,headers=None,**kwargs):
            nonlocal refresh_count
            refresh_count+=1
            if refresh_count>1:raise TransportUnconfirmed('Credential refresh retry refused')
            code,values,data=self._exchange(url,method,body,headers,refresh=True)
            return SimpleNamespace(status=code,headers=values,data=data)
        try:self.credentials.before_request(refresh,method,uri,request_headers)
        except Exception:raise TransportUnconfirmed('Provider credential preparation unavailable') from None
        code,values,data=self._exchange(uri,method,body,request_headers)
        # Preserve status for the client without returning private provider text.
        if not 200<=code<300:
            data=b'{"error":{"message":"Provider request was not confirmed"}}'
            values={'content-type':'application/json'}
        return httplib2.Response({**values,'status':str(code)}),data
