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
scp -q -r "$source\*" "HERALD:$remote/"

if ($PushGit) {
    $repo = Split-Path -Parent $source
    git -C $repo add WindanceAIContext
    if (git -C $repo diff --cached --quiet) {
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

Write-Host "Published Windance context to Production, HAL, and Herald."
