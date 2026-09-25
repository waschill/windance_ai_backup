"""Operator-only setup: prompts never echo keys or the private phone PIN."""
import base64
import getpass
import hashlib
import json
import os
import re
import secrets
from pathlib import Path


def main():
    os.umask(0o077)
    path = Path(__file__).parent / 'private/config.json'
    config = json.loads(path.read_text())
    print('Herald phone setup. Enter information here, not in chat.')
    number = input('Your mobile number, including +1: ').strip()
    if not re.fullmatch(r'\+[1-9]\d{7,14}', number):
        raise SystemExit('Use international format, for example +16055551234.')
    public_key = getpass.getpass('Telnyx PUBLIC webhook verification key (hidden): ').strip()
    try:
        if len(base64.b64decode(public_key, validate=True)) != 32:
            raise ValueError()
    except Exception:
        raise SystemExit('Expected the base64 Ed25519 public key, not an API key.')
    pin = getpass.getpass('Choose an 8–12 digit phone PIN (hidden): ')
    again = getpass.getpass('Repeat phone PIN (hidden): ')
    if not re.fullmatch(r'\d{8,12}', pin) or pin != again:
        raise SystemExit('PIN must match and contain 8–12 digits.')
    salt = secrets.token_bytes(16)
    config.update(allowed_numbers=[number], telnyx_public_key=public_key,
                  pin={'salt': salt.hex(), 'hash': hashlib.scrypt(pin.encode(), salt=salt,
                       n=16384, r=8, p=1).hex()}, enabled=True)
    pin = again = ''
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(config, indent=2) + '\n')
    os.chmod(temp, 0o600)
    temp.replace(path)
    print('Saved. The PIN itself was not stored. Inbound calling is ready for live testing once the route and number are connected.')


if __name__ == '__main__':
    main()
