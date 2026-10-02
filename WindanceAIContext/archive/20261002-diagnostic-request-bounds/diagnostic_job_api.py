"""Staged authenticated job ledger. No scheduler or execution route is enabled."""
import hashlib,hmac,json,re,sqlite3,uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Literal
from fastapi import FastAPI,Header,HTTPException
from pydantic import BaseModel,ConfigDict,Field

class Submission(BaseModel):
    model_config=ConfigDict(extra='forbid')
    request_key:str=Field(min_length=1,max_length=128,pattern=r'^[A-Za-z0-9_.:-]+$')
    kind:Literal['email_payload_diagnosis']
    evidence_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')

from diagnostic_job_ledger import Ledger, JobError
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from diagnostic_request_bounds import RequestBounds

def create_app(database,credential_principals,cancel_adapter=None):
    # Server-owned mapping of SHA256(token) -> principal; request body never selects it.
    principals=dict(credential_principals)
    if not principals or any(not re.fullmatch('[0-9a-f]{64}',k) or not isinstance(v,str) or not v.strip() for k,v in principals.items()):
        raise ValueError('Explicit nonempty credential/principal configuration required')
    ledger=Ledger(database);app=FastAPI();app.state.ledger=ledger
    app.add_middleware(RequestBounds)
    @app.exception_handler(RequestValidationError)
    async def invalid_request(request,exc):
        return JSONResponse(status_code=422,content={'detail':'Invalid diagnostic request'})
    @app.exception_handler(JobError)
    async def ledger_error(request,exc):
        return JSONResponse(status_code=exc.status_code,content={"detail":exc.detail})
    def owner(header):
        if not isinstance(header,str) or not header.startswith('Bearer ') or len(header)>512:raise HTTPException(401,'Authentication required')
        candidate=hashlib.sha256(header[7:].encode()).hexdigest()
        for digest,principal in principals.items():
            if hmac.compare_digest(digest,candidate):return principal
        raise HTTPException(401,'Authentication required')
    @app.post('/jobs')
    def submit(body:Submission,authorization:str|None=Header(default=None)):
        return ledger.submit(owner(authorization),body)
    @app.get('/jobs/{key}')
    def status(key:str,authorization:str|None=Header(default=None)):
        return ledger.read(owner(authorization),key)
    @app.post('/jobs/{key}/cancel')
    def cancel(key:str,authorization:str|None=Header(default=None)):
        result=ledger.cancel(owner(authorization),key)
        if result['state']=='cancel_requested' and cancel_adapter is not None:
            try:
                receipt=cancel_adapter(ledger,key)
                return ledger.acknowledge_cancel(key,receipt)
            except Exception:
                # Preserve intent on uncertain stop; no raw provider/transport errors.
                return {'id':key,'state':'cancel_requested','worker_stopped':False}
        return result
    @app.get('/jobs/{key}/result')
    def result(key:str,authorization:str|None=Header(default=None)):
        return ledger.result(owner(authorization),key)
    return app
