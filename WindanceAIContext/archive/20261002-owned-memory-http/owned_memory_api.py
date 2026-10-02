"""Staged FastAPI router; mount only with scoped credentials and content validation."""
from contextlib import closing
from typing import Literal
import sqlite3
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
import owned_fact_store as store
from source_fact_gateway import apply_fact_request
from memory_ingress_policy import Denied


class FactRequest(BaseModel):
    event_id: str = Field(min_length=1,max_length=200)
    owner: Literal['william','shawn']
    channel: str = Field(min_length=1,max_length=100)
    scope: Literal['business','personal']
    kind: str = Field(min_length=1,max_length=200)
    key: str = Field(min_length=1,max_length=200)
    value: str | None = Field(default=None,max_length=20000)
    expected_revision: int = Field(default=0,ge=0)
    operation: Literal['write','delete'] = 'write'


class FactQuery(BaseModel):
    owner: Literal['william','shawn']
    channel: str = Field(min_length=1,max_length=100)
    scope: Literal['business','personal']
    limit: int = Field(default=100,ge=1,le=500)


def make_router(connect, resolver, validate_content):
    if not callable(validate_content):raise ValueError('Content validator required')
    router=APIRouter()
    @router.post('/memory/owned/facts')
    def mutate(body:FactRequest,authorization:str|None=Header(default=None)):
        try:
            resolver.bind(authorization,owner=body.owner,channel=body.channel,scope=body.scope,
                          operation=body.operation,source_ref=body.event_id)
            if body.operation=='write':
                if body.value is None or not validate_content(body.value):
                    raise HTTPException(422,'Memory content was not accepted; nothing stored')
            elif body.value is not None:
                raise HTTPException(422,'Deletion must not carry a replacement value')
            with closing(connect()) as connection:
                receipt=apply_fact_request(resolver,connection,authorization,event_id=body.event_id,
                    owner=body.owner,channel=body.channel,scope=body.scope,kind=body.kind,key=body.key,
                    value=body.value,expected_revision=body.expected_revision,delete=body.operation=='delete')
            return {'status':'recorded','receipt':receipt}
        except Denied:
            raise HTTPException(403,'Scoped memory access denied') from None
        except store.Conflict:
            raise HTTPException(409,'Memory request conflicts with the current revision or event') from None
        except ValueError:
            raise HTTPException(422,'Invalid memory request; nothing stored') from None
        except sqlite3.Error:
            raise HTTPException(503,'Memory storage unavailable; retry only with the same event ID') from None
    @router.post('/memory/owned/query')
    def query(body:FactQuery,authorization:str|None=Header(default=None)):
        try:
            identity=resolver.bind(authorization,owner=body.owner,channel=body.channel,scope=body.scope,
                                  operation='read',source_ref='query')
            with closing(connect()) as connection:
                facts=store.visible_facts(connection,identity.owner,scopes=(identity.scope,),limit=body.limit)
            return {'facts':facts}
        except Denied:
            raise HTTPException(403,'Scoped memory access denied') from None
        except sqlite3.Error:
            raise HTTPException(503,'Memory storage unavailable') from None
    return router
