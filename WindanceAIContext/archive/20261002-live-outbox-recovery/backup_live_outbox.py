"""Stable read-only private outbox snapshot; never takes producer/daemon locks."""
import hashlib
import json
import os
from pathlib import Path
import time
import zipfile

source=Path.home()/'.local/share/windance-imessage-outbox'
folders=('queue','claims','results','inflight','uncertain')


def snapshot():
    files={};counts={}
    for folder in folders:
        paths=sorted((source/folder).glob('*.json'))
        if len(paths)>2000:raise RuntimeError('inventory_cap')
        if list((source/folder).glob('*.tmp')):raise RuntimeError('publication_in_progress')
        counts[folder]=len(paths)
        for path in paths:
            if path.stat().st_size>2*1024*1024:raise RuntimeError('file_cap')
            files['state/'+folder+'/'+path.name]=path.read_bytes()
    for name in ('imessage_outbox_daemon.py','send_imessage_payload.py'):
        files['code/'+name]=(Path.home()/'bin'/name).read_bytes()
    if sum(map(len,files.values()))>32*1024*1024:raise RuntimeError('total_cap')
    return files,counts


first,counts=snapshot()
timestamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())
destination=Path.home()/'backups'/('outbox-preintegration-'+timestamp)
destination.mkdir(mode=0o700,parents=True,exist_ok=False)
os.chmod(destination,0o700)
for name,content in first.items():
    path=destination/name;path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    path.write_bytes(content);os.chmod(path,0o600)
second,counts_after=snapshot()
assert first==second and counts==counts_after,'live_state_changed_backup_unverified'
manifest={name:hashlib.sha256(content).hexdigest() for name,content in first.items()}
(destination/'private-manifest.json').write_text(json.dumps(manifest,sort_keys=True))
os.chmod(destination/'private-manifest.json',0o600)
archive=destination/'outbox-private.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for name in sorted(manifest):z.write(destination/name,name)
    z.write(destination/'private-manifest.json','private-manifest.json')
os.chmod(archive,0o600)
restored=destination/'isolated-restoration';restored.mkdir(mode=0o700)
with zipfile.ZipFile(archive) as z:z.extractall(restored)
for name,digest in manifest.items():assert hashlib.sha256((restored/name).read_bytes()).hexdigest()==digest
third,counts_final=snapshot()
assert first==third and counts==counts_final,'live_state_changed_after_verification'
summary={'status':'verified_stable_snapshot','destination':str(destination),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
         'files':len(manifest),'counts':counts,'daemon_sha256':manifest['code/imessage_outbox_daemon.py'],
         'producer_sha256':manifest['code/send_imessage_payload.py'],'sending_enabled_in_restore':False,
         'live_state_stable_across_three_reads':True,'full_host_backup':False}
(destination/'public-summary.json').write_text(json.dumps(summary))
print(json.dumps(summary))
