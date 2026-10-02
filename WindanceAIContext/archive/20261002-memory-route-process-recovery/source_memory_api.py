"""Staged HTTP learning and revision changes from explicit retained owner requests."""
from contextlib import closing
import hashlib,re,sqlite3
from typing import Literal
from fastapi import APIRouter,Header,HTTPException
from pydantic import BaseModel,Field
import owned_fact_store as store
from memory_ingress_policy import Denied
from source_bound_facts import record_statement,read_verified

class SourceRequest(BaseModel):
    owner:Literal['william','shawn']
    channel:str=Field(min_length=1,max_length=100)
    scope:Literal['personal','business']
    source_ref:str=Field(min_length=1,max_length=200)
    class Config:extra='forbid'

class SourceQuery(BaseModel):
    owner:Literal['william','shawn']
    channel:str=Field(min_length=1,max_length=100)
    scope:Literal['personal','business']
    key:str=Field(min_length=1,max_length=80)
    class Config:extra='forbid'

class SourceChange(SourceRequest):
    key:str=Field(pattern=r'^[0-9a-f]{32}$')
    expected_revision:int=Field(ge=1)
    operation:Literal['correct','forget']

def explicit_change(text):
    text=re.sub(r'^\s*vega[, :]+','',text,flags=re.I).strip()
    correction=re.fullmatch(r'(?:please\s+)?correct\s+memory\s+([0-9a-f]{32})\s*:\s*(.+)',text,re.I|re.S)
    if correction:return 'correct',correction.group(1).lower(),correction.group(2).strip()
    deletion=re.fullmatch(r'(?:please\s+)?forget\s+memory\s+([0-9a-f]{32})\s*[.!]?',text,re.I)
    if deletion:return 'forget',deletion.group(1).lower(),text
    return None

def receipt_status(receipt):
    return 'superseded' if receipt['superseded'] else 'already_recorded' if receipt['replayed'] else 'recorded'

def explicit_intent(text,parse_remember):
    text=re.sub(r'^\s*vega[, :]+','',text,flags=re.I).strip()
    scoped=re.fullmatch(r'\s*(?:please\s+)?remember\s+for\s+(business|personal)\s*:\s*(.+)',text,re.I|re.S)
    if scoped:return scoped.group(1).lower(),scoped.group(2).strip()
    parsed=parse_remember(text)
    return ('personal',parsed) if parsed else None

def make_source_router(connect,resolver,load_source,parse_remember,validate_content):
    if not all(callable(f) for f in [connect,load_source,parse_remember,validate_content]):raise ValueError('Server dependencies required')
    router=APIRouter()
    @router.post('/memory/owned/from-message')
    def remember(body:SourceRequest,authorization:str|None=Header(default=None)):
        try:
            resolver.bind(authorization,owner=body.owner,channel=body.channel,scope=body.scope,operation='write',source_ref=body.source_ref)
            source=load_source(body.owner,body.source_ref)
            if source.owner!=body.owner or source.channel!=body.channel:raise Denied('Source mismatch')
            intent=explicit_intent(source.text,parse_remember)
            if intent is None or intent[0]!=body.scope:raise ValueError('Explicit matching memory intent required')
            quote=intent[1]
            # Server derives identity and value; caller cannot overwrite a chosen fact.
            key=hashlib.sha256((body.owner+'\0'+body.scope+'\0'+body.source_ref).encode()).hexdigest()[:32]
            event='remember-source:'+hashlib.sha256(body.source_ref.encode()).hexdigest()
            with closing(connect()) as c:
                receipt=record_statement(resolver,c,authorization,load_source,validate_content,event_id=event,
                    owner=body.owner,channel=body.channel,scope=body.scope,kind='source_quote',key=key,
                    source_ref=body.source_ref,quote=quote,expected_revision=0)
            return {'status':receipt_status(receipt),'receipt':receipt}
        except (Denied,PermissionError):raise HTTPException(403,'Scoped memory access denied') from None
        except KeyError:raise HTTPException(404,'Source unavailable') from None
        except store.Conflict:raise HTTPException(409,'Source or memory revision changed; correction required') from None
        except ValueError:raise HTTPException(422,'Explicit supported memory request required; nothing stored') from None
        except sqlite3.Error:raise HTTPException(503,'Storage unavailable; retry the same source only') from None
    @router.post('/memory/owned/change-from-message')
    def change(body:SourceChange,authorization:str|None=Header(default=None)):
        try:
            operation='delete' if body.operation=='forget' else 'write'
            resolver.bind(authorization,owner=body.owner,channel=body.channel,scope=body.scope,operation=operation,source_ref=body.source_ref)
            source=load_source(body.owner,body.source_ref)
            if source.owner!=body.owner or source.channel!=body.channel:raise Denied('Source mismatch')
            intent=explicit_change(source.text)
            if intent is None or intent[:2]!=(body.operation,body.key):raise ValueError('Exact target intent required')
            event='change-source:'+hashlib.sha256(body.source_ref.encode()).hexdigest()
            with closing(connect()) as c:
                receipt=record_statement(resolver,c,authorization,load_source,validate_content,event_id=event,
                    owner=body.owner,channel=body.channel,scope=body.scope,kind='source_quote',key=body.key,
                    source_ref=body.source_ref,quote=intent[2],expected_revision=body.expected_revision,delete=body.operation=='forget')
            return {'status':receipt_status(receipt),'receipt':receipt,'source_messages_retained':True}
        except (Denied,PermissionError):raise HTTPException(403,'Scoped memory access denied') from None
        except KeyError:raise HTTPException(404,'Source unavailable') from None
        except store.Conflict:raise HTTPException(409,'Source or memory revision changed; review current memory') from None
        except ValueError:raise HTTPException(422,'Explicit matching correction or forgetting request required') from None
        except sqlite3.Error:raise HTTPException(503,'Storage unavailable; retry the same source only') from None
    @router.post('/memory/owned/source-query')
    def query(body:SourceQuery,authorization:str|None=Header(default=None)):
        try:
            resolver.bind(authorization,owner=body.owner,channel=body.channel,scope=body.scope,operation='read',source_ref='query')
            with closing(connect()) as c:
                fact=read_verified(c,body.owner,body.owner,body.scope,'source_quote',body.key,load_source)
            return {'fact':fact}
        except (Denied,PermissionError):raise HTTPException(403,'Scoped memory access denied') from None
        except sqlite3.Error:raise HTTPException(503,'Storage unavailable') from None
    return router
