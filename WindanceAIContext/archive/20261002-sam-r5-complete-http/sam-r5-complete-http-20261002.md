# Complete staged SAM-to-producer HTTP composition

Full private r5 module and eight-file manifest were verified and imported in AL's pinned isolated container. The actual commit, rollover, source guard, snapshot, durable memory client and urllib transport communicated over real loopback HTTP with the staged FastAPI producer route and real temporary SQLite receiver. No extracted commit function or substituted network call replaced this path. The lost-response case deliberately raises after the actual HTTP transport has received the successful receiver response, approximating acknowledgment loss at that boundary.

Three scenarios passed:

| Scenario | HTTP transport attempts | Receiver commits | Local completion |
| --- | ---: | ---: | --- |
| Normal | 1 | 1 | yes |
| First acknowledgment lost | 2 | 1 | yes |
| Incorrect credential, then corrected | 2 | 1 | yes |

Each scenario retained one event identity, created one synthetic local carry and made no further transport call once the day was committed. Wrong credentials were tested with ephemeral files inside temporary storage; no production credential was copied or printed. The content-validation callback allowed synthetic text only for this fixture; this does not certify production classifier composition. Every listener stopped and thread joined; temporary data was removed.

Image sha256:9591b13f13843c7721c2b8eaf7382846c81b3ffe126526d1888d1fed50c6a33f was already installed. Container bb978e3dca6381185cd6410bb59d3a6684ab7e2373304fad1d752445db5dbb3d used network none, read-only root/evidence, UID/GID1000, dropped capabilities, no-new-privileges, 256MiB/0.5CPU/64PID limits and independent45s deadline. Configuration was inspected before starting; code verified only loopback. Exit0 and exact-container removal were verified afterward. No main/scheduler, live Odoo, external model, send, task dispatch or production service was started or changed. SAM remained untouched in its protected interval.

The test and server module copies are under /tmp/windance-sam-r5-recovery-20261002 on AL, a private volatile test directory. Durable current source and the private r5 manifest remain on HAL. No production rollback is needed. Reproduction requires the exact private stage, receiver modules and test under /evidence with the same container constraints; do not use live database or credentials.

This closes the staged complete-client HTTP composition gap. It does not establish production deployment readiness: real dedicated credentials/TLS, business-reader migration, source correction/recommit and the Odoo first-clear request-generation race remain open. No application model or paid API calls occurred; Codex consumption is separate and attributable dollars remain unknown. Phase1 and the original business pilots are not complete.
