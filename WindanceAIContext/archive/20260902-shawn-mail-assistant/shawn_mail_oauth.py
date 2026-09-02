#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

HOME = Path.home()
SOURCE_CLIENT = HOME / ".config" / "google-workspace" / "google-oauth-client.json"
CONFIG_DIR = HOME / ".config" / "google-workspace-shawn"
CLIENT_FILE = CONFIG_DIR / "google-oauth-client.json"
TOKEN_FILE = CONFIG_DIR / "google-token.json"
SCOPES = ["https://mail.google.com/"]


def main() -> None:
    if not SOURCE_CLIENT.exists():
        raise SystemExit("The established Google OAuth client is unavailable.")
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CLIENT_FILE.exists():
        CLIENT_FILE.write_bytes(SOURCE_CLIENT.read_bytes())
        os.chmod(CLIENT_FILE, 0o600)

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES)
    creds = flow.run_local_server(
        host="127.0.0.1",
        port=8800,
        open_browser=False,
        authorization_prompt_message="\nOpen this Google URL in HAL's browser:\n\n{url}\n",
        success_message="Shawn Gmail authorization completed. You may close this tab.",
    )

    gmail = build("gmail", "v1", credentials=creds, cache_discovery=False)
    email = str(gmail.users().getProfile(userId="me").execute().get("emailAddress", "")).lower()
    if email != "shawn@reflectsody.com":
        raise SystemExit(f"Wrong Google account authorized: {email or 'unknown'}. No token was saved.")
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    os.chmod(TOKEN_FILE, 0o600)
    print("Shawn Gmail authorization verified and saved.")


if __name__ == "__main__":
    main()
