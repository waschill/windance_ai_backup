"""Route legacy report callers through the fixed worker without child recursion."""
import ast,hashlib,json,shutil
from pathlib import Path
prior=Path('email-worker-error-guard-private');root=Path('email-bounded-entry-r2-private')
raw=(prior/'manifest.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='6d3856773f698946f84a97ad6442356861cae52b6a35b9029dbb6254351abcc2'
m=json.loads(raw);assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in m.items())
s=(prior/'agent_harness.candidate.private.py').read_text(encoding='utf-8');before=ast.parse(s)
node=next(n for n in before.body if getattr(n,'name','')=='summarize_email_for_william')
old=ast.get_source_segment(s,node)
wrapper='''def summarize_email_for_william(limit: int = 10) -> tuple[str, str, str]:
    require_william_mailbox()
    from email_process_deadline import run
    try:
        result = run(Path(__file__).with_name("email_fixed_worker.py"),
            {"owner": "william", "operation": "report", "limit": max(1, min(limit, 50))}, timeout=120)
        if set(result) != {"reply", "provider", "model"} or any(not isinstance(result[k], str) for k in result):
            raise RuntimeError("Invalid worker receipt")
        return result["reply"], result["provider"], result["model"]
    except Exception:
        try:
            audit("gmail_report_worker_error", {"status": "unconfirmed", "code": "email_worker_failed"})
        except Exception:
            pass
        return ("Email report invalid; worker completion could not be confirmed. Do not use report numbers. "
            "Earlier mailbox actions may have completed; inspect durable receipts and reconcile unconfirmed outcomes before retrying.",
            "deterministic", "gmail-error")
'''
s=s.replace(old,old.replace('def summarize_email_for_william(', 'def _summarize_email_for_william_inline(',1)+'\n\n'+wrapper)
node=next(n for n in before.body if getattr(n,'name','')=='post_gmail_report')
old=ast.get_source_segment((prior/'agent_harness.candidate.private.py').read_text(encoding='utf-8'),node)
new=old.replace('    require_token(authorization)','    if not HARNESS_TOKEN:\n        raise HTTPException(status_code=503, detail="Email report authentication unavailable")\n    require_token(authorization)',1)
new=new.replace('    return {"reply": reply, "provider": provider, "model": model}',
    '    result = {"reply": reply, "provider": provider, "model": model}\n    if model == "gmail-error":\n        return JSONResponse(status_code=503, content=result)\n    return result')
assert new!=old;s=s.replace(old,new)
after=ast.parse(s);changed={'summarize_email_for_william','_summarize_email_for_william_inline','post_gmail_report'}
assert [ast.dump(n) for n in before.body if getattr(n,'name','') not in changed]==[ast.dump(n) for n in after.body if getattr(n,'name','') not in changed]
compile(s,'<bounded-email-entry>','exec');root.mkdir()
for name in m:
 if name!='agent_harness.candidate.private.py':shutil.copy2(prior/name,root/name)
(root/'agent_harness.candidate.private.py').write_text(s,encoding='utf-8',newline='\n')
worker=(root/'email_fixed_worker.py').read_text().replace('h.summarize_email_for_william(limit=', 'h._summarize_email_for_william_inline(limit=')
(root/'email_fixed_worker.py').write_text(worker)
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2));digest=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()
(root/'worker-policy.json').write_text(json.dumps({'manifest_sha256':digest}))
print(json.dumps({'main':manifest['agent_harness.candidate.private.py'],'manifest':digest,'files':len(manifest),'unrelated_ast_preserved':True}))
