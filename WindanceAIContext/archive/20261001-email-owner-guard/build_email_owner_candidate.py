"""Prepare private candidate from exact current source, never install."""
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path('/Users/herald/services/email-owner-boundary-20261001')
SOURCE=Path('/Users/herald/services/agent-harness/agent_harness.py')
expected='709118f2ae2bf9df5d429e1343c06d709707f8f422db54058085801fca0e3aa7'
raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==expected
source=raw.decode();tree=ast.parse(source)
guarded={
 'request_approval','get_approval','find_pending_approval','latest_pending_approval',
 'approve_pending','always_allow_pending','reject_pending','execute_approved_action',
 'gmail_service','save_email_report_refs','latest_email_ref_map','consume_latest_email_ref_map',
 'upsert_email_sender_rule','upsert_email_domain_rule','email_sender_rules',
 'max_email_tracking_report','gmail_autonomy_report','summarize_email_for_william',
}
functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
assert guarded<=functions.keys()
lines=source.splitlines(keepends=True);edits=[]
for name in guarded:
 n=functions[name];first=n.body[0]
 if isinstance(first,ast.Expr) and isinstance(first.value,ast.Constant) and isinstance(first.value.value,str):
  index=first.end_lineno
 else:index=first.lineno-1
 edits.append((index,'    require_william_mailbox()\n'))
n=functions['message_sync'];edits.append((n.lineno-1,'@bind_mailbox_owner\n'))
first=min(n.lineno for n in functions.values());edits.append((first-1,'from email_owner_boundary import bind_mailbox_owner, require_william_mailbox, EmailOwnerBoundaryError\n\n'))
for index,text in sorted(edits,reverse=True):lines.insert(index,text)
candidate=''.join(lines)
# The old eager parser looked up William references even for unrelated text.
start=candidate.index('def process_numbered_gmail_pin_decisions(');end=candidate.index('\ndef ',start+1)
part=candidate[start:end];assert part.count('    refs = latest_email_ref_map()\n')==1
part=part.replace('    refs = latest_email_ref_map()\n','')
anchor='    if not decisions:\n        return None\n';assert anchor in part
part=part.replace(anchor,anchor+'    refs = latest_email_ref_map()\n',1);candidate=candidate[:start]+part+candidate[end:]
# These parsers query private approval rows directly only after matching intent.
for name in ['approve_latest_gmail_send_with_auth_word','approve_spoken_gmail_send','reject_spoken_gmail_send']:
 start=candidate.index('def '+name+'(');end=candidate.index('\ndef ',start+1);part=candidate[start:end]
 assert '    with db() as conn:\n' in part
 part=part.replace('    with db() as conn:\n','    require_william_mailbox()\n    with db() as conn:\n',1)
 candidate=candidate[:start]+part+candidate[end:]
anchor='    except Exception as exc:\n        audit("message_error",'
assert candidate.count(anchor)==1
candidate=candidate.replace(anchor,'    except EmailOwnerBoundaryError:\n        raise\n'+anchor)
ast.parse(candidate)
ROOT.mkdir(mode=0o700,exist_ok=False)
(ROOT/'agent_harness.py').write_text(candidate);(ROOT/'agent_harness.py').chmod(0o600)
manifest={'baseline_sha256':expected,'candidate_sha256':hashlib.sha256(candidate.encode()).hexdigest(),'guarded_functions':sorted(guarded),'state':'staged_only','source_path':str(SOURCE)}
(ROOT/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest))
