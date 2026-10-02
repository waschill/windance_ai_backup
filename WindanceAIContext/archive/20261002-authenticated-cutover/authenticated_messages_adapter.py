"""Staged SAL adapter helper. Caller retains installed sender/direct-chat checks."""
import json
from urllib.parse import urlsplit
import urllib.request
import urllib.error


def submit(endpoint, credential, owner, rowid, text, *, open_request=urllib.request.urlopen):
    destination = urlsplit(endpoint)
    if destination.username or destination.password or destination.query or destination.fragment:
        raise ValueError('Clean configured intake URL required')
    if destination.scheme != 'https' and not (destination.scheme == 'http' and destination.hostname in {'127.0.0.1', '::1'}):
        raise ValueError('TLS or loopback protected transport required')
    if not isinstance(credential,str) or not credential or any(ch.isspace() for ch in credential):
        raise ValueError('Configured adapter credential required')
    if owner not in {'William', 'Shawn'} or not isinstance(rowid,int) or isinstance(rowid,bool) or rowid < 1:
        raise ValueError('Verified owner and stable Messages row required')
    request = urllib.request.Request(endpoint, data=json.dumps({
        'owner':owner.lower(), 'source_id':'max-imessage:'+str(rowid), 'message':text
    }).encode(), headers={'Content-Type':'application/json','Authorization':'Bearer '+credential}, method='POST')
    try:
        with open_request(request, timeout=180) as response:
            if response.status != 202:
                raise RuntimeError('Authenticated intake did not accept the request')
            receipt=json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code != 422:
            raise
        rejection=json.loads(exc.read().decode())
        if rejection != {'status':'rejected','reason':'content_policy','stored':False}:
            raise
        return 'Vega: I did not store or queue that request because it failed the memory content policy. Keep passwords, keys and codes out of memory.'
    identifier=receipt.get('id','')
    if (receipt.get('status') != 'accepted' or not isinstance(identifier,str) or
        identifier != 'max-imessage:'+str(rowid) or
        receipt.get('source_ref') != 'manager-message:'+identifier):
        raise RuntimeError('Invalid authenticated source receipt')
    # Preserve the installed immediate acknowledgment. Manager owns later answer.
    return 'Vega: Received. I will follow up with the answer or a specific blocker.'
