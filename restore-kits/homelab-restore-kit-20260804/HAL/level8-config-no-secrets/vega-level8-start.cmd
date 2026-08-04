@echo off
setlocal

set MODE=%~1
if "%MODE%"=="" set MODE=dry-run

set EXEC_ARG=
if /I "%MODE%"=="execute" set EXEC_ARG=-Execute

set SCRIPT=%USERPROFILE%\.config\windance\level8\vega-level8-executor.ps1
set REASON=hal-detached-%MODE%

start "Windance Level 8 Vega" /MIN powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" %EXEC_ARG% -Reason "%REASON%"

echo Vega Level 8 %MODE% launcher accepted.
exit /b 0
