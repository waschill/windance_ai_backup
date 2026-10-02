"""Prepare private sender-sweep failure handling on exact current candidate."""
import ast,hashlib,json,shutil
from pathlib import Path
prior=Path(r'C:\Users\wasch\Documents\WindanceBaselineRecovery\20261002-email-route-package')
root=Path('email-sweep-hold-private')
s=(prior/'candidate.private.py').read_text(encoding='utf-8')
assert hashlib.sha256((prior/'candidate.private.py').read_bytes()).hexdigest()=='4600e59f380d1de53e42fff2535e9865eb4e2b97dc1739313a6291e4c37c54b7'
original=s;before=ast.parse(s)
for node in before.body:
    if getattr(node,'name','')=='gmail_sender_rule_sweep':
        old=ast.get_source_segment(original,node)
        target='''        except Exception as exc:
            errors.append(f"{address}: {str(exc)[:160]}")
            audit("gmail_sender_rule_sweep_fetch_error", {"sender": address, "error": str(exc)[:500]})'''
        assert old.count(target)==1
        replacement='''        except Exception:
            result = {"status": "held", "rules": len(active_rules), "checked": len(items),
                      "deleted": 0, "kept": len(items), "notices": [],
                      "errors": ["Mailbox listing unavailable; sweep held before changes"]}
            audit("gmail_sender_rule_sweep_fetch_error", {"status": "held", "checked": len(items)})
            return result'''
        new=old.replace(target,replacement).replace(').execute()',').execute(num_retries=0)')
        s=s.replace(old,new)
    elif getattr(node,'name','')=='post_gmail_sender_rule_sweep':
        old=ast.get_source_segment(original,node)
        target='''    except Exception as exc:
        audit("gmail_sender_rule_sweep_error", {"error": str(exc)[:500]})
        raise HTTPException(status_code=502, detail=str(exc)[:1500]) from exc'''
        assert old.count(target)==1
        replacement='''    except Exception:
        audit("gmail_sender_rule_sweep_error", {"status": "unavailable"})
        raise HTTPException(status_code=502, detail="Mailbox sweep outcome unavailable; inspect recovery status before retrying") from None'''
        s=s.replace(old,old.replace(target,replacement))
after=ast.parse(s);changed={'gmail_sender_rule_sweep','post_gmail_sender_rule_sweep'}
assert [ast.dump(n) for n in before.body if getattr(n,'name','') not in changed]==[ast.dump(n) for n in after.body if getattr(n,'name','') not in changed]
compile(s,'<email-sweep-hold>','exec');root.mkdir()
(root/'agent_harness.candidate.private.py').write_text(s,encoding='utf-8',newline='\n')
m=json.loads((prior/'manifest.private.json').read_text())
for name,digest in m.items():
    if name.endswith('.py') and name not in ('candidate.private.py','original.private.py'):
        assert hashlib.sha256((prior/name).read_bytes()).hexdigest()==digest
        shutil.copy2(prior/name,root/name)
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'files':len(manifest),'candidate_sha256':manifest['agent_harness.candidate.private.py'],'production_changes':False}))
