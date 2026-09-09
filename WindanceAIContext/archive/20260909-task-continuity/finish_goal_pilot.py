import json
import os
from pathlib import Path
import subprocess
import sys
import time

base=Path(__file__).resolve().parent/'goal-pilot'
os.environ['HERMES_HOME']=str(base/'hermes-home')
os.environ.pop('HERMES_PROFILE',None)
os.environ['OPENAI_BASE_URL']='http://192.168.36.10:11434/v1'
os.environ['OPENAI_API_KEY']='ollama'
sys.path.insert(0,'/Users/herald/.hermes/hermes-agent')
from hermes_cli.goals import GoalManager
os.chdir(base)
m=GoalManager('windance-goal-pilot-20260909')
assert m.state.turns_used==3 and m.state.max_turns==4
before=json.loads((base/'receipt.json').read_text())
started=time.monotonic()
m.resume(reset_budget=False)
validation=subprocess.run([sys.executable,str(Path(__file__).with_name('verify_pilot.py'))],capture_output=True,text=True,timeout=10)
assert validation.returncode==0
evidence='The artifact exists. Actual validator output (exit 0):\n'+validation.stdout+'\nActual report.json contents:\n'+(base/'report.json').read_text()+'\nThe requested three-source comparison is complete. No production or external changes occurred.'
d=m.evaluate_after_turn(evidence)
assert m.state.turns_used==4
trace=json.loads((base/'trace.json').read_text())
trace.append({'source':'verification evidence','decision':d,'model_generation_calls':0})
(base/'trace.json').write_text(json.dumps(trace,indent=2))
receipt={**before,'status':m.state.status,'turns_used':m.state.turns_used,'seconds':round(before['seconds']+time.monotonic()-started,2),'validation_exit':0,'budget_was_not_reset':True}
(base/'receipt.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({'decision':d,'receipt':receipt}),flush=True)
