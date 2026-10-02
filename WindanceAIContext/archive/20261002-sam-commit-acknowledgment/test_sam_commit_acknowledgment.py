"""Installed SAM commit function with synthetic schedule and intercepted all effects."""
import ast,hashlib,io,json,sqlite3,tempfile,urllib.request
from types import SimpleNamespace
from pathlib import Path
from typing import Any

path=Path('/home/williamschilling/services/sam-schedule/sam_schedule.py')
source=path.read_text();node=next(n for n in ast.parse(source).body if getattr(n,'name','')=='commit_day')
original=ast.get_source_segment(source,node)
helper=ast.get_source_segment(source,next(n for n in ast.parse(source).body if getattr(n,'name','')=='json_http'))
anchor='    result = json_http("POST", f"{HERALD_BASE}/memory", memory_payload, timeout=45)'
assert original.count(anchor)==1
candidate=original.replace(anchor,anchor+'\n    if not isinstance(result, dict) or result.get("status") != "ok":\n        raise RuntimeError("Memory acknowledgment did not confirm success; local day remains uncommitted")')
outcomes=[]
for version,code in [('installed',original),('candidate',candidate)]:
    for scenario in ['ok','provider_error','malformed','transport_failure','already_committed']:
        with tempfile.TemporaryDirectory(prefix='sam-commit-ack-') as directory:
            database=Path(directory)/'fixture.db';calls=[]
            def connect():return sqlite3.connect(database)
            with connect() as c:
                c.execute('CREATE TABLE schedule_days(date TEXT PRIMARY KEY,committed INTEGER,last_committed TEXT,commit_result TEXT)')
                c.execute('INSERT INTO schedule_days(date,committed) VALUES(?,?)',('2099-01-01',int(scenario=='already_committed')))
            def schedule(date):
                with connect() as c:committed=c.execute('SELECT committed FROM schedule_days').fetchone()[0]
                return {'date':'2099-01-01','day_name':'fixture-day','day':{'committed':committed},'items':[]}
            def http(request,timeout):
                payload=json.loads(request.data)
                assert request.method=='POST' and request.full_url=='http://fixture.invalid/memory' and payload['kind']=='sam_daily_schedule'
                calls.append('memory')
                if scenario=='transport_failure':raise OSError('fixture transport failure')
                body={'status':'error'} if scenario=='provider_error' else ['invalid'] if scenario=='malformed' else {'status':'ok'}
                return io.BytesIO(json.dumps(body).encode())
            namespace={'Any':Any,'get_schedule':schedule,'connect':connect,'json':json,'HERALD_BASE':'http://fixture.invalid',
                'urllib':SimpleNamespace(request=SimpleNamespace(Request=urllib.request.Request,urlopen=http)),
                'now_iso':lambda:'fixture-time','log_event':lambda *a,**k:calls.append('log'),
                'rollover_unfinished_training':lambda *a:{'enabled':False},
                'post_completed_service_history':lambda *a:{'errors':[],'posted':[]}}
            exec(compile(helper+'\n\n'+code,'<isolated-commit-day>','exec'),namespace)
            failed=False
            try:namespace['commit_day']('2099-01-01')
            except (RuntimeError,OSError):failed=True
            with connect() as c:committed=c.execute('SELECT committed FROM schedule_days').fetchone()[0]
            expected=(scenario in ['ok','already_committed'] or version=='installed' and scenario in ['provider_error','malformed'])
            assert committed==int(expected)
            if scenario=='already_committed':assert calls==[]
            if version=='candidate' and scenario in ['provider_error','malformed','transport_failure']:
                assert failed and 'log' not in calls
            outcomes.append({'version':version,'scenario':scenario,'committed':bool(committed),'raised':failed})
print(json.dumps({'installed_source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'cases':outcomes,
 'candidate_function_sha256':hashlib.sha256(candidate.encode()).hexdigest(),
 'installed_json_http_helper_used':True,'production_changes':False,'actual_api_calls':0,'odoo_calls':0,'schedule_data_used':'synthetic empty day only'}))
