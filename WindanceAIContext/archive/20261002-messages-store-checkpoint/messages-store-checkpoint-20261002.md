# Messages store checkpoint — October 2

Staged messages_store_checkpoint.py captures a readonlySQLite snapshot containing a hashed file device/inode plus first message row/GUID identity, the current highest row, and a hash of a selected boundary row/GUID. It never queries body or recipient columns. GUIDs remain local and only hashes leave the function; even these hashes are operational metadata requiring private handling. Public live probe exports booleans/timing only, no hashes or row identifiers.

HAL/SAL isolated tests pass: unchanged read preserves DBhash and checkpoint, append preserves the chosen anchor, same-file GUID change at boundary rejects, replacement file rejects, deleted anchor rejects, empty/missing DB and invalid row IDs hold without file creation. GUIDs must be nonempty strings at most512characters. ReadonlyURI/query_only,2-secondlock wait and100,000-operation SQLite budget apply. The helper must be invoked inside the supervised worker before integration.

SAL live probe under3-secondCPU/5-secondalarm limits captured a checkpoint and independently reread the selected anchor successfully in0.0274seconds. No message bodies, recipients, GUID values or row IDs exported. This proves current schema/access compatibility and consistency across those two reads, not durable send correlation or a particular delivery.

## Limits and next use

File replacement during/between reads, a missing/changed anchor and a lower observed high-water are rejected. Normal message append is allowed. This is not a universal anti-rollback guarantee: same-inode restoration retaining all compared anchors/high-water could escape detection, and file replacement after the last stat remains a race unless the complete reader compares the intended database consistently. First-row retention cleanup or a legitimate vacuum/replacement can conservatively hold; do not silently accept a new identity. Cross-file checkpoint comparison alone is insufficient to bind the later receipt query.

Next persist this checkpoint with the committed attempt and require the same store/anchor when observing its receipt; integrate the checkpoint comparison and exact query in the same supervised worker/database view. Extend composed crash tests to store replacement/rollback and anchor removal. Capture must occur before sending; do not invent anchors for old uncertain work. Full live handler/queue/consumer rollout remains pending.

Reproduce test_messages_store_checkpoint.py for synthetic coverage and verify_live_messages_checkpoint.py on SAL for aggregate-only live compatibility. Included candidate, probes and sanitized result are not installed in production. No sender/service/schedule changes or production rollback needed. No SAM/Odoo/SyncThing/Level8/Warden/phone/model-route changes, model call or paid commitment. Codex cost unknown. Phase1 open; no natural pilot pass or deployment claim.
