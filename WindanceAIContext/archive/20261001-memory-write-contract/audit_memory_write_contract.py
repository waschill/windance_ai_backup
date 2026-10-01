"""Read source only; execute extracted writer against disposable SQLite."""
import ast
import contextlib
import hashlib
import json
import pathlib
import sqlite3
import tempfile

p = pathlib.Path('/Users/herald/services/agent-harness/agent_harness.py')
source = p.read_text()
tree = ast.parse(source)
functions = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
writers = []
for name, node in functions.items():
    if any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == 'upsert_memory' for x in ast.walk(node)):
        writers.append(name)
with tempfile.TemporaryDirectory(prefix='windance-memory-contract-') as directory:
    database = pathlib.Path(directory) / 'fixture.db'
    @contextlib.contextmanager
    def db():
        connection = sqlite3.connect(database)
        try:
            yield connection
        finally:
            connection.close()
    with db() as connection:
        connection.execute('CREATE TABLE memories(kind TEXT,key TEXT,value TEXT,confidence REAL,source TEXT,created_at TEXT,updated_at TEXT,UNIQUE(kind,key))')
    vectors = []
    namespace = {'db': db, 'now': lambda: 'synthetic-time', 'audit': lambda *args: None,
                 'upsert_vector_memory': lambda *args: vectors.append(args)}
    exec(compile(ast.Module(body=[functions['upsert_memory']], type_ignores=[]), '<actual-writer>', 'exec'), namespace)
    namespace['upsert_memory']('preference', 'same-key', 'synthetic-owner-a', source='message:william')
    namespace['upsert_memory']('preference', 'same-key', 'synthetic-owner-b', source='message:shawn')
    with db() as connection:
        rows = connection.execute('SELECT value,source FROM memories').fetchall()
    collision = rows == [('synthetic-owner-b', 'message:shawn')]
    assert collision and len(vectors) == 2 and vectors[0][1] == vectors[1][1]
    print(json.dumps({'live_source_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
        'callers': sorted(writers), 'cross_owner_key_overwrite_reproduced': collision,
        'vector_source_id_collision_reproduced': True,
        'fixture_only': True, 'production_writes': 0, 'model_calls': 0,
        'limits': 'Caller source strings do not establish authentication or access grants. No historical disclosure established.'}, indent=2))

