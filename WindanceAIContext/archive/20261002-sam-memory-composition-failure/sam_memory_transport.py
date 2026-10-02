"""Explicit configured producer HTTP transport, no legacy credential fallback."""
import json,urllib.request,urllib.parse
from pathlib import Path
def send(url,credential_path,envelope):
    parsed=urllib.parse.urlsplit(url)
    if parsed.username or parsed.password or parsed.fragment or not parsed.hostname or not (parsed.scheme=='https' or parsed.scheme=='http' and parsed.hostname in ('127.0.0.1','localhost','::1')):
        raise RuntimeError('Configured HTTPS or loopback producer endpoint required')
    try:
        token=Path(credential_path).read_text(encoding='utf-8').strip()
        if not 32<=len(token)<=400 or any(c.isspace() for c in token):raise ValueError()
        req=urllib.request.Request(url,data=json.dumps(envelope,allow_nan=False).encode(),method='POST',
             headers={'Content-Type':'application/json','Authorization':'Bearer '+token})
        # Do not forward service credentials through redirects.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):return None
        with urllib.request.build_opener(NoRedirect()).open(req,timeout=10) as response:
            raw=response.read(16385)
            if len(raw)>16384:raise ValueError()
            result=json.loads(raw)
        if not isinstance(result,dict):raise ValueError()
        return result
    except Exception:
        raise RuntimeError('Producer acknowledgment unavailable; retain the same request for reconciliation/retry') from None
