"""Operational-queue boundary; private Claude reviews use their own session lane."""
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path

PRIVATE_NAMES = ('vega', 'claude', 'codex')
PRIVATE_SQL = ','.join(repr(n) for n in PRIVATE_NAMES)
TERMINAL = ('done','completed','cancelled','archived','failed','partial')


def install_guards(conn, table):
    if table not in {'tasks', 'staff_tasks'}:
        raise ValueError('Unexpected operational ledger')
    for action in ['insert', 'update']:
        name=f'windance_private_reviewer_{action}'
        conn.execute(f'DROP TRIGGER IF EXISTS {name}')
        event='INSERT' if action=='insert' else 'UPDATE OF assignee, status'
        history='' if action=='insert' else " AND NEW.status NOT IN ('done','completed','cancelled','archived','failed','partial')"
        conn.execute(f'''CREATE TRIGGER {name} BEFORE {event} ON {table}
            WHEN lower(trim(NEW.assignee)) IN ({PRIVATE_SQL}){history}
            BEGIN SELECT RAISE(ABORT, 'Private reviewer Claude is not an operational assignee; use Forge. Vega is Codex, not a Hermes worker.'); END''')


def migrate(stage, ledgers=None):
    receipts=[]
    for db, table in (ledgers or [('/Users/herald/.hermes/kanban.db','tasks'),
                      ('/Users/herald/.local/share/agent-harness/harness.db','staff_tasks')]):
        conn=sqlite3.connect(db,timeout=30)
        conn.row_factory=sqlite3.Row
        live=conn.execute(f"SELECT id,status FROM {table} WHERE lower(trim(assignee)) IN ({PRIVATE_SQL}) AND status NOT IN ('triage','blocked','done','completed','cancelled','archived','failed','partial')").fetchall()
        if live:
            raise RuntimeError('Private reviewer still has runnable work; inspect before migration: '+str([dict(r) for r in live]))
        backup=stage/'backup'/(table+'-before-private-review-'+str(time.time_ns())+'.db')
        backup.parent.mkdir(parents=True,exist_ok=True)
        with closing(sqlite3.connect(backup)) as dst: conn.backup(dst)
        backup.chmod(0o600)
        with conn:
            rows=conn.execute(f"SELECT id,status FROM {table} WHERE lower(trim(assignee)) IN ({PRIVATE_SQL}) AND status IN ('triage','blocked')").fetchall()
            for row in rows:
                conn.execute(f'UPDATE {table} SET assignee=? WHERE id=?',('forge' if table=='tasks' else 'Forge',row['id']))
                if table=='tasks':
                    note='William reassigned operational technical ownership to Forge on 2026-09-17. Status preserved; no task replayed. Former Hermes Vega is now private reviewer Claude, reporting to Vega (Codex).'
                    conn.execute('INSERT INTO task_comments(task_id,author,body,created_at) VALUES (?,?,?,?)',(row['id'],'Vega / Codex',note,int(time.time())))
                    conn.execute('INSERT INTO task_events(task_id,kind,payload,created_at) VALUES (?,?,?,?)',(row['id'],'assignee_changed',json.dumps({'from':'vega','to':'forge','reason':'William-directed private reviewer separation'}),int(time.time())))
            install_guards(conn,table)
        receipts.append({'ledger':table,'reassigned_without_replay':[dict(r) for r in rows],'private_assignment_guards':'installed'})
        conn.close()
    (stage/'queue-migration-receipt.json').write_text(json.dumps(receipts,indent=2))
    (stage/'queue-migration-receipt.json').chmod(0o600)
    print(json.dumps(receipts))
    return receipts


if __name__=='__main__': migrate(Path(__file__).resolve().parent)
