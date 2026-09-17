"""Process-local fault injection; never installed as the production Hermes CLI."""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from tools.registry import ToolRegistry

original_dispatch = ToolRegistry.dispatch
mode = os.environ.get('SCOUT_CANARY_MODE', '')
trace = Path(os.environ['SCOUT_CANARY_TRACE'])


def dispatch(self, name, args, **kwargs):
    deny = (mode in ('search_down', 'api_search_down', 'all_down') and name == 'web_search') or (
        mode == 'all_down' and (name.startswith('web_') or name.startswith('browser_')))
    if deny:
        result = json.dumps({'success': False, 'error': 'Controlled canary: this retrieval route is unavailable'})
    else:
        result = original_dispatch(self, name, args, **kwargs)
    # Persist tool names and success state only, not user/provider payloads.
    error = False
    try:
        data = json.loads(result) if isinstance(result, str) else result
        error = isinstance(data, dict) and (bool(data.get('error')) or data.get('success') is False)
    except (TypeError, ValueError):
        pass
    with trace.open('a') as stream:
        stream.write(json.dumps({'tool': name, 'injected_failure': deny, 'reported_error': error,
                                 'checked_at': datetime.now(timezone.utc).isoformat()}) + '\n')
    return result


ToolRegistry.dispatch = dispatch
if mode in ('search_down', 'api_search_down', 'all_down'):
    assert json.loads(dispatch(None, 'web_search', {}))['success'] is False
if mode == 'all_down':
    for name in ('web_extract', 'browser_navigate'):
        assert json.loads(dispatch(None, name, {}))['success'] is False
from hermes_cli.main import main
sys.exit(main())
