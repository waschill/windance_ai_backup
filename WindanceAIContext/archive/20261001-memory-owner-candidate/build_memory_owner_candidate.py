"""Stage retrieval containment from the current source; never deploy."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path('/Users/herald/services/memory-owner-boundary-20261001')
LIVE=Path('/Users/herald/services/agent-harness')
source=(LIVE/'agent_harness.py').read_text()
baseline='db8a435907a2fb49796818a17b29334874b1919d6a03640901a22b6b12ea8195'
assert hashlib.sha256(source.encode()).hexdigest()==baseline
tree=ast.parse(source)
functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
before=ast.get_source_segment(source,functions['vector_recall'])
after=before.replace('    query = (query or "").strip()',
 '''    owner = current_request_owner()
    if str(owner or '').strip().casefold() not in {'william','shawn'}:
        return {'configured': False, 'items': [], 'fallback': 'verified_owner_required'}
    query = (query or "").strip()''',1)
start=after.index('        rows = conn.execute(')
end=after.index('        ).fetchall()',start)+len('        ).fetchall()')
after=after[:start]+'        rows = owned_memory_rows(conn, owner, limit=500)'+after[end:]
start=after.index('        return {',after.index('scored.sort'))
end=after.index('\n\n    # Lexical fallback',start)
block=after[start:end]
after=after[:start]+"        if any(score > 0 for score, _ in scored):\n"+''.join('    '+line+'\n' for line in block.splitlines()).rstrip('\n')+after[end:]
after=after.replace('"source_id": row["source_id"],','"source_id": row["source_id"],\n                    "source_owner": row["source_owner"], "access_scope": row["access_scope"],')
assert before!=after;source=source.replace(before,after,1)
before=ast.get_source_segment(source,ast.parse(source).body[next(i for i,n in enumerate(ast.parse(source).body) if isinstance(n,ast.FunctionDef) and n.name=='memories_text')])
after='''def memories_text(limit: int = 200, max_chars: int | None = None) -> str:
    with db() as conn:
        rows = owned_memory_rows(conn, current_request_owner(), limit=limit)
    text = "\\n".join(f"- [{r['source_type']}:{r['source_id']}] {r['text']}" for r in rows)
    return text[:max_chars] if max_chars else text'''
source=source.replace(before,after,1)
source=source.replace('if second_brain_natural_language_intent(query):',"if current_request_owner() == 'william' and second_brain_natural_language_intent(query):")
# Keep the fallback source-aware through memories_text; absent identity yields no rows.
anchor='from email_owner_boundary import bind_mailbox_owner, require_william_mailbox, EmailOwnerBoundaryError'
assert source.count(anchor)==1
source=source.replace(anchor,anchor+', current_request_owner\nfrom memory_owner_boundary import owned_memory_rows')
assert source.count('f"William: {text}\\n\\n')==2
source=source.replace('f"William: {text}\\n\\n','f"{payload.user}: {text}\\n\\n')
assert source.count('f"William: {row[\'message\']}')==1
source=source.replace('f"William: {row[\'message\']}', 'f"{row[\'user\']}: {row[\'message\']}')
ast.parse(source)
ROOT.mkdir(mode=0o700,exist_ok=False)
(ROOT/'agent_harness.py').write_text(source);(ROOT/'agent_harness.py').chmod(0o600)
helper=(LIVE/'email_owner_boundary.py').read_text()
assert 'def current_request_owner' not in helper
helper+='\n\ndef current_request_owner():\n    """Identity bound by message handling; None is not a verified caller."""\n    return _owner.get()\n'
(ROOT/'email_owner_boundary.py').write_text(helper)
manifest={'baseline_sha256':baseline,'candidate_sha256':hashlib.sha256(source.encode()).hexdigest(),'helper_sha256':hashlib.sha256(helper.encode()).hexdigest(),'state':'staged_only','limits':'Legacy unclassified facts withheld; direct-tool authentication and explicit business grants still required.'}
(ROOT/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest))
