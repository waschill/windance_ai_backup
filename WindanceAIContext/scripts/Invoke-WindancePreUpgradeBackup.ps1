param(
    [string]$Reason = "scheduled-managed-software-upgrade",
    [switch]$ValidateOnly
)

$ErrorActionPreference = "Stop"
$repo = "C:\Users\wasch\Documents\Codex\2026-06-19\i-need-you-to-go-through\windance_ai_backup_repo"
$context = Join-Path $repo "WindanceAIContext"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$snapshot = Join-Path $env:USERPROFILE "Documents\WindanceMaintenanceRecovery\pending\$stamp-pre-managed-upgrade"
$publishedSnapshot = Join-Path $repo "current-control-plane\$stamp-pre-managed-upgrade"

function Invoke-InventoryCommand {
    param([string]$Program, [string[]]$Arguments)
    # Windows PowerShell maps native stderr to ErrorRecord, including harmless
    # progress messages. Judge native commands by their exit status instead.
    $savedPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = & $Program @Arguments 2>&1
        $nativeExit = $LASTEXITCODE
    } finally { $ErrorActionPreference = $savedPreference }
    if ($nativeExit -ne 0) { throw "Inventory command $Program failed (exit $nativeExit); partial snapshot retained outside Git." }
    $output | ForEach-Object { "$_" }
}

git -C $repo pull --ff-only
if ($LASTEXITCODE -ne 0) { throw "Backup repository could not be fast-forwarded." }
if ($ValidateOnly) {
    $head = (git -C $repo rev-parse HEAD).Trim()
    $remote = (git -C $repo ls-remote origin refs/heads/main).Split("`t")[0]
    $backupRecord = (git -C $repo log -1 --format="%H|%ct" --grep="^backup: pre-upgrade restore point").Trim().Split("|")
    if ($backupRecord.Count -ne 2) { throw "No GitHub restore-point commit was found." }
    $backupHash = $backupRecord[0]
    $ageSeconds = [int64]$backupRecord[1]
    $nowSeconds = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    if ($head -ne $remote) { throw "Latest local backup commit is not confirmed on GitHub." }
    git -C $repo merge-base --is-ancestor $backupHash $remote
    if ($LASTEXITCODE -ne 0) { throw "Restore-point commit is not present in GitHub main history." }
    if (($nowSeconds - $ageSeconds) -gt 7200) { throw "Latest GitHub restore point is older than two hours." }
    Write-Output $backupHash
    exit 0
}
if (git -C $repo status --porcelain) { throw "Backup repository is not clean before snapshot." }

New-Item -ItemType Directory -Force -Path (Join-Path $snapshot "hermes") | Out-Null
Copy-Item (Join-Path $context "inventory\infrastructure-inventory.yaml") $snapshot
Copy-Item (Join-Path $context "runbooks\WINDANCE_NETWORK_RUNBOOK.md") $snapshot

$hermesState = Invoke-InventoryCommand ssh @('HERALD', 'set -e; /Users/herald/.local/bin/hermes --version; cd ~/.hermes/hermes-agent; git status --short --branch; git rev-parse HEAD; git rev-parse origin/main')
$hermesState | Set-Content -Encoding utf8 (Join-Path $snapshot "hermes\pre-upgrade-state.txt")
Invoke-InventoryCommand ssh @('HERALD', 'cd ~/.hermes/hermes-agent && git diff --binary HEAD') | Set-Content -Encoding utf8 (Join-Path $snapshot "hermes\windance-customizations.patch")

$inventory = @(
    "Created: $((Get-Date).ToString('o'))",
    "Reason: $Reason",
    "",
    "HAL winget upgrades:",
    (Invoke-InventoryCommand winget @('list','--upgrade-available','--accept-source-agreements','--disable-interactivity')),
    "",
    "HAL Ollama:",
    (Invoke-InventoryCommand ollama @('--version')),
    (Invoke-InventoryCommand ollama @('list')),
    "",
    "HERALD:",
    (Invoke-InventoryCommand ssh @('HERALD', 'set -e; /Users/herald/.local/bin/hermes --version; sw_vers')),
    "",
    "SAL:",
    (Invoke-InventoryCommand ssh @('SAL', 'set -e; HOMEBREW_NO_AUTO_UPDATE=1 /opt/homebrew/bin/brew outdated; /opt/homebrew/bin/node /Users/zuzu/node-red-runtime/node_modules/node-red/red.js --version; /opt/homebrew/bin/cloudflared --version')),
    "",
    "AL:",
    (Invoke-InventoryCommand ssh @('AL', "set -e; apt list --upgradable 2>/dev/null; docker ps --format '{{.Names}} {{.Image}} {{.Status}}'")),
    "",
    "SAM:",
    (Invoke-InventoryCommand ssh @('SAM-WIFI', 'set -e; apt list --upgradable 2>/dev/null; systemctl is-active sam-schedule.service'))
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

Move-Item -LiteralPath $snapshot -Destination $publishedSnapshot
git -C $repo add -- $publishedSnapshot
git -C $repo commit -m "backup: pre-upgrade restore point $stamp"
if ($LASTEXITCODE -ne 0) { throw "Backup commit failed." }
git -C $repo push origin HEAD:main
if ($LASTEXITCODE -ne 0) { throw "Backup push failed." }
$localHead = (git -C $repo rev-parse HEAD).Trim()
$remoteHead = (git -C $repo ls-remote origin refs/heads/main).Split("`t")[0]
if ($localHead -ne $remoteHead) { throw "GitHub did not confirm the restore point." }

Write-Output $localHead
