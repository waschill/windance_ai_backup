param(
    [switch]$Execute,
    [string]$Reason = "unspecified"
)

$ErrorActionPreference = "Continue"

$LogDir = Join-Path $env:USERPROFILE "logs\level8-shutdown"
$LogFile = Join-Path $LogDir "vega-level8-shutdown.log"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Level8Log {
    param([string]$Message)
    $line = "$(Get-Date -Format o) $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

function Test-Level8ExecuteArm {
    $ArmFile = Join-Path $env:USERPROFILE ".config\windance\level8\level8-execute-armed.json"
    if (-not (Test-Path -LiteralPath $ArmFile)) {
        Write-Level8Log "SAFETY_BLOCK: -Execute requested but one-time arm file is missing: $ArmFile"
        return $false
    }

    try {
        $arm = Get-Content -LiteralPath $ArmFile -Raw | ConvertFrom-Json
    } catch {
        Write-Level8Log "SAFETY_BLOCK: -Execute requested but arm file is unreadable or invalid JSON"
        return $false
    }

    try {
        $created = [datetimeoffset]::Parse([string]$arm.created_at)
    } catch {
        Write-Level8Log "SAFETY_BLOCK: -Execute requested but arm file has no valid created_at"
        return $false
    }

    $age = [datetimeoffset]::Now - $created
    if ($arm.enabled -ne $true) {
        Write-Level8Log "SAFETY_BLOCK: -Execute requested but arm file is not enabled"
        return $false
    }
    if ([string]$arm.phrase -ne "LEVEL8_MANUAL_AUTHORIZED") {
        Write-Level8Log "SAFETY_BLOCK: -Execute requested but arm phrase is not valid"
        return $false
    }
    if ($age.TotalMinutes -gt 10 -or $age.TotalMinutes -lt -1) {
        Write-Level8Log "SAFETY_BLOCK: -Execute requested but arm file is stale or from the future; age_minutes=$([math]::Round($age.TotalMinutes, 2))"
        return $false
    }

    Remove-Item -LiteralPath $ArmFile -Force -ErrorAction SilentlyContinue
    Write-Level8Log "SAFETY_OK: one-time Level 8 execute arm accepted and consumed"
    return $true
}

function Invoke-Checked {
    param(
        [string]$Name,
        [string]$CheckCommand,
        [string]$ShutdownCommand
    )

    Write-Level8Log "CHECK ${Name}: $CheckCommand"
    $checkOutput = & powershell.exe -NoProfile -ExecutionPolicy Bypass -Command $CheckCommand 2>&1
    $checkRc = $LASTEXITCODE
    $checkText = (($checkOutput | Out-String).Trim() -replace "`r?`n", " | ")
    if ($checkText.Length -gt 300) { $checkText = $checkText.Substring(0, 300) }
    Write-Level8Log "CHECK_RESULT ${Name}: rc=$checkRc output='$checkText'"
    if ($checkRc -ne 0) {
        Write-Level8Log "BLOCK ${Name}: preflight failed"
        return $false
    }

    if ($Execute) {
        Write-Level8Log "EXEC ${Name}: $ShutdownCommand"
        Start-Process -WindowStyle Hidden -FilePath "powershell.exe" -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-Command", $ShutdownCommand
        )
    } else {
        Write-Level8Log "DRY_RUN ${Name}: would run $ShutdownCommand"
    }
    return $true
}

Write-Level8Log "Windance Level 8 Vega executor started. execute=$($Execute.IsPresent) reason='$Reason'"
Write-Level8Log "Planned order: AL -> REFWeb -> TMA-2 -> TMA-1 -> Odyssey -> SAL -> HERALD -> HAL"

if ($Execute) {
    $DisabledFlag = Join-Path $env:USERPROFILE ".config\windance\level8\LEVEL8_EXECUTE_DISABLED.flag"
    if (Test-Path -LiteralPath $DisabledFlag) {
        Write-Level8Log "SAFETY_BLOCK: -Execute requested but Level 8 real execution is globally disabled by $DisabledFlag"
        Write-Level8Log "Level 8 Vega executor refused real shutdown before any host checks or shutdown commands."
        exit 3
    }

    $executeArmOk = Test-Level8ExecuteArm
    if ($executeArmOk -ne $true) {
        Write-Level8Log "Level 8 Vega executor refused real shutdown before any host checks or shutdown commands."
        exit 2
    }
}

$SshKey = "C:/Users/wasch/.ssh/id_ed25519_homelab"
$SshOptions = "-i `"$SshKey`" -o IdentitiesOnly=yes -o BatchMode=yes -o NumberOfPasswordPrompts=0 -o KbdInteractiveAuthentication=no -o PreferredAuthentications=publickey -o StrictHostKeyChecking=accept-new -o ConnectionAttempts=1 -o ConnectTimeout=8 -o ServerAliveInterval=3 -o ServerAliveCountMax=2"

$steps = @(
    @{
        Name = "AL"
        Check = "ssh $SshOptions waschilladmin@192.168.36.20 'hostname; sudo -n -l /usr/sbin/shutdown >/dev/null 2>&1'"
        Shutdown = "ssh $SshOptions waschilladmin@192.168.36.20 'sudo /usr/sbin/shutdown -h now'"
    },
    @{
        Name = "REFWeb"
        Check = "ssh $SshOptions waschill@64.251.177.195 'hostname; sudo -n -l /usr/bin/systemctl >/dev/null 2>&1'"
        Shutdown = "ssh $SshOptions waschill@64.251.177.195 'sudo /usr/bin/systemctl poweroff'"
    },
    @{
        Name = "TMA-2"
        Check = "ssh $SshOptions William@192.168.36.133 'hostname; sudo -n -l /sbin/poweroff >/dev/null 2>&1'"
        Shutdown = "ssh $SshOptions William@192.168.36.133 'sudo /sbin/poweroff'"
    },
    @{
        Name = "TMA-1"
        Check = "ssh $SshOptions William@192.168.36.131 'hostname; sudo -n -l /sbin/poweroff >/dev/null 2>&1'"
        Shutdown = "ssh $SshOptions William@192.168.36.131 'sudo /sbin/poweroff'"
    },
    @{
        Name = "Odyssey"
        Check = "ssh $SshOptions William@192.168.36.31 'hostname; sudo -n -l /usr/sbin/shutdown >/dev/null 2>&1'"
        Shutdown = "ssh $SshOptions William@192.168.36.31 'sudo /usr/sbin/shutdown -h now'"
    },
    @{
        Name = "SAL"
        Check = "ssh $SshOptions zuzu@192.168.36.22 'hostname; sudo -n -l /sbin/shutdown >/dev/null 2>&1'"
        Shutdown = "ssh $SshOptions zuzu@192.168.36.22 'sudo /sbin/shutdown -h now'"
    },
    @{
        Name = "HERALD"
        Check = "ssh $SshOptions herald@192.168.36.21 'hostname; sudo -n -l /sbin/shutdown >/dev/null 2>&1'"
        Shutdown = "ssh $SshOptions herald@192.168.36.21 'sudo /sbin/shutdown -h now'"
    }
)

$failures = @()
foreach ($step in $steps) {
    $ok = Invoke-Checked -Name $step.Name -CheckCommand $step.Check -ShutdownCommand $step.Shutdown
    if (-not $ok) { $failures += $step.Name }
}

if ($failures.Count -gt 0) {
    Write-Level8Log "Level 8 Vega executor BLOCKED. Failed preflight: $($failures -join ', ')"
    exit 1
}

if ($Execute) {
    Write-Level8Log "EXEC HAL: shutdown.exe /s /t 60 /c `"Windance Level 8 shutdown initiated by Vega`""
    Start-Process -WindowStyle Hidden -FilePath "shutdown.exe" -ArgumentList @(
        "/s",
        "/t", "60",
        "/c", "Windance Level 8 shutdown initiated by Vega"
    )
    Write-Level8Log "Level 8 shutdown commands issued by Vega. HAL shutdown scheduled last."
} else {
    Write-Level8Log "DRY_RUN HAL: would run shutdown.exe /s /t 60"
    Write-Level8Log "Level 8 Vega executor completed OK in dry-run/preflight mode."
}

exit 0
