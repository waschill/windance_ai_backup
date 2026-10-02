"""Offline verification of fixed diagnostic evidence; never starts or retries work."""
import hashlib,json,re,sys
from pathlib import Path
IMAGE='sha256:9591b13f13843c7721c2b8eaf7382846c81b3ffe126526d1888d1fed50c6a33f'
def read_json(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size>65536:raise ValueError('Bounded regular file required')
    return json.loads(path.read_text())
def inspect(job):
    job=Path(job)
    base={'replay_authorized':False,'live_worker_state':'not_observed','evidence_trust':'local operator files, not cryptographic attestation'}
    try:
        m=read_json(job/'input-manifest.json')
        if set(m)!={'bounded_diagnosis_worker.py','failure.json'}:raise ValueError('Unexpected manifest')
        for name,digest in m.items():
            p=job/'inputs'/name
            if p.is_symlink() or p.stat().st_size>65536 or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:raise ValueError('Input drift')
        identity=read_json(job/'container.json'); terminal=read_json(job/'terminal.json')
        if not re.fullmatch('[0-9a-f]{64}',identity['id']):raise ValueError('Invalid identity')
        if terminal['container_id']!=identity['id'] or terminal['image']!=IMAGE or identity['image']!=IMAGE:raise ValueError('Identity drift')
        if terminal['input_hashes']!=m or terminal['worker_running'] is not False:raise ValueError('Incomplete terminal evidence')
        state=terminal['outcome']
        if state=='completed':
            p=job/'result.json';result=read_json(p)
            if terminal['exit_code']!=0 or hashlib.sha256(p.read_bytes()).hexdigest()!=terminal['result_sha256']:raise ValueError('Result drift')
            if result['status'] not in ('diagnosed','insufficient_evidence') or result['evidence']!=read_json(job/'inputs'/'failure.json'):raise ValueError('Unsupported result')
            if result['status']=='insufficient_evidence' and any(result.get(k) is not None for k in ('cause','repair_proposal','rollback')):raise ValueError('Unsupported cause or repair')
        elif state in ('timed_out','cancelled'):
            if terminal['exit_code']!=137 or terminal['result_sha256'] is not None or (job/'result.json').exists():raise ValueError('Contradictory result')
        else:raise ValueError('Unknown terminal state')
        return {**base,'verification':'verified_record','recorded_outcome':state,
                'diagnostic_status':result['status'] if state=='completed' else None}
    except (OSError,ValueError,KeyError,TypeError):
        return {**base,'verification':'unknown','reason':'Missing, changed or unsupported evidence; do not infer success or retry.'}
if __name__=='__main__':print(json.dumps(inspect(sys.argv[1])))
