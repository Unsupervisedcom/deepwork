<#
.SYNOPSIS
    Build DeepWork Windows executable

.DESCRIPTION
    This script builds a standalone Windows executable for DeepWork using PyInstaller.
    The resulting executable can be distributed and run without Python installed.

.PARAMETER OutputDir
    Directory for the output executable (default: dist/)

.EXAMPLE
    .\build-windows.ps1
    Builds the DeepWork executable in the dist/ directory.

.NOTES
    Requires Python 3.11+ and PyInstaller to be installed.
#>

param(
    [string]$OutputDir = "dist"
)

$ErrorActionPreference = "Stop"

function Write-Status {
    param([string]$Message)
    Write-Host "[*] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[+] $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "[-] $Message" -ForegroundColor Red
}

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host ""
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "      DeepWork Windows Build Script     " -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

# Check Python version
Write-Status "Checking Python version..."
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   Found: $pythonVersion" -ForegroundColor Gray

    # Extract version number
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
            Write-Error "Python 3.11 or higher is required (found $major.$minor)"
            exit 1
        }
    }
}
catch {
    Write-Error "Python not found. Please install Python 3.11 or higher."
    exit 1
}

# Check/install PyInstaller
Write-Status "Checking PyInstaller..."
$pyinstallerInstalled = python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Status "Installing PyInstaller..."
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install PyInstaller"
        exit 1
    }
}

# Install DeepWork dependencies
Write-Status "Installing DeepWork dependencies..."
Push-Location $ProjectRoot
try {
    pip install -e .
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install DeepWork dependencies"
        exit 1
    }
}
finally {
    Pop-Location
}

# Build executable
Write-Status "Building Windows executable..."
$specFile = Join-Path $ScriptDir "deepwork.spec"
Push-Location $ProjectRoot
try {
    pyinstaller $specFile --distpath $OutputDir --clean -y
    if ($LASTEXITCODE -ne 0) {
        Write-Error "PyInstaller build failed"
        exit 1
    }
}
finally {
    Pop-Location
}

# Verify output
$exePath = Join-Path $ProjectRoot "$OutputDir\deepwork.exe"
if (-not (Test-Path $exePath)) {
    Write-Error "Build completed but executable not found at: $exePath"
    exit 1
}

# Test the executable
Write-Status "Verifying build..."
try {
    $version = & $exePath --version 2>&1
    Write-Success "Build successful!"
    Write-Host "   Executable: $exePath" -ForegroundColor Gray
    Write-Host "   Version: $version" -ForegroundColor Gray
}
catch {
    Write-Error "Build verification failed: $_"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "           Build Complete!              " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Test: .\$OutputDir\deepwork.exe --help" -ForegroundColor Gray
Write-Host "  2. Install: .\scripts\install-windows.ps1 -ExePath .\$OutputDir\deepwork.exe" -ForegroundColor Gray
Write-Host ""
