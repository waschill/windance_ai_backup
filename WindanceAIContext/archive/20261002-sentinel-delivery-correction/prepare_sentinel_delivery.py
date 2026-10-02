"""Preserve private Sentinel source; replace only delivery and main control flow."""
import ast,hashlib
from pathlib import Path
root=Path(__file__).parent/'caller-contract-private'
source=root/'sentinel_daily_router_review.py';text=source.read_text()
assert hashlib.sha256(source.read_bytes()).hexdigest()=='1f8f1aaa283bd57ecd2895d13b81e2de150a2a0294320bc9de7d1d113078f6a1'
replacements={
'deliver':'''def deliver(message: str) -> None:
    from zoneinfo import ZoneInfo
    from receipt_report_transport import send_report
    day=dt.datetime.now(ZoneInfo('America/Denver')).date().isoformat()
    result=send_report(RECIPIENT,message,'sentinel-router:'+day)
    if result.get('ok') is not True:
        raise RuntimeError('Sentinel delivery unconfirmed; reconcile same request')
''',
'main':'''def main() -> int:
    parser=argparse.ArgumentParser(description='Daily Sentinel ASUS-router security review')
    parser.add_argument('--since',type=int,default=24*60,help='review window in minutes')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    minutes=min(max(args.since,1),7*24*60)
    report_failed=False
    try:
        message=report(minutes)
    except Exception as exc:
        report_failed=True
        message=f'Sentinel router review BLOCKED: {type(exc).__name__}; router status was not verified.'
    if args.dry_run:
        print(message)
        return 1 if report_failed else 0
    try:
        deliver(message)
    except Exception:
        log('delivery unconfirmed; reconcile existing daily request; no fallback send')
        return 1
    log('delivery independently verified')
    return 1 if report_failed else 0
'''}
lines=text.splitlines(keepends=True)
nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name in replacements]
assert len(nodes)==2
for node in sorted(nodes,key=lambda n:n.lineno,reverse=True):lines[node.lineno-1:node.end_lineno]=[replacements[node.name]+'\n']
candidate=root/'sentinel_daily_router_review_candidate.py'
assert not candidate.exists();candidate.write_text(''.join(lines))
print('candidate_sha256='+hashlib.sha256(candidate.read_bytes()).hexdigest())
