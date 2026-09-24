from pathlib import Path
import importlib.util
import sys

target = Path('/Users/herald/services/profile-staff-runner/profile_staff_runner.py')
before = Path('/Users/herald/services/maintenance-recovery-20260924/profile_staff_runner.before.py')
if not before.exists():
    before.write_bytes(target.read_bytes())
source = target.read_text()
anchor = '        research_rules += FORGE_CONTRACT\n'
replacement = anchor + '''        research_rules += """
Remote execution contract: Each terminal call starts a fresh LOCAL shell on
HERALD. A prior ssh command never changes the host of later terminal calls.
EVERY command for SAL must use ssh SAL 'command'; EVERY command for HAL must
use ssh HAL with Windows PowerShell syntax; AL and SAM likewise require their
SSH aliases on every call. Never run a remote host's absolute paths locally.
SAL uses /opt/homebrew/bin and /Users/zuzu/.node-red; its runtime is
/Users/zuzu/node-red-runtime. HAL's backup script is
C:/Users/wasch/Documents/Codex/2026-06-19/i-need-you-to-go-through/windance_ai_backup_repo/WindanceAIContext/scripts/Invoke-WindancePreUpgradeBackup.ps1
and must be invoked through ssh HAL powershell.exe -NoProfile -ExecutionPolicy
Bypass -File followed by that full path. Remote paths cannot be found using
local search_files. Do not infer missing software or request extra privileges
from a wrong-host PATH error. Verify on the target host using SSH first.
These facts do not expand the task's authorization or permitted scope.
"""
'''
if 'Remote execution contract:' not in source:
    if source.count(anchor) != 1:
        raise SystemExit('Expected exactly one Forge prompt insertion point')
    source = source.replace(anchor, replacement)
compile(source, str(target), 'exec')
source = source.replace('SAL uses /opt/homebrew/bin and /Users/zuzu/.node-red; its runtime is',
    'For SAL commands, export PATH=/opt/homebrew/bin:/usr/bin:/bin inside the\n'
    'remote quoted command, because npm uses env node in its shebang.\n'
    'SAL uses /opt/homebrew/bin and /Users/zuzu/.node-red; its runtime is') if 'because npm uses env node' not in source else source
compile(source, str(target), 'exec')
stage = target.with_name('profile_staff_runner.host-context-stage.py')
stage.write_text(source)
sys.path.insert(0, str(target.parent))
spec = importlib.util.spec_from_file_location('host_context_test', stage)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
base = {'id':'read-only-prompt-test','title':'prompt check','request':'No execution'}
forge = module.task_prompt(dict(base, assignee='Forge'))
sentinel = module.task_prompt(dict(base, assignee='Sentinel'))
assert 'Remote execution contract:' in forge
assert "EVERY command for SAL must use ssh SAL 'command'" in forge
assert 'Remote execution contract:' not in sentinel
assert 'read-only-prompt-test' in forge
target.write_text(source)
print('PASS: compile and Forge-specific prompt tests; no live task executed by test')
