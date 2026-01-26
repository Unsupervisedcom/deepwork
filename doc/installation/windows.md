# DeepWork Windows Installation Guide

This guide covers installing DeepWork on Windows for use with Claude Code.

## Prerequisites

- **Windows 10 or later**
- **Claude Code** - Install via [official instructions](https://code.claude.com/docs/en/setup)
- **Git for Windows** - Required for Claude Code hooks (provides Git Bash)

## Installation Methods

### Method 1: Pre-built Executable (Recommended)

Download and run the Windows installer:

```powershell
# Download the installer
Invoke-WebRequest -Uri "https://github.com/unsupervisedcom/deepwork/releases/latest/download/install-windows.ps1" -OutFile install-windows.ps1

# Run the installer
.\install-windows.ps1
```

The installer will:
1. Download the latest `deepwork.exe`
2. Install it to `%LOCALAPPDATA%\DeepWork\bin`
3. Add the installation directory to your PATH

### Method 2: pip/pipx Installation

If you have Python 3.11+ installed:

```powershell
# Using pip (requires Python in PATH)
pip install deepwork

# OR using pipx (isolated environment, recommended)
pipx install deepwork
```

### Method 3: Build from Source

For developers or custom builds:

```powershell
# Clone the repository
git clone https://github.com/unsupervisedcom/deepwork.git
cd deepwork

# Build Windows executable
.\scripts\build-windows.ps1

# Install the built executable
.\scripts\install-windows.ps1 -ExePath .\dist\deepwork.exe
```

## Verifying Installation

After installation, open a new terminal and verify:

```powershell
deepwork --version
deepwork --help
```

## Using with Claude Code

### Initial Setup

1. Navigate to your project directory
2. Install DeepWork in the project:

```powershell
cd your-project
deepwork install
```

3. Sync skills and hooks:

```powershell
deepwork sync
```

### How Hooks Work on Windows

Claude Code on Windows runs hooks through Git Bash (installed with Git for Windows). DeepWork hooks are configured to work cross-platform:

- Hooks use `deepwork hook <name>` commands
- Git Bash can find `deepwork` if it's in your Windows PATH
- All hook scripts are Python-based for cross-platform compatibility

### Troubleshooting

#### "deepwork" command not found

Ensure the installation directory is in your PATH:

```powershell
# Check if deepwork is in PATH
where.exe deepwork

# If not found, add manually
$env:PATH += ";$env:LOCALAPPDATA\DeepWork\bin"

# To make permanent, add to your PowerShell profile:
Add-Content $PROFILE "`n`$env:PATH += `";`$env:LOCALAPPDATA\DeepWork\bin`""
```

#### Hooks not running

1. Verify Claude Code is using Git Bash:
   ```powershell
   $env:CLAUDE_CODE_GIT_BASH_PATH = "C:\Program Files\Git\bin\bash.exe"
   ```

2. Re-sync hooks:
   ```powershell
   deepwork sync
   ```

3. Restart Claude Code session

#### Permission errors

Run PowerShell as Administrator for installation, or use the user-level installation (default).

## Architecture Notes

### Why Python Modules for Hooks?

DeepWork uses Python module-based hooks (`deepwork hook <name>`) instead of shell scripts for cross-platform compatibility:

- Works on Windows, macOS, and Linux
- No bash script dependencies
- Consistent behavior across platforms

### PATH Considerations

The Windows installer adds DeepWork to your user PATH. Git Bash inherits the Windows PATH, so `deepwork` commands work in both:

- PowerShell/CMD: `deepwork --help`
- Git Bash: `deepwork --help`
- Claude Code hooks: Automatically use Git Bash

## Uninstallation

```powershell
# Remove the executable
Remove-Item "$env:LOCALAPPDATA\DeepWork" -Recurse -Force

# Remove from PATH (manual step in System Properties > Environment Variables)
```

For pip/pipx installations:

```powershell
pip uninstall deepwork
# OR
pipx uninstall deepwork
```
