"""Staged source assertions. Source loader is a trusted server dependency, not client text.

Verifies source ownership and exact excerpts, not external truth or belief.
Deployment still requires authenticated ingress and owner-scoped source access.
"""
from dataclasses import dataclass,field
import hashlib,json
import owned_fact_store as store
from source_fact_gateway import apply_fact_request

@dataclass(frozen=True)
class Source:
    owner:str
    channel:str
    reference:str
    text:str=field(repr=False)
    @property
    def digest(self):return hashlib.sha256(self.text.encode()).hexdigest()

def install(connection):
    if connection.in_transaction:raise ValueError('Clean connection required')
    connection.execute('''CREATE TABLE IF NOT EXISTS owned_fact_sources (
      owner TEXT NOT NULL, scope TEXT NOT NULL, kind TEXT NOT NULL, fact_key TEXT NOT NULL,
      revision INTEGER NOT NULL, source_ref TEXT NOT NULL, source_sha256 TEXT NOT NULL,
      excerpt_sha256 TEXT NOT NULL, assertion_type TEXT NOT NULL,
      PRIMARY KEY(owner,scope,kind,fact_key,revision))''')
    connection.commit()

def assert_source(source,owner,channel,reference,quote,validate_content):
    if not isinstance(source,Source) or (source.owner,source.channel,source.reference)!=(owner,channel,reference):
        raise PermissionError('Source ownership or reference mismatch')
    if not isinstance(quote,str) or not quote.strip() or quote not in source.text:
        raise ValueError('Exact nonempty source excerpt required')
    if not validate_content(quote):raise ValueError('Memory content rejected')
    return {'source_ref':reference,'source_sha256':source.digest,
            'excerpt_sha256':hashlib.sha256(quote.encode()).hexdigest(),'assertion_type':'source_quote'}

def record_statement(resolver,connection,authorization,load_source,validate_content,*,event_id,
                     owner,channel,scope,kind,key,source_ref,quote,expected_revision=0,delete=False):
    # Authenticate before source lookup; unauthorized callers cannot probe existence.
    resolver.bind(authorization,owner=owner,channel=channel,scope=scope,operation='delete' if delete else 'write',source_ref=event_id)
    if not callable(validate_content):raise ValueError('Content validation required')
    source=load_source(owner,source_ref)
    provenance=assert_source(source,owner,channel,source_ref,quote,validate_content)
    with store.transaction(connection):
        receipt=apply_fact_request(resolver,connection,authorization,event_id=event_id,owner=owner,
          channel=channel,scope=scope,kind=kind,key=key,value=None if delete else quote,expected_revision=expected_revision,delete=delete,
          provenance=provenance,_joined_transaction=True)
        if not receipt['replayed']:
            connection.execute('INSERT INTO owned_fact_sources VALUES(?,?,?,?,?,?,?,?,?)',
                (owner,scope,kind,key,receipt['revision'],source_ref,source.digest,provenance['excerpt_sha256'],'source_quote'))
        # Detect a changed source before committing. Retrieval also revalidates:
        # this is not a distributed transaction with an external source database.
        current=load_source(owner,source_ref)
        if current!=source:raise store.Conflict('Source changed during recording')
    return {**receipt,'provenance':provenance}

def read_verified(connection,actor,owner,scope,kind,key,load_source):
    fact=store.read(connection,actor,owner,scope,kind,key)
    if fact is None:return None
    # Source itself must not be opened for a different reader just because a
    # business fact has a grant. Shared-source redaction policy is not yet defined.
    if actor!=owner:return None
    row=connection.execute('''SELECT source_ref,source_sha256,excerpt_sha256,assertion_type
      FROM owned_fact_sources WHERE owner=? AND scope=? AND kind=? AND fact_key=? AND revision=?''',
      (owner,scope,kind,key,fact['revision'])).fetchone()
    if row is None:return None
    try:source=load_source(owner,row[0])
    except (KeyError,PermissionError):return None
    if not isinstance(source,Source) or source.owner!=owner or source.reference!=row[0] or source.digest!=row[1]:return None
    if fact['value'] not in source.text or hashlib.sha256(fact['value'].encode()).hexdigest()!=row[2]:return None
    return {**fact,'provenance':{'source_ref':row[0],'source_sha256':row[1],'assertion_type':row[3]}}

def manager_source_loader(connect):
    """Read exact message columns only. Manager's upstream identity remains a separate gate."""
    def load(owner,reference):
        if not isinstance(reference,str) or not reference.startswith('manager-message:'):raise KeyError('Unsupported source')
        identifier=reference[len('manager-message:'):]
        connection=connect()
        try:row=connection.execute('SELECT owner,channel,request FROM messages WHERE id=?',(identifier,)).fetchone()
        finally:connection.close()
        if row is None:raise KeyError('Source missing')
        if str(row[0]).lower()!=owner:raise PermissionError('Source owner mismatch')
        return Source(owner,str(row[1]),reference,str(row[2]))
    return load
