"""Stage explicit local service authentication without changing any live configuration."""
import ast,hashlib
from pathlib import Path
p=Path('gmail-caller-private/original.private.py');s=p.read_text(encoding='utf-8')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='61364689b38b2eb036ef252d5325785378d9d30fcb5907ae7751d1f65092ef9e'
t=ast.parse(s);node=next(n for n in t.body if getattr(n,'name','')=='submit');old=ast.get_source_segment(s,node)
new=old.replace('    normalized =', '''    import os
    token = os.environ.get("AGENT_HARNESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Gmail service authentication is not configured")
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    normalized =''',1)
new=new.replace('{"Content-Type": "application/json"}', '{"Content-Type": "application/json", "Authorization": "Bearer " + token}')
new=new.replace('urllib.request.urlopen(req, timeout=180)', 'opener.open(req, timeout=180)')
new=new.replace('data = json.loads(response.read().decode("utf-8"))', '''raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise ValueError("Response exceeds bound")
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Invalid service response")''')
new=new.replace(' from exc', ' from None').replace('"isError": False','"isError": data.get("model") == "gmail-error"')
s=s.replace(old,new);after=ast.parse(s)
assert [ast.dump(n) for n in t.body if getattr(n,'name','')!='submit']==[ast.dump(n) for n in after.body if getattr(n,'name','')!='submit']
out=Path('gmail-caller-private/candidate.private.py');out.write_text(s,encoding='utf-8',newline='\n')
print(hashlib.sha256(out.read_bytes()).hexdigest())
