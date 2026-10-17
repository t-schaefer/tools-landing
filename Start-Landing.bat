@echo off
rem Runs the Tools landing page in this window (no service) - for a quick test.
rem Port 8099 by default here so it does not clash with the installed service on 80:
rem     Start-Landing.bat        -> http://localhost:8099/
rem     Start-Landing.bat 8100   -> http://localhost:8100/
setlocal
set "HERE=%~dp0"
set "PORT=%~1"
if "%PORT%"=="" set "PORT=8099"
cd /d "%HERE%"
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python was not found on PATH - install Python 3.8+ and tick "Add python.exe to PATH".
    pause
    exit /b 1
)
echo Tools landing page - http://localhost:%PORT%/   Ctrl+C stops it.
python server.py --port %PORT%
echo.
pause
