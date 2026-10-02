"""Bounded read-only draft lookup. Never create, send, delete or release a hold."""
import base64,hashlib,json,re
from email import policy
from email.parser import BytesParser
from email.message import EmailMessage
def marker(key):
    if not isinstance(key,str) or not re.fullmatch('[0-9a-f]{64}',key):raise ValueError('Exact operation key required')
    return '<windance-'+key+'@windance.invalid>'
def fingerprint(raw):
    message=BytesParser(policy=policy.default).parsebytes(raw)
    if message.defects or message.is_multipart() or message.get_content_type()!='text/plain':raise ValueError('Unsupported or malformed draft')
    for name in ['To','Subject','Message-ID']:
        if len(message.get_all(name,[]))!=1:raise ValueError('Ambiguous identity headers')
    if message.get_all('Cc',[]) or message.get_all('Bcc',[]):raise ValueError('Unexpected recipients')
    values=[str(message['To']),str(message['Subject']),str(message['Message-ID']),message.get_content()]
    return hashlib.sha256(json.dumps(values,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def prepare(key,to,subject,body):
    message=EmailMessage();message['To']=to;message['Subject']=subject;message['Message-ID']=marker(key);message.set_content(body)
    raw=message.as_bytes()
    return {'raw':base64.urlsafe_b64encode(raw).decode('ascii'),'fingerprint':fingerprint(raw),'marker':marker(key)}
def inspect(service,key,expected_fingerprint,expected_thread=None):
    wanted=marker(key)
    if not isinstance(expected_fingerprint,str) or not re.fullmatch('[0-9a-f]{64}',expected_fingerprint):raise ValueError('Stored draft fingerprint required')
    try:
        drafts=service.users().drafts()
        listing=drafts.list(userId='me',q='rfc822msgid:'+wanted,maxResults=2,includeSpamTrash=True).execute(num_retries=0)
        if not isinstance(listing,dict) or listing.get('nextPageToken'):return {'state':'held','reason':'incomplete_search'}
        hits=listing.get('drafts',[])
        if not isinstance(hits,list) or len(hits)!=1:return {'state':'held','reason':'missing_or_ambiguous'}
        hit=hits[0]
        if not isinstance(hit,dict) or not isinstance(hit.get('id'),str) or not hit['id']:return {'state':'held','reason':'malformed_search'}
        result=drafts.get(userId='me',id=hit['id'],format='raw').execute(num_retries=0)
        if not isinstance(result,dict) or result.get('id')!=hit['id']:return {'state':'held','reason':'identity_mismatch'}
        msg=result.get('message',{})
        if not isinstance(msg,dict) or 'DRAFT' not in msg.get('labelIds',[]) or (expected_thread is not None and msg.get('threadId')!=expected_thread):return {'state':'held','reason':'draft_state_changed'}
        encoded=msg.get('raw')
        if not isinstance(encoded,str) or len(encoded)>262144:return {'state':'held','reason':'missing_or_oversized_payload'}
        raw=base64.b64decode(encoded+'='*((-len(encoded))%4),altchars=b'-_',validate=True)
        parsed=BytesParser(policy=policy.default).parsebytes(raw)
        if str(parsed.get('Message-ID',''))!=wanted or fingerprint(raw)!=expected_fingerprint:return {'state':'held','reason':'draft_content_changed'}
        return {'state':'matched','draft_id':hit['id'],'evidence':'exact_marker_and_payload','write_permitted':False}
    except Exception:
        return {'state':'held','reason':'lookup_failed'}
