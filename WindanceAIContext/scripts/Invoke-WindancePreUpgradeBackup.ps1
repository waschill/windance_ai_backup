param(
    [string]$Reason = "scheduled-managed-software-upgrade",
    [switch]$ValidateOnly,
    [switch]$PrepareOnly
)

$ErrorActionPreference = "Stop"
$repo = "C:\Users\wasch\Documents\Codex\2026-06-19\i-need-you-to-go-through\windance_ai_backup_repo"
$context = Join-Path $repo "WindanceAIContext"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$snapshot = Join-Path $env:USERPROFILE "Documents\WindanceMaintenanceRecovery\pending\$stamp-pre-managed-upgrade"
$publishedSnapshot = Join-Path $repo "current-control-plane\$stamp-pre-managed-upgrade"

function ConvertTo-NativeArgument {
    param([string]$Value)
    if ($Value -notmatch '[\s"]' -and $Value.Length) { return $Value }
    $escaped = [regex]::Replace($Value, '(\\*)"', '$1$1\"')
    $escaped = [regex]::Replace($escaped, '(\\+)$', '$1$1')
    return '"' + $escaped + '"'
}

function Invoke-InventoryCommand {
    param([string]$Program, [string[]]$Arguments, [int]$TimeoutSeconds = 120)
    if ($Program -eq 'ssh') {
        $Arguments = @('-o','BatchMode=yes','-o','ConnectTimeout=10','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2') + $Arguments
    }
    $resolved = (Get-Command $Program -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
    $start = New-Object System.Diagnostics.ProcessStartInfo
    $start.FileName = $resolved
    $start.Arguments = (($Arguments | ForEach-Object { ConvertTo-NativeArgument $_ }) -join ' ')
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $start.EnvironmentVariables['GIT_TERMINAL_PROMPT'] = '0'
    $start.EnvironmentVariables['GIT_SSH_COMMAND'] = 'ssh -o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=15 -o ServerAliveCountMax=2'
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $start
    try {
        if (-not $process.Start()) { throw "Inventory command $Program could not start." }
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            # Stop this invocation and its children; never leave a timed-out SSH/installer running.
            & "$env:SystemRoot\System32\taskkill.exe" /PID $process.Id /T /F 2>&1 | Out-Null
            throw "Inventory command $Program timed out after $TimeoutSeconds seconds; partial snapshot retained outside Git."
        }
        if (-not [System.Threading.Tasks.Task]::WaitAll([System.Threading.Tasks.Task[]]@($stdout,$stderr), 5000)) {
            & "$env:SystemRoot\System32\taskkill.exe" /PID $process.Id /T /F 2>&1 | Out-Null
            throw "Inventory command $Program output drain timed out; partial snapshot retained outside Git."
        }
        $output = $stdout.GetAwaiter().GetResult()
        $diagnostic = $stderr.GetAwaiter().GetResult()
        $global:LASTEXITCODE = $process.ExitCode
        if ($process.ExitCode -ne 0) { throw "Inventory command $Program failed (exit $($process.ExitCode)); partial snapshot retained outside Git." }
        # Success stdout is the machine contract; harmless stderr never contaminates the commit SHA.
        $output.TrimEnd() -split "`r?`n"
    } finally { $process.Dispose() }
}

$null = Invoke-InventoryCommand git @('-C',$repo,'pull','--ff-only')
if ($LASTEXITCODE -ne 0) { throw "Backup repository could not be fast-forwarded." }
if ($ValidateOnly) {
    $head = (Invoke-InventoryCommand git @('-C',$repo,'rev-parse','HEAD')).Trim()
    $remote = (Invoke-InventoryCommand git @('-C',$repo,'ls-remote','origin','refs/heads/main')).Split("`t")[0]
    $backupRecord = (Invoke-InventoryCommand git @('-C',$repo,'log','-1','--format=%H|%ct','--grep=^backup: pre-upgrade restore point')).Trim().Split("|")
    if ($backupRecord.Count -ne 2) { throw "No GitHub restore-point commit was found." }
    $backupHash = $backupRecord[0]
    $ageSeconds = [int64]$backupRecord[1]
    $nowSeconds = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    if ($head -ne $remote) { throw "Latest local backup commit is not confirmed on GitHub." }
    $null = Invoke-InventoryCommand git @('-C',$repo,'merge-base','--is-ancestor',$backupHash,$remote)
    if ($LASTEXITCODE -ne 0) { throw "Restore-point commit is not present in GitHub main history." }
    if (($nowSeconds - $ageSeconds) -gt 7200) { throw "Latest GitHub restore point is older than two hours." }
    Write-Output $backupHash
    exit 0
}
if (Invoke-InventoryCommand git @('-C',$repo,'status','--porcelain')) { throw "Backup repository is not clean before snapshot." }

New-Item -ItemType Directory -Force -Path (Join-Path $snapshot "hermes") | Out-Null
# Reference already-confirmed canonical artifacts without republishing contact data.
$canonicalCommit = (Invoke-InventoryCommand git @('-C',$repo,'rev-parse','HEAD')).Trim()
$canonicalRemote = (Invoke-InventoryCommand git @('-C',$repo,'ls-remote','origin','refs/heads/main')).Split("`t")[0]
if ($canonicalCommit -ne $canonicalRemote) { throw 'Canonical reference is not GitHub-confirmed.' }
$canonicalReferences = @('WindanceAIContext/inventory/infrastructure-inventory.yaml','WindanceAIContext/runbooks/WINDANCE_NETWORK_RUNBOOK.md') | ForEach-Object {
    $blob = (Invoke-InventoryCommand git @('-C',$repo,'rev-parse',"${canonicalCommit}:$_")).Trim()
    [pscustomobject]@{commit=$canonicalCommit;path=$_;git_blob=$blob;local_worktree_sha256=(Get-FileHash -LiteralPath (Join-Path $repo $_) -Algorithm SHA256).Hash.ToLowerInvariant()}
}

$hermesState = Invoke-InventoryCommand ssh @('HERALD', 'set -e; /Users/herald/.local/bin/hermes --version; cd ~/.hermes/hermes-agent; git status --short --branch; git rev-parse HEAD; git rev-parse origin/main')
$hermesState | Set-Content -Encoding utf8 (Join-Path $snapshot "hermes\pre-upgrade-state.txt")
$patchEncoded = Invoke-InventoryCommand ssh @('HERALD', '/bin/bash -o pipefail -c ''cd /Users/herald/.hermes/hermes-agent && git diff --binary HEAD | /usr/bin/base64''')
[IO.File]::WriteAllBytes((Join-Path $snapshot 'hermes\windance-customizations.patch'), [Convert]::FromBase64String(($patchEncoded -join '')))
# Explicit reviewed untracked dependency; never copy arbitrary untracked files.
$ownerGuardEncoded = Invoke-InventoryCommand ssh @('HERALD', '/usr/bin/base64 -i /Users/herald/.hermes/hermes-agent/gateway/windance_owner_guard.py')
[IO.File]::WriteAllBytes((Join-Path $snapshot 'hermes\windance_owner_guard.py'), [Convert]::FromBase64String(($ownerGuardEncoded -join '')))


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

This sanitized restore point was created before unattended Windance software maintenance. It references the confirmed canonical commit for the runbook and infrastructure inventory, and contains exact managed-software state, tracked Hermes customization patch, and its explicit owner-guard dependency. Credentials, tokens, keys, `.env` files, credential stores, Syncthing configuration/data, user data, and NAS data are excluded.
"@ | Set-Content -Encoding utf8 (Join-Path $snapshot "BACKUP_MANIFEST.md")

[IO.File]::WriteAllText((Join-Path $snapshot '.gitattributes'), "* -text`n", (New-Object Text.UTF8Encoding($false)))
$restoreFiles = @(Get-ChildItem -LiteralPath $snapshot -Recurse -File | ForEach-Object {
    [pscustomobject]@{path=$_.FullName.Substring($snapshot.Length + 1); sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
})
[pscustomobject]@{schema=1; canonical_references=$canonicalReferences; files=$restoreFiles; restore='Apply tracked Hermes patch to recorded HEAD and restore hermes/windance_owner_guard.py at gateway/windance_owner_guard.py. Preserve existing private runtime/config backups.'} | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 (Join-Path $snapshot 'RECONSTRUCTION_MANIFEST.json')

$sensitive = Get-ChildItem -Recurse -File $snapshot | Where-Object {
    $_.Name -match '(?i)(\.env|id_rsa|id_ed25519|credentials|token|secret|oauth|authorization)'
}
if ($sensitive) { throw "Sensitive-looking filename detected; refusing backup push." }

# Fail closed on private content, not only suspicious filenames.
$contentPattern = '(?im)(\bsk-[A-Za-z0-9_-]{20,}|\b[0-9]{7,}:[A-Za-z0-9_-]{30,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|\+1[0-9]{10}\b|\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b|(?:api[_-]?key|password|access[_-]?token|refresh[_-]?token)["'']?\s*[:=]\s*["'']?[A-Za-z0-9_+/=-]{1,})'
foreach ($artifact in Get-ChildItem -LiteralPath $snapshot -Recurse -File) {
    $artifactText = [IO.File]::ReadAllText($artifact.FullName)
    if ($artifactText -match $contentPattern -or $artifactText -match '(?m)^GIT binary patch\r?$|^diff --git .*?(?:\.env|credentials|id_rsa|id_ed25519|secrets|oauth|authorization)') {
        throw "Private-content guard rejected backup artifact $($artifact.Name); exact snapshot retained outside Git."
    }
}
$privateRoot = [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE 'Documents\WindanceMaintenanceRecovery\pending')) + [IO.Path]::DirectorySeparatorChar
$publicRoot = [IO.Path]::GetFullPath((Join-Path $repo 'current-control-plane')) + [IO.Path]::DirectorySeparatorChar
$resolvedSnapshot = (Resolve-Path -LiteralPath $snapshot).Path
$resolvedPublished = [IO.Path]::GetFullPath($publishedSnapshot)
if (-not $resolvedSnapshot.StartsWith($privateRoot, [StringComparison]::OrdinalIgnoreCase) -or
    -not $resolvedPublished.StartsWith($publicRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Backup move target escaped the intended private/public directories.'
}
if ($PrepareOnly) { Write-Output $resolvedSnapshot; exit 0 }
Move-Item -LiteralPath $resolvedSnapshot -Destination $resolvedPublished
$null = Invoke-InventoryCommand git @('-C',$repo,'add','--',$publishedSnapshot)
$null = Invoke-InventoryCommand git @('-C',$repo,'commit','-m',"backup: pre-upgrade restore point $stamp")
if ($LASTEXITCODE -ne 0) { throw "Backup commit failed." }
$null = Invoke-InventoryCommand git @('-C',$repo,'push','origin','HEAD:main')
if ($LASTEXITCODE -ne 0) { throw "Backup push failed." }
$localHead = (Invoke-InventoryCommand git @('-C',$repo,'rev-parse','HEAD')).Trim()
$remoteHead = (Invoke-InventoryCommand git @('-C',$repo,'ls-remote','origin','refs/heads/main')).Split("`t")[0]
if ($localHead -ne $remoteHead) { throw "GitHub did not confirm the restore point." }

Write-Output $localHead
