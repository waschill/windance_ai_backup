"""Finish the already downloaded, signed Sparkle update by quitting normally."""
import json
import plistlib
import subprocess
import time
from pathlib import Path

app=Path('/Applications/Codex.app')
before=plistlib.loads((app/'Contents/Info.plist').read_bytes())['CFBundleShortVersionString']
p=subprocess.run(['/usr/bin/osascript','-e','tell application id "com.openai.codex" to quit'],capture_output=True,text=True,timeout=30)
if p.returncode: raise RuntimeError('Normal app quit failed')
for _ in range(45):
    time.sleep(1)
    for candidate in (Path('/Applications/ChatGPT.app'),Path('/Applications/Codex.app')):
        info=candidate/'Contents/Info.plist'
        if info.exists():
            version=plistlib.loads(info.read_bytes())['CFBundleShortVersionString']
            if version != before:
                subprocess.run(['/usr/bin/codesign','--verify','--deep','--strict',str(candidate)],check=True)
                subprocess.run(['/usr/bin/open','-a',str(candidate)],check=True)
                print(json.dumps({'before':before,'after':version,'path':str(candidate)}))
                raise SystemExit(0)
raise RuntimeError('Sparkle update did not complete; app backup preserved')
