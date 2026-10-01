"""Exercise restored manager HTTP handlers with every worker path disabled.

Run only inside a no-network, read-only container with inputs mounted read-only.
No production credential, runtime socket, home, or service volume is mounted.
"""
import asyncio
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import time
from aiohttp import web, ClientSession

INPUT = Path('/audit')
SOURCE = INPUT / 'manager_source.py'
DATABASE = INPUT / 'manager-selected.db'
EXPECTED = json.loads((INPUT / 'input-hashes.json').read_text())

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def snapshots(path):
    c = sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True)
    try:
        return {table: [list(row) for row in c.execute('SELECT * FROM ' + table + ' ORDER BY rowid')]
                for table in ('projects', 'stages', 'events')}
    finally:
        c.close()

async def main():
    start = time.monotonic()
    assert sorted(p.name for p in Path('/sys/class/net').iterdir()) == ['lo']
    assert digest(SOURCE) == EXPECTED['source']
    assert digest(DATABASE) == EXPECTED['database']
    before = snapshots(DATABASE)
    attempts = []
    output = {'test': 'restored manager HTTP application, workers suppressed', 'starts': []}
    with tempfile.TemporaryDirectory(prefix='manager-restore-') as work:
        os.environ['VEGA_MANAGER_DATA'] = work
        shutil.copyfile(DATABASE, Path(work) / 'manager.db')
        spec = importlib.util.spec_from_file_location('restored_manager', SOURCE)
        manager = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(manager)
        assert manager.BASE == Path(work)
        assert not manager.TOKEN.exists()
        async def forbidden(*args, **kwargs):
            attempts.append('blocked external or worker operation')
            raise AssertionError('Workers, sends and task dispatch are forbidden in restoration')
        for name in ('http', 'send', 'process_messages', 'advance', 'follow_up', 'status_alerts', 'loop'):
            setattr(manager, name, forbidden)

        for iteration in range(2):
            manager.init()
            app = manager.app()
            # Retain unmodified HTTP handlers; intentionally do not restore worker lifecycle.
            app.cleanup_ctx.clear()
            runner = web.AppRunner(app, access_log=None)
            await runner.setup()
            site = web.TCPSite(runner, '127.0.0.1', 0)
            await site.start()
            port = site._server.sockets[0].getsockname()[1]
            try:
                async with ClientSession() as client:
                    async with client.get(f'http://127.0.0.1:{port}/health') as response:
                        assert response.status == 200
                        health = await response.json()
                    # A suppressed loop must NOT masquerade as operational health.
                    assert health['status'] == 'starting'
                    assert health['tick_age_seconds'] is None
                    async with client.get(f'http://127.0.0.1:{port}/projects') as response:
                        assert response.status == 200
                        projects = await response.json()
                    c = sqlite3.connect(Path(work) / 'manager.db')
                    c.row_factory = sqlite3.Row
                    expected = {r['id']: dict(r) for r in c.execute('SELECT * FROM projects')}
                    c.close()
                    assert len(projects) == len(expected)
                    assert {p['id'] for p in projects} == set(expected)
                    for project in projects:
                        for key in ('status', 'owner', 'report_hash', 'delivery'):
                            assert project[key] == expected[project['id']][key]
                        async with client.get(f'http://127.0.0.1:{port}/projects/' + project['id']) as response:
                            assert response.status == 200
                            detail = await response.json()
                        # Endpoint shape is verified explicitly; no assumption about wrappers.
                        record = detail.get('project', detail)
                        assert record['id'] == project['id']
                        assert record['status'] == project['status']
                        assert len(record['stages']) == sum(r[0] == project['id'] for r in before['stages'])
                assert snapshots(Path(work) / 'manager.db') == before
                assert not attempts
                output['starts'].append({'iteration': iteration + 1, 'http': 200,
                                         'projects': len(projects), 'retained_rows_unchanged': True,
                                         'health': 'starting (workers intentionally suppressed)'})
            finally:
                await runner.cleanup()
        output.update({'source_hash': digest(SOURCE), 'database_input_hash': digest(DATABASE),
                       'input_hashes_unchanged': digest(DATABASE) == EXPECTED['database'],
                       'row_counts': {k: len(v) for k, v in before.items()},
                       'interfaces': ['lo'], 'external_or_worker_attempts': len(attempts),
                       'elapsed_seconds': round(time.monotonic() - start, 3),
                       'limitations': 'selected operational tables only; no credentials, message recovery, worker execution, dispatch, sending, scheduling or production boot test'})
    print(json.dumps(output, indent=2))

asyncio.run(main())
