"""Offline SDK compatibility and refresh replay bounds, with synthetic credentials."""
import datetime,json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from gmail_single_attempt_transport import GmailTransport,TransportUnconfirmed

results=[]
for mode in ('success','refresh_failure','api_401'):
    creds=Credentials(token='synthetic-expired',refresh_token='synthetic-refresh',
        token_uri='https://oauth2.googleapis.com/token',client_id='fixture',client_secret='fixture',
        expiry=datetime.datetime(2000,1,1))
    transport=GmailTransport(creds);calls=[]
    def exchange(url,method,body,headers,*,refresh=False):
        calls.append('refresh' if refresh else 'api')
        if refresh:
            if mode=='refresh_failure':return 503,{},b'{"error":"temporarily_unavailable"}'
            return 200,{},b'{"access_token":"synthetic-new","expires_in":3600,"token_type":"Bearer"}'
        if mode=='api_401':return 401,{},b'PRIVATE_SENTINEL'
        return 200,{'content-type':'application/json'},b'{"id":"fixture-draft"}'
    transport._exchange=exchange
    try:
        service=build('gmail','v1',http=transport,cache_discovery=False,static_discovery=True)
        assert calls==[], 'Discovery performed network activity'
        error=None
        try:
            result=service.users().drafts().create(userId='me',body={'message':{'raw':'Zml4dHVyZQ=='}}).execute(num_retries=0)
        except Exception as exc:
            error=type(exc).__name__;assert 'PRIVATE_SENTINEL' not in str(exc)
        assert calls==(['refresh'] if mode=='refresh_failure' else ['refresh','api']),calls
        assert (error is None)==(mode=='success')
        if error is None:assert result=={'id':'fixture-draft'}
        results.append({'scenario':mode,'exchanges':calls,'error':error})
    finally:transport.close()
print(json.dumps({'cases':results,'network_calls':0,'static_discovery':True,'limits':'Injected exchange only; loopback transport is tested separately. No live credentials or Harness integration.'}))
