"""Staged deterministic processing of authenticated memory messages only."""
import hashlib,json,re,time
import owned_fact_store as store
import source_bound_facts as facts
from authenticated_message_ingress import authenticated_source_loader
from memory_ingress_policy import Policy,Resolver
from source_memory_api import explicit_intent


def memory_query(text):
    text=re.sub(r'^\s*vega[, :]+','',text,flags=re.I).strip()
    if re.fullmatch(r'what do you remember about me[?.!]*',text,re.I):return ('personal','')
    match=re.fullmatch(r'(?:please\s+)?(?:show|list)\s+my\s+(?:(personal|business)\s+)?memor(?:y|ies)(?:\s+after\s+([0-9a-f]{32}))?[?.!]*',text,re.I)
    return ((match[1] or 'personal').lower(),(match[2] or '').lower()) if match else None


def memory_intent(text):
    if memory_query(text):return True
    text=re.sub(r'^\s*vega[, :]+','',text,flags=re.I).strip()
    return bool(re.match(r'^(?:please\s+)?(?:remember\b|learn\b|save\b.*\bmemory\b|commit\b.*\bmemory\b|correct\s+memory\b|forget\b)',text,re.I|re.S))


class Processor:
    def __init__(self,connect,parse_remember,classify_secret,issuer,credential,owners):
        self.connect=connect;self.parse_remember=parse_remember;self.classify_secret=classify_secret
        self.loader=authenticated_source_loader(connect)
        self.authorization='Bearer '+credential
        self.resolver=Resolver([Policy(issuer,credential,frozenset((owner,'max-imessage',scope,op)
          for owner in owners for scope in ['personal','business'] for op in ['read','write','delete']))])

    def install(self):
        with self.connect() as c:store.install(c);facts.install(c)

    def process_pending(self):
        with self.connect() as c:
            rows=[dict(row) for row in c.execute("SELECT id,owner FROM messages WHERE status='memory_pending' ORDER BY created LIMIT 8")]
        for row in rows:self.process(row['id'],row['owner'].lower())

    def process(self,mid,owner):
        reference='manager-message:'+mid
        try:
            source=self.loader(owner,reference)
            query=memory_query(source.text)
            if query:
                self.answer(mid,self.inspect(owner,*query))
                return
            intent=explicit_intent(source.text,self.parse_remember)
            change=re.fullmatch(r'\s*(?:Vega[, :]+)?(?:please\s+)?(correct|forget)\s+memory\s+([0-9a-f]{32})\s+revision\s+([1-9][0-9]*)(?:\s*:\s*(.+))?\s*',source.text,re.I|re.S)
            if intent:
                scope,quote=intent
                key=hashlib.sha256((owner+'\0'+scope+'\0'+reference).encode()).hexdigest()[:32]
                revision=0;delete=False
            elif change:
                operation,key,number,quote=change.groups();key=key.lower();revision=int(number)
                delete=operation.lower()=='forget'
                if (delete and quote is not None) or (not delete and not quote):raise ValueError('Unsupported change')
                with self.connect() as c:
                    matches=c.execute("SELECT scope FROM owned_facts WHERE owner=? AND kind='source_quote' AND fact_key=?",(owner,key)).fetchall()
                if len(matches)!=1:raise ValueError('Target unavailable')
                scope=matches[0][0]
                if delete:quote=source.text
            else:
                raise ValueError('Explicit supported command required')
            with self.connect() as c:
                receipt=facts.record_statement(self.resolver,c,self.authorization,self.loader,
                    lambda value:not self.classify_secret(value),event_id=mid,owner=owner,channel=source.channel,
                    scope=scope,kind='source_quote',key=key,source_ref=reference,quote=quote,
                    expected_revision=revision,delete=delete)
            if receipt['superseded']:
                answer='This memory request was already processed and a newer revision now exists. I did not restore the older value.'
            else:
                answer=('Forgot' if delete else 'Saved')+f" {scope} memory {key}, revision {receipt['revision']}."
                answer+=' Source messages remain retained.' if delete else ' This records your statement, not independently verified truth.'
                if not delete:answer+=f' To change it, use: correct memory {key} revision {receipt["revision"]}: replacement. To forget it, use: forget memory {key} revision {receipt["revision"]}.'
        except store.Conflict:
            answer='The memory or source revision changed. Nothing was overwritten. Review the current memory before retrying with its revision.'
        except (ValueError,KeyError,PermissionError):
            answer='I did not change memory or start a worker. Use an explicit remember request, or identify the memory and revision to correct or forget. Source messages remain retained.'
        # Storage errors deliberately leave memory_pending for same-ID retry.
        self.answer(mid,answer)

    def answer(self,mid,answer):
        with self.connect() as c:
            c.execute("UPDATE messages SET status='answered',answer=?,updated=? WHERE id=? AND status='memory_pending'",(answer,time.time(),mid))

    def inspect(self,owner,scope,after):
        # Owner/scope filtering occurs before bounded scanning; every displayed
        # row is independently source-verified. Shared grants are not assumed.
        displayed=[];last=after
        with self.connect() as c:
            keys=[row[0] for row in c.execute("SELECT fact_key FROM owned_facts WHERE owner=? AND scope=? AND kind='source_quote' AND deleted=0 AND fact_key>? ORDER BY fact_key LIMIT 50",(owner,scope,after))]
            for key in keys:
                last=key
                fact=facts.read_verified(c,owner,owner,scope,'source_quote',key,self.loader)
                if fact is None:continue
                value=fact['value'];excerpt=json.dumps(value[:500],ensure_ascii=False)
                if len(value)>500:excerpt+=' [excerpt; truncated]'
                displayed.append(f"{key} revision {fact['revision']}: {excerpt}\nSource: {fact['provenance']['source_ref']}")
                if len(displayed)==10:break
            more=c.execute("SELECT 1 FROM owned_facts WHERE owner=? AND scope=? AND kind='source_quote' AND deleted=0 AND fact_key>? LIMIT 1",(owner,scope,last)).fetchone() is not None
        answer=(f'Your current source-verified {scope} statements (not independently verified facts):\n'+'\n'.join(displayed)
                if displayed else f'No current source-verified {scope} memories on this page.')
        if more:answer+=f'\nMore records may be available. Use: show my {scope} memories after {last}.'
        answer+='\nForgotten or changed/missing-source facts are withheld. Source messages and earlier answers remain retained.'
        return answer
