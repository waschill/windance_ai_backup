import ast,hashlib,json,shutil
from pathlib import Path
prior=Path('email-exchange-budget-private');root=Path('email-sweep-batches-r2-private')
raw=(prior/'manifest.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='45e0cda659cd4291f1f35591fb15310486a788097582f13c2ed4d7d41064c41e'
manifest=json.loads(raw)
assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
root.mkdir()
for name in manifest:shutil.copyfile(prior/name,root/name)
for name in ('email_sweep_batch.py','email_sweep_contract.py'):shutil.copyfile(name,root/name)
p=root/'agent_harness.py';s=p.read_text(encoding='utf-8');original=ast.parse(s)
needle='CREATE TABLE IF NOT EXISTS email_action_intents ('
from email_sweep_batch import SCHEMA
assert s.count(needle)==1;s=s.replace(needle,SCHEMA+'\n'+needle)
node=next(n for n in ast.parse(s).body if getattr(n,'name','')=='_gmail_sender_rule_sweep_inline')
old=ast.get_source_segment(s,node);new=old
new=new.replace('    service = gmail_service()',"    from email_sweep_batch import choose, advance, MESSAGE_CAP\n    from email_mailbox_admission import is_held\n    plan=choose(db,list(active_rules))\n    visited=[];provider_more=False\n    service = gmail_service()",1)
new=new.replace('    for address in sorted(active_rules):','    for address in plan["keys"]:\n        if len(items)>=MESSAGE_CAP:break')
new=new.replace('maxResults=per_sender,','maxResults=min(per_sender,MESSAGE_CAP-len(items)),')
new=new.replace('            refs = listing.get("messages", []) or []','            provider_more=provider_more or bool(listing.get("nextPageToken"))\n            refs = listing.get("messages", []) or []\n            if not isinstance(refs,list) or len(refs)>min(per_sender,MESSAGE_CAP-len(items)):raise ValueError("Provider listing exceeds batch")')
new=new.replace('                items.append(message_summary(msg, include_body=False))','                items.append(message_summary(msg, include_body=False))\n            visited.append(address)')
new=new.replace('    deleted = len(items) - len(kept)','    deleted = len(items) - len(kept)\n    held=is_held(db)\n    if not held:advance(db,plan,visited)\n    more=held or provider_more or len(visited)<len(active_rules) or len(items)>=MESSAGE_CAP')
new=new.replace('    audit("gmail_sender_rule_sweep", result)','    result["coverage"]={"version":1,"rules_visited":len(visited),"rules_total":len(active_rules),"message_cap":MESSAGE_CAP,"has_more":bool(more),"cursor_advanced":not held}\n    if more:result["status"]="partial"\n    audit("gmail_sender_rule_sweep", result)')
assert new!=old;s=s.replace(old,new)
node=next(n for n in ast.parse(s).body if getattr(n,'name','')=='gmail_sender_rule_sweep')
old=ast.get_source_segment(s,node)
start=old.index('        required = ');end=old.index('        return result',start)
new=old[:start]+'        from email_sweep_contract import validate\n        validate(result)\n'+old[end:]
s=s.replace(old,new)
changed={'db','_gmail_sender_rule_sweep_inline','gmail_sender_rule_sweep'}
assert [ast.dump(n) for n in original.body if getattr(n,'name','') not in changed]==[ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','') not in changed]
p.write_text(s,encoding='utf-8',newline='\n')
manifest={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in list(manifest)+['email_sweep_batch.py','email_sweep_contract.py']}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2));digest=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()
(root/'worker-policy.json').write_text(json.dumps({'manifest_sha256':digest}))
print(json.dumps({'main':manifest['agent_harness.py'],'manifest':digest,'files':len(manifest),'unrelated_ast_preserved':True,'deployment':False}))
