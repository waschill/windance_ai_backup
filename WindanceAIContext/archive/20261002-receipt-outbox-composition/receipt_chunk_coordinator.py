"""Staged trusted outbox composition; callbacks require external bounded execution.

No CLI, production paths or scheduler. A recovered attempt may be observed, never resent.
"""


def run_request(journal,request_id,recipient,chunks,capture,observe,send_one):
    journal.register(request_id,recipient,chunks)
    existing=journal.status(request_id)['chunks']
    recovering=journal.is_held(request_id) or any(state in ('attempting','submitted') for state in existing)
    if recovering:
        journal.hold(request_id)
    for index,text in enumerate(chunks):
        saved=journal.chunk(request_id,index)
        if saved['state']=='delivered':continue
        if saved['state']=='ready':
            # A restart may reconcile existing attempts, but never starts a new
            # chunk after an interrupted request without an explicit continuation.
            if recovering:
                return {'status':'held','reason':'remaining_chunks_after_interruption'}
            captured=capture()
            if set(captured)!= {'store_id','boundary'}:
                return {'status':'held','reason':'invalid_store_capture'}
            permission=journal.begin(request_id,index,captured['store_id'],captured['boundary'])
            if permission!='attempt_committed':
                return {'status':'held','reason':'attempt_not_authorized'}
            # A thrown send error leaves the committed attempt held.
            try:
                send_one(recipient,text,False)
            except Exception:
                journal.hold(request_id)
                return {'status':'held','reason':'send_outcome_uncertain'}
            journal.submitted(request_id,index)
            saved=journal.chunk(request_id,index)
        captured=capture()
        if captured['store_id']!=saved['store_id'] or captured['boundary']<saved['boundary']:
            journal.hold(request_id)
            return {'status':'held','reason':'message_store_changed'}
        receipt=observe(recipient,text,saved['boundary'])
        committed=journal.confirm(request_id,index,saved['store_id'],receipt)
        if committed not in ('receipt_committed','existing_receipt'):
            journal.hold(request_id)
            return {'status':'held','reason':'delivery_unconfirmed'}
    return {'status':'delivered','evidence':'local_messages_flags','chunks':len(chunks)}
