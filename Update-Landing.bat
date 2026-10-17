@echo off
rem One double-click update of the Tools landing page: stops the task, updates the
rem files (git pull, or the GitHub zip when git is not installed), starts it again.
rem Self-elevates via UAC, pauses so errors stay visible.
setlocal
set "HERE=%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator rights...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%update-windows.ps1"
echo.
pause
