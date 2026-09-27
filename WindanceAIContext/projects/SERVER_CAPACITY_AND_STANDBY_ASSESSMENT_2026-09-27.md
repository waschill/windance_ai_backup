# Server capacity and standby assessment

Assessed 2026-09-27, approximately 10:56–11:01 Mountain. Requested by William. Read-only infrastructure assessment; no failover, migration, restart, new scheduler, SyncThing change or purchase was performed.

## Recommendation

Existing hardware has enough spare capacity to cover selected services from a failed sister server. AL and Herald are the strongest existing compute candidates. A dedicated refurbished standby is the cleaner operational choice if budget permits: reserve its capacity for a single failed server's portable services, while SAL and Herald provide the Mac-dependent fallback for each other. This is a recommendation, not an approved purchase or deployment.

Target an x86 business SFF/tower with an i7-10700-class eight-core CPU or newer comparable CPU, 64 GB RAM, and 2 TB SSD capacity for operating systems/application state. Prefer two independently replaceable SSDs with a planned mirror where the chassis supports it, wired Ethernet, UPS protection, automatic power recovery, and a meaningful seller warranty. No discrete GPU is needed for cloud-model orchestration. 32 GB may suffice for a single portable workload, but 64 GB provides a better margin for recovery tools, VM overhead and growth. Bulk Production files require separate capacity.

Start with a powered, patched warm standby and tested operator cutover. Automatic failover is a later engineering step requiring health checks, old-primary isolation, consistent state replication and duplicate-action protection. This is not a three-node cluster proposal and does not make existing physical installations automatically restartable as VMs.

## Measured hardware and capacity

RAM hardware capacities are nominal GB. Filesystem free values are the OS-reported binary GiB/TiB where indicated. CPU readings are short observations unless otherwise stated.

| Host | Live hardware | Observed resource/storage position | Assessment |
|---|---|---|---|
| HAL | i5-13400F, 10 cores/16 threads; 64 GB RAM; RTX 5070, about 12 GB VRAM | Approximately 39 GiB RAM free; C: 1 TB class SSD; Production P: local DrivePool volume | Keep GPU-heavy AI separate. Some light services could be recovered elsewhere, but another ordinary standby does not replace GPU inference or Production storage. |
| AL | Dell OptiPlex 3070; i5-8500, 6 cores/6 threads; 32 GB RAM; 2 TB SATA SSD | About 27.6 GiB RAM available, zero swap; CPU mostly idle. Root LV is only 100 GiB with about 34 GiB free despite the larger physical SSD | Strong candidate to cover portable SAL services or a prepared Linux deployment of Herald. Disk allocation should be checked before adding images. No capacity change performed. |
| SAL | Macmini9,1 / Apple M1, 8 cores; 16 GB RAM; 512 GB class SSD | About 411 GiB filesystem free; second CPU sample 96% idle; zero swap. macOS reports high physical usage but memory_pressure -Q reports 83% free by its own pressure metric | Enough apparent headroom for selected lightweight services. Not established as a full Herald-plus-AL replacement. ARM architecture requires compatible images/dependencies. |
| Herald | iMac20,1; i9-10910, 10 cores/20 threads; 32 GB RAM; 1 TB SSD | About 13 GiB unused RAM, about 315 MiB allocated swap but no swap activity during sample; roughly 95–99% CPU idle; 868 GiB filesystem free | Strong existing standby for SAL and potentially AL's apps in a prepared Linux VM. A supported VM/container environment was not verified installed. |
| SAM | Raspberry Pi 5, 8 GB RAM; 128 GB microSD | About 6.8 GiB available RAM; 101 GiB filesystem free; near-zero observed load | Its application is small and is a good standby candidate on another host. Avoid making a Wi-Fi/microSD kiosk the central emergency server. Backend recovery does not replace a failed physical display. |
| REFWeb | ARM64 Pi-class host, 8 GB RAM; about 1 TB NVMe filesystem | About 6.8 GiB RAM available; 867 GiB filesystem free | Web application/image serving can be considered for standby; public routing and data currency still require a dedicated test. |
| Odyssey | Intel N95, approximately 8 GB RAM | About 6.2 GiB RAM available; 22 TiB volume, 7.2 TiB used, 15 TiB available | Storage candidate, not preferred for absorbing heavy compute while also preserving backups. |
| TMA-1 and TMA-2 | ARM64 NAS, approximately 2 GB RAM each | Each approximately 21.7 TiB volume, 7.2 TiB used, 14.4 TiB available | Retain storage/backup role. No compute-failover recommendation. Backup contents/currency were not verified by matching volume sizes. |

Herald's live identity supersedes the older inventory's 2019 description. A CPU model and core count do not establish performance equivalence across generations or architectures. HAL remains unique for GPU work; this assessment does not claim its CPU wins every workload.

## Historical load evidence

AL has existing sysstat records. Read-only sadf exports supplied these per-day summaries:

| UTC date | Recorded samples | Mean CPU non-idle | Highest interval non-idle | Lowest available RAM |
|---|---:|---:|---:|---:|
| September 24 | 124 | 4.36% | 11.30% | 27.35 GiB |
| September 25 | 22 | 0.70% | 0.90% | 28.02 GiB |
| September 26 | 129 | 4.05% | 11.17% | 27.63 GiB |
| September 27, partial | 101 | 3.99% | 11.77% | 27.63 GiB |

Samples are generally about ten minutes apart. Non-idle includes I/O wait. Gaps include offline periods; brief spikes and events in gaps are not represented. These measurements show capacity headroom, not the cause of AL's recent failures. No historic Mac peak-load series or combined-load stress test was established. macOS cached/reclaimable memory is not equivalent to irrevocably committed application RAM.

AL's six running containers consumed about 2.8 GiB in a point sample: production Open WebUI ~1.1 GiB, isolated lab ~835 MiB, Syncthing ~664 MiB, SearXNG ~164 MiB, Portainer ~91 MiB, Valkey ~13 MiB. Container memory and host totals use different accounting; do not add them together.

Herald's services directory is ~5.3 GiB, .hermes ~7 GiB, and .local/share ~239 MiB. SAL services ~297 MiB and .node-red ~218 MiB, mostly dependencies. These are scoped directory measurements, not complete recoverable-system image sizes. Credentials, permissions, user sessions and external storage need separate protected provisioning.

## Viable sister-server coverage

| Failure | Existing-hardware option | Dedicated-PC option | Remaining limitation |
|---|---|---|---|
| AL | Herald hosts prepared Linux apps; SAL can cover selected compatible lightweight apps | Strong fit for Linux containers/services | Syncthing identity, mounts, consistent configuration and single-owner handoff must be designed; no SyncThing modification authorized here. |
| SAL | AL handles portable services; Herald handles Messages | PC handles tunnel, Node-RED and ported scripts; Herald retains Messages fallback | Current workflows contain Mac-specific commands and hardcoded paths. |
| Herald | AL handles ported backend; SAL handles Apple-dependent pieces | Strong fit for portable assistant, phone connector, dashboard and queue after porting | Requires authenticating providers, paths, databases, worker ownership and channel identity on the standby. No live-call continuation guarantee. |
| SAM / REFWeb | AL or Herald can host prepared backend copies | Small additional standby footprints | Physical kiosk and public route continuity are separate from backend recovery. |
| HAL | Recover selected small services elsewhere | Can cover some CPU-only utilities and cloud orchestration | Not equivalent local model performance; Production P: availability remains a separate design. |
| NAS | Other storage may hold recoverable copies | PC can serve only data actually available to it | Compute capacity does not establish coherent, current writable storage failover. |

SAL's live Node-RED flow file has 306 nodes, including 26 exec nodes and 78 function nodes. A scoped scan of SAL Python scripts found osascript, launchctl, /Users paths and fixed Herald/HAL IPs. Therefore copying Node-RED flows alone is not a tested portable replacement. Mac-only Messages must remain on a prepared, signed-in Mac with tested permissions and the right account identity. Do not assume the two Macs' existing identities are interchangeable.

Planning envelopes for validation, not measured requirements: AL portable service bundle 8–12 GB RAM; SAL portable bundle 4–8 GB; Herald portable bundle 16–24 GB; host/management reserve 4–8 GB. A 64 GB standby has a sensible margin for the largest single failure. Multiple simultaneous host failures and local model inference are excluded from that sizing claim. RAM fit does not prove I/O performance, latency or service compatibility.

## Storage and HAL dependency

Live Windows Get-Volume identifies P: as a local DrivePool volume, not a mapped NAS share: approximately 25.03 TB logical capacity, 19.10 TB reported free, roughly 5.93 TB in use. HAL also exposes six 4 TB TerraMaster attached devices. This establishes a HAL dependency; DrivePool duplication policy and exact physical placement were not audited.

AL's /mnt/odyssey_syncthing is an NFS mount from 192.168.36.31:/Volume2/syncthing, and the Syncthing container binds /mnt. A backup AL on the same NAS does not protect against Odyssey failing. Likewise, a 2 TB standby SSD cannot contain all 5.93 TB of current P: data. An independently accessible current business-data copy and stable file path/share identity must be designed. Existing NAS copies are not assumed current or ready for promotion merely because their used capacities look similar.

Cloud-backed Herald processing may work without HAL for some requests, but workflows using HAL Ollama, the Second Brain or P: still depend on it. Cloud model providers, Odoo, Telnyx, WAN, router, switch and power remain separate dependencies.

## Refurbished buying direction

Candidate chassis: Dell OptiPlex 7080 SFF/tower with i7-10700. Dell documents four DIMM slots and up to 128 GB RAM for the SFF, supporting a 64 GB plan. Verify exact chassis drive bays, caddies, SSD condition, PSU and NIC slots before buying. Prefer SFF/tower for serviceability and drive expansion; a Micro listing is not the same chassis.

Observed market anchor: PCLiquidations SKU 163402 showed $490.98 for an i7-10700 / 8 GB / 256 GB SSD base configuration, one-year warranty and 30-day returns. This is NOT a quote for the recommended 64 GB / 2 TB configuration. Upgrade, tax, UPS and extra SSD costs are additional and unquoted. System Liquidation's 32 GB/1 TB listing showed $899 and conflicting sold-out/in-stock text; do not treat it as verified available stock or a preferred purchase. No complete configured offer was validated or ordered.

Sources checked September 27:
- Dell specifications: https://www.dell.com/support/manuals/en-us/optiplex-7080-sff/7080_sff_ss/memory?guid=guid-5dde3559-1c4a-4fe6-a4db-263e2ee75f18&lang=en-us
- Base-price market anchor: https://www.pcliquidations.com/dell-optiplex-7080-sff/p/163402
- Second listing: https://systemliquidation.com/products/dell-optiplex-7080-small-form-factor-desktop-intel-core-i7-10700-2-9ghz-32gb-ram-1tb-ssd-windows-10-pro-grade-a-refurbished
- Cloudflare connector redundancy: https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/tunnel-availability/
- Synchronization versus backup: https://docs.syncthing.net/users/faq.html#is-syncthing-my-ideal-backup-application

## Work required before declaring readiness

1. Select critical functions and acceptable recovery delay/data-loss window. A warm standby targets recovery, not uninterrupted sessions.
2. Prepare isolated replacement installations without activating production schedulers, Messages sending or task dispatch.
3. Provision protected credentials privately; sanitized Git backups intentionally omit them and are not a complete recovery package.
4. Use consistent database backup/replication, preserve task/delivery receipts, and prevent simultaneous writers. File sync alone is not a live database HA mechanism.
5. Validate origin reachability, stable names, storage access and independent tunnel connectors. Do not let identical loopback routes point at the wrong host.
6. Test largest expected workloads on the candidate, then perform supervised primary-stop / standby-start / failback drills. Verify no duplicate actions and no missing accepted tasks.
7. Only then consider automatic takeover with reliable failed-primary isolation. Any Warden autonomous repair retains William's existing same-revision Codex/Claude approval policy. This assessment does not change it.

The dedicated standby should stay powered and receive protected state updates and health checks, but run no competing production business jobs until promoted. It can remain useful as a tunnel replica if William chooses. A powered-off spare has a materially longer recovery path. A single standby covers one-primary-failure scenarios; it is not a guarantee against arbitrary simultaneous failures or shared infrastructure loss.
