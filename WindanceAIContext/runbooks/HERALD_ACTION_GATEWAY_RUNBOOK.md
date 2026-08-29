# Herald Action Gateway Runbook

Version: 1.0  
Effective: 2026-07-22  
Owner: William Schilling  
Technical steward: Vega/Codex

## Purpose

Herald is William's single user-facing operations agent. Dashboard chat, direct web chat, walkie text/voice, and approved Node-RED/iMessage traffic converge on the Herald Agent Harness. Herald uses deterministic tools for known operations, a constrained plan/execute/verify gateway for homelab actions, and staff tasks for work that needs Forge, Vega, or another specialist.

The production source of truth is the Herald Agent Harness at `http://192.168.36.21:8791`, not the experimental raw Hermes terminal session.

## Operating contract

1. Understand the requested outcome and use relevant recent conversation and durable memory.
2. Inspect current state before changing it.
3. Prefer an existing typed tool over free-form delegation.
4. Produce a plan containing only registered actions and exact resources.
5. Check the permission ledger for that exact action and resource.
6. If authority is missing, request approval and stop before mutation.
7. Execute the smallest necessary change.
8. Verify the outcome independently where possible.
9. Record the plan, step status, evidence, and final result.
10. Say `I don't know` or clearly report a blocker rather than inventing completion.

## Approval model

- Read-only registered actions run without an approval prompt.
- Mutating actions require an exact, current grant for the principal, action, and resource.
- `APPROVE <id>` grants one-time permission for the pending request.
- `ALWAYS ALLOW <id>` records permanent permission for that exact action/resource pair.
- `REJECT <id>` cancels the request.
- Stale approvals fail closed.
- Permissions can be inspected at `GET /permissions` and revoked at `POST /permissions/{id}/revoke` from a trusted control host.
- A permission for one host, service, or action does not silently expand to another.

## Registered actions

As of 2026-07-23, the baseline toolbox exposes 20 typed actions. The catalog is available at `GET /action/tools`; it is the source of truth rather than this summary.

- Homelab: inventory, status, bounded host diagnostics, registered service status, approval-backed service restart.
- Operations: staff delegation, staff-task status, operations-ledger status, and a live Herald self-model.
- Information: Brave research, read-only Odoo queries, Gmail summary, upcoming Calendar, current briefing, memory recall.
- Memory and artifacts: safe non-secret memory write, daily reflection, SAM Training Schedule read, local Excalidraw diagram creation, approval-backed Image Studio creation.

Gmail/Calendar writes, SAM commits, external messages, account changes, destructive operations, SyncThing, and Level 8 remain outside the general toolbox or behind their specialized approval flows.

Current named actions are:

- `homelab.inventory`, `homelab.status`, `host.diagnostics`
- `service.status`, `service.restart`
- `delegate.staff_task`, `staff.status`, `operations.status`, `self.status`
- `web.research`, `odoo.query`, `gmail.summary`, `calendar.upcoming`, `briefing.generate`
- `memory.recall`, `memory.remember`, `memory.reflect`
- `sam.schedule.read`, `diagram.create`, `image.create`

The registry is implemented in `/Users/herald/services/agent-harness/windance_action_gateway.py`. There is deliberately no arbitrary-shell action. Static host/service mappings are used with `shell=False`.

## Network scope

Registered nodes are HAL, AL, SAL, HERALD, SAM, SAM-WIFI, ODYSSEY, TMA-1, TMA-2, and REFWEB. Read-only connectivity and service checks have been verified from Herald for every node except HAL SSH. HAL is ping-reachable, but Windows OpenSSH requires a one-time elevated installation of Herald's public key.

The subnet is not exposed as an arbitrary target range. A new device must be added to the authoritative inventory and typed registry before Herald can act on it.

Never store passwords, OAuth tokens, API keys, private SSH keys, Cloudflare tunnel tokens, or approval secrets in this runbook, memory, logs, or source control.

## Hard safety boundaries

- SyncThing is outside this gateway. Do not inspect, modify, restart, or reconfigure it unless William explicitly asks for a SyncThing change in that turn.
- Level 8 shutdown remains disabled and hazardous. The gateway refuses shutdown, reboot, and destructive disk actions. Do not re-enable or test Level 8 without William's explicit request in that turn.
- No unregistered raw shell supplied by a model.
- No destructive filesystem or account action through the general gateway.
- Email sends, deletes, and Calendar mutations retain their specialized approval workflows.

## Delegated staff work

When no typed action can complete a bounded technical request, Herald creates a real `staff_tasks` row. The plan remains `delegated` until the worker posts a real result. Completion reconciles the task, action step, and action plan with evidence. Herald must not call delegated work complete merely because it created a task.

Forge's Codex worker runs in `workspace-write` mode with network access and noninteractive approvals disabled. It does not run with `danger-full-access`. Direct William requests are treated as one-time authorization for necessary, non-destructive changes within the exact task scope; destructive, account, DNS, firewall, shutdown, and reboot changes require a new explicit approval.

## Control-plane security

Sensitive Agent Harness routes are limited to trusted Windance control hosts and may also use the configured bearer token. Current trusted addresses are loopback, HAL, AL, SAL, SAM LAN, and SAM Wi-Fi. This is a compatibility control, not a substitute for eventually issuing a dedicated service token to every front door.

## Important endpoints

- Health: `GET /health`
- User interaction: `POST /message`
- Walkie text: `POST /walkie/text`
- Tool registry: `GET /action/tools`
- Submit a plan: `POST /action/plan`
- Inspect a plan: `GET /action/plans/{id}`
- Permission ledger: `GET /permissions`
- Revoke a permission: `POST /permissions/{id}/revoke`
- Staff tasks: `GET /staff/tasks`

## Verification baseline (2026-07-22)

- Agent Harness health reports OpenRouter `openai/gpt-5.6-terra` as lead, Gemini fallback configuration, Ollama `gemma4:latest` fallback, valid Google access, Odoo and Brave configured, and vector memory fully embedded.
- Homelab status plan verified all ten registered hosts ping-reachable.
- Node-RED status on SAL verified HTTP 200.
- A service restart request produced an approval and did not mutate before approval.
- One-time permission consumption and stale-approval fail-closed behavior passed isolated database tests.
- Read-only diagnostics succeeded for AL, SAL, HERALD, SAM, SAM-WIFI, ODYSSEY, TMA-1, TMA-2, and REFWEB.
- Registered services reported healthy on HERALD, AL, SAL, SAM, and REFWEB.
- SAL Node-RED has a registered approval-backed restart command using its existing `com.zuzu.nodered` LaunchAgent; the restart guard was verified by requesting and rejecting an approval while confirming the Node-RED PID did not change.
- A Forge canary executed `ssh SAL hostname`, returned `Zuzus-Mac-mini.local`, posted evidence, and reconciled the delegated action plan to `succeeded`.

## Model routing and credits

OpenRouter `openai/gpt-5.6-terra` is configured as Herald's lead reasoning model. Gemini is the cloud fallback and Ollama `gemma4:latest` is the local fallback. A credit/quota response places OpenRouter on a one-hour in-process cooldown so one exhausted account does not delay every request. The operational trace identifies when a fallback model actually answered.

At the final 2026-07-23 verification, OpenRouter reported insufficient remaining credits for sustained normal replies. This is an account-balance constraint, not a harness configuration failure; typed/deterministic operations continue and model work falls back automatically.

## Rollback

Timestamped pre-deployment backups of the Agent Harness and Forge runner are stored next to their live files on Herald. To roll back, restore the selected backup, run a Python syntax check, restart only the affected LaunchAgent, and verify `/health` before restoring front-door traffic.

## Adding capability safely

Add a typed action with a fixed schema, explicit risk classification, exact resource format, deterministic executor, verification rule, and regression canary. Do not solve a missing capability by exposing a general remote shell to the language model.
