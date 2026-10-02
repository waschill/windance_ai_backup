"""Preserve failed-read semantics through actual HTTP and chat callers."""
import ast,hashlib,json,shutil
from pathlib import Path
prior=Path('email-sweep-hold-private');root=Path('email-sweep-hold-r2-private')
m=json.loads((prior/'manifest.json').read_text());assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in m.items())
assert m['agent_harness.candidate.private.py']=='164b09b8a74f01dc108d678e698cb7c0140f1f9be86670b4327a24188ea3f865'
s=(prior/'agent_harness.candidate.private.py').read_text(encoding='utf-8');original=s;before=ast.parse(s)
for node in before.body:
    if getattr(node,'name','')=='post_gmail_sender_rule_sweep':
        old=ast.get_source_segment(original,node)
        new=old.replace('return gmail_sender_rule_sweep(limit_per_sender=limit_per_sender)','result = gmail_sender_rule_sweep(limit_per_sender=limit_per_sender)')
        new+='\n    if result.get("status") == "held":\n        raise HTTPException(status_code=503, detail="Mailbox listing unavailable; sweep held before changes")\n    return result'
        s=s.replace(old,new)
    elif getattr(node,'name','')=='direct_email_domain_rule':
        old=ast.get_source_segment(original,node)
        anchor='    sweep = gmail_sender_rule_sweep(limit_per_sender=50)';assert old.count(anchor)==1
        new=old.replace(anchor,'''    try:
        sweep = gmail_sender_rule_sweep(limit_per_sender=50)
    except Exception:
        audit("gmail_domain_rule_initial_sweep_unavailable", {"status": "unavailable"})
        return "The domain rule was saved, but the initial sweep outcome is unavailable. Inspect recovery status before retrying.", "deterministic", "gmail-domain-rule-held"
    if sweep.get("status") == "held":
        return "The domain rule was saved. The initial sweep is held because mailbox listing failed; that sweep made no mailbox changes.", "deterministic", "gmail-domain-rule-held"''')
        s=s.replace(old,new)
after=ast.parse(s);changed={'post_gmail_sender_rule_sweep','direct_email_domain_rule'}
assert [ast.dump(n) for n in before.body if getattr(n,'name','') not in changed]==[ast.dump(n) for n in after.body if getattr(n,'name','') not in changed]
compile(s,'<email-sweep-hold-r2>','exec');root.mkdir()
for name in m:
    if name!='agent_harness.candidate.private.py':shutil.copy2(prior/name,root/name)
(root/'agent_harness.candidate.private.py').write_text(s,encoding='utf-8',newline='\n')
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'files':len(manifest),'candidate_sha256':manifest['agent_harness.candidate.private.py']}))
