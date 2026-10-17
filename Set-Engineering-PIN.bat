@echo off
rem Sets the engineering PIN of the Tools landing page (needed for Start / Stop / Update
rem and for saving the tool list). Only a salted hash is stored, in engineering.json.
rem Setting a new PIN logs out everybody who is logged in. Takes effect immediately.
setlocal
cd /d "%~dp0"
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python was not found on PATH.
    pause
    exit /b 1
)
python server.py --set-pin
echo.
pause
