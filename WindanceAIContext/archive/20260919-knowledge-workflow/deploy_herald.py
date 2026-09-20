from pathlib import Path
import json
import shutil
import yaml

home=Path('/Users/herald')
base=home/'services/knowledge-workflow-20260919'
targets={'agent_harness.py':home/'services/agent-harness/agent_harness.py',
 'herald_staff_mcp.py':home/'services/herald-staff-mcp/herald_staff_mcp.py',
 'plugin_api.py':home/'.hermes/plugins/windance-vega-desktop/dashboard/plugin_api.py'}
for name,target in targets.items():
    if target.read_bytes() != (base/'before'/name).read_bytes():
        raise RuntimeError(f'Live file changed after backup: {name}')
for name,target in targets.items():shutil.copy2(base/'staged'/name,target)

root_path=home/'.hermes/config.yaml'
profile_path=home/'.hermes/profiles/herald/config.yaml'
root=yaml.safe_load(root_path.read_text()); profile=yaml.safe_load(profile_path.read_text())
backup={'root_include':root['mcp_servers']['herald-staff']['tools']['include'],
 'profile_server':profile.get('mcp_servers',{}).get('herald-staff'),
 'profile_toolsets':profile.get('toolsets'), 'profile_platform_toolsets':profile.get('platform_toolsets')}
(base/'before/selected-tool-settings.json').write_text(json.dumps(backup,indent=2))
newtools=['capture_idea','list_ideas','review_idea']
root['mcp_servers']['herald-staff']['tools']['include']=list(dict.fromkeys(backup['root_include']+newtools))
# Use a minimal server declaration for Herald; preserve every other setting.
profile.setdefault('mcp_servers',{})['herald-staff']={
 'command':'/Users/herald/services/google-workspace-mcp/.venv/bin/python',
 'args':['/Users/herald/services/herald-staff-mcp/herald_staff_mcp.py'],
 'enabled':True,'tools':{'include':newtools}}
profile['toolsets']=list(dict.fromkeys(profile.get('toolsets',[])+['herald-staff']))
for platform in ['cli','telegram']:
    selections=profile.setdefault('platform_toolsets',{}).setdefault(platform,[])
    if 'herald-staff' not in selections:selections.append('herald-staff')
root_path.write_text(yaml.safe_dump(root,sort_keys=False))
profile_path.write_text(yaml.safe_dump(profile,sort_keys=False))

policy='''

## Ideas, SOPs and decision records — William 2026-09-19

Read /Users/herald/knowledge/WindanceAIContext/operations/README.md for the shared workflow.
When William says Idea: ... or asks to save a thought to the Idea Board, capture it using capture_idea (herald-staff). Report the returned CAP receipt. Never create a Kanban card, staff task, placeholder or implementation plan in place of saving an idea. The board is non-executing; staff may assess and archive with a reason. review_idea archive retains content; never substitute capture discard. Private captures and Jim's content are excluded. Show/list ideas via list_ideas; paginate until empty for a complete review.
After repeatable fixes or process changes, submit a Draft SOP using the canonical template and intake queue. Archivist owns structure/indexing; Forge checks technical accuracy. An SOP contribution is not accepted until both actual review receipts exist. Do not call untested operational steps verified. Existing Claude review suspension remains unchanged.
Weekly reviews require a decision log with topic, disposition, evidence, rationale, owner, measurable next step and revisit date. Athena checks it; Herald signs off coordination; Archivist preserves it. Recommendations are not execution authorization. Never claim a save, delegation, sign-off or completion without a durable receipt.
'''
for name in ['herald','forge','archivist','athena','scout','sentinel','max','iris','ledger']:
    path=home/'.hermes/profiles'/name/'SOUL.md'
    text=path.read_text()
    if '## Ideas, SOPs and decision records — William 2026-09-19' in text:raise RuntimeError('Policy already installed')
    path.write_text(text+policy)
print('Deployed source, selected tool registration and operational profile instructions')
