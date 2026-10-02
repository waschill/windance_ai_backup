"""Private SAL staging only; no live bridge import or restart."""
import ast
import hashlib
import json
from pathlib import Path

source_path=Path('/Users/zuzu/bin/imessage_herald_bridge.py')
raw=source_path.read_bytes();source=raw.decode()
assert hashlib.sha256(raw).hexdigest()=='0b4753c2823be856d2124566e04e59108f346309d301c9b6cf00962d6418ed4a'
nodes={n.name:n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)}
old=ast.get_source_segment(source,nodes['normalize_sender'])
source=source.replace(old,'def normalize_sender(sender: str) -> str:\n    return strict_normalize_sender(sender)',1)
old=ast.get_source_segment(source,nodes['pending'])
new='''def pending(after: int) -> list[tuple[int, str, str, int]]:
    connection = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=10)
    try:
        return pending_messages(connection, after)
    finally:
        connection.close()'''
source=source.replace(old,new,1)
assert source.count('for rowid, text, sender in rows:')==1
source=source.replace('for rowid, text, sender in rows:','for rowid, text, sender, direct_verified in rows:',1)
assert source.count('if key not in ALLOWED:')==1
source=source.replace('if key not in ALLOWED:',"if not direct_verified or not key or key not in ALLOWED:",1)
source=source.replace('log("message_skipped_unapproved", rowid=rowid)',
 'log("message_skipped_unverified_chat" if not direct_verified else "message_skipped_unapproved", rowid=rowid)',1)
# Insert before the first ordinary definition, after any future imports.
first=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef))
lines=source.splitlines(keepends=True)
lines.insert(first.lineno-1,'from bridge_sender_boundary import normalize_sender as strict_normalize_sender, pending_messages\n\n')
source=''.join(lines);ast.parse(source)
target=Path('/Users/zuzu/backups/sender-boundary-candidate-20261002')
target.mkdir(mode=0o700,exist_ok=False)
(target/'bridge.original.py').write_bytes(raw)
(target/'imessage_herald_bridge.py').write_text(source)
for p in target.iterdir():p.chmod(0o600)
manifest={'baseline_sha256':hashlib.sha256(raw).hexdigest(),'candidate_sha256':hashlib.sha256(source.encode()).hexdigest(),'state':'staged_only','live_source_unchanged':source_path.read_bytes()==raw}
(target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest))
