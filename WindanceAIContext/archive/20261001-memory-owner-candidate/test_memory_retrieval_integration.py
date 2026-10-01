"""AST-extracted candidate retrieval with actual candidate ownership helpers."""
import ast
import contextlib
import json
from pathlib import Path
import re
import sqlite3
import sys
from types import SimpleNamespace
from typing import Any

ROOT=Path('/Users/herald/services/memory-owner-boundary-20261001')
sys.path.insert(0,str(ROOT))
from email_owner_boundary import bind_mailbox_owner,current_request_owner
from memory_owner_boundary import owned_memory_rows
from test_memory_owner_candidate import MemoryOwnerTests
fixture=MemoryOwnerTests();fixture.setUp()
try:
    fixture.conversation('w','William',text='synthetic william')
    fixture.conversation('s','Shawn',text='synthetic shawn',derived='William: synthetic shawn\n\nHerald: answer')
    c=fixture.c
    c.execute('insert into vector_memory values (?,?,?,?,?,?,?,?)',('unscoped','memory','unscoped','synthetic legacy','PRIVATE_UNCLASSIFIED_SENTINEL','[1,0]','synthetic','2027'))
    @contextlib.contextmanager
    def db():yield c
    source=(ROOT/'agent_harness.py').read_text();tree=ast.parse(source)
    names={'vector_recall','relevant_memory_text','memories_text'}
    ns={'Any':Any,'sqlite3':sqlite3,'re':re,'json':json,'db':db,
        'owned_memory_rows':owned_memory_rows,'current_request_owner':current_request_owner,
        'cosine_similarity':lambda a,b:1.0,'embedding_vector':lambda q:(None,'synthetic'),
        'second_brain_natural_language_intent':lambda q:False,'audit':lambda *a:None}
    code=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[])
    exec(compile(code,'<candidate-retrieval>','exec'),ns)
    results=[]
    for mode in ['semantic','lexical']:
        ns['embedding_vector']=lambda q,mode=mode:([1,0] if mode=='semantic' else None,'synthetic')
        for owner,identifier,other in [('William','w','s'),('Shawn','s','w')]:
            @bind_mailbox_owner
            def query(payload):return ns['vector_recall']('synthetic')
            r=query(SimpleNamespace(user=owner))
            assert [x['source_id'] for x in r['items']]==[identifier],(mode,owner,r)
            assert r['items'][0]['source_owner']==owner
            assert 'PRIVATE_UNCLASSIFIED_SENTINEL' not in json.dumps(r)
            assert r['items'][0]['text'].startswith(owner+':')
            results.append({'mode':mode,'owner':owner,'only_own_source':True})
    assert ns['vector_recall']('synthetic')['fallback']=='verified_owner_required'
    assert ns['memories_text']()==''
    # Empty search and embedding failure can fall back only to owned source rows.
    for failure in [False,True]:
        def embedding(q):
            if failure:raise RuntimeError('synthetic unavailable')
            return None,'synthetic'
        ns['embedding_vector']=embedding
        @bind_mailbox_owner
        def fallback(payload):return ns['relevant_memory_text']('absentkeyword')
        text=fallback(SimpleNamespace(user='Shawn'))
        assert 'synthetic shawn' in text and 'synthetic william' not in text and 'PRIVATE_UNCLASSIFIED_SENTINEL' not in text
    # Source correction propagates without reindex or returning stale vector text.
    c.execute("update conversations set message='corrected current phrase' where id='s'")
    ns['embedding_vector']=lambda q:([1,0],'synthetic')
    @bind_mailbox_owner
    def corrected(payload):return ns['vector_recall']('corrected')
    r=corrected(SimpleNamespace(user='Shawn'))
    assert len(r['items'])==1 and 'corrected current phrase' in r['items'][0]['text'] and 'synthetic shawn' not in r['items'][0]['text']
    print(json.dumps({'owner_mode_cases':results,'missing_scope_withheld':True,'empty_and_error_fallbacks_owner_scoped':True,'source_correction_propagates_without_reindex':True,'legacy_unclassified_withheld':True,'real_embeddings':0,'production_modified':False}))
finally:fixture.tearDown()
