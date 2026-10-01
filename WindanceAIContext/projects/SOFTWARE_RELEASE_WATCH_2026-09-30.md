# Windance software release watch

September30, 2026. William confirmed HERALD's update is complete and requested watching for subsequent releases, suggesting vendor schedules inform the workflow. Live SSH reported macOS26.7.1 build25G241. The OS installation item is complete; this does not certify every service or authorize macOS27.

Existing automation windance-software-upgrade-follow-through is now named Windance software release watch, ACTIVE daily10:00 Mountain in its existing chat. Former15-minute installation polling has ended. This read-only watch does not install, restart, dispatch staff or send external messages. Implementation belongs to the gated agentic-stack project.

## Release research

Sources checked September30. Monitoring cadence is our choice, not a vendor promise. Compare actual installed hardware/channel/version/commit and pins, not merely a global latest-version listing.

| Component | Official evidence | Watch policy |
|---|---|---|
| Windows | [Release cycle](https://learn.microsoft.com/en-us/windows/deployment/update/release-cycle): security releases second Tuesday, optional previews fourth Tuesday, out-of-band as needed | Daily advisory delta, focused review after Patch Tuesday; previews excluded by default and HAL reboot remains deferred |
| macOS/Safari | [Apple security releases](https://support.apple.com/en-us/100100) lists dated releases; no fixed patch day established here | Daily advisory delta, supported hardware/channel check; retain macOS27 exclusion |
| Node.js | [Lifecycle](https://nodejs.org/en/about/previous-releases) and [schedule](https://github.com/nodejs/Release) distinguish Current/LTS/EOL | Weekly lifecycle review, daily security delta; preserve SAL Node26.8.1 pin |
| Node-RED | [Release plan](https://nodered.org/about/releases/) aims at annual majors aligned with Node.js, minor/maintenance as needed; dates can change | Weekly release assessment, daily security delta; test contributed nodes and actual flows |
| Hermes | [Official releases](https://github.com/NousResearch/hermes-agent/releases); fixed timetable not established | Daily feed delta, weekly substantive review; exact installed channel/commit and local customizations matter |
| Ollama/model artifacts | [Ollama releases](https://github.com/ollama/ollama/releases); fixed timetable not established | Daily feed delta, weekly benefit assessment; track engine and model digest separately; never pull mutable tags just because labeled latest |
| Open WebUI | [Update guidance](https://docs.openwebui.com/getting-started/updating/) recommends production pinning, release-note review and staging | Daily release/security delta, weekly assessment; isolated lab and volume recovery before production replacement |
| Debian/package base | [Security advisories](https://www.debian.org/security/) and [point-release plans](https://release.debian.org/) separate security updates from tentative point-release dates | Daily advisories, weekly installed-repository reconciliation; verify SAM's actual distro/repositories, no implicit firmware/distro migration |
| Ubuntu where installed | [Lifecycle](https://ubuntu.com/about/release-cycle), [security updates](https://documentation.ubuntu.com/security/security-updates/) | Weekly lifecycle and daily security delta; support extensions are not automatically free included coverage |
| Docker | [Engine release notes](https://docs.docker.com/engine/release-notes/) | Weekly compatibility review plus daily security delta; engine packages and application images tracked separately |
| Odoo Online | Current-version support/cadence review still pending; tenant was saas19.3+e at baseline | Provider-managed change awareness and read-only connector regression; no tenant upgrade/accounting write implied |
| Cloudflared, SearXNG, Valkey, Portainer, NAS, router, backup tools and remaining installed components | Official-source coverage still incomplete | Complete source registry against inventory before claiming all-vendor coverage; no invented release day; SyncThing/Level8/firmware restrictions remain |

Daily does not mean a full model audit of every component. Reuse cached installed inventory and changed release/advisory identifiers. Reuse existing weekly review findings, avoiding duplicate reports and staff assignments. A deterministic feed cache could reduce cost further but is not yet implemented; the current app heartbeat consumes some model quota and is not a zero-cost daemon.

Classify changed items: urgent applicable security fix, routine corrective patch, useful feature to test, incompatible/deferred, irrelevant. Record source/version/date, affected host/channel, benefit, dependency effects and backup/rollback/test needs. Promptly notify William of urgent applicable advisories; consolidate routine recommendations; remain quiet on unchanged/irrelevant releases. No arbitrary waiting period should suppress an urgent issue and no announcement alone authorizes installation.

## Service recovery is separate

At18:15 Mountain manager8797 refused connections via connector and HERALD localhost. Approximately18:20 SAL Warden was unpaused: HERALD:runner incident INC-20260930-148740cb escalated, HERALD:harness INC-20260930-51ef44e0 held; dashboard/gateway incidents resolved. The former upgrade chat's latest receipts likewise reported unresolved Harness/task-runner recovery. This is not evidence the OS installer is still pending.

The agentic-stack project now owns diagnosis of these service failures. Check exact live incident/proposal state before any repair and preserve Warden consensus; do not erase evidence or replay tasks. The release watcher does not repair or repeatedly poll these issues.

## Verification and recovery

Automation update returned ACTIVE with the existing ID; future execution remains unobserved and depends on host/app availability. Earlier prompt/cadence are in this chat's tool history; historical upgrade guide remains. Do not restore obsolete installer polling over newer direction. Publish via canonical publisher -PushGit and verify indexing.

## October 1 daily delta — actionable Docker security patch

Read-only live AL check: Docker29.8.1; existing Ubuntu resolute/stable amd64 package metadata offers29.8.2. [Docker official release notes](https://docs.docker.com/engine/release-notes/29/) date29.8.2 September30 and identify crafted-image resource exhaustion (CVE-2026-53493), registry TLS/HTTP downgrade via malicious DNS (CVE-2026-92543), and encrypted Swarm overlay injection (CVE-2026-92542). AL Swarm is inactive, so that feature-specific exposure was not established. Registry/image-pull fixes warrant a prioritized gated upgrade. No exploitation was observed or tested. Two linked Moby advisory pages returned404; those details rely on Docker's release notes. The [containerd advisory](https://github.com/containerd/containerd/security/advisories/GHSA-pg57-6jwg-q645) was accessible; exact separately installed containerd applicability still needs reconciliation.

Implementation requirements for the owning stack project: fresh restore point and application-volume recovery; retain current packages/config/image digests; coordinate Docker restart and all hosted services, including the protected Syncthing workload, without reconfiguring it; verify registry TLS/pull behavior with trusted images and every existing container's health after the upgrade. Retain a tested package/state rollback. This watch installed nothing, refreshed no package indexes, restarted nothing and dispatched no staff.

Other deterministic feed checks: Hermes tagged stable v2026.9.24 unchanged (do not replace newer customized main runtime with an older tag); Node-RED5.0.7, Open WebUI0.11.4, cloudflared2026.9.3, Portainer2.45.1 and Valkey9.1.2 match the recorded baseline. HAL's live Ollama CLI and API already report0.35.0, matching the [September28 release](https://github.com/ollama/ollama/releases/tag/v0.35.0); this watch did not install it. [Apple's advisory list](https://support.apple.com/en-us/100100) still lists Tahoe26.7.1 and Safari27 as latest for the observed channel; excluded macOS27 is not an eligible recommendation. Windows/Node/Debian advisory pages were consulted but no comprehensive package/CVE reconciliation is claimed. Ubuntu/NAS/router and remaining vendor coverage remains incomplete. Preserve all existing pins and deferrals; no whole-stack current/security certification follows from this bounded delta check.
