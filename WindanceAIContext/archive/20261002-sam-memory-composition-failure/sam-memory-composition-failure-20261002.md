# SAM composed memory recovery gate — failed, staged only

Eight isolated scenarios exercised the private r3 candidate's actual connect, schema initialization, service-history posting, memory helper and day-commit functions. Odoo and the network transport were substituted; the durable memory client and receiver used real, separate temporary SQLite databases. No production service, schedule, Odoo record, message, note collection or model route changed.

Candidate main SHA-256: a9288a5549ea50491caf771cfad67a818b442cbe27460d492cbbd8036fa58377. The complete five-file manifest is emitted by the reproduction. The private full source remains in HAL workspace sam-memory-r3-private; it is intentionally excluded from this publication.

## Finding

Normal completion succeeds with one synthetic history create, one clear and one receiver commit; subsequent calls do nothing. However, when the receiver commits and its response is lost, subsequent SAM attempts do not recover. On the first attempt, the renderer includes the newly created history entry. On retry, the history receipt prevents another create, and that entry is classified as already posted; the renderer includes only newly posted entries. The regenerated memory content consequently differs. The durable client correctly rejects replacement of its existing request with different content. One receiver commit exists while SAM remains uncommitted after three attempts.

This is an integration defect, not permission failure or receiver duplication. Earlier seam tests used simplified history behavior and did not prove this composition. Candidate acceptance is FAILED. An exit-zero reproduction confirms the expected failure; it does not certify the candidate.

Other observations: wrong receipts remain uncommitted; missing configuration makes no memory call but currently occurs after simulated history/clear effects; unknown history/clear outcomes prevent repeats and memory completion; failed local clear-receipt insertion recovers without clearing a newer synthetic need. All SQLite integrity checks pass. The test's initial missing Connection annotation stub was corrected before these observations.

## Next repair and gates

Prepare a durable commit snapshot and explicit recovery behavior that retains the exact admitted summary across response loss, while detecting changed schedule input rather than silently marking changed work complete. Cover history, rollover and automatic/manual trigger differences; simply weakening the content check is unacceptable. Check required memory configuration before side effects. Exercise full startup, restart and isolated restore of the final composed package before installation.

The independent first-clear Odoo Boolean race remains unresolved: durable intent alone cannot prove that the need being cleared is the same request that was serviced. No Odoo schema or server action change is implied or authorized here. Real dedicated credentials, TLS, production reader policy and migration remain unverified. Phase 1 stays open.

## Recovery and reproduction

Production rollback is unnecessary because nothing was installed. Preserve the private r3 candidate as failed evidence and create a new revision for correction; do not overwrite the failed stage or alter its recorded hashes. Run test_sam_memory_r3.py from the original HAL workspace with its matching sam-memory-r3-private directory and sam_business_memory/sam_memory_contract modules. The shared packet alone is not a self-contained private-source recovery bundle. Temporary databases contain only synthetic data and are closed and removed by the test.

No application model calls or paid services were invoked. Codex account usage is separate; attributable project dollars are unknown. Node-RED access remains a separate unresolved tool restriction; this work does not bypass it.
