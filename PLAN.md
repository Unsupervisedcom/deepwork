# Plan: Python Environment Management in DeepWork

## Overview

When DeepWork is installed via Homebrew, it includes `uv` for managing Python environments. This plan outlines how DeepWork can ask users how they want Python dependencies managed and implement that choice throughout the workflow.

## User Experience

### During `deepwork install`

After platform detection, prompt the user:

```
Python Environment Setup
========================

How should Python dependencies be managed for this project?

  [1] uv (Recommended)
      Creates isolated .venv with project-specific Python
      No system Python required, fast installs

  [2] System Python
      Uses existing python3 from PATH
      Requires Python 3.11+ already installed

  [3] Skip
      No Python environment setup
      You'll manage dependencies manually

Choice [1]:
```

### Configuration Persistence

Store the choice in `.deepwork/config.yml`:

```yaml
version: 0.1.0
platforms:
  - claude
python:
  manager: uv          # "uv" | "system" | "skip"
  version: "3.11"      # Target Python version
  venv_path: .venv     # Path to virtual environment
```

---

## Files to Change

### 1. `src/deepwork/cli/install.py`

**Changes:**
- Add `_prompt_python_setup()` function after platform detection
- Add `_setup_python_environment()` function to create venv
- Update config schema to include `python` section
- Call python setup before syncing skills

**New code location:** After line ~336 (after platform detection, before directory creation)

```python
def _prompt_python_setup(console: Console) -> dict:
    """Prompt user for Python environment preferences."""
    console.print("\n[bold]Python Environment Setup[/bold]")
    console.print("=" * 40)
    console.print("\nHow should Python dependencies be managed?\n")

    choices = [
        ("1", "uv (Recommended)", "Creates isolated .venv with project-specific Python"),
        ("2", "System Python", "Uses existing python3 from PATH"),
        ("3", "Skip", "No Python environment setup"),
    ]

    for key, name, desc in choices:
        console.print(f"  [{key}] {name}")
        console.print(f"      {desc}\n")

    choice = Prompt.ask("Choice", default="1", choices=["1", "2", "3"])

    manager_map = {"1": "uv", "2": "system", "3": "skip"}
    return {
        "manager": manager_map[choice],
        "version": "3.11",
        "venv_path": ".venv"
    }
```

### 2. `src/deepwork/utils/python_env.py` (NEW FILE)

**Purpose:** Encapsulate Python environment management logic

```python
"""Python environment management utilities."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional

class PythonEnvironment:
    """Manages Python virtual environments."""

    def __init__(self, config: dict):
        self.manager = config.get("manager", "uv")
        self.version = config.get("version", "3.11")
        self.venv_path = Path(config.get("venv_path", ".venv"))

    def setup(self, project_root: Path) -> bool:
        """Create virtual environment based on configured manager."""
        if self.manager == "skip":
            return True

        venv_dir = project_root / self.venv_path

        if self.manager == "uv":
            return self._setup_with_uv(venv_dir)
        elif self.manager == "system":
            return self._setup_with_system(venv_dir)

        return False

    def _setup_with_uv(self, venv_dir: Path) -> bool:
        """Create venv using uv."""
        if not shutil.which("uv"):
            raise RuntimeError("uv not found. Install via: brew install uv")

        cmd = ["uv", "venv", str(venv_dir), "--python", self.version]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def _setup_with_system(self, venv_dir: Path) -> bool:
        """Create venv using system Python."""
        python = shutil.which("python3") or shutil.which("python")
        if not python:
            raise RuntimeError("Python not found in PATH")

        cmd = [python, "-m", "venv", str(venv_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0

    def install_package(self, package: str, project_root: Path) -> bool:
        """Install a package into the virtual environment."""
        venv_dir = project_root / self.venv_path

        if self.manager == "uv":
            cmd = ["uv", "pip", "install", package]
        else:
            pip = venv_dir / "bin" / "pip"
            cmd = [str(pip), "install", package]

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
        return result.returncode == 0

    @staticmethod
    def detect_existing(project_root: Path) -> Optional[Path]:
        """Detect existing virtual environment."""
        candidates = [".venv", "venv", ".virtualenv"]
        for name in candidates:
            venv_dir = project_root / name
            if (venv_dir / "bin" / "python").exists():
                return venv_dir
        return None
```

### 3. `src/deepwork/cli/install.py` - Integration

**Add imports:**
```python
from deepwork.utils.python_env import PythonEnvironment
from rich.prompt import Prompt
```

**Modify `install()` function:**

```python
@click.command()
@click.option("--platform", "-p", multiple=True, help="Target platform(s)")
@click.option("--python-manager", type=click.Choice(["uv", "system", "skip"]),
              help="Python environment manager (skips interactive prompt)")
def install(platform: tuple[str, ...], python_manager: Optional[str] = None):
    """Install DeepWork in a project."""
    console = Console()
    project_root = Path.cwd()

    # ... existing git check and platform detection ...

    # Python environment setup (after platform detection)
    if python_manager:
        python_config = {"manager": python_manager, "version": "3.11", "venv_path": ".venv"}
    else:
        # Check for existing venv
        existing = PythonEnvironment.detect_existing(project_root)
        if existing:
            console.print(f"[green]Found existing venv:[/green] {existing}")
            python_config = {"manager": "skip", "venv_path": str(existing)}
        else:
            python_config = _prompt_python_setup(console)

    # Create Python environment
    if python_config["manager"] != "skip":
        console.print(f"\n[bold]Setting up Python environment with {python_config['manager']}...[/bold]")
        env = PythonEnvironment(python_config)
        try:
            env.setup(project_root)
            console.print("[green]✓[/green] Virtual environment created")
        except RuntimeError as e:
            console.print(f"[red]✗[/red] Failed: {e}")
            return

    # ... existing directory creation and config saving ...

    # Update config to include python section
    config["python"] = python_config
    save_yaml(config_path, config)
```

### 4. `.deepwork/config.yml` Schema Update

**Before:**
```yaml
version: 0.1.0
platforms:
  - claude
```

**After:**
```yaml
version: 0.1.0
platforms:
  - claude
python:
  manager: uv
  version: "3.11"
  venv_path: .venv
```

### 5. `src/deepwork/schemas/config.json` (NEW or UPDATE)

Add JSON schema validation for the config:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["version", "platforms"],
  "properties": {
    "version": { "type": "string" },
    "platforms": {
      "type": "array",
      "items": { "type": "string", "enum": ["claude", "gemini", "copilot"] }
    },
    "python": {
      "type": "object",
      "properties": {
        "manager": { "type": "string", "enum": ["uv", "system", "skip"] },
        "version": { "type": "string" },
        "venv_path": { "type": "string" }
      }
    }
  }
}
```

### 6. Update `deepwork sync` Command

**File:** `src/deepwork/cli/sync.py`

Optionally verify Python environment exists when syncing:

```python
def sync_skills():
    config = load_yaml(config_path)

    # Verify Python environment if configured
    python_config = config.get("python", {})
    if python_config.get("manager") != "skip":
        venv_path = project_root / python_config.get("venv_path", ".venv")
        if not venv_path.exists():
            console.print("[yellow]Warning:[/yellow] Virtual environment not found")
            console.print(f"  Run: deepwork install --python-manager {python_config['manager']}")
```

---

## Test Cases

### Unit Tests (`tests/unit/utils/test_python_env.py`)

```python
def test_detect_existing_venv(tmp_path):
    """Detect existing .venv directory."""
    venv = tmp_path / ".venv" / "bin"
    venv.mkdir(parents=True)
    (venv / "python").touch()

    result = PythonEnvironment.detect_existing(tmp_path)
    assert result == tmp_path / ".venv"

def test_setup_with_uv(tmp_path, mocker):
    """Create venv using uv."""
    mocker.patch("shutil.which", return_value="/usr/bin/uv")
    mocker.patch("subprocess.run", return_value=Mock(returncode=0))

    env = PythonEnvironment({"manager": "uv", "version": "3.11"})
    assert env.setup(tmp_path) is True

def test_setup_with_system_python(tmp_path, mocker):
    """Create venv using system Python."""
    mocker.patch("shutil.which", return_value="/usr/bin/python3")
    mocker.patch("subprocess.run", return_value=Mock(returncode=0))

    env = PythonEnvironment({"manager": "system"})
    assert env.setup(tmp_path) is True

def test_skip_setup(tmp_path):
    """Skip environment setup."""
    env = PythonEnvironment({"manager": "skip"})
    assert env.setup(tmp_path) is True
```

### Integration Tests (`tests/integration/test_install_python.py`)

```python
def test_install_with_uv(tmp_git_repo):
    """Full install flow with uv."""
    result = runner.invoke(cli, ["install", "--platform", "claude", "--python-manager", "uv"])
    assert result.exit_code == 0
    assert (tmp_git_repo / ".venv").exists()

    config = load_yaml(tmp_git_repo / ".deepwork" / "config.yml")
    assert config["python"]["manager"] == "uv"

def test_install_detects_existing_venv(tmp_git_repo):
    """Install detects and uses existing venv."""
    (tmp_git_repo / ".venv" / "bin").mkdir(parents=True)
    (tmp_git_repo / ".venv" / "bin" / "python").touch()

    result = runner.invoke(cli, ["install", "--platform", "claude"], input="3\n")
    config = load_yaml(tmp_git_repo / ".deepwork" / "config.yml")
    assert config["python"]["manager"] == "skip"
```

---

## Migration Strategy

### For Existing Projects

When running `deepwork install` on an existing project:

1. Detect if `.deepwork/config.yml` exists
2. Check if `python` section is present
3. If missing, prompt user (or skip if `--python-manager skip`)
4. Preserve existing config values

### Backward Compatibility

- Projects without `python` config continue to work
- `python` section is optional in config schema
- Default to `skip` if not specified (no environment created)

---

## Implementation Order

1. **Phase 1: Core Infrastructure**
   - [ ] Create `src/deepwork/utils/python_env.py`
   - [ ] Add unit tests for `PythonEnvironment` class
   - [ ] Update config schema

2. **Phase 2: CLI Integration**
   - [ ] Add `--python-manager` flag to install command
   - [ ] Implement `_prompt_python_setup()` interactive flow
   - [ ] Integrate into install workflow
   - [ ] Add integration tests

3. **Phase 3: Documentation**
   - [ ] Update README with Python environment options
   - [ ] Update CONTRIBUTING guide
   - [ ] Add examples to documentation

---

## Open Questions

1. **Should `deepwork sync` auto-create missing venv?**
   - Pro: Convenient for CI/CD
   - Con: Unexpected side effects

2. **Should we support pyenv/asdf for version management?**
   - Could detect `.python-version` file
   - More complex but flexible

3. **Should we add `deepwork python` subcommand?**
   - `deepwork python install <package>` - install into project venv
   - `deepwork python shell` - activate venv
   - Useful for AI agents to manage dependencies

4. **Integration with pyproject.toml?**
   - Auto-detect `requires-python` from project
   - Use as default version instead of hardcoded 3.11
