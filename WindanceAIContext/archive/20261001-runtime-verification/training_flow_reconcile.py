import datetime
import hashlib
import json
from pathlib import Path

current_path = Path('/Users/zuzu/.node-red/flows.json')
prior_path = Path('/Users/zuzu/services/photos-status-20260930/before-flows.json')
raw, prior = current_path.read_bytes(), prior_path.read_bytes()
current = {n['id']:n for n in json.loads(raw)}
before = {n['id']:n for n in json.loads(prior)}
targets = ['wr_train_format','wr_train_send','wr_train_exec','wr_train_eod_memory_format']
changed = sorted(k for k in current.keys()|before.keys() if current.get(k)!=before.get(k))
out = {'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'current_saved_flow_sha256':hashlib.sha256(raw).hexdigest(),
       'prior_saved_flow_sha256':hashlib.sha256(prior).hexdigest(),
       'changed_node_ids':changed,
       'training_targets_unchanged':all(current.get(k)==before.get(k) and k in current for k in targets),
       'training_target_hashes':{k:hashlib.sha256(json.dumps(current[k],sort_keys=True).encode()).hexdigest() for k in targets},
       'runtime_revision_verified':False, 'production_modified':False}
print(json.dumps(out))
