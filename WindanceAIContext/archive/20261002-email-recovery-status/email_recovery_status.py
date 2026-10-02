"""Read-only, content-free inspection. Does not reconcile, retry, or release holds."""
import argparse
import hashlib
import json
import sqlite3
import time
from pathlib import Path

TABLES = ('approvals', 'email_action_intents', 'email_approved_item_intents',
          'email_undo_intents', 'email_mailbox_admission')

def inspect(path, *, seconds=2.0, limit=20):
    if not 0.01 <= seconds <= 5 or type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError('Bounded inspection parameters required')
    deadline = time.monotonic() + seconds
    result = {'inspection': 'unknown', 'mutation_authorized': False,
              'worker_liveness': 'not_measured', 'provider_outcome': 'not_measured'}
    conn = None
    try:
        conn = sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro', uri=True,
                               timeout=min(seconds, 1.0))
        conn.execute('PRAGMA query_only=ON')
        conn.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
        conn.execute('BEGIN')
        present = {t for t in TABLES if conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone()}
        result['missing_tables'] = [t for t in TABLES if t not in present]
        counts = {}
        for table in TABLES[1:4]:
            if table in present:
                counts[table] = conn.execute('SELECT count(*) FROM '+table+
                    " WHERE state='unconfirmed'").fetchone()[0]
        slots = conn.execute('SELECT count(*) FROM email_mailbox_admission').fetchone()[0] if TABLES[4] in present else None
        result['unconfirmed_items'] = counts
        result['reservation_count'] = slots
        if 'approvals' in present:
            result['approval_counts'] = {state: conn.execute(
                "SELECT count(*) FROM approvals WHERE action LIKE 'gmail.%' AND status=?", (state,)).fetchone()[0]
                for state in ('pending', 'executing', 'uncertain')}
            # Hash identifiers; never export action payload, notes, IDs, or recipients.
            rows = conn.execute("SELECT id,status FROM approvals WHERE action LIKE 'gmail.%' AND status IN ('executing','uncertain') ORDER BY id LIMIT ?", (limit,)).fetchall()
            result['held_approval_references'] = [
                {'reference_sha256': hashlib.sha256(str(row[0]).encode()).hexdigest(),
                 'recorded_state': row[1]} for row in rows]
            result['references_truncated'] = sum(result['approval_counts'][s] for s in ('executing','uncertain')) > len(rows)
        result['recorded_mutation_hold'] = bool(slots or any(counts.values()))
        result['inspection'] = 'incomplete_schema' if result['missing_tables'] else 'complete'
        result['interpretation'] = 'Recorded state only. Executing does not prove a live worker. Absence of a recorded hold does not authorize retry or mutation.'
        return result
    except (sqlite3.Error, OSError, ValueError):
        # Partial results could look healthy; discard them on timeout/schema errors.
        return {'inspection': 'unknown', 'mutation_authorized': False,
                'reason': 'Read failed, schema unsupported, or bounded query interrupted.'}
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('database')
    args=parser.parse_args()
    report=inspect(args.database)
    print(json.dumps(report,sort_keys=True))
    raise SystemExit(0 if report['inspection']=='complete' else 2)
