"""Compose private SAM candidate with both intent journals, never import app."""
import ast,hashlib,json,shutil
from pathlib import Path
base=Path('/home/williamschilling/backups/sam-reliability-candidate-20261002/sam_schedule.candidate.private.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='148adcb085f0e51264b3b1d5d811f5d34c2ce8fba5a934b8a27b9c97156ee8a5'
live=Path('/home/williamschilling/services/sam-schedule/sam_schedule.py')
assert hashlib.sha256(live.read_bytes()).hexdigest()=='824026967ab935b2563f0a77021668754fa5969f704e17e3619137a455643bc1'
s=base.read_text();tree=ast.parse(s);candidate=s
for node in tree.body:
 if getattr(node,'name','')=='init_db':
  old=ast.get_source_segment(s,node)
  candidate=candidate.replace(old,old+'\n    from sam_clear_intent import install as install_clear_intents\n    with connect() as clear_db:\n        install_clear_intents(clear_db)')
 elif getattr(node,'name','')=='post_completed_service_history':
  old=ast.get_source_segment(s,node)
  anchor='herald_odoo_write("x_horses", int(horse_id), {needs_field: False})';assert old.count(anchor)==1
  new=old.replace(anchor,'from sam_clear_intent import perform as clear_once\n                clear_once(connect, date_key, item["id"], int(horse_id), service_type, int(history_receipt["odoo_history_id"]) if history_receipt else history_id, lambda: herald_odoo_write("x_horses", int(horse_id), {needs_field: False}))')
  candidate=candidate.replace(old,new)
exclude={'init_db','post_completed_service_history'}
assert [ast.dump(n) for n in tree.body if getattr(n,'name','') not in exclude]==[ast.dump(n) for n in ast.parse(candidate).body if getattr(n,'name','') not in exclude]
root=Path('/home/williamschilling/backups/sam-reliability-r2-20261002');root.mkdir(mode=0o700,exist_ok=True)
p=root/'sam_schedule.candidate.private.py';p.write_text(candidate);p.chmod(0o600)
for name in ['sam_history_intent.py','sam_clear_intent.py']:
 shutil.copyfile(Path('/tmp')/name,root/name);(root/name).chmod(0o600)
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.iterdir()) if p.is_file() and p.name!='manifest.json'}
(root/'manifest.json').write_text(json.dumps(manifest,indent=2));(root/'manifest.json').chmod(0o600)
print(json.dumps({'private_candidate_directory':str(root),'sha256':manifest,'production_changes':False}))
