# Authenticated intake mounted on full staged manager app

October 2 UTC / October 1 Mountain 2026. No production deployment; Phase1 open.

Private builder rebased on the current installed manager SHA0ad87dcebb5844736ca218101ded61ce15c525c0042222f3f9e90d319f5445d5 changes only its app factory, verified by AST equality for all other top-level nodes. The app factory optionally attaches authenticated intake using `VEGA_AUTHENTICATED_INTAKE_CONFIG`. When unset, the new route and schema installation remain disabled. When set, the JSON policy must be an owner-private regular file with explicit issuer, credential and owner list; malformed or unsafe configuration fails startup. No fallback to unauthenticated intake is added. Existing legacy routes remain and are not accepted as authenticated memory sources.

The staged adapter fixes channel, follow-up notification policy and existing Messages namespace server-side. The content-policy wrapper is now packaged in `manager_authenticated_routes.py`, using exact extracted current Harness remember parser/secret classifier functions and the expanded source-intent grammar. It does not import production Harness or read its private runtime. The extracted functions and upstream source hash are archived. This is still keyword classification, not comprehensive secret detection.

## Full-app verification

`test_full_manager_authenticated.py` executes the full candidate manager module in a disposable data directory. Before execution, only its private Harness-token loading assignment is replaced with a synthetic fixture value, avoiding real credential reads. It constructs the actual app with its middleware and routes, then explicitly removes the background lifecycle before serving through a loopback aiohttp test server. Manager network/send entry points are replaced with failure sentinels. No manager loop, worker or external sender runs.

HTTP health, unauthorized intake, authenticated acceptance, same-source retry, attested-source readback, extra-field rejection and Vega-addressed business secret rejection passed. Only one synthetic accepted message/provenance row and zero projects were stored. Missing configuration omits the route. World-readable config and malformed JSON fail app construction. Exact candidate SHAe1c4b2aa6ac07d5d4f3625d78085a083d4ba34cd1ee3bf8ea8317f8350bcce59 is recorded in the receipt. This is stronger than function-only testing but deliberately does not prove worker lifecycle or natural delivery.

## Remaining rollout gates and recovery

Production manager, Harness, credentials, routes and schema remain unchanged. The private full-source candidate stays at `/Users/herald/services/source-memory-http-20261002/manager-authenticated-candidate.private.py`; do not publish it or replace production merely because the isolated app passes. Reproduction uses that directory's builder and `test_full_manager_authenticated.py` with existing Harness Python. Archive includes exact wiring, dependencies, policy, builder, tests and sanitized receipts, with hashes. No production rollback is required.

Complete the actual sender candidate and protected transport ownership/credentials; reconcile old-ID and cursor cutover; preserve the existing control-code/approval redaction performed by Harness forwarding before bypassing it; enforce the legacy identity boundary; wire learning, correction, forgetting and retrieval to authenticated source records without shared-copy leakage; verify fresh backups, cold recovery and idle maintenance conditions. The pending candidate still queues ordinary manager work; it does not itself intercept memory commands or ensure workers use the new store. Those are explicit acceptance gates, not implied by this HTTP result.

No model calls, external sends, task dispatches, Odoo writes or paid commitments. Codex work cost unmeasured. SAM, Warden suspension, SyncThing, disabled Level8 and disabled phone unchanged. Node-RED browser denial was not bypassed. Project goal remains active and incomplete.
