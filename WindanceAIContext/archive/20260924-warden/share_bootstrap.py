"""Append public Warden discovery pointers; preserve every existing instruction."""
import json
import shutil
from pathlib import Path
home=Path.home()
backup=home/'services/windance-supervisor/backups/bootstrap'
backup.mkdir(parents=True,exist_ok=True)
pointer='''

## Warden independent supervision — 2026-09-24

Warden is William's independent supervisor on SAL, outside Herald's Harness.
For health/recovery work read projects/WARDEN_SUPERVISOR_2026-09-24.md in the
shared WindanceAIContext package. Live incident authority is SAL:
/Users/zuzu/services/windance-supervisor/status.json and incidents.sqlite.
Herald's read-only mirror is /Users/herald/.local/share/windance-supervisor/status.json;
check its timestamp. The Work board has a Supervisor link. Pause Warden before
planned maintenance and resume afterward. Do not confuse incidents with staff
tasks or claim model advice is an executed repair. Warden is not a Hermes queue
worker. Keep private memories isolated. Existing authorities remain unchanged.
'''
targets=[home/'.codex/AGENTS.md']
if home.name=='herald':
    targets += [p/'SOUL.md' for p in (home/'.hermes/profiles').iterdir() if p.is_dir() and (p/'SOUL.md').exists()]
    if (home/'.hermes/SOUL.md').exists(): targets.append(home/'.hermes/SOUL.md')
changed=[]
for path in targets:
    original=path.read_text() if path.exists() else ''
    if '## Warden independent supervision — 2026-09-24' in original: continue
    relative=str(path.relative_to(home)).replace('/','__')
    (backup/relative).write_text(original)
    prefix=''
    if home.name=='zuzu' and not original.strip():
        prefix='''# Windance bootstrap on SAL

For Windance, Reflectsody, AI staff, Hermes, Odoo, Google Workspace, Node-RED,
SAM or named network-node work, first read
/Users/zuzu/knowledge/WindanceAIContext/START_HERE.md and its required reading order.
If unavailable, retrieve /Users/herald/knowledge/WindanceAIContext/START_HERE.md
through the configured HERALD SSH alias. Verify live state before changes.
Never disclose/store credentials. Do not alter SyncThing or the disabled hazardous
Level 8 shutdown system without William's explicit current-turn request.
Claude reviews remain suspended by William since 2026-09-18. Read the current
policy in the shared package before stack changes. Preserve and verify changes.
Canonical publication is performed on HAL from the private windance_ai_backup
repository via scripts/publish-windance-context.ps1 -PushGit; verify Second Brain
retrieval. Never treat a local draft or a mirrored file as verified publication.
'''
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(original+prefix+pointer)
    changed.append(str(path))
print(json.dumps({'updated_instruction_files':len(changed),'paths':changed}))
