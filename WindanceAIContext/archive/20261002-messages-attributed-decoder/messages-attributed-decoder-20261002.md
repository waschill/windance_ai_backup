# Attributed Messages decoder evaluation — October 2

## Verified result

Pinned pytypedstream 0.1.0 wheel SHA256 `499920d4cb8bec8fd9d9cdd4c6312765eb418c398c10371ab1c9c0051104d278` downloaded into the HAL workspace decoder-evaluation-private directory, then copied to SAL /tmp for isolated import. No pip installation or production Python/service changes. Package metadata declares LGPL-3.0-or-later, upstream https://github.com/dgelessus/python-typedstream. Retain its licensing if later distributed; this packet does not redistribute the wheel.

SAL Foundation generated seven synthetic legacy NSArchiver fixtures using the included Swift source: plain, Unicode/newline/emoji, long body, embedded substring, empty string, wrong NSString root, and mutable attributed text with misleading metadata. NSArchiver emits a deprecation warning; it is intentionally used to exercise legacy typedstream format, not selected as a new production serialization format.

The candidate accepts only the known version-zero NSAttributedString/NSMutableAttributedString class chain and the first typed NSString text field. It does not concatenate arbitrary archive strings or use substring matching. Input is capped at 256 KiB and decoded text at 20,000 characters. Unknown classes, malformed input and errors return unavailable text without logging archive content. It is experimental and must run inside a bounded worker before use with real message data; size caps alone do not bound parser CPU/memory.

Actual pinned-wheel tests passed 145 assertions on HAL and SAL, including every truncation of the plain archive, trailing garbage/second archive rejection, non-bytes/oversize input rejection, exact Unicode preservation, and rejection of EXPECTED when merely embedded in a larger body or formatting metadata. HAL measured approximately 0.0 seconds at its timer resolution; SAL 0.0052 seconds. These small synthetic timings are not live workflow latency estimates.

Initial JXA fixture generation failed because its bridge lacked the attempted initWithString selector. Swift Foundation replaced it. An inspection print hit Windows console Unicode encoding; ASCII-escaped diagnostic output fixed the inspection only. Neither failure affected production or sent a message.

## Limits and next gate

No actual Messages database was read during this evaluation. Synthetic fixtures do not prove coverage of real Messages archive variants or parser hardening. Next use a resource-bounded, read-only worker to measure aggregate live decoding coverage without exporting bodies, recipients or identifiers. Then integrate exact text extraction into the staged receipt observer, preserving recipient/direct-chat, trusted pre-send boundary, ambiguity, sent/delivered/error and chunk-correlation checks. Unknown/malformed archives must remain unconfirmed. No parser result alone proves delivery or human reading.

No sender, scheduler, task dispatch, SAM service, Warden, phone, SyncThing, Level8, Odoo or model routing was changed. Natural training acceptance remains unverified; no pilot pass is claimed. No new paid commitment or application-model call; Codex cost unknown. Phase1 remains open.

## Reproduction and recovery

Run generate_attributed_fixtures.swift with SAL /usr/bin/swift and save its JSON as attributed-fixtures-20261002.json. Obtain the exact wheel, verify the SHA256 above, then run test_attributed_text_candidate.py with wheel path and fixture JSON path. The test imports directly from the wheel without installing it. Included fixtures contain synthetic data only.

Candidate and tests reside in this packet; evaluation copies are in the HAL project workspace and SAL /tmp. No production rollback is required because nothing was installed. Do not deploy the candidate by copying it into an active sender. Keep the prior plain-text observer intact until the combined bounded receipt path has passed its complete checks.
