# Windance SearXNG — installed 2026-09-16

## Verified deployment and access

William authorized installation on AL and requested the browser address after canary testing.

- Browser: http://192.168.36.20:8888/ from the Windance LAN/Wi-Fi.
- Instance title: Windance Search. Version: 2026.9.16-461f174b0.
- JSON API: GET /search?q=QUERY&format=json (URL-encode QUERY).
- AL directory: /home/waschilladmin/services/searxng; Compose project windance-searxng.
- Containers: searxng-core and searxng-valkey. Restart policy unless-stopped.
- Only published port: 192.168.36.20:8888 -> core:8080. Valkey has no host port. No public DNS, Cloudflare route or router forwarding was added. This is a trusted-LAN HTTP service without an application login; do not expose it to the Internet.
- Persistent volumes: windance-searxng_core-data and windance-searxng_valkey-data; settings bind-mounted from core-config. The generated server secret stays only in AL's protected settings file and is never included in this package.
- Official images pinned by digest:
  - searxng/searxng@sha256:a31763b7af3caf6ae9aac1816ba774214eb550252e06a4998f276ded8d60461b
  - valkey/valkey@sha256:a0dbf4c1d5708782907c10e2c72deff317518518b5288a58416981d9db95d30b
- CPU/RAM ceilings: core 2 CPUs/1536 MiB; Valkey 0.5 CPU/256 MiB, with 128 MB cache ceiling. Logs rotate at 5 MB with two files.
- HTML and JSON enabled; autocomplete and debug disabled; SafeSearch moderate; image proxy enabled. Upstream timeout 5 seconds, maximum 10 seconds.
- Engines: Google, Bing, Brave and Wikipedia. Google/Bing/Brave returned useful results; Wikipedia returned no results on the initial query. DuckDuckGo returned CAPTCHA and was removed from the enabled engine set rather than attempting a bypass.

## Integration

- Scout's /Users/herald/.hermes/profiles/scout/config.yaml now sets web.search_backend=searxng and web.keyless_rescue=false. Its profile-local .env has the non-secret SEARXNG_URL=http://192.168.36.20:8888 endpoint.
- Existing web.extract_backend=tavily is preserved: page extraction can still consume existing Tavily credits. SearXNG searches require neither an OpenAI call nor a paid search API key. Model use remains separate. No credit purchase, subscription or reset was performed.
- Scout SOUL now identifies SearXNG as the search service, preserves primary-source/Truth Mode/Athena gates, and explicitly requires checking exact entity matches even when search engines return unrelated results for quoted nonsense queries.
- Fresh Scout-profile processes (including the Harness profile runner) load the setting. The multiplex gateway was not restarted; pre-existing interactive sessions may need a new session/reload before adopting it. No whole-staff routing change was made.
- The separate Open WebUI lab on AL port 3001 has persistent web-search configuration enabled with engine searxng, URL http://192.168.36.20:8888/search?q=<query>, result count 3 and concurrency 3. Lab restarted and health passed. Production Open WebUI on port 3000 was not reconfigured.

## Canary evidence

- Browser homepage rendered Windance Search; submitted browser query returned official SearXNG links, with displayed 1.2-second response time.
- HAL JSON searches reached the LAN endpoint. Individual engine checks returned Brave 20 results, Bing 10, Google 10. DuckDuckGo failed CAPTCHA and was excluded.
- Herald JSON checks returned 24 official-documentation-query results and 38 horse-pasture-query results, with no engine errors in those runs.
- Three concurrent documentation searches returned 32, 34 and 33 results, in 0.43, 1.75 and 0.82 seconds respectively, with no engine errors.
- A quoted nonexistent query returned unrelated results rather than zero. This is a known upstream relevance limitation, not evidence that the entity exists. Scout policy explicitly covers it. These canaries do not establish research accuracy or exhaustive source coverage.
- The actual Hermes web_search_tool under Scout's saved configuration passed and returned three structured source links. An isolated process with a deliberately unavailable endpoint returned success=false with rescue disabled; no paid fallback was invoked.
- The actual installed Open WebUI search_searxng function inside the lab returned three official documentation URLs.
- Both SearXNG containers restarted successfully; the post-restart search returned 32 results.
- Final sampled resource use: core 153 MiB, Valkey 3.77 MiB; CPU below 1% each at that snapshot. This is a sample, not a load guarantee.
- Port-binding inspection verified LAN-only publication and no Valkey port. Both production Open WebUI and lab health returned HTTP 200/healthy.
- No end-to-end LLM research report, authenticated lab chat, physical phone test, host reboot, sustained stress test or outside-network access test is claimed.

## Operation and recovery

On AL: cd ~/services/searxng; docker compose ps, docker compose logs --tail 100 core, docker compose restart. Docker owns the configuration file after startup; use an authorized container administrative command to edit it without printing its secret. Pin a reviewed image update and retest before promotion.

To stop the new service without deleting persistent data: cd ~/services/searxng && docker compose down. No volume deletion is required.

Scout backups on Herald:
- /Users/herald/.hermes/profiles/scout/config.yaml.bak-before-searxng-20260916
- /Users/herald/.hermes/profiles/scout/SOUL.md.bak-before-searxng-20260916

For rollback, restore these files and remove only the SEARXNG_URL line added to Scout's profile-local .env, preserving all other entries. Existing sessions may need reload. Do not publish that .env or other credentials.

Lab rollback: /app/backend/data/searxng-settings-backup-20260916.json inside truth-engine-lab contains only the five prior non-secret web-search settings. Restore those config table values and restart only the lab. Production, Syncthing, SAM, Odoo and other profiles were not changed.

## Documentation

- https://docs.searxng.org/admin/installation-docker.html
- https://docs.searxng.org/dev/search_api.html
- https://docs.openwebui.com/features/chat-conversations/web-search/providers/searxng/
- https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search
