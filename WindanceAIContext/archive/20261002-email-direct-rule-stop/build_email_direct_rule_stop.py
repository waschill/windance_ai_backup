"""Stage fail-stop numbered sender-rule handling; never touch production."""
import ast, hashlib, json, shutil
from pathlib import Path
src = Path('/Users/herald/backups/email-direct-rule-intent-20261002')
dst = Path('/Users/herald/backups/email-direct-rule-stop-20261002')
manifest = json.loads((src/'manifest.json').read_text())
assert manifest['agent_harness.candidate.private.py'] == '220379118346add7c2ff8229fe6af5a77be5114dbaeb59852f9644c706153b8b'
assert all(hashlib.sha256((src/n).read_bytes()).hexdigest() == v for n,v in manifest.items())
text = (src/'agent_harness.candidate.private.py').read_text()
before = ast.parse(text)
target = next(n for n in before.body if getattr(n, 'name', '') == 'prepare_gmail_report_reply_actions')
segment = ast.get_source_segment(text, target)
for action in ('always delete', 'notify delete'):
    old = f'            lines.append(f"- {action} requires verification for {{label}}. The sender rule may have been saved and the mailbox change may have occurred; do not repeat blindly.")'
    assert segment.count(old) == 1
    segment = segment.replace(old, old + '\n            lines.append("Stopped processing the remaining instructions. Verify this action before continuing.")\n            return "\\n".join(lines), "deterministic", "gmail-summary-held"')
text = text.replace(ast.get_source_segment(text, target), segment, 1)
after = ast.parse(text)
assert [ast.dump(n) for n in before.body if n is not target] == [ast.dump(n) for n in after.body if getattr(n,'name','') != target.name]
compile(text, '<staged-harness>', 'exec')
dst.mkdir(mode=0o700, exist_ok=False)
for name in manifest:
    shutil.copy2(src/name, dst/name)
(dst/'agent_harness.candidate.private.py').write_text(text)
updated = {name: hashlib.sha256((dst/name).read_bytes()).hexdigest() for name in manifest}
(dst/'manifest.json').write_text(json.dumps(updated, indent=2)+'\n')
print(json.dumps({'stage':str(dst),'candidate_sha256':updated['agent_harness.candidate.private.py'],'files':len(updated)}))
