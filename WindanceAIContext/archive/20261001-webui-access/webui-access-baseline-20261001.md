# Existing WebUI access baseline — October 1, 2026

Read-only checks of AL's existing open-webui and truth-engine-lab containers found both running Open WebUI0.11.4 with HTTP200 health. No new installation or replacement interface is needed merely to obtain WebUI. This does not establish the required interface or knowledge acceptance cases.

| Check | Production | Lab |
|---|---|---|
| Runtime auth flag | true | true |
| Runtime signup flag | false | true |
| Unauthenticated chats/users endpoints | HTTP401 | HTTP401 |
| User roles | one admin | no users |
| Chats |22, one owner |0 |
| Uploaded-file rows |1, one owner |0 |
| Knowledge rows / memory rows / groups |0 /0 /0 |0 /0 /0 |
| Custom functions / tools |2 /0 |0 /0 |

These are counts only. No chat, document, personal memory, function body, account identity or credential was exported. SQLite reads used mode=ro and query_only. The two negative HTTP checks do not prove all endpoints or owner boundaries are secure. Public configuration flags are runtime evidence; missing environment variables were not mistaken for disabled auth.

## Lab bootstrap exposure

Docker binds the lab to 192.168.36.20:3001, and a HAL LAN request successfully read its public configuration with auth=true and signup=true. The installed auths.py signup path, lines874–879, checks for exactly one user after insertion and promotes that first user to admin. With zero current users, an actor able to reach signup may claim initial administrator access. No signup was attempted. Internet exposure, perimeter firewall coverage and active exploitation were not tested and must not be inferred.

Do not treat this empty lab as an authenticated private operational workspace yet. Before adding business or personal data, establish intended administrator ownership and close bootstrap signup through supported configuration, or restrict its network reachability until enrollment. This is a proposed access-control correction, not a deployed change. Reinspect current configuration, preserve the exact container definition and volume state, and verify rollback before changing it. Do not copy secret-bearing configuration or authentication databases into the shared context. Existing production accounts and routing remain untouched.

## Separation and recovery limits

Separate container data mounts were previously inventoried, but these checks do not prove business/personal privacy separation within an account, document authorization, source citations, stale-source handling, correction persistence or tool safety. Production's two custom functions need scoped permission/behavior inspection before declaring the interface safe for bounded jobs. Empty knowledge/memory tables are not proof that there is no other mounted/indexed memory provider.

Both custom functions are active, non-global Python Filter classes. Their hashes are retained in the receipt; both import requests and urllib.parse alongside parsing/typing modules. That establishes potential network-capable code, not that either function ran or accessed a particular service. Function bodies and valve settings were not exported or executed. Model associations and actual network/authorization boundaries remain unverified.

No application-level WebUI restoration was performed in this pass. Earlier AL backup covered deployment metadata only, so chat/document/configuration recovery remains an explicit baseline gap. No account, configuration, container, model route, schedule or record was changed; no rollback is needed for this inspection. No model inference or paid installation was introduced.

Next useful step: inspect supported lab bootstrap configuration and production custom-function permission boundaries, then define exact interface acceptance tests using synthetic data in isolation. Retain the original three business pilots. Overall Phase1 remains open; this evidence does not advance Phase3 to passed.
