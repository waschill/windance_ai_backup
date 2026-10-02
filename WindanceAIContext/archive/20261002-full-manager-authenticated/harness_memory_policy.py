"""Exact installed Harness policy functions frozen for staged integration."""
import re

def memory_looks_secret(text: str) -> bool:
    lowered = (text or "").lower()
    secret_words = [
        "password",
        "passwd",
        "api key",
        "apikey",
        "bearer token",
        "access token",
        "refresh token",
        "client secret",
        "private key",
        "ssh key",
        "authorization code",
        "confirmation code",
    ]
    return any(word in lowered for word in secret_words)

def parse_remember_command(text: str) -> str | None:
    intent = re.sub(r"^\s*(?:max|herald|harold|reacher)[, :]+", "", text or "", flags=re.I).strip()
    patterns = [
        r"^(?:please\s+)?(?:remember|learn|save|commit)\s+(?:this|that|it)?\s*(?:to\s+memory)?\s*[:,-]\s*(.+)$",
        r"^(?:please\s+)?(?:remember|learn|save|commit)\s+(?:this|that|it)\s+(?:to\s+memory\s+)?(.+)$",
        r"^(?:please\s+)?(?:save|commit)\s+(.+?)\s+to\s+memory\s*$",
    ]
    for pattern in patterns:
        match = re.match(pattern, intent, flags=re.I | re.S)
        if match:
            return match.group(1).strip()
    return None
