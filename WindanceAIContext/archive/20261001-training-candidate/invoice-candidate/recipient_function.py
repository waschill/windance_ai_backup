def shawn_recipient() -> str:
    """Resolve the existing private Shawn pin, never a report-formatting field."""
    from pathlib import Path
    import json
    import re
    try:
        pin = json.loads((Path.home() / '.config/windance-recipients/shawn-email.json').read_text())
        target = pin.get('recipient')
        if not isinstance(target, str) or not re.fullmatch(r'\+?[0-9 ()-]{10,24}', target.strip()):
            raise ValueError('Invalid recipient')
        target = target.strip()
        digits = re.sub(r'\D', '', target)
        if not 10 <= len(digits) <= 15:
            raise ValueError('Invalid recipient')
        nodes = json.loads(FLOWS_FILE.read_text(encoding='utf-8'))
        william = next(n for n in nodes if n.get('id') == 'wr_brief_format')
        match = re.search(r'msg\.recipient\s*=\s*[\"\x27]([^\"\x27]+)', william.get('func', ''))
        if not match:
            raise ValueError('Owner separation unavailable')
        owner_digits = re.sub(r'\D', '', match.group(1))
        if len(owner_digits) < 10 or digits[-10:] == owner_digits[-10:]:
            raise ValueError('Owner separation failed')
        return target
    except (OSError, ValueError, TypeError, AttributeError, StopIteration):
        # Never expose private contact contents or fall back to William.
        raise RuntimeError('Verified Shawn recipient configuration is unavailable; delivery withheld.') from None
