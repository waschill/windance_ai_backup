"""Owner context for legacy William-mail capabilities in Harness messages.

No scope denotes existing trusted service/scheduler calls, not a user identity.
This module does not authenticate direct HTTP clients or replace per-owner tools.
"""
from contextvars import ContextVar
from functools import wraps
import uuid

_owner = ContextVar('windance_mailbox_request_owner', default=None)

class EmailOwnerBoundaryError(PermissionError):
    pass

def require_william_mailbox():
    owner = _owner.get()
    if owner is not None and owner != 'william':
        raise EmailOwnerBoundaryError('This request cannot use the shared William mailbox or approval records.')

def bind_mailbox_owner(function):
    @wraps(function)
    def bound(payload, *args, **kwargs):
        owner = str(getattr(payload, 'user', '') or '').strip().casefold()
        token = _owner.set(owner)
        try:
            return function(payload, *args, **kwargs)
        except EmailOwnerBoundaryError:
            return {'id':str(uuid.uuid4()), 'reply':
                'That shared email or approval handler belongs to William. '
                'I withheld this request; your separately scoped mailbox route is required.',
                'provider':'deterministic', 'model':'mailbox-owner-denied', 'work_trace':''}
        finally:
            _owner.reset(token)
    return bound
