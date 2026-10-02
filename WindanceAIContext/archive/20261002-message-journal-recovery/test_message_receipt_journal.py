"""Disposable journal tests, concurrency and cold restoration; no sender."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
from message_receipt_journal import Journal

checks=[]
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)/'receipt.db'
    j=Journal(path,create=True)
    assert j.register('r1','synthetic-owner',['private chunk 1','private chunk 2'])=='registered'
    assert j.register('r1','synthetic-owner',['private chunk 1','private chunk 2'])=='existing'
    try:j.register('r1','other',['private chunk 1','private chunk 2'])
    except ValueError as e:assert str(e)=='request_content_conflict'
    else:raise AssertionError('content conflict accepted')
    checks.append('idempotent_registration_and_content_conflict')
    assert j.begin('r1',1,'store-a',10)=='held_prior_chunk'
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes=list(pool.map(lambda _:Journal(path).begin('r1',0,'store-a',10),range(2)))
    assert sorted(outcomes)==['attempt_committed','held_existing_attempt']
    assert Journal(path).begin('r1',0,'store-a',10)=='held_existing_attempt'
    checks.append('single_concurrent_attempt_and_reopen_no_repeat')
    j.submitted('r1',0)
    assert j.begin('r1',0,'store-a',12)=='held_existing_attempt'
    receipt=lambda n:{'status':'delivered','evidence':'local_messages_flags','message_rowid':n}
    assert j.confirm('r1',0,'store-a',{'ok':True})=='held_unverified'
    assert j.confirm('r1',0,'other-store',receipt(11))=='held_correlation_mismatch'
    assert j.confirm('r1',0,'store-a',receipt(10))=='held_correlation_mismatch'
    assert j.confirm('r1',0,'store-a',receipt(11))=='receipt_committed'
    assert j.confirm('r1',0,'store-a',receipt(11))=='existing_receipt'
    assert j.confirm('r1',0,'store-a',receipt(12))=='held_receipt_conflict'
    assert j.status('r1')['status']=='unconfirmed'
    checks.append('receipt_schema_store_boundary_and_immutable_claim')
    assert j.begin('r1',1,'store-a',10)=='held_boundary_regression'
    assert j.begin('r1',1,'other-store',11)=='held_boundary_regression'
    assert j.begin('r1',1,'store-a',11)=='attempt_committed'
    assert j.confirm('r1',1,'store-a',receipt(11))=='held_correlation_mismatch'
    assert j.confirm('r1',1,'store-a',receipt(12))=='receipt_committed'
    assert j.status('r1')['status']=='delivered'
    checks.append('all_chunks_required_and_receipt_not_reused')
    j.register('r2','synthetic-owner',['private chunk 1'])
    assert j.begin('r2',0,'store-a',10)=='attempt_committed'
    assert j.confirm('r2',0,'store-a',receipt(11))=='held_row_already_claimed'
    checks.append('cross_request_claim_exclusion')
    cold=Path(tmp)/'cold.db'
    shutil.copyfile(path,cold)
    restored=Journal(cold)
    assert restored.status('r1')['status']=='delivered'
    assert restored.begin('r2',0,'store-a',10)=='held_existing_attempt'
    with closing(sqlite3.connect(cold)) as c:assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    assert b'private chunk' not in path.read_bytes() and b'synthetic-owner' not in path.read_bytes()
    checks.append('cold_restore_retains_uncertain_and_completed_states_without_body_storage')
    absent=Path(tmp)/'missing.db'
    try:Journal(absent)
    except sqlite3.OperationalError:pass
    else:raise AssertionError('missing history recreated')
    assert not absent.exists()
    empty=Path(tmp)/'empty.db'
    empty.write_bytes(b'')
    try:Journal(empty)
    except ValueError as e:assert str(e)=='uninitialized_journal'
    else:raise AssertionError('truncated history recreated')
    try:Journal(path,create=True)
    except FileExistsError:pass
    else:raise AssertionError('history reprovisioned')
    checks.append('missing_history_holds_and_explicit_provision_never_overwrites')
print(json.dumps({'status':'passed','checks':checks,'real_sends':0,'production_changes':False}))
