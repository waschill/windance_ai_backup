"""Native operational profiles are owner-only private conversations.

Runs before gateway permissive group/pairing/role grants or model construction.
None means this narrow rule is inapplicable, not an authorization grant.
"""
OPERATIONAL_PROFILES=frozenset({'herald','scout','forge','athena','iris','ledger','archivist','sentinel','max'})
# Installed gateway SessionSource and both Telegram/Discord adapters normalize
# private messages to "dm". Transport-native "private" is normalized upstream;
# do not broaden this admission check to unrecognized labels.
NATIVE_DM_CHAT_TYPES=frozenset({'dm'})

def owner_dm_admission(source, adapter_profile, auth_env):
    platform=getattr(getattr(source,'platform',None),'value',getattr(source,'platform',''))
    if platform not in ('telegram','discord'):
        return None
    profiles={str(adapter_profile or '').lower(),str(getattr(source,'profile','') or '').lower()}
    if not profiles.intersection(OPERATIONAL_PROFILES):
        return None
    if getattr(source,'chat_type',None) not in NATIVE_DM_CHAT_TYPES or getattr(source,'is_bot',False):
        return False
    key=platform.upper()+'_ALLOWED_USERS'
    allowed=[x.strip() for x in str(auth_env(key) or '').split(',') if x.strip()]
    # One explicit numeric principal. Wildcards, usernames, roles, pairing and
    # group grants cannot authorize this private operational surface.
    if len(allowed)!=1 or not allowed[0].isdigit():
        return False
    user=str(getattr(source,'user_id','') or '')
    if user!=allowed[0]:
        return False
    # Telegram private chat IDs equal the sender ID; preserve both checks.
    if platform=='telegram' and str(getattr(source,'chat_id','') or '')!=user:
        return False
    return True
