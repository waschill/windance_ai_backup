"""Tool-free inference using the installed Hermes provider and credential resolver.

Secrets remain inside the existing credential resolver. stdout is JSON only.
Herald is pinned to Codex OAuth; no alternate provider is tried.
"""
import json
import os
import sys
from pathlib import Path


def main():
    wire = sys.stdout
    sys.stdout = sys.stderr
    request = json.load(sys.stdin)
    profile_name = request.get('profile', 'herald')
    if profile_name not in {'herald', 'athena'}:
        raise ValueError('Unsupported profile')
    profile = Path('/Users/herald/.hermes/profiles') / profile_name
    os.environ['HERMES_HOME'] = str(profile)
    os.environ['HERMES_CONFIG_PATH'] = str(profile / 'config.yaml')
    sys.path.insert(0, '/Users/herald/.hermes/hermes-agent')
    import yaml
    from openai import OpenAI
    from hermes_cli.runtime_provider import resolve_runtime_provider
    from agent.auxiliary_client import CodexAuxiliaryClient
    from agent.codex_headers import apply_required_codex_headers
    cfg = yaml.safe_load((profile / 'config.yaml').read_text())
    if profile_name == 'herald':
        request['system'] += '\n\nCurrent identity and voice:\n' + (profile / 'PUBLIC_IDENTITY.md').read_text()
    model = cfg['model']['default']
    provider = cfg['model']['provider']
    if profile_name == 'herald' and (provider, model) != ('openai-codex', 'gpt-5.6-terra'):
        raise RuntimeError('Herald OAuth route changed; revalidation required')
    runtime = resolve_runtime_provider(requested=provider, target_model=model)
    if runtime.get('provider') != provider:
        raise RuntimeError('Unexpected provider')
    kwargs = {'api_key': runtime.get('api_key'), 'base_url': runtime.get('base_url'), 'max_retries': 0}
    if provider == 'openai-codex':
        apply_required_codex_headers(kwargs, access_token=runtime['api_key'], base_url=runtime['base_url'])
    real = OpenAI(**kwargs)
    client = CodexAuxiliaryClient(real, model) if provider == 'openai-codex' else real
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{'role': 'system', 'content': request['system']}, {'role': 'user', 'content': request['user']}],
            max_tokens=1800, timeout=75,
        )
        content = (response.choices[0].message.content or '').strip()
        if not content:
            raise RuntimeError('Empty inference response')
        wire.write(json.dumps({'reply': content, 'provider': provider, 'model': model}))
        wire.flush()
    finally:
        client.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Do not print exception messages: provider failures may contain secrets.
        sys.__stdout__.write(json.dumps({'error': type(exc).__name__}))
        raise SystemExit(1)
