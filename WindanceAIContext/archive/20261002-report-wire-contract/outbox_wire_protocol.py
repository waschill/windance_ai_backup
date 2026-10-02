"""Versioned trusted SSH result contract; no sends or credentials."""
import hashlib,json

CODES={'verified_delivery':0,'pending':10,'uncertain':11,'legacy_submission':12,
       'conflict':13,'unknown':14,'unavailable':15}

def identity(key,payload):
    if type(key) is not str or not key.strip() or len(key)>512:raise ValueError('invalid_key')
    return ('key-'+hashlib.sha256(key.encode()).hexdigest(),
            hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest())

def envelope(key,payload,result):
    request_id,fingerprint=identity(key,payload)
    if type(result) is not dict or result.get('status') not in CODES:raise ValueError('invalid_result')
    # Never echo arbitrary worker exception text or private input.
    safe={'status':result['status']}
    if result['status']=='verified_delivery':
        if (result.get('independent_delivery_verified') is not True or
            type(result.get('chunks')) is not int or result['chunks']!=len(payload['chunks'])):
            raise ValueError('invalid_verified_result')
        safe.update(independent_delivery_verified=True,chunks=result['chunks'])
    return {'version':1,'request_id':request_id,'content_sha256':fingerprint,'result':safe}

def parse_response(raw,exit_code,key,payload):
    if len(raw)>4096:raise ValueError('response_cap')
    value=json.loads(raw)
    request_id,fingerprint=identity(key,payload)
    if (type(value) is not dict or set(value)!={'version','request_id','content_sha256','result'} or
        type(value['version']) is not int or value['version']!=1 or value['request_id']!=request_id or
        value['content_sha256']!=fingerprint):raise ValueError('response_identity')
    canonical=envelope(key,payload,value['result'])
    if value!=canonical or type(exit_code) is not int or exit_code!=CODES[value['result']['status']]:
        raise ValueError('response_contract')
    return value['result']
