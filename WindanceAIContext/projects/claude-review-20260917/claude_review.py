#!/Users/herald/.hermes/hermes-agent/venv/bin/python
"""Private operator CLI. Supports fresh reviews and evidence-backed follow-ups."""
import argparse
import os
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--query-file', required=True, help='UTF-8 review instructions; - for stdin')
    parser.add_argument('--resume', help='Exact Claude session ID for a follow-up')
    args = parser.parse_args()
    if os.environ.get('HERMES_KANBAN_TASK'):
        raise SystemExit('Claude is not an operational Kanban worker. Assign Forge.')
    hermes = '/Users/herald/.hermes/hermes-agent/venv/bin/hermes'
    command = [hermes, '-p', 'claude', 'chat', '-Q', '--source', 'direct-code-review',
               '--provider', 'openrouter', '--model', 'anthropic/claude-opus-5',
               '--toolsets', 'claude-review', '--max-turns', '20', '--run-budget', '240',
               '--query-file', args.query_file]
    if args.resume:
        command.extend(['--resume', args.resume])
    return subprocess.call(command, env={**os.environ, 'HERMES_PROFILE': 'claude',
         'HERMES_HOME': str(Path.home()/'.hermes/profiles/claude')})


if __name__ == '__main__':
    raise SystemExit(main())

