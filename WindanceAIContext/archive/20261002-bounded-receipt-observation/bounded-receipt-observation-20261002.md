# Supervised receipt observation composition — October 2

New staged bounded_message_observer.py runs the actual exact SQLite/attributed receipt observer in a separate SAL Python process. Request body/recipient travel through stdin, not command arguments or logs. Parent validates the response schema and fixed reason vocabulary. Child verifies pinned wheel499920d4cb8bec8fd9d9cdd4c6312765eb418c398c10371ab1c9c0051104d278 before import and uses the prior readonly observer.

Worker CPU limit5seconds, alarm10seconds; parent deadline15seconds and sampled256MiBRSS watchdog. Parent kills/reaps an unfinished worker. RSS sampling is not a hard allocation cap, and subprocess pipe capture is trusted-small-output behavior rather than a hostile unlimited-output memory sandbox. Child input capped256KiB, decoded response4096bytes at parent validation. Child audit denies Python-level writes, sockets/subprocesses and unexpected SQLite URI after imports. OS capability isolation is not claimed. Caller is trusted to supply the intended database path; production path/continuity enforcement remains to be integrated.

## Verified tests

Five actual-send-function composition cases from the prior packet pass on SAL with each observer call now running in the real supervised subprocess, retaining two subsequent restarts: normal delivery, sent-only hold, abrupt exit after attempt, after send and after receipt. The production send_one body remains unchanged with its subprocess object intercepted locally; the shared subprocess module is no longer monkeypatched, so supervision really launches its worker. Parent audit permits only that fixed worker command and the RSS ps query; no osascript invocation.

Six separate supervisor fault-injection cases pass using a disposable copied child target: malformed JSON, invalid delivered-row type, private/unknown reason, oversized response, exit17, and60-second sleep. All produce the fixed unavailable result without leaking private sentinel text or creating a database. Sleep worker terminated after15.003seconds; PID absence verified after reaping. Other failures returned in approximately0.014–0.015seconds. These timings measure synthetic supervisor behavior, not real report latency.

Fault injection replaces only a disposable child file after loading the parent's actual code. Production/source modules remain untouched. It tests process boundary failure behavior, not supply-chain tamper resistance. The wheel is pinned; a complete deployed module manifest/package is still needed.

## Remaining gates and recovery

Still staged: actual queue/lock integration, fixed live Messages path and database continuity, delayed-receipt polling versus deadlines, consumer receipt migration and coherent queue/journal backups. A transient unavailable result does not authorize resend. Do not deploy this wrapper alone or count these synthetic receipts as natural pilot delivery. The runtime's complete deadline must include sender and all chunks, not merely each observer invocation.

Files are HAL workspace/SALtmp artifacts; no production installation or rollback required. Reproduce test_receipt_outbox_composition.py with matching modules/fixture JSON and exact wheel/source, then test_bounded_message_observer.py on SAL. No real Messages send, SAM/Odoo/SyncThing/Level8/Warden/phone/model-route change, schedule/dispatch, model call or paid commitment. Codex cost unknown. Phase1 remains open; Node-RED restriction not bypassed.
