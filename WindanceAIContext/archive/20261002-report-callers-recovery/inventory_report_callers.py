"""Read-only code references; output paths and key-marker presence, never source."""
import json,os
from pathlib import Path
matches=[];skipped=0
for base in ('/Users/herald/bin','/Users/herald/services','/Users/herald/Library/LaunchAgents'):
    for directory,dirs,files in os.walk(base,followlinks=False):
        dirs[:]=[d for d in dirs if d not in ('.git','venv','.venv','node_modules','backups','__pycache__')]
        for name in files:
            p=Path(directory)/name
            if p.suffix not in ('.py','.sh','.plist') or p.is_symlink():continue
            try:
                if p.stat().st_size>2*1024*1024:skipped+=1;continue
                data=p.read_bytes()
                if b'windance_report_send.py' in data:
                    matches.append({'path':str(p),'delivery_key_literal_present':b'WINDANCE_DELIVERY_KEY' in data})
            except OSError:skipped+=1
print(json.dumps({'references':matches,'skipped_files':skipped,'static_presence_not_dataflow_proof':True}))
