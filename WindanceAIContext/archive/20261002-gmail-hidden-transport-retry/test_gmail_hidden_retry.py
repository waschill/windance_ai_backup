"""Installed client transport reproduction: no sockets or real Gmail operation."""
import hashlib,http.client,inspect,json
import httplib2
from googleapiclient.http import HttpRequest
class Reply(http.client.HTTPResponse):
    def __init__(self):
        self.status=200;self.reason='OK';self.version=11
    def getheaders(self):return [('Content-Type','application/json')]
    def read(self,*args):return b'{"id":"synthetic"}'
    def close(self):pass
class Connection:
    host='fixture.invalid'
    def __init__(self,mode):self.sock=object();self.mode=mode;self.requests=[];self.reads=0
    def connect(self):self.sock=object()
    def close(self):self.sock=None
    def request(self,method,uri,body,headers):self.requests.append(method)
    def getresponse(self):
        self.reads+=1
        if self.reads==1:
            if self.mode=='bad_status':raise http.client.BadStatusLine('synthetic response loss')
            raise http.client.ResponseNotReady('synthetic response loss')
        return Reply()
results=[]
for mode in ('bad_status','response_not_ready'):
    connection=Connection(mode);transport=httplib2.Http(timeout=1)
    class Adapter:
        def request(self,uri,method='GET',body=None,headers=None,**kwargs):
            return transport._conn_request(connection,'/synthetic-write',method,body,headers)
    request=HttpRequest(Adapter(),lambda response,content:json.loads(content),uri='https://fixture.invalid/synthetic-write',method='POST',body='{}')
    result=request.execute(num_retries=0)
    assert result=={'id':'synthetic'} and connection.requests==['POST','POST']
    results.append({'failure':mode,'application_execute_calls':1,'configured_api_retries':0,'transport_write_attempts':len(connection.requests),'returned_success':True})
print(json.dumps({'installed_httplib2_version':httplib2.__version__,'transport_function_sha256':hashlib.sha256(inspect.getsource(httplib2.Http._conn_request).encode()).hexdigest(),'cases':results,'real_network_calls':0,'production_changes':False,'conclusion':'Application no-retry setting does not prevent installed lower-layer write replay'}))
