"""Immutable historical-state review: counts/digests only, no IDs, payloads or repairs."""
import hashlib,json,sqlite3,sys
from contextlib import closing
from pathlib import Path
from gmail_history_binding import HISTORY_TABLES

KNOWN_APPROVAL={'pending','approved','rejected','denied','executed','failed','expired','cancelled','executing','uncertain','completed'}
KNOWN_ACTION={'archived','trashed','draft_created','left_untouched','action_outcome_unknown','error_before_action','error_left_untouched','undone','undo_failed'}
def grouped(c,table,column,known,where='',args=()):
    out={}
    for value,count in c.execute('SELECT '+column+',COUNT(*) FROM '+table+where+' GROUP BY '+column,args):
        label=value if value in known else 'other_unclassified'
        out[label]=out.get(label,0)+count
    return out
def inspect(path):
    path=Path(path).resolve();before=hashlib.sha256(path.read_bytes()).hexdigest()
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True)) as c:
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        tables={row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        inventory={}
        for table in HISTORY_TABLES:
            if table not in tables:continue
            # Exact row digest remains content-free; never serialize private rows to output.
            rows=sorted(repr(tuple(row)) for row in c.execute('SELECT * FROM '+table))
            inventory[table]={'rows':len(rows),'sha256':hashlib.sha256('\n'.join(rows).encode()).hexdigest()}
        approvals=grouped(c,'approvals','status',KNOWN_APPROVAL," WHERE action LIKE 'gmail%'") if 'approvals' in tables else {}
        actions=grouped(c,'email_autonomy_actions','action',KNOWN_ACTION) if 'email_autonomy_actions' in tables else {}
        bindings=c.execute('SELECT COUNT(*) FROM gmail_history_binding').fetchone()[0] if 'gmail_history_binding' in tables else 0
    assert before==hashlib.sha256(path.read_bytes()).hexdigest()
    unresolved=sum(v for k,v in approvals.items() if k in {'pending','executing','uncertain','failed','other_unclassified'})
    unresolved+=sum(v for k,v in actions.items() if k in {'action_outcome_unknown','error_left_untouched','undo_failed','other_unclassified'})
    return {'snapshot_sha256':before,'tables':inventory,'gmail_approval_status_counts':approvals,'autonomy_action_counts':actions,
        'existing_account_bindings':bindings,'records_requiring_review_not_replay':unresolved,
        'source_unchanged':True,'migration_ready':False,
        'limits':'Historical snapshot only. Counts and stored labels do not prove provider delivery, human/account identity, action completion or current live state. Legacy error_left_untouched catches exceptions around provider writes; it does not prove no effect occurred.'}
if __name__=='__main__':print(json.dumps(inspect(sys.argv[1]),indent=2))
