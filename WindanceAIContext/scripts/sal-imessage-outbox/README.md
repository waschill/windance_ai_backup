# SAL iMessage outbox

The production files are:

- `/Users/zuzu/bin/imessage_outbox_daemon.py`
- `/Users/zuzu/bin/send_imessage_payload.py`
- `/Users/zuzu/Library/LaunchAgents/com.windance.imessage-outbox.plist`

The daemon must run through the signed Command Line Tools `Python.app` executable so the stable `com.apple.python3` Messages Automation grant owns delivery. Producers pass a base64 JSON request to the client. The client writes an atomic queue file and waits up to 60 seconds for the daemon's result file, so an upstream HTTP success cannot precede actual Messages delivery.

Do not treat process health or HTTP acceptance as a delivery receipt. Verify the daemon log and a new outbound Messages database row after maintenance.
