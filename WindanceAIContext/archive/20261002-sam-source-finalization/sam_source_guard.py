"""Local SAM source fingerprint and atomic finalization; staged, no remote calls."""
import hashlib,json
from contextlib import closing
class SourceChanged(RuntimeError):pass
def source_token(db,date_key,*,include_carries=True):
    # Fixed queries only. Include all carry rows because effective chain selection
    # can consult rows outside this date; conservative holds are preferable to
    # accepting a stale completion until a narrower dependency proof exists.
    queries=[('items','SELECT * FROM schedule_items WHERE date=? ORDER BY id',(date_key,)),
             ('details','SELECT * FROM training_completion_details WHERE date=? ORDER BY item_id',(date_key,)),
             ('suppressions','SELECT * FROM carryover_suppressions WHERE date=? ORDER BY horse_key,training_code',(date_key,))]
    if include_carries:queries.append(('carries','SELECT * FROM missed_training ORDER BY id',()))
    result=[]
    for name,query,args in queries:
        cursor=db.execute(query,args)
        result.append([name,[col[0] for col in cursor.description],[list(row) for row in cursor]])
    return hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def finalize(connect,date_key,expected_token,receipt,stamp):
    # Receipt validation belongs to the memory client before this local step.
    encoded=json.dumps(receipt,sort_keys=True,separators=(',',':'),allow_nan=False)
    with closing(connect()) as db:
        db.execute('BEGIN IMMEDIATE')
        if source_token(db,date_key)!=expected_token:
            raise SourceChanged('Schedule source changed; accepted memory must be reconciled before completion')
        row=db.execute('SELECT committed,commit_result FROM schedule_days WHERE date=?',(date_key,)).fetchone()
        if not row:raise SourceChanged('Schedule day missing')
        if row[0]:
            if row[1]!=encoded:raise SourceChanged('Day already binds another receipt')
            return {'already_committed':True}
        db.execute('UPDATE schedule_days SET committed=1,last_committed=?,commit_result=? WHERE date=?',(stamp,encoded,date_key))
        db.commit()
    return {'already_committed':False}
