# Read-only actual OAuth resolution and profile integration

October2. No live service changes, model request or credential values published.

Executed check_email_runtime_resolution.py in a separate HERALD Python process with bytecode writes disabled. It selected the existing Herald profile and installed an audit boundary denying network connects, subprocess/fork/system operations and filesystem mutations (except the null output sink). All library stdout/stderr was suppressed; result metadata contains only route-match/auth-presence booleans and denied operation types.

Actual configured route matches openai-codex/gpt-5.6-terra. Existing Hermes resolve_runtime_provider succeeded and returned the same provider plus nonempty cached authentication material. This is presence/resolution evidence, not proof the provider will accept it or an independent human-identity check. os.mkdir, os.chmod and subprocess.Popen were attempted and denied; the resolver still completed. No writes or subprocesses were permitted by this test.

The same restricted process exercised the unchanged actual profile_inference entry through the staged inline adapter with actual configuration/identity reads, actual runtime resolver, required-header code and actual OpenAI SDK construction. Only CodexAuxiliaryClient was replaced with a test wrapper that intercepted chat.completions.create before network and returned synthetic content. The wrapper verified exact model, max_tokens1800 and timeout75, then closed the real constructed SDK client. Correct provider/model/result and cleanup passed. No real model request, quota use attributable to an application inference, mailbox access or OAuth refresh network call occurred.

This resolves the earlier uncertainty about whether cached resolution and SDK construction can complete while child dispatch is denied. It does not validate token freshness with the remote provider, actual inference quality/latency, refresh-required behavior, all library subprocess paths, host-failure guarantees or real Gmail account ownership. A provider can still reject the cached material. Full exact-package recovery, coordinated shared-token caller rollout and inaccessible scheduled Node-RED consumer remain open before deployment.

Current staged package remains email-inline-model-private manifest1262ea18e24c244c75a63545afbbae8bab1485c82218f021c4f44029e591046e. No source/routing/configuration changed in this check. Recovery requires no rollback; private auth files and production databases were not modified. Do not infer permission to trigger a mail report or send from these diagnostic results.

No SAM, Odoo, Warden, phone, Level8, SyncThing, schedule or external communication change. Existing software and no paid commitment. Codex usage and dollar attribution remain separate. Phase1 open.
