"""Explicit expected Gmail account; no discovery-based ownership assumption."""
import json,re
from pathlib import Path

class AccountUnverified(PermissionError):pass

def expected_account(path):
    try:
        with Path(path).open('rb') as stream:raw=stream.read(4097)
        if len(raw)>4096:raise ValueError('Policy exceeds bound')
        value=json.loads(raw)
        if not isinstance(value,dict) or set(value)!={'expected_email'}:raise ValueError('Invalid policy')
        address=value['expected_email']
        if not isinstance(address,str) or len(address)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',address):raise ValueError('Explicit address required')
        return address.casefold()
    except Exception:raise AccountUnverified('Expected Gmail account is not configured or valid') from None

def verify(service,expected):
    try:
        profile=service.users().getProfile(userId='me').execute(num_retries=0)
        actual=profile.get('emailAddress') if isinstance(profile,dict) else None
        if not isinstance(actual,str) or actual.casefold()!=expected:raise ValueError('Account mismatch')
    except Exception:raise AccountUnverified('Gmail account verification failed; mailbox actions withheld') from None
    return service
