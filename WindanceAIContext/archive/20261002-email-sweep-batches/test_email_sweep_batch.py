import json,sqlite3,tempfile
from pathlib import Path
from email_sweep_batch import SCHEMA,choose,advance
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)/'batch.db'
    def connect():return sqlite3.connect(path)
    c=connect();c.executescript(SCHEMA);c.close()
    keys=[f'{i:03}@example.invalid' for i in range(181)]
    seen=[]
    for _ in range(23):
        plan=choose(connect,keys);assert len(plan['keys'])==8
        seen.extend(plan['keys']);advance(connect,plan,plan['keys'])
    assert set(seen)==set(keys)
    stale=choose(connect,keys);advance(connect,stale,stale['keys'][:1])
    current=choose(connect,keys)
    try:advance(connect,stale,stale['keys'])
    except RuntimeError:pass
    else:raise AssertionError('stale cursor overwrite')
    assert choose(connect,keys)==current
    # Missing cursor key and new earlier key are visited after bounded wrap.
    changed=[k for k in keys if k!=current['after_key']]+['000-new@example.invalid']
    seen=[]
    for _ in range(24):
        plan=choose(connect,changed);seen.extend(plan['keys']);advance(connect,plan,plan['keys'])
    assert set(changed)<=set(seen)
    plan=choose(connect,changed)
    assert choose(connect,changed)==plan # no implicit advance on selection/failed work
    try:advance(connect,plan,list(reversed(plan['keys'])))
    except ValueError:pass
    else:raise AssertionError('non-prefix accepted')
print(json.dumps({'status':'passed','all_181_rules_visited_in_23_batches':True,'max_rules':8,'stale_cursor_held':True,'changed_rules_wrap':True,'selection_does_not_advance':True}))
