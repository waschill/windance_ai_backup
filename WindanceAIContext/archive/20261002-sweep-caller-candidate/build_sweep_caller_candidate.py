"""Prepare a private caller candidate; no installation or endpoint call."""
import ast,hashlib,json
from pathlib import Path
p=Path('sweep-caller-private/original.private.py');s=p.read_text(encoding='utf-8')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='20c9295addda27835b6d6520556a2390b58146a6ed5d76dd8e60353b4aea566d'
before=ast.parse(s)
replacements={
'post_json':'''def post_json(url: str, payload: dict, timeout: int = 30) -> dict:
    import os
    headers = {"Content-Type": "application/json"}
    if url == HARNESS_SWEEP_URL:
        token = os.environ.get("AGENT_HARNESS_TOKEN", "").strip()
        if not token:
            raise RuntimeError("Sweep authentication unavailable")
        headers["Authorization"] = "Bearer " + token
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with opener.open(req, timeout=timeout) as resp:
        raw = resp.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise RuntimeError("Response exceeds bound")
    result = json.loads(raw.decode("utf-8"))
    if not isinstance(result, dict):
        raise RuntimeError("Invalid response")
    return result
''',
'main':'''def main() -> int:
    try:
        result = post_json(HARNESS_SWEEP_URL, {}, timeout=150)
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
            raise RuntimeError("Invalid sweep status")
        if result.get("status") == "held" or result["errors"]:
            print(json.dumps({"status": "held", "notification_attempted": False}))
            return 1
        if result["notices"]:
            lines = ["Gmail sender-rule results (review notices for uncertain outcomes):"]
            lines.extend(result["notices"][:10])
            if len(result["notices"]) > 10:
                lines.append("Additional notices require review in the saved sweep results.")
            post_json(NODE_RED_SEND_URL, {"to": PHONE, "message": "\\n".join(lines)}, timeout=15)
            # The current notice endpoint has no verified delivery contract here.
            # A response is not delivery evidence. No automatic retry is added.
            print(json.dumps({"status": "notification_unconfirmed", "notification_attempted": True}))
            return 1
        print(json.dumps({"status": "sweep_completed", "checked": result["checked"],
                          "deleted": result["deleted"], "notification_attempted": False}))
        return 0
    except Exception:
        print(json.dumps({"status": "outcome_unconfirmed", "retry_safe": False}))
        return 1
'''}
for name,new in replacements.items():
 n=next(n for n in before.body if getattr(n,'name','')==name)
 s=s.replace(ast.get_source_segment(p.read_text(encoding='utf-8'),n),new)
after=ast.parse(s)
assert [ast.dump(n) for n in before.body if getattr(n,'name','') not in replacements]==[ast.dump(n) for n in after.body if getattr(n,'name','') not in replacements]
compile(s,'<candidate>','exec')
out=p.with_name('candidate.private.py');out.write_text(s,encoding='utf-8',newline='\n')
print(json.dumps({'candidate_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'unrelated_ast_preserved':True,'installed':False}))
