"""Three local GET status probes; response content is neither read nor stored."""
import datetime,json,urllib.request,urllib.error
results=[]
for path,headers in [('/health',{}),('/team',{}),('/team',{'X-Forwarded-For':'198.51.100.123'})]:
    req=urllib.request.Request('http://127.0.0.1:8791'+path,headers=headers,method='GET')
    try:
        with urllib.request.urlopen(req,timeout=8) as r: status=r.status
    except urllib.error.HTTPError as e:
        status=e.code;e.close()
    results.append({'path':path,'synthetic_forwarded_header':bool(headers),'status':status})
print(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'results':results,'response_content_read':False,'limits':'Trusted loopback only; does not test external reachability or other proxy hops.'},indent=2))
