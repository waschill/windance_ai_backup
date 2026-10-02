"""Disposable account-binding database checks; no mailbox or production state."""
import concurrent.futures,json,sqlite3,tempfile
from contextlib import closing
from pathlib import Path
from gmail_history_binding import bind_verified,BindingHeld,HISTORY_TABLES
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);db=root/'clean.db'
    def connect():return sqlite3.connect(db,timeout=2)
    bind_verified(connect,'owner@example.invalid');bind_verified(connect,'OWNER@example.invalid')
    try:bind_verified(connect,'other@example.invalid');raise AssertionError('Account switch accepted')
    except BindingHeld:pass
    with closing(connect()) as c:assert c.execute('SELECT COUNT(*) FROM gmail_history_binding').fetchone()[0]==1
    # Competing first bindings serialize and cannot both claim the same state.
    db=root/'race.db'
    def race(address):
        try:bind_verified(connect,address);return 'bound'
        except BindingHeld:return 'held'
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        states=list(pool.map(race,['one@example.invalid','two@example.invalid']))
    assert sorted(states)==['bound','held']
    held=0
    for table in HISTORY_TABLES:
        db=root/(table+'.db')
        with closing(connect()) as c:c.execute('CREATE TABLE '+table+' (fixture TEXT)');c.execute('INSERT INTO '+table+" VALUES('preserved')");c.commit()
        try:bind_verified(connect,'owner@example.invalid');raise AssertionError('History adopted')
        except BindingHeld:held+=1
        with closing(connect()) as c:
            assert c.execute('SELECT fixture FROM '+table).fetchall()==[('preserved',)]
            assert not c.execute("SELECT 1 FROM sqlite_master WHERE name='gmail_history_binding'").fetchone()
    db=root/'approvals.db'
    with closing(connect()) as c:c.execute('CREATE TABLE approvals(action TEXT)');c.execute("INSERT INTO approvals VALUES('gmail_send')");c.commit()
    try:bind_verified(connect,'owner@example.invalid');raise AssertionError('Approval history adopted')
    except BindingHeld:pass
    db=root/'unrelated.db'
    with closing(connect()) as c:c.execute('CREATE TABLE approvals(action TEXT)');c.execute("INSERT INTO approvals VALUES('fixture_nonmail')");c.commit()
    bind_verified(connect,'owner@example.invalid')
print(json.dumps({'same_account_reuse':True,'changed_account_held':True,'concurrent_binding_one_winner':True,
    'historical_tables_held_without_changes':held,'mail_approvals_held':True,'unrelated_approval_preserved':True,
    'production_changes':False,'limits':'Standalone helper; no historical adoption workflow, service integration or real identity proof.'}))
