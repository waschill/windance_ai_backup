# Live Harness forwarded-address check

At 2026-10-02T17:45:27Z, three read-only GETs from HERALD loopback returned: /health 200; /team without Authorization 200; /team with only synthetic X-Forwarded-For:198.51.100.123 returned401. Response bodies were not read or stored. No report, message, action, dispatch or mutation endpoint was called.

This establishes that the running HTTP stack uses the forwarded address from this trusted local connection in its access decision. The preceding application-only ASGI test deliberately omitted server proxy middleware, so its observation that a forwarded header alone did not bypass application checks is limited to that layer. These findings are compatible; they must not be confused. Neither establishes access from arbitrary external clients.

Read-only source/configuration metadata: installed source remains c2fa4c908a2ff5cdcc92d58da0ac5cf38534d800a235cbdf3bfcaed5341e3ef7. Installed uvicorn reports0.41.0 and Config defaults proxy_headers=True, forwarded_allow_ips=None. Saved com.windance.agent-harness.plist SHA2565e7597948183dc177137902369f6c234968a02da5f3ced8e9a555be315a46e2c supplies host0.0.0.0/port8791, no explicit proxy-header flags and no FORWARDED_ALLOW_IPS environment entry. No uvicorn.run call exists in the main source. Saved configuration does not by itself prove the running process arguments/environment or actual trusted proxy list.

Remaining deployment evidence: permitted inspection of actual reverse-proxy client-address handling and active caller identity; distinguish service authentication from human owner authorization. Do not change global authentication or infer internet exposure from listener bind alone. Do not use this investigation to bypass the Node-RED browser denial. No new network exposure was created.

The attached scanner prints only safe configuration metadata, not environment values or credentials. The probe reads status only and has an eight-second timeout per request. No production rollback is needed because this was read-only; normal access logs may record the probes. Phase1 remains open. Existing backups, approval histories, schedules and privacy restrictions remain unchanged.
