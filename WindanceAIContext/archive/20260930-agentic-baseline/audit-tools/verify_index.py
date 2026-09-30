import json,pathlib,hashlib,sqlite3,importlib.util,sys,time
S=pathlib.Path(r'C:\Users\wasch\services\second-brain');sys.path.insert(0,str(S/'venv/Lib/site-packages'))
spec=importlib.util.spec_from_file_location('baseline_indexer',S/'second_brain.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
c=m.connect(m.DEFAULT_DB);out={'at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'checks':[]}
for kind in ['BASELINE','DEPENDENCIES','RECOVERY','PILOTS','COSTS']:
 name=f'AGENTIC_STACK_{kind}_2026-09-30.md';p=pathlib.Path(r'P:\Business\Networksetup\WindanceAIContext\projects')/name
 row=c.execute('select id,sha256,error,deleted_at from source_files where path=?',(str(p),)).fetchone();assert row is not None
 count=c.execute('select count(*),count(embedding_json) from document_chunks where source_file_id=?',(row['id'],)).fetchone()
 result=m.query(c,p.stem,8)
 check={'file':name,'source_hash_matches':row['sha256']==hashlib.sha256(p.read_bytes()).hexdigest(),'chunks':count[0],'embedded_chunks':count[1],'retrieved':any(pathlib.Path(r['path']).name==name for r in result),'error':row['error'],'deleted':bool(row['deleted_at'])}
 assert check['source_hash_matches'] and count[0]>0 and count[0]==count[1] and check['retrieved'] and not check['error'] and not check['deleted'],name
 out['checks'].append(check)
c.close();print(json.dumps(out,indent=2))
