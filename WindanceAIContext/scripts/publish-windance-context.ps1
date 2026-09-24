param(
    [switch]$PushGit
)

$ErrorActionPreference = 'Stop'
$source = Split-Path -Parent $PSScriptRoot
$production = 'P:\Business\Networksetup\WindanceAIContext'
$localMirror = Join-Path $env:USERPROFILE 'Documents\WindanceAIContext'

$blockedNames = @('*.pem','*.key','id_*','*.env','*token*','*secret*','*credential*')
foreach ($pattern in $blockedNames) {
    $found = Get-ChildItem $source -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue
    if ($found) { throw "Refusing to publish sensitive-looking file(s) matching $pattern" }
}

foreach ($destination in @($production, $localMirror)) {
    New-Item -ItemType Directory -Force -Path $destination | Out-Null
    robocopy $source $destination /MIR /XD .git /XF '*.pem' '*.key' 'id_*' '*.env' '*token*' '*secret*' '*credential*' /R:2 /W:2 | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "Publishing to $destination failed with robocopy code $LASTEXITCODE" }
}

$remote = '/Users/herald/knowledge/WindanceAIContext'
ssh -o BatchMode=yes HERALD "mkdir -p '$remote'"
if ($LASTEXITCODE -ne 0) { throw 'Herald context directory could not be reached.' }
scp -q -r "$source\*" "HERALD:$remote/"
if ($LASTEXITCODE -ne 0) { throw 'Herald mirror publication failed.' }

$salMirror = '/Users/zuzu/knowledge/WindanceAIContext'
ssh -o BatchMode=yes SAL "mkdir -p '$salMirror'"
if ($LASTEXITCODE -ne 0) { throw 'SAL context directory could not be reached.' }
scp -q -r "$source\*" "SAL:$salMirror/"
if ($LASTEXITCODE -ne 0) { throw 'SAL mirror publication failed.' }

if ($PushGit) {
    $repo = Split-Path -Parent $source
    git -C $repo add WindanceAIContext
    git -C $repo diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host 'No Git changes to push.'
    } else {
        git -C $repo commit -m "Update centralized Windance operating context"
        if ($LASTEXITCODE -ne 0) { throw 'Git commit failed.' }
        git -C $repo pull --rebase origin main
        if ($LASTEXITCODE -ne 0) { throw 'Git pull/rebase failed; mirrors were updated but GitHub was not.' }
        git -C $repo push origin HEAD
        if ($LASTEXITCODE -ne 0) { throw 'Git push failed; do not treat the GitHub backup as current.' }
    }
}

$indexPython = 'C:\Users\wasch\services\second-brain\venv\Scripts\python.exe'
& $indexPython (Join-Path $PSScriptRoot 'refresh-windance-context-index.py')
if ($LASTEXITCODE -ne 0) { throw 'Context files were published, but Second Brain indexing/retrieval verification failed.' }
Write-Host "Published Windance context to Production, HAL, Herald, SAL and verified the Second Brain index."
