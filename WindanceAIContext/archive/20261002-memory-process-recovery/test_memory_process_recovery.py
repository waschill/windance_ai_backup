"""Disposable real-process crash/reopen and cold restore; synthetic facts only."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import owned_fact_store as store
from memory_ingress_policy import Policy,Resolver
from source_fact_gateway import apply_fact_request


def resolver():
    return Resolver([Policy('fixture','fixture-token',frozenset(
        ('william','fixture','business',op) for op in ['write','delete','read','share']))])


def request(c):
    return apply_fact_request(resolver(),c,'Bearer fixture-token',event_id='stable-request',owner='william',
       channel='fixture',scope='business',kind='fact',key='same',value='original fixture',expected_revision=0)


def child(path,mode):
    class CrashConnection(sqlite3.Connection):
        def commit(self):
            if mode=='before-commit':os._exit(73)
            super().commit()
            if mode=='after-commit':os._exit(74)
    c=sqlite3.connect(path,factory=CrashConnection)
    if mode=='inspect':
        print(json.dumps({'visible':store.visible_facts(c,'william',scopes=('business',)),
                         'other_visible':store.visible_facts(c,'shawn',scopes=('business',)),
                         'integrity':c.execute('PRAGMA integrity_check').fetchone()[0]}))
    else:print(json.dumps(request(c)))
    c.close()


def main():
    outcomes=[]
    with tempfile.TemporaryDirectory(prefix='windance-memory-recovery-') as directory:
        root=Path(directory)
        def run(path,mode):
            return subprocess.run([sys.executable,str(Path(__file__).resolve()),str(path),mode],
                                  capture_output=True,text=True,timeout=20)
        for crash,expected_exit,expected_rows in [('before-commit',73,0),('after-commit',74,1)]:
            path=root/(crash+'.db');c=sqlite3.connect(path);store.install(c);c.close()
            result=run(path,crash);assert result.returncode==expected_exit,(crash,result.stderr)
            c=sqlite3.connect(path)
            assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            assert c.execute('SELECT count(*) FROM owned_facts').fetchone()[0]==expected_rows
            assert c.execute('SELECT count(*) FROM owned_fact_requests').fetchone()[0]==expected_rows
            c.close()
            result=run(path,'retry');assert result.returncode==0,result.stderr
            receipt=json.loads(result.stdout);assert receipt['revision']==1 and receipt['replayed']==bool(expected_rows)
            outcomes.append({'scenario':crash,'actual_child_exit':expected_exit,'retry_revision':1,'passed':True})
        # Correct/revoke in one process; inspect from an entirely fresh process.
        path=root/'after-commit.db';c=sqlite3.connect(path)
        store.share(c,'william','william','business','fact','same','shawn',1)
        store.write(c,'william','william','business','fact','same','corrected fixture','fixture:correction',1)
        store.install(c) # Repeated install must not clear records or access history.
        c.close()
        result=run(path,'inspect');assert result.returncode==0,result.stderr
        actual=json.loads(result.stdout)
        assert actual['integrity']=='ok' and actual['other_visible']==[]
        assert [f['value'] for f in actual['visible']]==['corrected fixture']
        # SQLite backup, closed cold copy, separate interpreter read and replay.
        backup=root/'cold-restored.db';source=sqlite3.connect(path);target=sqlite3.connect(backup)
        source.backup(target);target.close();source.close()
        result=run(backup,'inspect');assert result.returncode==0,result.stderr
        assert json.loads(result.stdout)==actual
        result=run(backup,'retry');assert result.returncode==0,result.stderr
        assert json.loads(result.stdout)['superseded'] is True
        c=sqlite3.connect(backup)
        assert c.execute('SELECT count(*) FROM owned_fact_events').fetchone()[0]==2
        assert c.execute('SELECT count(*) FROM owned_fact_grants').fetchone()[0]==0
        assert [r[0] for r in c.execute('SELECT action FROM owned_fact_grant_events ORDER BY event_id')]==['grant','invalidate']
        c.close()
        outcomes.append({'scenario':'fresh-process-and-cold-restore','corrected_value_preserved':True,
                         'revoked_grant_preserved':True,'old_request_cannot_resurrect':True,'passed':True})
    print(json.dumps({'scenarios':outcomes,'production_writes':0,'model_calls':0,'real_sends':0,
      'limits':'Current consistent synthetic snapshot only; restoring an older backup still requires post-backup reconciliation.'},indent=2))


if __name__=='__main__':
    if len(sys.argv)==3:child(Path(sys.argv[1]),sys.argv[2])
    else:main()
