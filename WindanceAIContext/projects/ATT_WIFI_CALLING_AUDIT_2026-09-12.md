# AT&T Wi-Fi Calling router audit — 2026-09-12

William requested inspection against an AT&T screenshot and authorized useful router changes. Read-only live inspection found no demonstrated router configuration defect; no router settings, firmware, DNS overrides, or port forwards were changed.

## Verified router state

- Gateway 192.168.36.1 is ASUS RT-AX3000 (odmpid), platform productid RT-AX58U. Existing key-authenticated SSH works as William using HAL's homelab identity.
- Firmware 3.0.0.4.388_25277-g6b455f2 matches the latest entry returned by ASUS's RT-AX58U support page during this audit; the router's cached update version agrees.
- Static WAN on eth4; WAN, LAN bridge and active wireless interfaces have MTU 1500.
- IPSec passthrough is enabled (fw_pt_ipsec=1). Stateful forwarding allows established/related replies and traffic originating on br0, including UDP 500/4500 and TCP 143. No outbound VPN client diversion was present in the inspected chains.
- URL, keyword, network-service and DNS filters are disabled. The router's explicit DNS/IP deny rules did not name the AT&T destinations. QoS is disabled. UDP conntrack timeouts are 30 seconds unreplied and 180 seconds stream.
- An existing inbound UDP 500/1701/4500 forwarding rule is labeled L2TP / IPSec VPN Server and points to 192.168.36.100. Its target was not resolved in the ARP snapshot. This is not a Wi-Fi Calling prerequisite and was preserved because its intended service and current need are not established. Stateful return traffic is handled before new inbound forwarding; the rule's presence alone does not establish a calling fault.
- Two conntrack snapshots showed no UDP 500/4500 sessions. This does not prove a calling failure: no phone test was coordinated and hardware acceleration can limit visibility.

## Upstream findings and limitations

- HAL's do-not-fragment probes to 1.1.1.1 and 8.8.8.8 succeeded at 1464 bytes payload (1492-byte IPv4 packet), failed at 1465 (1493 total), and a 1472-byte payload also failed. Fragmentation-needed replies came from ISP gateway 64.251.177.193. Thus the tested Internet paths have a 1492-byte ceiling, despite router MTU 1500. This is not proof of the path MTU to an AT&T calling gateway or a cause of call failures. Leave router MTU unchanged pending an actual call trace or ISP guidance; forcing 1500 cannot enlarge the upstream path.
- sentitlement2.mobile.att.net and vvm.mobile.att.net resolved through the router, Google DNS and Cloudflare DNS.
- epdg.epc.att.net returned NXDOMAIN through all three. An independent HTTPS query to Google Public DNS also returned status 3 with CNAME epdg.epc.att-idns.net and att-idns.net authority. This establishes that the observed lookup failure is not confined to the router's DNS handling; it does not establish an AT&T-wide outage or which hostname a particular phone currently uses. No hardcoded IP or DNS change was applied.
- Wi-Fi Calling registration, actual calls, Wi-Fi coverage at the phone and ISP handling of an active IPSec tunnel remain unverified. Ask whether William is on Windance Wi-Fi and whether symptoms are failure to register, dropped calls, or a preventive concern. If on site, test a normal call with airplane mode enabled and Wi-Fi re-enabled, then restore airplane mode off.

## Sources and recovery

- AT&T requirements: https://www.att.com/support/article-modal/wireless/KM1114459/ (UDP 500/4500, TCP 143, IPSec passthrough, preferred MTU 1500, three named hosts).
- ASUS firmware: https://www.asus.com/supportonly/rt-ax58u/helpdesk_bios/
- No operational rollback is needed because this was an audit. This sanitized record is the durable evidence summary; no credentials or full configuration backup were stored.
