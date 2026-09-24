from pathlib import Path
import shutil
p=Path('/Users/zuzu/bin/start-node-red.sh')
backup=Path('/Users/zuzu/services/maintenance-recovery-20260924/start-node-red.before-pin.sh')
if not backup.exists(): shutil.copy2(p, backup)
s=p.read_text()
assert s.count('/opt/homebrew/bin/node ')==1
p.write_text(s.replace('/opt/homebrew/bin/node ', '/opt/homebrew/Cellar/node/26.8.1/bin/node '))
print('Node-RED launcher restored to Node 26.8.1; other configuration preserved')
