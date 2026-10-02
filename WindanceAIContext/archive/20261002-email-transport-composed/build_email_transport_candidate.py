"""Compose Gmail-only transport into exact staged source; preserve Calendar AST."""
import ast,hashlib,json,shutil
from pathlib import Path
prior=Path('email-sweep-hold-r2-private');root=Path('email-transport-private')
manifest=json.loads((prior/'manifest.json').read_text())
assert all(hashlib.sha256((prior/n).read_bytes()).hexdigest()==v for n,v in manifest.items())
assert manifest['agent_harness.candidate.private.py']=='b30bd912cacacac187a5799984b6c20ad6baaabd1da89fac3ca73a00a8987cb1'
s=(prior/'agent_harness.candidate.private.py').read_text(encoding='utf-8');before=ast.parse(s)
n=next(n for n in before.body if getattr(n,'name','')=='gmail_service')
replacement='''def gmail_service() -> Any:
    require_william_mailbox()
    from gmail_single_attempt_transport import GmailTransport
    try:
        creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_FILE), SCOPES)
    except Exception:
        raise RuntimeError("Gmail credential loading unavailable") from None
    return build("gmail", "v1", http=GmailTransport(creds), cache_discovery=False, static_discovery=True)'''
s=s.replace(ast.get_source_segment(s,n),replacement)
after=ast.parse(s)
assert [ast.dump(n) for n in before.body if getattr(n,'name','')!='gmail_service']==[ast.dump(n) for n in after.body if getattr(n,'name','')!='gmail_service']
compile(s,'<staged-email-transport>','exec');root.mkdir()
for name in manifest:
 if name!='agent_harness.candidate.private.py':shutil.copy2(prior/name,root/name)
(root/'agent_harness.candidate.private.py').write_text(s,encoding='utf-8',newline='\n')
shutil.copy2('gmail_single_attempt_transport.py',root/'gmail_single_attempt_transport.py')
out={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
(root/'manifest.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'files':len(out),'hashes':out,'unrelated_ast_unchanged':True,'production_changes':False}))
