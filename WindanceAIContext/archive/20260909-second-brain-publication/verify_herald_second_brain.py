import json
import urllib.parse
import urllib.request

checks=[('SECOND_BRAIN_CHANGE_RECORDING','SECOND_BRAIN_CHANGE_RECORDING.md'),
        ('TASK_CONTINUITY_AND_GOALS_2026-09-09','TASK_CONTINUITY_AND_GOALS_2026-09-09.md')]
for query,expected in checks:
    url='http://127.0.0.1:8791/second-brain/search?'+urllib.parse.urlencode({'q':query,'limit':3})
    with urllib.request.urlopen(url,timeout=90) as response: result=json.load(response)
    answer=result.get('answer','')
    assert expected in answer, 'Herald failed to retrieve '+expected
    print(json.dumps({'query':query,'retrieved':expected,'through':'Herald -> HAL Second Brain','status':'PASS'}),flush=True)
