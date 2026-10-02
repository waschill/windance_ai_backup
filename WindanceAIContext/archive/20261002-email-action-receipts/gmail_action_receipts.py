"""Validate provider acceptance evidence; never claims recipient delivery."""
def validate_ack(kind,result,expected_id=None):
    if kind not in {'mark_read','archive','create_draft','send'}:raise ValueError('Unsupported receipt kind')
    if not isinstance(result,dict) or not isinstance(result.get('id'),str) or not result['id'].strip():raise RuntimeError('Gmail outcome unconfirmed: missing resource receipt')
    if expected_id is not None and result['id']!=expected_id:raise RuntimeError('Gmail outcome unconfirmed: resource mismatch')
    if kind in {'mark_read','archive'}:
        labels=result.get('labelIds');removed='UNREAD' if kind=='mark_read' else 'INBOX'
        if not isinstance(labels,list) or any(not isinstance(x,str) for x in labels) or removed in labels:raise RuntimeError('Gmail outcome unconfirmed: label receipt mismatch')
