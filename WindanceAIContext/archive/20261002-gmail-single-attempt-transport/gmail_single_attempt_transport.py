"""Staged Gmail transport: no API replay, redirects or raw provider error bodies."""
from types import SimpleNamespace
from urllib.parse import urlsplit
import httpx,httplib2
class TransportUnconfirmed(RuntimeError):pass
class GmailTransport:
    def __init__(self,credentials,*,allow_loopback=False,read_timeout=15):
        if not 0<read_timeout<=15:raise ValueError('Bounded read timeout required')
        self.credentials=credentials;self.allow_loopback=allow_loopback
        self.client=httpx.Client(transport=httpx.HTTPTransport(retries=0,trust_env=False),
            timeout=httpx.Timeout(read_timeout,connect=min(5,read_timeout)),follow_redirects=False,trust_env=False)
    def close(self):self.client.close()
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
            with self.client.stream(method,url,content=body,headers=headers,follow_redirects=False) as response:
                if 300<=response.status_code<400:raise TransportUnconfirmed('Provider redirect refused; outcome unconfirmed')
                chunks=[];size=0
                for part in response.iter_bytes(chunk_size=32768):
                    size+=len(part)
                    if size>16*1024*1024:raise TransportUnconfirmed('Provider response exceeds bound; outcome unconfirmed')
                    chunks.append(part)
                return response.status_code,dict(response.headers),b''.join(chunks)
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
