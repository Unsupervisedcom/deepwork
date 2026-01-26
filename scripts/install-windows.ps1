<#
.SYNOPSIS
    DeepWork Windows Installer

.DESCRIPTION
    This script installs DeepWork on Windows by:
    1. Downloading or using a local deepwork.exe
    2. Installing it to %LOCALAPPDATA%\DeepWork\bin
    3. Adding the installation directory to the user's PATH

.PARAMETER ExePath
    Optional path to a local deepwork.exe file to install.
    If not provided, the script will try to download from GitHub releases.

.PARAMETER Version
    Version to install (default: latest).
    Only used when downloading from GitHub.

.EXAMPLE
    .\install-windows.ps1
    Installs the latest version of DeepWork.

.EXAMPLE
    .\install-windows.ps1 -ExePath .\deepwork.exe
    Installs DeepWork from a local executable.

.NOTES
    Requires Windows 10 or later.
    Requires PowerShell 5.1 or later.
#>

param(
    [string]$ExePath = "",
    [string]$Version = "latest"
)

$ErrorActionPreference = "Stop"

# Configuration
$AppName = "DeepWork"
$ExeName = "deepwork.exe"
$InstallDir = Join-Path $env:LOCALAPPDATA "DeepWork\bin"
$GithubRepo = "unsupervisedcom/deepwork"

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

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Add-ToUserPath {
    param([string]$Directory)

    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")

    if ($currentPath -split ";" | Where-Object { $_ -eq $Directory }) {
        Write-Status "$Directory is already in PATH"
        return $false
    }

    $newPath = if ($currentPath) { "$currentPath;$Directory" } else { $Directory }
    [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")

    # Also update current session
    $env:PATH = "$env:PATH;$Directory"

    Write-Success "Added $Directory to user PATH"
    return $true
}

function Get-LatestReleaseUrl {
    param([string]$Repo)

    $apiUrl = "https://api.github.com/repos/$Repo/releases/latest"

    try {
        $release = Invoke-RestMethod -Uri $apiUrl -Headers @{ "User-Agent" = "DeepWork-Installer" }
        $asset = $release.assets | Where-Object { $_.name -eq "deepwork-windows-x64.exe" -or $_.name -eq "deepwork.exe" } | Select-Object -First 1

        if ($asset) {
            return @{
                Url = $asset.browser_download_url
                Version = $release.tag_name
            }
        }
    }
    catch {
        Write-Error "Failed to fetch release info: $_"
    }

    return $null
}

function Install-DeepWork {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Magenta
    Write-Host "       DeepWork Windows Installer       " -ForegroundColor Magenta
    Write-Host "========================================" -ForegroundColor Magenta
    Write-Host ""

    # Create installation directory
    if (-not (Test-Path $InstallDir)) {
        Write-Status "Creating installation directory: $InstallDir"
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    }

    $targetPath = Join-Path $InstallDir $ExeName

    if ($ExePath) {
        # Install from local file
        if (-not (Test-Path $ExePath)) {
            Write-Error "Executable not found: $ExePath"
            exit 1
        }

        Write-Status "Installing from local file: $ExePath"
        Copy-Item -Path $ExePath -Destination $targetPath -Force
    }
    else {
        # Download from GitHub
        Write-Status "Fetching latest release information..."
        $releaseInfo = Get-LatestReleaseUrl -Repo $GithubRepo

        if (-not $releaseInfo) {
            Write-Error "Could not find a Windows release. Please build from source or provide -ExePath"
            Write-Host ""
            Write-Host "To build from source:" -ForegroundColor Yellow
            Write-Host "  1. Install Python 3.11+" -ForegroundColor Yellow
            Write-Host "  2. pip install pyinstaller" -ForegroundColor Yellow
            Write-Host "  3. pyinstaller scripts/deepwork.spec" -ForegroundColor Yellow
            Write-Host "  4. Run this script with: .\install-windows.ps1 -ExePath dist\deepwork.exe" -ForegroundColor Yellow
            exit 1
        }

        Write-Status "Downloading DeepWork $($releaseInfo.Version)..."

        try {
            Invoke-WebRequest -Uri $releaseInfo.Url -OutFile $targetPath -UseBasicParsing
        }
        catch {
            Write-Error "Failed to download: $_"
            exit 1
        }
    }

    # Verify installation
    if (-not (Test-Path $targetPath)) {
        Write-Error "Installation failed - executable not found"
        exit 1
    }

    Write-Success "Installed to: $targetPath"

    # Add to PATH
    Write-Status "Updating PATH..."
    $pathUpdated = Add-ToUserPath -Directory $InstallDir

    # Verify it works
    Write-Status "Verifying installation..."
    try {
        $versionOutput = & $targetPath --version 2>&1
        Write-Success "DeepWork installed successfully!"
        Write-Host "   Version: $versionOutput" -ForegroundColor Gray
    }
    catch {
        Write-Error "Installation completed but verification failed: $_"
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "         Installation Complete!         " -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""

    if ($pathUpdated) {
        Write-Host "IMPORTANT: Restart your terminal or run the following to use deepwork:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  `$env:PATH = `"$env:PATH`"" -ForegroundColor Cyan
        Write-Host ""
    }

    Write-Host "Quick start:" -ForegroundColor White
    Write-Host "  deepwork --help       # Show available commands" -ForegroundColor Gray
    Write-Host "  deepwork install      # Install DeepWork in a project" -ForegroundColor Gray
    Write-Host ""
}

# Run installer
Install-DeepWork
