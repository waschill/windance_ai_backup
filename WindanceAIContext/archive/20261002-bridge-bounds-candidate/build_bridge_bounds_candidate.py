"""Stage exact guarded bridge change only; never install/restart services."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
source=Path('/Users/herald/services/windance-codex-bridge/server.mjs').read_bytes().decode()
assert hashlib.sha256(source.encode()).hexdigest()=='62483284dea6eefe010ea9d34cc4bb4438a6042bb910462f8679ab676ef80c1c'
def replace(old,new):
 global source
 assert source.count(old)==1,old[:60]
 source=source.replace(old,new)
start=source.index('function codexTurn(');end=source.index('\nfunction authorized(',start)
source=source[:start]+(root/'bridge_codex_turn_candidate.js').read_text()+source[end:]
replace("task.current_status='interrupted';task.error_message='Service restarted during execution; reconcile evidence before retry.';",
        "task.current_status='execution_uncertain';task.error_message='Service restarted during execution; remote stop unconfirmed. Reconcile before retry.';")
replace("if(activeJobs.size>=2)return;", "const uncertain=Object.values(state.tasks).filter(t=>t.manager_v2 && t.current_status==='execution_uncertain');\n  if(activeJobs.size+uncertain.length>=2)return;")
replace("const task=candidates.find(t=>![...activeJobs.values()].includes(`${t.requested_by.toLowerCase()}:manager-v2:${t.session}`));",
        "const held=new Set(uncertain.map(t=>`${t.requested_by.toLowerCase()}:manager-v2:${t.session}`));\n  const task=candidates.find(t=>!held.has(`${t.requested_by.toLowerCase()}:manager-v2:${t.session}`) && ![...activeJobs.values()].includes(`${t.requested_by.toLowerCase()}:manager-v2:${t.session}`));")
replace("current_status:error.code==='INTERRUPTED'?'interrupted':'failed'",
        "current_status:error.code==='EXECUTION_UNCERTAIN'?'execution_uncertain':error.code==='INTERRUPTED'?'interrupted':'failed'")
replace("error_message:'Codex turn did not complete; accepted project work is preserved.'",
        "error_message:error.code==='EXECUTION_UNCERTAIN'?'Execution stop unconfirmed; accepted work preserved and conflicting session held.':'Codex turn did not complete; accepted project work is preserved.'")
target=root/'server-candidate.mjs';target.write_text(source);target.chmod(0o600)
print(json.dumps({'candidate_sha256':hashlib.sha256(source.encode()).hexdigest(),'production_changed':False}))
