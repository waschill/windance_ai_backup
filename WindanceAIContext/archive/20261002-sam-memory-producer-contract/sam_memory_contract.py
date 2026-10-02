"""Staged narrow producer admission, not storage, migration or human identity."""
import datetime,hashlib,hmac,json,math
class ProducerDenied(PermissionError):pass
def admit(authorization,credential,payload,validate_content):
    if not isinstance(credential,str) or len(credential)<32 or any(c.isspace() for c in credential):
        raise ValueError('Dedicated configured service credential required')
    if not isinstance(authorization,str) or len(authorization)>512 or not authorization.startswith('Bearer '):
        raise ProducerDenied('SAM producer credential required')
    if not hmac.compare_digest(authorization[7:].encode(),credential.encode()):
        raise ProducerDenied('SAM producer credential required')
    if not isinstance(payload,dict) or set(payload)!={'kind','key','value','confidence','source'}:
        raise ProducerDenied('Only the established SAM record shape is allowed')
    if payload['kind']!='sam_daily_schedule':raise ProducerDenied('Unsupported producer kind')
    key=payload['key']
    if not isinstance(key,str) or len(key)!=10:raise ProducerDenied('Canonical date required')
    try:
        if datetime.date.fromisoformat(key).isoformat()!=key:raise ValueError()
    except ValueError:raise ProducerDenied('Canonical date required') from None
    value=payload['value']
    if not isinstance(value,str) or not value.strip() or len(value.encode())>65536:
        raise ProducerDenied('Bounded nonempty producer summary required')
    confidence=payload['confidence']
    if type(confidence) not in (int,float) or not math.isfinite(confidence) or confidence!=0.92:
        raise ProducerDenied('Unexpected producer confidence')
    if payload['source']!='SAM schedule display':raise ProducerDenied('Unexpected producer source')
    if not callable(validate_content) or validate_content(value) is not True:
        raise ProducerDenied('Producer content rejected')
    return {'producer':'sam','scope':'business','kind':'sam_daily_schedule','key':key,
            'value':value,'source':'SAM schedule display','source_ref':'sam:daily-schedule:'+key,
            'content_sha256':hashlib.sha256(value.encode()).hexdigest(),
            'human_owner':None,'independently_verified':False}
