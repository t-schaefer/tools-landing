@echo off
rem Stops the Tools landing page service (ToolsLandingPage). It starts again at the next boot,
rem with Update-Landing.bat, or: schtasks /run /tn ToolsLandingPage
rem Self-elevates via UAC, pauses so the result stays visible.
setlocal
set "HERE=%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator rights...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%stop-windows.ps1"
echo.
pause
