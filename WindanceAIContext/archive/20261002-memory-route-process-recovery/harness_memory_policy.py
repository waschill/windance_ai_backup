"""Exact installed Harness policy functions frozen for staged integration."""
import re

def redact_approval_auth_word(text: str) -> str:
    # Redact approval-shaped phrases before they enter audit or conversation logs.
    return re.sub(
        r"\b(?:approve|approved|authorize|authorise|auth|code)\s+[A-Za-z0-9]{4,}\b(?:\s+to\s+all)?",
        "[REDACTED AUTHORIZATION]",
        text,
        flags=re.I,
    )

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

def redact_level8_code(text: str) -> str:
    redacted = re.sub(
        r"(?i)((?:max|herald|harold)?[, ]*CONFIRM\s+LEVEL\s*(?:8|EIGHT)\s+SHUTDOWN\s+).+",
        r"\1[REDACTED]",
        text,
    )
    redacted = re.sub(
        r"(?i)((?:max|herald|harold)?[, ]*(?:confirm\s+)?(?:windance|windows)?\s*level\s*(?:8|eight)\s+shutdown\s+(?:with\s+)?code\s+).+",
        r"\1[REDACTED]",
        redacted,
    )
    return redacted
