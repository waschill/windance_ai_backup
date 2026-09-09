"""Refresh only published Windance context; retain unrelated index records."""
import importlib.util
import json
from pathlib import Path
import sys

SERVICE = Path(r'C:\Users\wasch\services\second-brain')
SOURCE = Path(r'P:\Business\Networksetup\WindanceAIContext')


def refresh(indexer, conn, source, business_root):
    if not source.is_dir():
        raise RuntimeError('Published context folder is unavailable')
    paths = sorted(p for p in source.rglob('*') if p.is_file() and indexer.allowed(p))
    if not paths:
        raise RuntimeError('No eligible context files found')
    changed = 0
    for path in paths:
        # One transaction per document: failed embeddings must preserve the old record.
        with conn:
            existing = conn.execute('SELECT id,sha256 FROM source_files WHERE path=?', (str(path),)).fetchone()
            if existing:
                counts = conn.execute('SELECT count(*),count(embedding_json) FROM document_chunks WHERE source_file_id=?',(existing['id'],)).fetchone()
                if not counts[0] or counts[0] != counts[1] or existing['sha256'] != indexer.sha256_file(path):
                    conn.execute('UPDATE source_files SET modified_ns=-1 WHERE id=?',(existing['id'],))
            updated, outcome = indexer.upsert_file(conn, business_root, path, True)
            if outcome not in ('indexed','unchanged'):
                raise RuntimeError(f'Context extraction failed for {path.name}: {outcome}')
            row = conn.execute('SELECT * FROM source_files WHERE path=?',(str(path),)).fetchone()
            count = conn.execute('SELECT count(*),count(embedding_json) FROM document_chunks WHERE source_file_id=?',(row['id'],)).fetchone()
            fts = conn.execute('SELECT count(*) FROM document_fts WHERE path=?',(str(path),)).fetchone()[0]
            if row['sha256'] != indexer.sha256_file(path) or row['deleted_at'] or row['error'] or not count[0] or count[0] != count[1] or fts != count[0]:
                raise RuntimeError(f'Index verification failed for {path.name}')
            changed += int(updated)
    return {'verified_files':len(paths),'changed_files':changed,'unrelated_records_removed':0}


def main():
    sys.path.insert(0,str(SERVICE/'venv/Lib/site-packages'))
    spec=importlib.util.spec_from_file_location('windance_second_brain', SERVICE/'second_brain.py')
    indexer=importlib.util.module_from_spec(spec);spec.loader.exec_module(indexer)
    conn=indexer.connect(indexer.DEFAULT_DB)
    try:
        receipt=refresh(indexer,conn,SOURCE,Path(r'P:\Business'))
        # A real retrieval call must find the standing policy, not just a catalog row.
        results=indexer.query(conn,'SECOND_BRAIN_CHANGE_RECORDING',6)
        if not any(Path(row['path']).name=='SECOND_BRAIN_CHANGE_RECORDING.md' for row in results):
            raise RuntimeError('The standing change-recording policy was not retrieved')
        indexer.backup_database(conn,Path(r'P:\Business\Networksetup\SecondBrain\second_brain.sqlite'))
        receipt.update({'policy_retrieval':'verified','shared_database_backup':'updated','verified_at':indexer.utc_now()})
        output=SERVICE/'logs/context-publication-latest.json'
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
        print(json.dumps(receipt))
    finally:
        conn.close()


if __name__=='__main__':main()
