"""Remove raw report exception disclosure while preserving successful reports."""
import ast,hashlib,json,shutil
from pathlib import Path
prior=Path('email-worker-package-private');root=Path('email-worker-error-guard-private')
raw=(prior/'manifest.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='e41e91ef1902d434db654f7a93d22561b1d51cfdd948727fd22eede0ff750dfb'
m=json.loads(raw);assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in m.items())
s=(prior/'agent_harness.candidate.private.py').read_text(encoding='utf-8');before=ast.parse(s)
node=next(n for n in before.body if getattr(n,'name','')=='summarize_email_for_william')
replacement='''def summarize_email_for_william(limit: int = 10) -> tuple[str, str, str]:
    require_william_mailbox()
    try:
        return gmail_autonomy_report(limit=max(limit, 25))
    except Exception:
        try:
            audit("gmail_report_error", {"status": "unconfirmed", "code": "email_report_failed"})
        except Exception:
            pass
        return (
            "Email report invalid; report generation terminated.\\n\\n"
            "The report could not be completed. Do not use numbers from this failed report. "
            "No fallback inbox list will be substituted. Earlier mailbox actions may have completed; "
            "inspect durable action receipts and reconcile unconfirmed outcomes before retrying.",
            "deterministic", "gmail-error",
        )'''
s=s.replace(ast.get_source_segment(s,node),replacement);after=ast.parse(s)
assert [ast.dump(n) for n in before.body if getattr(n,'name','')!='summarize_email_for_william']==[ast.dump(n) for n in after.body if getattr(n,'name','')!='summarize_email_for_william']
compile(s,'<email-report-error-guard>','exec');root.mkdir()
for name in m:
 if name!='agent_harness.candidate.private.py':shutil.copy2(prior/name,root/name)
(root/'agent_harness.candidate.private.py').write_text(s,encoding='utf-8',newline='\n')
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2))
digest=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()
(root/'worker-policy.json').write_text(json.dumps({'manifest_sha256':digest}))
print(json.dumps({'main':manifest['agent_harness.candidate.private.py'],'manifest_sha256':digest,'files':len(manifest),'unrelated_ast_unchanged':True}))
