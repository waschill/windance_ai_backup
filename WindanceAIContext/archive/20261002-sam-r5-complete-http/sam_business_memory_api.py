"""Staged dedicated write-only producer API; no default credentials or legacy access."""
import sqlite3
from fastapi import FastAPI,Header,HTTPException
from pydantic import BaseModel,ConfigDict,Field,StrictInt
from sam_business_memory import record,SourceConflict
from sam_memory_contract import ProducerDenied
class Envelope(BaseModel):
    model_config=ConfigDict(extra='forbid')
    event_id:str=Field(min_length=1,max_length=128,pattern=r'^[A-Za-z0-9_.:-]+$')
    expected_revision:StrictInt=Field(ge=0,lt=2**63-1)
    payload:dict
def create_app(connect,credential,validate_content):
    if not callable(connect) or not callable(validate_content) or not isinstance(credential,str) or len(credential)<32:
        raise ValueError('Explicit storage, credential and validator required')
    app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
    @app.post('/memory/business/sam-schedule')
    def write(body:Envelope,authorization:str|None=Header(default=None)):
        try:
            return record(connect,authorization,credential,body.payload,event_id=body.event_id,
                          expected_revision=body.expected_revision,validate_content=validate_content)
        except ProducerDenied:raise HTTPException(403,'Producer request denied') from None
        except SourceConflict:raise HTTPException(409,'Source or event changed; reconcile before retry') from None
        except ValueError:raise HTTPException(422,'Invalid producer request') from None
        except sqlite3.Error:raise HTTPException(503,'Storage unavailable; retain and retry the same event only') from None
    return app
