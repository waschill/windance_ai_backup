"""Stage account policy verification before returning any Gmail service client."""
import ast,hashlib,json,shutil
from pathlib import Path
prior=Path('email-inline-model-private');root=Path('email-account-bound-private')
raw=(prior/'manifest.json').read_bytes();assert hashlib.sha256(raw).hexdigest()=='1262ea18e24c244c75a63545afbbae8bab1485c82218f021c4f44029e591046e'
m=json.loads(raw);assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in m.items())
s=(prior/'agent_harness.py').read_text(encoding='utf-8');before=ast.parse(s)
node=next(n for n in before.body if getattr(n,'name','')=='gmail_service');old=ast.get_source_segment(s,node)
new='''def gmail_service() -> Any:
    require_william_mailbox()
    from gmail_account_boundary import expected_account, verify
    expected = expected_account(GOOGLE_TOKEN_FILE.parent / "gmail-account-policy.json")
    from gmail_single_attempt_transport import GmailTransport
    from gmail_credential_cache import load
    service = build("gmail", "v1", http=GmailTransport(load(GOOGLE_TOKEN_FILE, SCOPES)), cache_discovery=False, static_discovery=True)
    return verify(service, expected)'''
s=s.replace(old,new);after=ast.parse(s)
assert [ast.dump(n) for n in before.body if getattr(n,'name','')!='gmail_service']==[ast.dump(n) for n in after.body if getattr(n,'name','')!='gmail_service']
compile(s,'<account-bound-email>','exec');root.mkdir()
for n in m:
 if n!='agent_harness.py':shutil.copy2(prior/n,root/n)
(root/'agent_harness.py').write_text(s,encoding='utf-8',newline='\n');shutil.copy2('gmail_account_boundary_r2.py',root/'gmail_account_boundary.py')
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2));digest=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()
(root/'worker-policy.json').write_text(json.dumps({'manifest_sha256':digest}))
print(json.dumps({'files':len(manifest),'main':manifest['agent_harness.py'],'manifest':digest,'live_account_policy_created':False}))
