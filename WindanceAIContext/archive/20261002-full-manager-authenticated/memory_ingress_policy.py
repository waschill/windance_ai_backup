"""Staged bearer-to-principal policy, no production credential configuration.

Authentication covers the adapter/session. A multi-owner adapter remains
responsible for authenticating its upstream sender. Transport must protect
bearer credentials; this module does not provide TLS or replay prevention.
"""
from dataclasses import dataclass, field
from hmac import compare_digest


class Denied(PermissionError):
    pass


@dataclass(frozen=True)
class Policy:
    issuer: str
    credential: str = field(repr=False)
    # Explicit combinations avoid accidentally creating a Cartesian permission set.
    grants: frozenset[tuple[str, str, str, str]]


@dataclass(frozen=True)
class BoundIdentity:
    issuer: str
    owner: str
    channel: str
    scope: str
    operation: str
    source_ref: str


class Resolver:
    def __init__(self, policies):
        self.policies = tuple(policies)
        issuers = set()
        credentials = set()
        for policy in self.policies:
            if not policy.issuer or policy.issuer in issuers:
                raise ValueError('Unique nonempty issuer required')
            if not policy.credential or policy.credential in credentials or any(c.isspace() for c in policy.credential):
                raise ValueError('Unique nonempty credential required')
            for owner, channel, scope, operation in policy.grants:
                if owner not in {'william','shawn'} or not channel or scope not in {'business','personal'} or operation not in {'read','write','delete','share'}:
                    raise ValueError('Invalid explicit permission')
            issuers.add(policy.issuer); credentials.add(policy.credential)

    def bind(self, authorization, *, owner, channel, scope, operation, source_ref):
        if not isinstance(authorization, str) or not authorization.startswith('Bearer '):
            raise Denied('Authenticated scoped caller required')
        presented = authorization[7:]
        # Encode to avoid compare_digest throwing on untrusted non-ASCII input.
        matches = [p for p in self.policies if compare_digest(p.credential.encode(), presented.encode())]
        if len(matches) != 1:
            raise Denied('Authenticated scoped caller required')
        policy = matches[0]
        if not all(isinstance(x,str) for x in (owner,channel,scope,operation)):
            raise Denied('Explicit owner, channel, scope and operation required')
        if (owner, channel, scope, operation) not in policy.grants:
            raise Denied('Caller is not authorized for this memory operation')
        if not isinstance(source_ref,str) or not source_ref.strip() or len(source_ref)>1000:
            raise Denied('Source reference required')
        return BoundIdentity(policy.issuer, owner, channel, scope, operation, source_ref)


def save_fact(resolver, connection, authorization, *, owner, channel, scope,
              kind, key, value, source_ref, expected_revision=0, delete=False):
    """Integration seam; caller must validate source, content and secret policy."""
    from owned_fact_store import write
    identity = resolver.bind(authorization, owner=owner, channel=channel, scope=scope,
                             operation='delete' if delete else 'write', source_ref=source_ref)
    return write(connection, identity.owner, identity.owner, identity.scope, kind, key,
                 value, identity.source_ref, expected_revision, delete=delete)


def read_fact(resolver, connection, authorization, *, actor, channel, scope,
              fact_owner, kind, key, source_ref):
    from owned_fact_store import read
    identity = resolver.bind(authorization, owner=actor, channel=channel, scope=scope,
                             operation='read', source_ref=source_ref)
    return read(connection, identity.owner, fact_owner, identity.scope, kind, key)
