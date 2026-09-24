# Warden installation history — 2026-09-24

William authorized an independent supervisor on SAL, then required Codex and Claude
both to approve each exact repair. SAL messaging remains selected. Initial engine
was paused while consensus was built; no production repair used the old gate.

- Initial installation: 16 tests, five board checks, disposable service test,
  actual background Codex diagnosis, successful SAL notification outbox receipt.
- Revisions 1 and 2: Claude rejected defects; corrected before production use.
- Revision 3: 41 tests, source approved; live Codex held the insufficiently specified
  canary. No execution. Added concrete service and authority evidence.
- Revision 4: 42 tests, source approved; both runtime reviewers approved, but stderr
  session receipt was not captured. No execution; disposable job cleaned up.
- Revision 5: 43 tests, source approved; both approved, but CLI stdout parsing failed.
  Actual saved Claude verdict was valid. No execution; job cleaned up.
- Revision 6: 44 tests; Claude rejected insufficient request/response turn binding.
- Revision 7: 44 tests and compilation; Claude approved exact-turn canonical response
  retrieval. Live unanimous canary passed, same positive PID verified twice, cleanup
  succeeded. Runtime Claude session 20260924_154645_3c8f55 used Opus 5/OpenRouter.
- Canary proposal created=1790286389.78195, expires=1790287289.78195: numeric TTL is
  exactly 900 seconds. Reviewer display redacted these timestamps; executor checked
  original numbers. Reviews and authenticated same-account receipts are not
  cryptographic attestations against a compromised operating-system account.
- Four production fingerprints stable twice; exact reviewed deployment manifest
  checked on SAL and Herald. Activated both 120-second jobs at 21:52 UTC.
- Initial active check: all monitored checks healthy, no incidents. Later scheduler
  evidence is in scheduled-verification-receipt.json.
- Archivist revised-guide/shared-memory acceptance and final Forge procedure PASS
  are identified in the guide/SOP. Earlier partial staff tasks remain in Harness.

Runtime incidents and decisions continue in SAL HISTORY.md, incidents.sqlite and
reviews/. This archive preserves installation evidence, including unsuccessful
canaries. The board is authenticated. No whole-SAL outage protection or universal
failure prevention is claimed; YouTube process completion is not message delivery.
