param(
    [string]$Reason = "scheduled-managed-software-upgrade",
    [switch]$ValidateOnly
)

$ErrorActionPreference = "Stop"
$repo = "C:\Users\wasch\Documents\Codex\2026-06-19\i-need-you-to-go-through\windance_ai_backup_repo"
$context = Join-Path $repo "WindanceAIContext"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$snapshot = Join-Path $repo "current-control-plane\$stamp-pre-managed-upgrade"

git -C $repo pull --ff-only
if ($LASTEXITCODE -ne 0) { throw "Backup repository could not be fast-forwarded." }
if ($ValidateOnly) {
    $head = (git -C $repo rev-parse HEAD).Trim()
    $remote = (git -C $repo ls-remote origin refs/heads/main).Split("`t")[0]
    $subject = (git -C $repo log -1 --format=%s).Trim()
    $ageSeconds = [int](git -C $repo log -1 --format=%ct)
    $nowSeconds = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    if ($head -ne $remote) { throw "Latest local backup commit is not confirmed on GitHub." }
    if ($subject -notlike "backup: pre-upgrade restore point*") { throw "Latest GitHub commit is not a restore point." }
    if (($nowSeconds - $ageSeconds) -gt 7200) { throw "Latest GitHub restore point is older than two hours." }
    Write-Output $head
    exit 0
}
if (git -C $repo status --porcelain) { throw "Backup repository is not clean before snapshot." }

New-Item -ItemType Directory -Force -Path (Join-Path $snapshot "hermes") | Out-Null
Copy-Item (Join-Path $context "inventory\infrastructure-inventory.yaml") $snapshot
Copy-Item (Join-Path $context "runbooks\WINDANCE_NETWORK_RUNBOOK.md") $snapshot

$hermesState = & ssh HERALD "/Users/herald/.local/bin/hermes --version; cd ~/.hermes/hermes-agent && git status --short --branch && git rev-parse HEAD && git rev-parse origin/main"
$hermesState | Set-Content -Encoding utf8 (Join-Path $snapshot "hermes\pre-upgrade-state.txt")
& ssh HERALD "cd ~/.hermes/hermes-agent && git diff --binary HEAD" | Set-Content -Encoding utf8 (Join-Path $snapshot "hermes\windance-customizations.patch")

$inventory = @(
    "Created: $((Get-Date).ToString('o'))",
    "Reason: $Reason",
    "",
    "HAL winget upgrades:",
    (& winget list --upgrade-available --accept-source-agreements --disable-interactivity 2>&1),
    "",
    "HAL Ollama:",
    (& ollama --version 2>&1),
    (& ollama list 2>&1),
    "",
    "HERALD:",
    (& ssh HERALD "/Users/herald/.local/bin/hermes --version; sw_vers" 2>&1),
    "",
    "SAL:",
    (& ssh SAL "/opt/homebrew/bin/brew outdated; /opt/homebrew/bin/node /Users/zuzu/node-red-runtime/node_modules/node-red/red.js --version; /opt/homebrew/bin/cloudflared --version" 2>&1),
    "",
    "AL:",
    (& ssh AL "apt list --upgradable 2>/dev/null; docker ps --format '{{.Names}} {{.Image}} {{.Status}}'" 2>&1),
    "",
    "SAM:",
    (& ssh SAM-WIFI "apt list --upgradable 2>/dev/null; systemctl is-active sam-schedule.service" 2>&1)
)
$inventory | Set-Content -Encoding utf8 (Join-Path $snapshot "managed-software-inventory.txt")

@"
# Pre-managed-upgrade restore point

Created: $((Get-Date).ToString('o'))
Reason: $Reason

This sanitized restore point was created before unattended Windance software maintenance. It contains the current runbook, infrastructure inventory, exact managed-software state, and the tracked Hermes customization patch. Credentials, tokens, keys, `.env` files, credential stores, Syncthing configuration/data, user data, and NAS data are excluded.
"@ | Set-Content -Encoding utf8 (Join-Path $snapshot "BACKUP_MANIFEST.md")

$sensitive = Get-ChildItem -Recurse -File $snapshot | Where-Object {
    $_.Name -match '(?i)(\.env|id_rsa|id_ed25519|credentials|token|secret|oauth|authorization)'
}
if ($sensitive) { throw "Sensitive-looking filename detected; refusing backup push." }

git -C $repo add -- $snapshot
git -C $repo commit -m "backup: pre-upgrade restore point $stamp"
if ($LASTEXITCODE -ne 0) { throw "Backup commit failed." }
git -C $repo push origin HEAD:main
if ($LASTEXITCODE -ne 0) { throw "Backup push failed." }
$localHead = (git -C $repo rev-parse HEAD).Trim()
$remoteHead = (git -C $repo ls-remote origin refs/heads/main).Split("`t")[0]
if ($localHead -ne $remoteHead) { throw "GitHub did not confirm the restore point." }

Write-Output $localHead
