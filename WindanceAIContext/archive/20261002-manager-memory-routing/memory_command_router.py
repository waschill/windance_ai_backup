"""Staged deterministic processing of authenticated memory messages only."""
import hashlib,re,time
import owned_fact_store as store
import source_bound_facts as facts
from authenticated_message_ingress import authenticated_source_loader
from memory_ingress_policy import Policy,Resolver
from source_memory_api import explicit_intent


def memory_intent(text):
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
        with self.connect() as c:
            c.execute("UPDATE messages SET status='answered',answer=?,updated=? WHERE id=? AND status='memory_pending'",(answer,time.time(),mid))
