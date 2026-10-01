"""Current retrieval functions against synthetic owner-labelled fixtures only."""
import ast
import contextlib
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
from typing import Any

sys.path.insert(0,'/Users/herald/services/agent-harness')
from email_owner_boundary import bind_mailbox_owner
source=Path('/Users/herald/services/agent-harness/agent_harness.py').read_text()
tree=ast.parse(source)
names={'vector_recall','relevant_memory_text'}
with tempfile.TemporaryDirectory(prefix='windance-memory-boundary-') as temp:
    database=Path(temp)/'memory.db'
    c=sqlite3.connect(str(database));c.executescript('''
    CREATE TABLE vector_memory(id TEXT,source_type TEXT,source_id TEXT,title TEXT,text TEXT,embedding_json TEXT,embedding_model TEXT,updated_at TEXT);
    CREATE TABLE conversations(id TEXT,user TEXT);
    ''')
    for owner in ['William','Shawn']:
        c.execute('insert into conversations values (?,?)',(owner,owner))
        c.execute('insert into vector_memory values (?,?,?,?,?,?,?,?)',('conversation:'+owner,'conversation',owner,'synthetic '+owner,'synthetic private '+owner,'[1.0,0.0]','synthetic','2026-10-01T00:00:00+00:00'))
    c.commit();c.close()
    @contextlib.contextmanager
    def db():
        connection=sqlite3.connect(str(database));connection.row_factory=sqlite3.Row
        try:yield connection
        finally:connection.close()
    ns={'Any':Any,'db':db,'sqlite3':sqlite3,'json':json,'re':re,'cosine_similarity':lambda a,b:1.0,
        'embedding_vector':lambda text:(None,'synthetic'),'second_brain_natural_language_intent':lambda q:False,
        'audit':lambda *a:None,'memories_text':lambda **kw:'synthetic unscoped fallback'}
    code=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
    exec(compile(code,'<current-retrieval-functions>','exec'),ns)
    results=[]
    for mode in ['lexical','semantic']:
        ns['embedding_vector']=lambda text,mode=mode:([1.0,0.0] if mode=='semantic' else None,'synthetic')
        for owner in ['William','Shawn']:
            @bind_mailbox_owner
            def probe(payload):return ns['vector_recall']('synthetic',8)
            result=probe(SimpleNamespace(user=owner))
            other='Shawn' if owner=='William' else 'William'
            results.append({'mode':mode,'owner':owner,'own_fixture_returned':any(x['source_id']==owner for x in result['items']),'other_owner_fixture_returned':any(x['source_id']==other for x in result['items'])})
    ns['vector_recall']=lambda *a,**kw:{'items':[]}
    @bind_mailbox_owner
    def fallback(payload):return ns['relevant_memory_text']('synthetic')
    fallback_unscoped=fallback(SimpleNamespace(user='Shawn'))=='synthetic unscoped fallback'
    assert all(x['other_owner_fixture_returned'] for x in results)
    assert fallback_unscoped
    print(json.dumps({'cases':results,'unscoped_fallback_reached':True,'private_production_records_read':False,'real_embedding_calls':0,'production_modified':False}))

