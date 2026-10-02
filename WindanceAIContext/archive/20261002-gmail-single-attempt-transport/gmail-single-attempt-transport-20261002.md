# Gmail single-attempt transport — staged evidence, October 2

Phase 1 remains open. No deployment, Gmail call, real credential access, mailbox change, model call, service restart or SAM action occurred in this test run.

## Problem and result

The preceding hidden-retry record demonstrated that installed httplib2 can issue two simulated POSTs despite Google execute(num_retries=0). A standalone GmailTransport now uses HTTPX with transport retries disabled and redirects refused. API 401 does not trigger refresh-and-replay. Provider error bodies are replaced with fixed content. Destination validation precedes credential preparation. This component is not yet composed into the private Harness candidate or live service; Calendar remains unchanged.

On HERALD's existing Hermes Python environment, test_gmail_single_attempt_transport.py passed seven actual Google HttpRequest/HTTPX/temporary loopback-server cases: normal, dropped connection, malformed response, read timeout, redirect 307, HTTP401 and HTTP503. Each recorded exactly one server POST. Only the normal response succeeded. The timeout case finished in 0.152 seconds using a fixture timeout of 0.15 seconds. Non-provider destination rejection passed. All temporary listeners were stopped; no real Google endpoint was contacted.

test_gmail_transport_refresh.py passed three additional offline SDK cases using actual Google Credentials and static Gmail discovery with an injected exchange: successful refresh plus one draft request; refresh503 followed by refusal of a second refresh exchange and no API request; refresh success plus API401 with no API replay. Static discovery issued no exchanges. Error output excluded PRIVATE_SENTINEL. This confirms SDK compatibility with synthetic credentials, not production OAuth/TLS operation.

## Limits and next gate

Per-read/connect timeouts are not a hard whole-job deadline. DNS, slow response bodies, decompression/resource behavior and credential SDK waiting need explicit treatment. The response cap is 16MiB after decoding. Production host isolation, real account/human identity, direct privileged writers and all application callers remain outside this evidence. Callers must retain num_retries=0; higher-level client retry settings could still replay a transport call. A single attempted write can succeed remotely without an acknowledgment and must remain uncertain until reconciled.

Integrate only after preserving the current private candidate's ownership, durable intent, receipt and sweep guards. Gmail's existing eager google_credentials refresh must be addressed so it does not bypass this transport; Calendar must retain its existing behavior. Prove the complete durable-intent path against dropped responses, then repeat full startup and off-host recovery for the exact composed revision. Do not reuse prior candidate recovery certification for a new hash. No live send is authorized by these tests.

## Recovery and costs

No production rollback is necessary: only the three named standalone workspace files and /tmp copies on HERALD were created. They are inert unless explicitly run/imported. The canonical archive manifest records exact hashes. Prior production backups and private candidate remain unchanged. Tests used existing software with zero application model calls and no new paid commitments. Codex work itself consumes account allowance; dollar attribution remains unknown.

Node-RED is separately still blocked by its browser saved-permission denial following the owner's Chrome reload. The alarm restoration remains authorized but unperformed; no alternate route was used.
