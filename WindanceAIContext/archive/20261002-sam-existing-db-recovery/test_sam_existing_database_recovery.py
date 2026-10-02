"""Private online backup and isolated actual-schema migration; never run main."""
import ast, datetime, hashlib, json, os, shutil, sqlite3
from contextlib import closing
from pathlib import Path
os.umask(0o077)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
root=Path('/home/williamschilling/backups')/('sam-existing-db-recovery-'+stamp)
root.mkdir(mode=0o700)
live=Path('/home/williamschilling/services/sam-schedule/sam_schedule.py')
candidate=Path('/home/williamschilling/backups/sam-reliability-candidate-20261002/sam_schedule.candidate.private.py')
assert hashlib.sha256(live.read_bytes()).hexdigest()=='824026967ab935b2563f0a77021668754fa5969f704e17e3619137a455643bc1'
assert hashlib.sha256(candidate.read_bytes()).hexdigest()=='148adcb085f0e51264b3b1d5d811f5d34c2ce8fba5a934b8a27b9c97156ee8a5'
for src,name in [(live,'sam_schedule.original.private.py'),(candidate,'sam_schedule.candidate.private.py'),(Path('/tmp/sam_history_intent.py'),'sam_history_intent.py')]:
    shutil.copyfile(src,root/name)
db=Path('/home/williamschilling/.local/share/sam-schedule/sam_schedule.db')
with closing(sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)) as src, closing(sqlite3.connect(root/'snapshot.private.db')) as dst:
    src.backup(dst,pages=128,sleep=0.05)
def digest(path):
    with closing(sqlite3.connect(path)) as c:
        assert c.execute('PRAGMA integrity_check').fetchone()==('ok',)
        result={}
        for (name,sql) in c.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"):
            q='"'+name.replace('"','""')+'"'
            rows=sorted(repr(tuple(r)) for r in c.execute('SELECT * FROM '+q))
            result[name]=(sql,len(rows),hashlib.sha256('\n'.join(rows).encode()).hexdigest())
        return result
before=digest(root/'snapshot.private.db')
assert 'sam_history_intents' not in before
for variant,source in [('baseline',live),('candidate',candidate)]:
    target=root/(variant+'.private.db');shutil.copyfile(root/'snapshot.private.db',target)
    tree=ast.parse(source.read_text())
    defaults=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DEFAULT_TRAINERS' for t in n.targets)]
    assert len(defaults)==1
    ns={'sqlite3':sqlite3,'DATA_DIR':root,'DB_PATH':target,'DEFAULT_TRAINERS':ast.literal_eval(defaults[0].value),'now_iso':lambda:'2099-01-01T00:00:00'}
    nodes=[n for n in tree.body if getattr(n,'name','') in {'connect','init_db'}]
    assert len(nodes)==2
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<schema-only>','exec'),ns)
    ns['init_db']();first=digest(target);ns['init_db']();assert digest(target)==first
baseline=digest(root/'baseline.private.db');after=digest(root/'candidate.private.db')
assert set(after)==set(baseline)|{'sam_history_intents'}
assert all(after[k]==baseline[k] for k in baseline)
assert after['sam_history_intents'][1]==0
assert baseline==before, 'Existing startup would change records; inspect privately before proceeding'
shutil.copyfile(root/'candidate.private.db',root/'cold-restored.private.db')
assert digest(root/'cold-restored.private.db')==after
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.iterdir()) if p.is_file()}
(root/'private-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'backup_directory':str(root),'verified_at':stamp,'existing_tables_preserved':len(before),'candidate_added_empty_intent_table':True,'repeated_initialization_preserved':True,'cold_restore_integrity_and_all_tables_match':True,'files_sha256':manifest,'live_db_opened_read_only':True,'production_changes':False,'api_calls':0,'limits':'Schema functions only; no main, scheduler, listener, remote reconciliation or need-clear concurrency test'}))
