"""Bounded read-only training-note coverage; never export note bodies or identities."""
import datetime
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import re

home = Path.home()
module_path = home/'services/agent-harness/odoo_json2.py'
spec = importlib.util.spec_from_file_location('training_probe_odoo',module_path)
adapter = importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
cfg = json.loads((home/'.config/agent-harness/odoo.json').read_text())
calls = []
def read(method,args,kwargs,model='x_farrier'):
    assert method in {'fields_get','search_count','search_read'}
    assert len(calls)<3
    calls.append(model+'.'+method)
    return adapter.call(cfg,model,method,args,kwargs)
out = {'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'model':'x_farrier',
       'adapter_sha256':hashlib.sha256(module_path.read_bytes()).hexdigest()}
try:
    category = 'x_studio_selection_field_54q_1i29nlfc9'
    fields = ['x_studio_date',category,'x_studio_notes','x_studio_horse','create_uid','create_date']
    schema = read('fields_get',[fields],{'attributes':['type','selection']})
    out['field_types'] = {k:v.get('type') for k,v in schema.items()}
    options = schema.get(category,{}).get('selection',[])
    out['history_category_options'] = options
    selected = [key for key,label in options if re.search(r'train|school',str(label),re.I)]
    out['matched_training_categories'] = selected
    if selected:
        domain = [[category,'in',selected]]
        total = read('search_count',[domain],{})
        rows = read('search_read',[domain],{'fields':fields,'limit':1000,'order':'x_studio_date desc,id desc'})
        notes = [r for r in rows if html.unescape(re.sub('<[^>]+>',' ',str(r.get('x_studio_notes') or ''))).strip()]
        dated = [str(r['x_studio_date'])[:10] for r in notes if r.get('x_studio_date')]
        out['coverage'] = {'total_matching_rows':total,'examined_rows':len(rows),'capped':total>len(rows),
            'nonempty_note_rows':len(notes),'notes_with_horse':sum(bool(r.get('x_studio_horse')) for r in notes),
            'notes_with_creator':sum(bool(r.get('create_uid')) for r in notes),
            'dated_notes':len(dated),'first_note_date':min(dated,default=None),'last_note_date':max(dated,default=None),
            'notes_since_sep22':sum(d>='2026-09-22' for d in dated)}
    else:
        out['limit'] = 'No schema category label matched training/school; no blanket content search performed.'
        out['training_model_metadata'] = read('search_read',[[ '|', ['name','ilike','train'], ['model','ilike','train'] ]],
            {'fields':['model','name'],'limit':20},model='ir.model')
except Exception as exc:
    out['error_type'] = type(exc).__name__
out.update(read_calls=calls,mutation_calls=0,note_bodies_exported=False,identifiers_exported=False)
print(json.dumps(out))
