from pathlib import Path
import shutil,yaml
p=Path('/Users/herald/.hermes/profiles/herald/config.yaml')
backup=Path('/Users/herald/services/gmail-scope-backup-20260909')
backup.mkdir(mode=0o700,exist_ok=True)
if not (backup/'config.yaml').exists():shutil.copy2(p,backup/'config.yaml')
c=yaml.safe_load(p.read_text())
for selected in [c['toolsets'],c['platform_toolsets']['telegram'],c['platform_toolsets']['cli']]:
 if 'windance-gmail' not in selected:selected.append('windance-gmail')
p.write_text(yaml.safe_dump(c,sort_keys=False))
print('Restored only windance-gmail to Herald base, Telegram and CLI tool selections; private backup retained.')
