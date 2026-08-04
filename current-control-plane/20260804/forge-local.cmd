@echo off
setlocal
set "PATH=C:\Users\wasch\AppData\Local\hermes\bin;C:\Users\wasch\AppData\Local\hermes\node;%PATH%"
"C:\Users\wasch\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" "C:\Users\wasch\services\forge-local\forge_local_worker.py" run-once
