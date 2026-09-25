$ErrorActionPreference = 'Continue'
$recovery = 'C:\Users\wasch\Documents\WindanceMaintenanceRecovery\20260925-HAL'
Write-Host 'Finishing PuTTY, UltraVNC, WSL and the existing Microsoft Edge updater.'
foreach ($app in @('PuTTY.PuTTY','uvncbvba.UltraVNC','Microsoft.WSL')) {
    Write-Host "Updating $app"
    & winget upgrade --id $app --exact --silent --accept-source-agreements --accept-package-agreements --disable-interactivity *> (Join-Path $recovery ($app+'-elevated.log'))
    "${app}: exit=$LASTEXITCODE" | Tee-Object -FilePath (Join-Path $recovery 'elevated-results.txt') -Append
}
Start-Service edgeupdate -ErrorAction Continue
& 'C:\Program Files (x86)\Microsoft\EdgeUpdate\MicrosoftEdgeUpdate.exe' /ua /installsource scheduler
Write-Host 'Installer commands finished. Vega will verify versions. No Windows restart was requested.'
