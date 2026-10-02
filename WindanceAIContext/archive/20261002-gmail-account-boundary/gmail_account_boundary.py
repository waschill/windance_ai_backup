"""Validate the configured mailbox before exposing Gmail capabilities."""
class MailboxIdentityError(PermissionError):pass
def expected_account(value):
    if not isinstance(value,str) or value!=value.strip() or value.count('@')!=1 or any(c.isspace() or c in '<>,;' for c in value):
        raise MailboxIdentityError('An explicit expected mailbox account is required')
    local,domain=value.split('@')
    if not local or not domain or '.' not in domain:raise MailboxIdentityError('An explicit expected mailbox account is required')
    return value.casefold()
def verify(service,expected):
    wanted=expected_account(expected)
    try:
        profile=service.users().getProfile(userId='me').execute(num_retries=0)
        actual=expected_account(profile.get('emailAddress')) if isinstance(profile,dict) else None
    except Exception:
        raise MailboxIdentityError('Mailbox account identity could not be verified') from None
    if actual!=wanted:raise MailboxIdentityError('Connected mailbox does not match the configured owner account')
    return service
