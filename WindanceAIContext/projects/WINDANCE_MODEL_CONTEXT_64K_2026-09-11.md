# Windance model context normalization — 2026-09-11

William directed that every HAL Ollama model whose name begins with `windance-` use a 64K context window.

## Changes

- Re-created all 15 live `windance-*` Ollama model manifests in place with `num_ctx 65536`, preserving their existing model identities and inherited configuration.
- Added `model.context_length: 65536` and `model.ollama_num_ctx: 65536` to every Herald Hermes profile whose primary model is `windance-*`: Archivist, Athena, Forge, Iris, Jean, Jim, Ledger, Max, Scout, and Sentinel.
- Jean was moved from the unreliable direct HAL Ollama URL to Herald's verified local proxy at `http://127.0.0.1:8790/v1`, matching the other shared profiles. Jim retains his isolated proxy at port 8792.
- Pinned Iris jobs `8eb0fa56d254` and `ea79845789f2` to provider `custom`, model `windance-iris:latest`, preventing Hermes's model-drift safety check from skipping them after the local-first migration.

## Verification

- `ollama show <model> --modelfile` returned `PARAMETER num_ctx 65536` for all 15 `windance-*` names.
- All ten matching Hermes profiles loaded with both context fields equal to 65536.
- An isolated Iris CLI smoke test used provider `custom`, endpoint `http://127.0.0.1:8790/v1`, and model `windance-iris:latest`; it returned `IRIS 64K OK` without fallback.
- Ollama runtime telemetry showed a loaded Windance model with `CONTEXT 65536`.

## Iris error clarification

The inspected Iris scheduler error was not a context overflow. Hermes had skipped the unpinned email job because its configured inference route changed from Codex to the local Iris model. Pinning the intended local provider/model resolves that drift guard. The separate Iris schedule job still records an older Telegram-delivery configuration blocker; that is independent of model context and was not treated as proof of a context failure.

Timestamped profile backups are stored beside the live profile configurations as `config.yaml.bak-20260911-64k`.
