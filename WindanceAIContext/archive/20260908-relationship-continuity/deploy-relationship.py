"""Bounded profile configuration rollout. No model calls; no transcript harvesting.
Run on Herald using its Hermes venv, from outside the upstream checkout.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sys

import yaml

ROOT = Path('/Users/herald/.hermes')
BACKUP = ROOT / 'backups' / 'relationship-continuity-v1-20260908'
NAMES = ['default', 'archivist', 'athena', 'forge', 'herald', 'iris', 'jean',
         'jim', 'kanak', 'ledger', 'max', 'sandbox', 'scout', 'sentinel', 'tactical', 'vega']
BEGIN = '<!-- WINDANCE-RELATIONSHIP-V1 BEGIN -->'
END = '<!-- WINDANCE-RELATIONSHIP-V1 END -->'
SEED = ('[William, direct preference, 2026-09-08] William prefers being called William, '
        'warm natural conversation, and affectionate, obviously fictional banter about the AI staff. '
        'He values each bot\'s distinct voice, candid disagreement, and seriousness when the situation '
        'calls for it. He wants useful preferences and corrections to carry across conversations, '
        'with private memories kept separate for each bot. He is cost-conscious and prefers '
        'bounded interactions over unnecessary multi-agent chatter.')


def home(name):
    return ROOT if name == 'default' else ROOT / 'profiles' / name


def backup_folder(name):
    # Jim's pre-change record stays inside Jim's private profile too.
    return (home(name) / 'backups' / BACKUP.name) if name == 'jim' else BACKUP / name


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    tmp = path.with_name(path.name + '.relationship-tmp')
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def safe_backup(data):
    # Fail closed rather than archiving credential-like material. Never print it.
    text = data.decode('utf-8')
    if re.search(r'-----BEGIN .*PRIVATE KEY|\b(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,})|\b\d{8,12}:[A-Za-z0-9_-]{30,}', text):
        raise RuntimeError('Credential-like content detected; no backup performed')


def candidates(policy):
    plans = []
    for name in NAMES:
        p = home(name)
        files = [p / 'SOUL.md', p / 'config.yaml', p / 'memories' / 'USER.md']
        for f in files:
            if f.is_symlink() or not f.resolve().is_relative_to(p.resolve()):
                raise RuntimeError(f'Unexpected redirected profile path: {name}')
        cfg = yaml.safe_load(files[1].read_text()) or {}
        old = copy.deepcopy(cfg)
        mem = cfg.setdefault('memory', {})
        mem.update(memory_enabled=True, user_profile_enabled=True)
        mem['memory_char_limit'] = max(4000, mem.get('memory_char_limit', 2200))
        mem['user_char_limit'] = max(2400, mem.get('user_char_limit', 1375))
        # Keep each profile's write-approval and external-provider choices intact.
        platforms = cfg.setdefault('platform_toolsets', {})
        if 'cli' not in platforms:
            raise RuntimeError(f'Missing explicit CLI tool list: {name}')
        for platform, tools in platforms.items():
            if not isinstance(tools, list):
                raise RuntimeError(f'Unexpected tool list: {name}/{platform}')
            if 'memory' not in tools:
                tools.append('memory')
        pinned = cfg.get('tools', {}).get('enabled_toolsets')
        if isinstance(pinned, list) and 'memory' not in pinned:
            raise RuntimeError('Unexpected pin; inspect before broadening')
        if 'memory' in cfg.get('agent', {}).get('disabled_toolsets', []):
            raise RuntimeError('Memory explicitly disabled; inspect first')
        soul = files[0].read_text()
        if BEGIN in soul:
            raise RuntimeError(f'Policy already installed: {name}; use verify')
        if name == 'jim':
            old_jim = 'never call or invent a tool merely to listen, counsel, remember, or converse.'
            new_jim = ('never call or invent a tool merely to listen, counsel, or converse. '
                       'The sole exception is the real profile-local memory tool for selective '
                       'persistence under the Relationship continuity rules below; it grants '
                       'no browsing, messaging, delegation, or other operational capability.')
            if old_jim not in soul:
                raise RuntimeError('Jim wording changed; inspect before editing')
            soul = soul.replace(old_jim, new_jim, 1)
        soul = soul.rstrip() + '\n\n' + BEGIN + '\n' + policy.strip() + '\n' + END + '\n'
        user = files[2].read_text() if files[2].exists() else ''
        if SEED not in user:
            user = (user.rstrip() + '\n\n§\n\n' if user.strip() else '') + SEED + '\n'
        if len(user) > mem['user_char_limit']:
            raise RuntimeError(f'User memory over budget: {name}')
        plans.append((name, files, old, cfg, soul.encode(), user.encode()))
    return plans


def prepare(policy):
    plans = candidates(policy)
    BACKUP.mkdir(parents=True, exist_ok=False, mode=0o700)
    manifest = []
    for name, files, old, cfg, soul, user in plans:
        folder = backup_folder(name)
        folder.mkdir(parents=True, mode=0o700)
        row = {'profile': name, 'config_before_hash': digest(files[1].read_bytes()), 'files': {}}
        # No raw config backup: selected sections contain no credentials.
        sections = {k: old.get(k) for k in ('memory', 'platform_toolsets')}
        write(folder / 'config-sections.json', json.dumps(sections, indent=2).encode())
        for f in (files[0], files[2]):
            raw = f.read_bytes() if f.exists() else None
            if raw is not None:
                safe_backup(raw)
                write(folder / f.name, raw)
            row['files'][f.name] = digest(raw) if raw is not None else None
        manifest.append(row)
    write(BACKUP / 'manifest.json', json.dumps(manifest, indent=2).encode())
    print(json.dumps({'prepared': len(manifest), 'backup': str(BACKUP), 'manifest': manifest}))


def apply(policy):
    plans = candidates(policy)
    manifest = json.loads((BACKUP / 'manifest.json').read_text())
    for plan, row in zip(plans, manifest):
        name, files, old, cfg, soul, user = plan
        assert name == row['profile']
        assert digest(files[1].read_bytes()) == row['config_before_hash'], 'Configuration changed since backup'
        for f in (files[0], files[2]):
            assert (digest(f.read_bytes()) if f.exists() else None) == row['files'][f.name], 'Profile changed since backup'
    for name, files, old, cfg, soul, user in plans:
        write(files[1], yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False).encode())
        write(files[0], soul)
        write(files[2], user)
        print(json.dumps({'applied': name, 'approval': cfg['memory'].get('write_approval', False)}))


def verify():
    sys.path.insert(0, str(ROOT / 'hermes-agent'))
    from hermes_constants import set_hermes_home_override, reset_hermes_home_override
    from hermes_cli.config import load_config
    from hermes_cli.tools_config import _get_platform_tools
    from tools.memory_tool import MemoryStore, get_memory_dir
    from tools.threat_patterns import scan_for_threats
    from agent.prompt_builder import load_soul_md
    manifest = json.loads((BACKUP / 'manifest.json').read_text())
    for row in manifest:
        name = row['profile']
        p = home(name)
        token = set_hermes_home_override(p)
        try:
            cfg = load_config()
            mem = cfg['memory']
            store = MemoryStore(mem['memory_char_limit'], mem['user_char_limit'])
            store.load_from_disk()
            assert get_memory_dir().resolve() == (p / 'memories').resolve()
            assert SEED in store.format_for_system_prompt('user'), f'Seed not loaded: {name}'
            assert not scan_for_threats(SEED, scope='strict')
            identity = load_soul_md(home_override=p)
            assert BEGIN in identity and END in identity, f'Policy not loaded: {name}'
            enabled = _get_platform_tools(cfg, 'cli', include_default_mcp_servers=False)
            assert 'memory' in enabled, f'Tool gated off: {name}'
            before = json.loads((backup_folder(name) / 'config-sections.json').read_text())
            assert mem.get('write_approval', False) == (before['memory'] or {}).get('write_approval', False)
            if name == 'jim':
                assert enabled == {'memory'}, 'Jim gained unrelated tools'
            print(json.dumps({'verified': name, 'native_seed_loaded': True, 'soul_loaded': True,
                              'private_path': True, 'memory_tool_enabled': True,
                              'user_chars': store._char_count('user')}))
        finally:
            reset_hermes_home_override(token)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'apply', 'verify'])
    args = parser.parse_args()
    policy = Path(__file__).with_name('relationship-policy.md').read_text()
    {'prepare': lambda: prepare(policy), 'apply': lambda: apply(policy), 'verify': verify}[args.action]()
