"""One existing-credential profile read; no mailbox contents or token persistence."""
import datetime,hashlib,json,time
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
import httplib2
token=Path('/Users/herald/.config/google-workspace/google-token.json')
before=hashlib.sha256(token.read_bytes()).hexdigest();started=time.monotonic()
try:
 creds=Credentials.from_authorized_user_file(str(token),['https://mail.google.com/','https://www.googleapis.com/auth/calendar.events'])
 refreshed=False
 if creds.expired and creds.refresh_token:
  transport=Request()
  def bounded_request(*a,**k):k['timeout']=10;return transport(*a,**k)
  creds.refresh(bounded_request);refreshed=True
 if not creds.valid:raise RuntimeError('Invalid credential')
 service=build('gmail','v1',http=AuthorizedHttp(creds,http=httplib2.Http(timeout=10)),cache_discovery=False)
 profile=service.users().getProfile(userId='me').execute(num_retries=0)
 assert isinstance(profile.get('emailAddress'),str) and '@' in profile['emailAddress']
 result={'authenticated_profile_read':True,'profile_has_account_identity':True,'credential_refreshed_in_memory':refreshed,
  'configured_scope_includes_full_mail':bool(creds.has_scopes(['https://mail.google.com/'])),'intended_human_owner_independently_verified':False}
except Exception as exc:
 result={'authenticated_profile_read':False,'error_type':type(exc).__name__,'raw_error_suppressed':True}
assert hashlib.sha256(token.read_bytes()).hexdigest()==before
result.update(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_seconds=round(time.monotonic()-started,3),
 credential_file_unchanged=True,mailbox_content_reads=0,mailbox_writes=0,model_calls=0,account_address_exported=False)
print(json.dumps(result))
