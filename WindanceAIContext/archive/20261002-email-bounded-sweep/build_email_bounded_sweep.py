"""Stage sweep execution through the existing fixed worker; never deploy."""
import ast,hashlib,json,shutil
from pathlib import Path
prior=Path('email-account-bound-private');root=Path('email-bounded-sweep-private')
raw=(prior/'manifest.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='dcfdd1100d28895db508edf4875b409a49687eed1e0599350c5212fef42967c5'
m=json.loads(raw)
assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in m.items())
s=(prior/'agent_harness.py').read_text(encoding='utf-8');before=ast.parse(s)
node=next(n for n in before.body if getattr(n,'name','')=='gmail_sender_rule_sweep')
old=ast.get_source_segment(s,node)
wrapper='''def gmail_sender_rule_sweep(limit_per_sender: int = 25) -> dict[str, Any]:
    require_william_mailbox()
    from email_process_deadline import run
    try:
        result = run(Path(__file__).with_name("email_fixed_worker.py"),
            {"owner": "william", "operation": "sender_rule_sweep",
             "limit": max(1, min(int(limit_per_sender or 25), 50))}, timeout=120)
        required = {"rules", "checked", "deleted", "kept", "notices", "errors"}
        if not required <= set(result) or set(result) - required - {"status"}:
            raise RuntimeError("Invalid sweep receipt")
        if any(type(result[k]) is not int or result[k] < 0 for k in ("rules", "checked", "deleted", "kept")):
            raise RuntimeError("Invalid sweep counts")
        if result["deleted"] + result["kept"] != result["checked"]:
            raise RuntimeError("Inconsistent sweep counts")
        if any(not isinstance(result[k], list) or any(not isinstance(v, str) for v in result[k]) for k in ("notices", "errors")):
            raise RuntimeError("Invalid sweep details")
        if result.get("status") not in (None, "held"):
            raise RuntimeError("Invalid sweep state")
        return result
    except Exception:
        try:
            audit("gmail_sweep_worker_error", {"status": "unconfirmed", "code": "email_worker_failed"})
        except Exception:
            pass
        raise RuntimeError("Mailbox sweep outcome unavailable; reconcile durable receipts before retrying") from None
'''
s=s.replace(old,old.replace('def gmail_sender_rule_sweep(', 'def _gmail_sender_rule_sweep_inline(',1)+'\n\n'+wrapper)
endpoint=next(n for n in before.body if getattr(n,'name','')=='post_gmail_sender_rule_sweep')
old=ast.get_source_segment((prior/'agent_harness.py').read_text(encoding='utf-8'),endpoint)
new=old.replace('    require_token(authorization)','    if not HARNESS_TOKEN:\n        raise HTTPException(status_code=503, detail="Mailbox sweep authentication unavailable")\n    require_token(authorization)',1)
assert old!=new;s=s.replace(old,new)
changed={'gmail_sender_rule_sweep','_gmail_sender_rule_sweep_inline','post_gmail_sender_rule_sweep'}
assert [ast.dump(n) for n in before.body if getattr(n,'name','') not in changed]==[ast.dump(n) for n in ast.parse(s).body if getattr(n,'name','') not in changed]
compile(s,'<bounded-sweep>','exec');root.mkdir()
for name in m:shutil.copy2(prior/name,root/name)
(root/'agent_harness.py').write_text(s,encoding='utf-8',newline='\n')
worker=(root/'email_fixed_worker.py').read_text().replace('h.gmail_sender_rule_sweep(', 'h._gmail_sender_rule_sweep_inline(')
(root/'email_fixed_worker.py').write_text(worker,encoding='utf-8',newline='\n')
manifest={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in m}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2))
digest=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()
(root/'worker-policy.json').write_text(json.dumps({'manifest_sha256':digest}))
print(json.dumps({'main':manifest['agent_harness.py'],'manifest':digest,'source_files':len(manifest),'unrelated_ast_preserved':True,'deployed':False}))
