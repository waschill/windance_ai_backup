"""Select source-backed private memories. Unknown scope is withheld, not erased.

Candidate only. Business sharing requires explicit access metadata; titles and
stored prose never grant ownership. No caller authentication is performed here.
"""
VALID_OWNERS={'william':'William','shawn':'Shawn'}

def owned_memory_rows(connection, owner, limit=500):
    normalized=str(owner or '').strip().casefold()
    if normalized not in VALID_OWNERS:
        return []
    owner_name=VALID_OWNERS[normalized]
    # Filter ownership in SQL before LIMIT. A flood of another owner's rows
    # cannot hide the caller's older records or be loaded for scoring.
    rows=connection.execute('''
      SELECT v.*,
        c.user AS conversation_owner,c.channel AS conversation_channel,
        c.message AS source_message,c.response AS source_response,
        t.requester AS task_owner,t.assignee AS task_assignee,t.title AS task_title,
        t.request AS task_request,t.result AS task_result,t.status AS task_status
      FROM vector_memory v
      LEFT JOIN conversations c ON v.source_type='conversation' AND c.id=v.source_id
      LEFT JOIN staff_tasks t ON v.source_type='staff_task' AND t.id=v.source_id
      WHERE (v.source_type='conversation' AND lower(trim(c.user))=?)
         OR (v.source_type='staff_task' AND lower(trim(t.requester))=?)
      ORDER BY v.updated_at DESC,v.id
      LIMIT ?
    ''',(normalized,normalized,max(1,min(int(limit),500)))).fetchall()
    output=[]
    for row in rows:
        if row['source_type']=='conversation':
            message=row['source_message'] or ''
            response=row['source_response'] or ''
            text=f'{owner_name}: {message}\n\nAssistant: {response}'
            candidates=[f'{owner_name}: {message}\n\n{role}: {response}' for role in ['Herald','Bridge Lounge','Assistant']]
            title=f"conversation/{owner_name}/{row['conversation_channel'] or 'unknown-channel'}"
        else:
            text=(f"Assignee: {row['task_assignee']}\nStatus: {row['task_status']}\n"
                  f"Requester: {row['task_owner']}\nRequest: {row['task_request']}")
            if row['task_status']!='pending':text+=f"\nResult: {row['task_result'] or ''}"
            candidates=[text]
            title=f"staff_task/{row['task_assignee']}/{row['task_title']}"
        # Current source supplies the text. A stale derived record cannot
        # resurrect corrected/deleted words; stale vectors cannot rank it.
        derived_matches=row['text'] in candidates
        output.append({
            'id':row['id'],'source_type':row['source_type'],'source_id':row['source_id'],
            'title':title,'text':text,'embedding_json':row['embedding_json'] if derived_matches else None,
            'embedding_model':row['embedding_model'],'updated_at':row['updated_at'],
            'source_owner':owner_name,'access_scope':'private','source_verified':True,
            'derived_text_matches_source':derived_matches,
        })
    return output
