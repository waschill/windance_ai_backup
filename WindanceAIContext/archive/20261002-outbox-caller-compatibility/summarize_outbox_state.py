"""Aggregate outbox file state only, no identifiers/recipients/bodies in output."""
import json
from pathlib import Path
root=Path.home()/'.local/share/windance-imessage-outbox'
result={}
for folder in ('queue','inflight','uncertain','results','claims'):
    counts={'files':0,'read':0,'invalid_or_oversize':0,'sms_true':0,'sms_false':0,'missing_sms':0,
            'keyed_names':0,'legacy_ok':0,'uncertain_status':0,'versioned_delivered':0,'limited':False}
    for path in (root/folder).glob('*.json'):
        counts['files']+=1
        if counts['read']>=1000:counts['limited']=True;continue
        if path.name.startswith('key-'):counts['keyed_names']+=1
        try:
            if path.stat().st_size>2*1024*1024:raise ValueError()
            value=json.loads(path.read_text());counts['read']+=1
            if type(value) is not dict:raise ValueError()
            if value.get('sms') is True:counts['sms_true']+=1
            elif value.get('sms') is False:counts['sms_false']+=1
            else:counts['missing_sms']+=1
            if value.get('ok') is True and 'version' not in value:counts['legacy_ok']+=1
            if value.get('status')=='uncertain':counts['uncertain_status']+=1
            if value.get('version')==2 and value.get('status')=='delivered':counts['versioned_delivered']+=1
        except (OSError,ValueError):counts['invalid_or_oversize']+=1
    result[folder]=counts
print(json.dumps(result))
