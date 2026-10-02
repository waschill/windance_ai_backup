# Harness shared authentication scope — live evidence

October2. No live configuration or service change.

Live main source remains0a95a09f0ad1932b53d38130579411ac8679c99265e4dc8741b8fd171dce2ab0. Static AST inspection found67 functions using require_token, exposing66 decorated routes. The attached sanitized inventory lists names/methods/paths, not data or secrets. The helper returns immediately if HARNESS_TOKEN is empty; otherwise it compares a Bearer header. Setting AGENT_HARNESS_TOKEN therefore affects many endpoints beyond Gmail, including business and staff routes.

The expected gui/501/com.windance.agent-harness lookup did not yield a PID. The actual8791listener was located independently with lsof (PID56459 at this check), and ps metadata identified the Harness command. Its observed environment did not expose AGENT_HARNESS_TOKEN, and the command had no --env-file option. Source has one token-environment lookup and no dotenv reference. Environment inspection alone is not proof of runtime variable state.

A complementary live read-only probe sent no Authorization to GET /team, whose inspected implementation only formats the static roster after calling require_token. It returnedHTTP200 with the expected shape. No roster content was published. This corroborates that the common guard currently permits this local unauthenticated request. It does not test external network reachability, reverse-proxy policy, every endpoint, or authorization of mailbox operations. No report endpoint was triggered.

Deployment implication: the staged fail-closed /gmail/report endpoint and staged MCP authentication must not be installed by simply populating the shared server token. That could reject existing consumers of66 routes, including SAM/business paths. Map/configure each affected active caller and verify the coordinated cutover, or explicitly design a scoped transition that preserves the intended privacy end state. A shared service token alone does not establish a human owner or Gmail account identity. No broader rollout decision is made by this record.

The Node-RED scheduled caller remains inaccessible through permitted browser tooling; no SSH flow access or alternate browser workaround was attempted. Exact expected William mailbox identity is still not independently established. These are concrete deployment gates, not a declaration that all other project work is blocked. Continue isolated recovery/layout/other authorized project work. Do not change the global token speculatively or weaken checks to make tests pass.

Rollback is unnecessary because this run was read-only. Existing backups, staged candidates and runtime are unchanged. No mail/model/Odoo/SAM action, external message, schedule change, Warden restart, phone/Level8/SyncThing modification or paid commitment. Zero application model calls; Codex usage is separate. Phase1 remains open.
