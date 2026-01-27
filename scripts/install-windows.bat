@echo off
REM DeepWork Windows Installer (Batch wrapper)
REM This script calls the PowerShell installer with appropriate execution policy

echo.
echo DeepWork Windows Installer
echo ==========================
echo.

REM Check if PowerShell is available
where powershell >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: PowerShell is required but not found.
    echo Please install PowerShell or use an alternative installation method.
    exit /b 1
)

REM Get the directory of this script
set SCRIPT_DIR=%~dp0

REM Run the PowerShell installer
powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install-windows.ps1" %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo Installation failed with error code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)

exit /b 0
