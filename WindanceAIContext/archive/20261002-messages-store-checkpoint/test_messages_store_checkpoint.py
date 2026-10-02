from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from messages_store_checkpoint import checkpoint,same_checkpoint


def make(path):
    with closing(sqlite3.connect(path)) as c:
        c.execute('CREATE TABLE message(guid TEXT,text TEXT)')
        c.executemany('INSERT INTO message VALUES(?,?)',[('synthetic-guid-1','PRIVATE_BODY'),('synthetic-guid-2','PRIVATE_BODY')])
        c.commit()


checks=[]
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)/'messages.db';make(path)
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    saved=checkpoint(path)
    assert saved['status']=='captured' and saved['boundary']==2
    assert same_checkpoint(saved,checkpoint(path,2))
    assert before==hashlib.sha256(path.read_bytes()).hexdigest()
    assert 'PRIVATE_BODY' not in json.dumps(saved) and 'synthetic-guid' not in json.dumps(saved)
    checks.append('readonly_exact_anchor_private_safe')
    with closing(sqlite3.connect(path)) as c:
        c.execute("INSERT INTO message VALUES('synthetic-guid-3','PRIVATE_BODY')");c.commit()
    assert same_checkpoint(saved,checkpoint(path,2))
    checks.append('normal_append_preserves_anchor')
    with closing(sqlite3.connect(path)) as c:
        c.execute("UPDATE message SET guid='changed-guid' WHERE ROWID=2");c.commit()
    assert not same_checkpoint(saved,checkpoint(path,2))
    checks.append('same_inode_anchor_replacement_rejected')
    replacement=Path(tmp)/'replacement.db';make(replacement)
    os.replace(replacement,path)
    assert not same_checkpoint(saved,checkpoint(path,2))
    checks.append('file_replacement_rejected')
    new=checkpoint(path)
    with closing(sqlite3.connect(path)) as c:
        c.execute('DELETE FROM message WHERE ROWID=2');c.commit()
    assert not same_checkpoint(new,checkpoint(path,2))
    checks.append('missing_anchor_rejected')
    with closing(sqlite3.connect(path)) as c:
        c.execute('DELETE FROM message');c.commit()
    assert checkpoint(path)['reason']=='empty_store'
    absent=Path(tmp)/'absent.db'
    assert checkpoint(absent)['status']=='unavailable' and not absent.exists()
    for bad in (True,0,-1,2**63):assert checkpoint(path,bad)['reason']=='invalid_anchor'
    checks.append('empty_missing_invalid_hold')
print(json.dumps({'status':'passed','checks':checks,'messages_read':'synthetic_only','writes_to_live_store':0}))
