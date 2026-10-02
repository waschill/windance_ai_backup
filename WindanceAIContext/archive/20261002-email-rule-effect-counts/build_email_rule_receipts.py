import ast,hashlib,json,shutil
from pathlib import Path
prior=Path('email-sweep-batches-r2-private');root=Path('email-rule-receipts-private')
raw=(prior/'manifest.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='29a06470175b046bc0ad9280b87c12270226df3ebcadeec40c90dad69a5fd093'
manifest=json.loads(raw)
assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
root.mkdir()
for name in manifest:shutil.copyfile(prior/name,root/name)
p=root/'agent_harness.py';s=p.read_text(encoding='utf-8');before=ast.parse(s)
schema="""CREATE TABLE IF NOT EXISTS email_sender_rule_receipts (
 operation_key TEXT PRIMARY KEY,sender_key TEXT NOT NULL,rule_action TEXT NOT NULL,
 recorded_at TEXT NOT NULL);
"""
s=s.replace('CREATE TABLE IF NOT EXISTS email_sweep_cursor (',schema+'CREATE TABLE IF NOT EXISTS email_sweep_cursor (',1)
node=next(n for n in ast.parse(s).body if getattr(n,'name','')=='apply_email_sender_rules')
old=ast.get_source_segment(s,node);new=old
new=new.replace('items: list[dict[str, Any]])','items: list[dict[str, Any]], *, effect_counts: dict[str, int] | None = None)')
new=new.replace('from email_action_intent import perform as mailbox_once','from email_action_intent import perform as mailbox_once, operation_key')
line='            mailbox_once(db, "william", str(item["id"]), "trash", {}, lambda: gmail_delete_message(str(item["id"])))\n            note_sender_rule_match(rule_key, str(rule["action"]))'
replacement='''            performed_now=False
            def perform_delete():
                nonlocal performed_now
                performed_now=True
                return gmail_delete_message(str(item["id"]))
            mailbox_once(db, "william", str(item["id"]), "trash", {"sender_rule":rule_key,"rule_action":str(rule["action"])}, perform_delete)'''
assert line in new;new=new.replace(line,replacement)
start=new.index('                conn.execute(');end=new.index('                conn.commit()',start)
tracking=new[start:end]
insert='''                conn.execute('BEGIN IMMEDIATE')
                recorded=conn.execute('INSERT OR IGNORE INTO email_sender_rule_receipts VALUES(?,?,?,?)',
                    (operation_key('william',str(item['id'])),rule_key,str(rule['action']),now())).rowcount==1
                if recorded:
                    conn.execute('UPDATE max_email_sender_rules SET last_matched_at=?,match_count=match_count+1 WHERE sender_email=? AND action=?',
                        (now(),rule_key,str(rule['action'])))
'''
new=new[:start]+insert+''.join('    '+line if line.strip() else line for line in tracking.splitlines(keepends=True))+new[end:]
new=new.replace('            if rule["action"] == "notify_delete":','            if effect_counts is not None:\n                effect_counts["newly_confirmed" if performed_now else "previously_confirmed"]+=1\n            if rule["action"] == "notify_delete" and recorded:')
new=new.replace('f"- Deleted from {short_sender', 'f"- {\'Deleted\' if performed_now else \'Confirmed previously deleted\'} from {short_sender')
s=s.replace(old,new)
node=next(n for n in ast.parse(s).body if getattr(n,'name','')=='_gmail_sender_rule_sweep_inline')
old=ast.get_source_segment(s,node)
new=old.replace('    kept, notices = apply_email_sender_rules(items)','    effect_counts={"newly_confirmed":0,"previously_confirmed":0}\n    kept, notices = apply_email_sender_rules(items,effect_counts=effect_counts)')
new=new.replace('    result["coverage"]=', '    result["effects"]=effect_counts\n    result["coverage"]=')
s=s.replace(old,new)
changed={'db','apply_email_sender_rules','_gmail_sender_rule_sweep_inline'}
assert [ast.dump(n) for n in before.body if getattr(n,'name','') not in changed]==[ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','') not in changed]
p.write_text(s,encoding='utf-8',newline='\n')
p=root/'email_sweep_contract.py';s=p.read_text()
s=s.replace("-{'status','coverage'}", "-{'status','coverage','effects'}")
s=s.replace('    return result', '''    effects=result.get('effects')
    if effects is not None:
        if type(effects) is not dict or set(effects)!={'newly_confirmed','previously_confirmed'} or any(type(v) is not int or v<0 for v in effects.values()) or sum(effects.values())!=result['deleted']:raise ValueError('Invalid effect counts')
    return result''')
ast.parse(s);p.write_text(s,encoding='utf-8',newline='\n')
manifest={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in manifest}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2));digest=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()
(root/'worker-policy.json').write_text(json.dumps({'manifest_sha256':digest}))
print(json.dumps({'main':manifest['agent_harness.py'],'manifest':digest,'files':len(manifest),'unrelated_ast_preserved':True,'deployment':False}))
