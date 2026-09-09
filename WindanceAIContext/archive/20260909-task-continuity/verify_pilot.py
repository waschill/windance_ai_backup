import json
from pathlib import Path
rows=json.loads((Path(__file__).resolve().parent / 'goal-pilot/report.json').read_text())
assert len(rows)==3, f'Expected three sources; currently {len(rows)}. Add the missing records.'
assert {r['source'] for r in rows}=={'goals','kanban','memory'}
for row in rows:
    assert row['url'].rstrip('/')=='https://hermes-agent.nousresearch.com/docs/user-guide/features/'+row['source']
    assert all(isinstance(row[k],str) and 15<len(row[k])<2500 for k in ['capability','limitation'])
print('PASS: three source-linked capability/limitation records. Semantic review remains separate.')
