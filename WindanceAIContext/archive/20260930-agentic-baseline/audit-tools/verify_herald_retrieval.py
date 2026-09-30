import json,urllib.parse,urllib.request,time
out={'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'checks':[]}
for kind in ['BASELINE','DEPENDENCIES','RECOVERY','PILOTS','COSTS']:
 name=f'AGENTIC_STACK_{kind}_2026-09-30.md';url='http://127.0.0.1:8791/second-brain/search?'+urllib.parse.urlencode({'q':name[:-3],'limit':5})
 with urllib.request.urlopen(url,timeout=55) as response:j=json.load(response)
 found=name in j.get('answer','');out['checks'].append({'file':name,'retrieved':found,'through':'HERALD -> HAL Second Brain'});assert found,name
print(json.dumps(out,indent=2))
