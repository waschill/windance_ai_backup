"""Archivist's approved idempotent shared-memory registration with read-back."""
import json
import urllib.request
from pathlib import Path
path=Path('/Users/herald/knowledge/WindanceAIContext/projects/WARDEN_SUPERVISOR_2026-09-24.md')
assert path.exists()
payload={'kind':'operations','key':'warden-independent-supervisor',
 'value':'Warden is William\'s independent supervisor on SAL. Runtime and live incident history: /Users/zuzu/services/windance-supervisor. '
         'Read projects/WARDEN_SUPERVISOR_2026-09-24.md in WindanceAIContext; Work board has Supervisor link. '
         'Pause before maintenance and wait for pause completion. Polling is configured every 120 seconds, independently of review work. '
         'William requires BOTH background Codex/Vega and private Claude to approve the SAME exact repair before Warden executes it. '
         'Disagreement, missing review, expired/changed proposal or uncertainty holds for William; never interpret silence as approval. '
         'Known service operations only; no arbitrary automatic code deployment. Read live status for activation and incident state. '
         'Keep direct SAL iMessage outbox route (William deferred Herald Messages). '
         'HAL canonical publisher distributes to Production/HAL/Herald/SAL and verifies Second Brain indexing. '
         'Harness staff tasks remain authoritative; Warden owns incidents only. No private memories or credentials are shared.',
 'confidence':1.0,'source':'Archivist:warden-installation:2026-09-24'}
req=urllib.request.Request('http://127.0.0.1:8791/memory',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req,timeout=30) as r: saved=json.load(r)
with urllib.request.urlopen('http://127.0.0.1:8791/memory',timeout=30) as r: memory=json.load(r)
assert payload['key'] in json.dumps(memory), 'Shared memory readback failed'
receipt={'saved':saved,'readback':True,'key':payload['key'],'source_document':str(path),
         'file_index_publication':'Vega must verify HAL publisher separately'}
Path('/Users/herald/services/windance-supervisor/archivist-memory-receipt.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt))
