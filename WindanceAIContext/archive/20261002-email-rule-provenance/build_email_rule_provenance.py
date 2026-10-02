import ast,hashlib,json,shutil
from pathlib import Path
from email_rule_accounting import SCHEMA
prior=Path('email-rule-receipts-private');root=Path('email-rule-provenance-private')
raw=(prior/'manifest.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='3ae7b5e2c2575ae15db53971d2087cf04c469f6787cfbd05116f62d158277291'
manifest=json.loads(raw);assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
root.mkdir()
for name in manifest:shutil.copyfile(prior/name,root/name)
shutil.copyfile('email_rule_accounting.py',root/'email_rule_accounting.py')
p=root/'email_action_intent.py';s=p.read_text()
s=s.replace('SCHEMA+=ADMISSION_SCHEMA','SCHEMA+=ADMISSION_SCHEMA\nfrom email_rule_accounting import SCHEMA as RULE_SCHEMA\nSCHEMA+=RULE_SCHEMA')
s=s.replace('draft_evidence=None,operation_scope=None):','draft_evidence=None,operation_scope=None,rule_evidence=None):')
s=s.replace("    key=operation_key(owner,message_id,operation_scope)","    if rule_evidence is not None and (action!='trash' or operation_scope is not None):raise ValueError('Rule evidence scope refused')\n    key=operation_key(owner,message_id,operation_scope)")
s=s.replace("            return json.loads(row[3])", "            if rule_evidence is not None:\n                from email_rule_accounting import require_existing\n                require_existing(c,key,digest,rule_evidence)\n            return json.loads(row[3])",1)
needle='        if draft_evidence is not None:'
s=s.replace(needle,'        if rule_evidence is not None:\n            from email_rule_accounting import reserve\n            reserve(c,key,digest,rule_evidence)\n'+needle,1)
ast.parse(s);p.write_text(s,encoding='utf-8',newline='\n')
p=root/'agent_harness.py';s=p.read_text(encoding='utf-8');before=ast.parse(s)
s=s.replace('CREATE TABLE IF NOT EXISTS email_sender_rule_receipts (',SCHEMA+'\nCREATE TABLE IF NOT EXISTS email_sender_rule_receipts (',1)
node=next(n for n in ast.parse(s).body if getattr(n,'name','')=='apply_email_sender_rules');old=ast.get_source_segment(s,node);new=old
new=new.replace('            performed_now=False','            from email_rule_accounting import evidence as rule_evidence, account\n            performed_now=False',1)
new=new.replace('}, perform_delete)','}, perform_delete,rule_evidence=rule_evidence(rule_key,str(rule["action"]),item,email_importance(item),gmail_state(item)))',1)
start=new.index('            with db() as conn:');end=new.index('            if effect_counts is not None:',start)
new=new[:start]+"            recorded=account(db,operation_key('william',str(item['id'])))\n"+new[end:];s=s.replace(old,new)
node=next(n for n in ast.parse(s).body if getattr(n,'name','')=='_gmail_sender_rule_sweep_inline');old=ast.get_source_segment(s,node)
new=old.replace('    rules = email_sender_rules()', '    from email_rule_accounting import reconcile\n    accounting_reconciled=reconcile(db)\n    rules = email_sender_rules()',1)
new=new.replace('        return {"rules": 0, "checked": 0, "deleted": 0, "kept": 0, "notices": [], "errors": []}', '        result={"rules":0,"checked":0,"deleted":0,"kept":0,"notices":[],"errors":[]}\n        if accounting_reconciled:result["accounting_reconciled"]=accounting_reconciled\n        return result')
new=new.replace('    result["effects"]=effect_counts','    result["effects"]=effect_counts\n    result["accounting_reconciled"]=accounting_reconciled');s=s.replace(old,new)
changed={'db','apply_email_sender_rules','_gmail_sender_rule_sweep_inline'}
assert [ast.dump(n) for n in before.body if getattr(n,'name','') not in changed]==[ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','') not in changed]
p.write_text(s,encoding='utf-8',newline='\n')
p=root/'email_sweep_contract.py';s=p.read_text().replace("'status','coverage','effects'","'status','coverage','effects','accounting_reconciled'")
s=s.replace('    return result',"    if 'accounting_reconciled' in result and (type(result['accounting_reconciled']) is not int or not 0<=result['accounting_reconciled']<=20):raise ValueError('Invalid accounting count')\n    return result")
ast.parse(s);p.write_text(s,encoding='utf-8',newline='\n')
manifest={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in list(manifest)+['email_rule_accounting.py']}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2));digest=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()
(root/'worker-policy.json').write_text(json.dumps({'manifest_sha256':digest}))
print(json.dumps({'main':manifest['agent_harness.py'],'manifest':digest,'files':len(manifest),'deployment':False}))
