# Training rejection diagnostics and alarm approval — October 1, 2026

## Current owner direction

William explicitly approved restoring SAM's temperature-alarm notification connection during voice conversation: "Yes, please restore that." This supersedes the earlier unanswered alarm-repair approval hold. The approved repair is the existing supported link-out/link-in restoration, preserving the original parser, thresholds and recipient. No test send was requested.

Execution remains blocked by the browser tool's access policy. The owner opened and signed into the public Node-RED page, but selection of that tab was denied for https://nr.reflectsody.com. Earlier private-address access was also denied. No import, deploy or alternative execution path was attempted after these denials. Do not infer that authentication cleared the tool restriction, or call the alarm repair complete. Do not ask again for approval of the repair itself. The outstanding requirement is permitted tool access. Existing alarm disconnection and recovery files remain as previously recorded.

## Independent progress

Prepared an isolated candidate for wr_train_format only. On rejection, it adds a node.warn entry containing a fixed schema: UTC observation time, Mountain business date, fixed reason/status classes and boolean contract checks. It does not log response contents, raw exceptions, contacts, message IDs or tokens. The existing node.error and return-null behavior remain identical, and accepted messages are unchanged. No catch routing, sender, recipient, timer, model, phone, SAM or Odoo behavior was changed.

Candidate.json includes before/after function source and hashes. Baseline hash 756895241c214baa4d6cbbc29a404b0d21ba58650deb37b0857ce8443094f990 matches the previously verified function; a fresh live hash and complete graph inspection are required before any installation. Candidate hash: 1f86a199df2fad16965a23df88884cbd626e68c33605aa0753b48c732388bfc1.

HAL's existing Node runtime passed 18 isolated cases: accepted input, HTTP/transport/missing status, upstream error, wrong provider/model, null/string/array/empty payloads, nonstring/invalid/stale reply, missing/invalid/oversize identity, and numeric-string status compatibility. Each case compares original and candidate results and original error messages. Every new diagnostic is checked against an exact schema, boolean fields and enums; a private sentinel in rejected input never appears in the diagnostic. Execution uses VM timeouts of 1000ms with no network or sender bindings. This does not prove log retention, installed-runtime behavior or production delivery. No diagnostics are yet installed.

Repeat locally: run build_training_diagnostics.py with the archived original training-candidate/node-changes.json available at its documented relative location, then run test_training_diagnostics.js with candidate.json in training-diagnostics. For the archived test alone, keep test_training_diagnostics.js one directory above a training-diagnostics directory containing candidate.json, or adjust only that fixture path. No application import or external dependencies are needed.

Next: after browser access is permitted, revalidate maintenance ownership and Warden pause, create and verify a fresh private flow recovery copy, apply the approved alarm repair with Modified Nodes and compare the whole graph. Treat this separate diagnostic candidate as its own exact diff; validate against the then-current flow and runtime before deployment. Do not bundle unverified changes. Confirm resulting local log retention without injecting any report or alarm. Preserve existing rejection safeguards.

Recovery: no production mutation in this work unit, so nothing to roll back. For a later diagnostic installation, restore only the verified prior wr_train_format function while preserving the repaired alarm links and all unrelated newer changes. Do not restore an old full flow containing the known wrong-recipient route or disconnected alarm as a known-good baseline.

Phase 1 remains open; training natural acceptance remains zero and Shawn note collection remains deferred. Warden's jobs stay unloaded during the project. No paid commitment or application model call; Codex usage is not zero and its dollar cost remains unmeasured. Latest account check showed 20% weekly usage, not project cost attribution.
