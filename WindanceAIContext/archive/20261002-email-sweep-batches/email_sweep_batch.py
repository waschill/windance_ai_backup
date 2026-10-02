"""Private bounded rule cursor; no mailbox effects or automatic hold clearing."""
from bisect import bisect_right
from contextlib import closing
RULE_CAP=8
MESSAGE_CAP=20
SCHEMA='''CREATE TABLE IF NOT EXISTS email_sweep_cursor (
 singleton INTEGER PRIMARY KEY CHECK(singleton=1),revision INTEGER NOT NULL CHECK(revision>=0),after_key TEXT NOT NULL);
INSERT OR IGNORE INTO email_sweep_cursor VALUES(1,0,'');'''
def choose(connect,keys):
    keys=sorted(set(keys))
    if len(keys)>10000 or any(type(k) is not str or not k or len(k)>320 for k in keys):raise ValueError('Invalid bounded rule set')
    with closing(connect()) as c:row=c.execute('SELECT revision,after_key FROM email_sweep_cursor WHERE singleton=1').fetchone()
    if row is None or type(row[0]) is not int or row[0]<0 or type(row[1]) is not str or len(row[1])>320:raise ValueError('Sweep cursor unavailable')
    start=bisect_right(keys,row[1])
    ordered=keys[start:]+keys[:start]
    return {'revision':row[0],'after_key':row[1],'keys':ordered[:RULE_CAP],'total':len(keys)}
def advance(connect,plan,visited):
    if not visited or list(visited)!=plan['keys'][:len(visited)]:raise ValueError('Visited cursor prefix required')
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE')
        changed=c.execute('UPDATE email_sweep_cursor SET revision=revision+1,after_key=? WHERE singleton=1 AND revision=? AND after_key=?',(visited[-1],plan['revision'],plan['after_key'])).rowcount
        if changed!=1:raise RuntimeError('Sweep cursor changed; preserve action receipts')
        c.commit()
