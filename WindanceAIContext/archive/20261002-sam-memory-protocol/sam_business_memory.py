"""Staged SAM business-source storage; no personal memory, readers, mirrors or dispatch."""
import hashlib,json,re
from contextlib import closing
from sam_memory_contract import admit
class SourceConflict(ValueError):pass
SCHEMA='''CREATE TABLE IF NOT EXISTS sam_business_sources(
 date_key TEXT PRIMARY KEY,revision INTEGER NOT NULL,summary TEXT NOT NULL,
 content_sha256 TEXT NOT NULL,source_ref TEXT NOT NULL,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS sam_business_receipts(
 event_id TEXT PRIMARY KEY,date_key TEXT NOT NULL,request_sha256 TEXT NOT NULL,
 revision INTEGER NOT NULL,content_sha256 TEXT NOT NULL,recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);'''

def record(connect,authorization,credential,payload,*,event_id,expected_revision,validate_content):
    source=admit(authorization,credential,payload,validate_content)
    if not isinstance(event_id,str) or not re.fullmatch('[A-Za-z0-9_.:-]{1,128}',event_id):raise ValueError('Stable event identity required')
    if type(expected_revision) is not int or not 0<=expected_revision<2**63-1:raise ValueError('Expected revision required')
    digest=hashlib.sha256(json.dumps([source,expected_revision],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    with closing(connect()) as c:
        c.execute('BEGIN IMMEDIATE')
        try:
            prior=c.execute('SELECT date_key,request_sha256,revision,content_sha256 FROM sam_business_receipts WHERE event_id=?',(event_id,)).fetchone()
            current=c.execute('SELECT revision,content_sha256,summary FROM sam_business_sources WHERE date_key=?',(source['key'],)).fetchone()
            version=current[0] if current else 0
            if current and hashlib.sha256(current[2].encode()).hexdigest()!=current[1]:raise SourceConflict('Stored source content changed')
            if prior:
                if prior[0]!=source['key'] or prior[1]!=digest:raise SourceConflict('Event identity already binds another request')
                if version<prior[2]:raise SourceConflict('Receipt/source state inconsistent')
                if version==prior[2] and current[1]!=prior[3]:raise SourceConflict('Receipt/source content inconsistent')
                c.rollback()
                return {'status':'ok','event_id':event_id,'producer':'sam','scope':'business','date':prior[0],
                        'revision':prior[2],'content_sha256':prior[3],'replayed':True,'superseded':version>prior[2]}
            if version!=expected_revision:raise SourceConflict('Source revision changed; do not overwrite')
            revision=version+1
            c.execute('INSERT INTO sam_business_sources(date_key,revision,summary,content_sha256,source_ref) VALUES(?,?,?,?,?) ON CONFLICT(date_key) DO UPDATE SET revision=excluded.revision,summary=excluded.summary,content_sha256=excluded.content_sha256,source_ref=excluded.source_ref,updated_at=CURRENT_TIMESTAMP',
                      (source['key'],revision,source['value'],source['content_sha256'],source['source_ref']))
            c.execute('INSERT INTO sam_business_receipts(event_id,date_key,request_sha256,revision,content_sha256) VALUES(?,?,?,?,?)',
                      (event_id,source['key'],digest,revision,source['content_sha256']))
            c.commit()
            return {'status':'ok','event_id':event_id,'producer':'sam','scope':'business','date':source['key'],
                    'revision':revision,'content_sha256':source['content_sha256'],'replayed':False,'superseded':False}
        except BaseException:
            c.rollback();raise
