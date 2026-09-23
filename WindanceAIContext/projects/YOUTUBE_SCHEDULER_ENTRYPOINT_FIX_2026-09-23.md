# YouTube scheduler entry-point repair — 2026-09-23

## Cause and correction

William reported no YouTube list today. Live SAL inspection found the loaded
YouTube LaunchAgent had three runs and last exit code 127. Its stderr contained
three `env: python3\r: No such file or directory` errors. The Sept22 Vega deployment
introduced CRLF line endings into the directly executed Python script. Prior
manual tests invoked Python explicitly and therefore missed its broken shebang.
The exact timestamps of those three failures were not established.

Normalized the production producer to LF, retaining executable mode 0700. The
loaded Mon–Thu 08:00, 12:00 and 16:00 Mountain schedule remains intact. Shared
preferences and Julian Goldie's exclusion are unchanged. Local patch generation
now writes LF explicitly; both deployment helpers reject CRLF shebangs before
mutation. Corrected helpers are staged on SAL and HERALD. No other directly
launched changed HERALD script was identified by the manifest/LaunchAgent audit.

## Verification and limits

The actual executable ran successfully with a minimal launchd-like environment
and `--print-only`, exit 0, generating a 29-line preview with zero Goldie matches.
Both deployment guards were checked to accept LF and reject CRLF shebangs; all
four modified Python files parsed successfully. This verifies startup and report
generation, not a subsequent scheduled delivery. At 15:31 MDT the next scheduled
run was 16:00 today; launchd still displayed its historical exit 127 until the
next run. No manual report was sent and the production job was not kicked.

## Recovery and evidence

Private SAL backup: `/Users/zuzu/services/youtube-launch-fix-20260923/windance_youtube_briefing.before.py`.
Private preview: same directory, `preview.txt`. The backup retains the broken
line endings and must not be restored without LF normalization.
Live source: `/Users/zuzu/bin/windance_youtube_briefing.py`.
Verified SHA256: `95f4dd690e171c7a0b268c0bac6a311351de546bf000fa134f6fd175e6d17ffd`.
The corresponding SAL reliability stage and applied hash receipt were updated;
the original deployment manifest remains historical. Do not replay initial deploy.
Future validation must execute the actual scheduler entry point, in addition to
module tests, and separately confirm a normal scheduled delivery.
