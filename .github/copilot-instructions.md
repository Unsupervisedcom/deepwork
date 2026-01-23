# GitHub Copilot Development Environment

This document describes the development environment setup for GitHub Copilot agents working on this repository.

## Overview

GitHub Copilot agents use a **uv/Python-based environment** rather than the Nix environment recommended for human developers. This is because Nix causes Copilot agent Bash tool calls to silently hang during workflow execution.

For comprehensive agent instructions and repository context, see [`AGENTS.md`](../AGENTS.md) in the root directory.

## Environment Setup

The environment is configured via the `.github/workflows/copilot-setup-steps.yml` workflow and includes:

### Prerequisites

- **Python 3.11** - Base interpreter
- **uv** - Python package manager for dependency installation
- **Git** - Version control

### Setup Steps

The following steps are executed in GitHub Actions workflows to prepare the development environment:

1. **Install uv** - Modern Python package manager
   ```bash
   # Installed via astral-sh/setup-uv@v4
   uv --version
   ```

2. **Set up Python 3.11** - Using actions/setup-python@v5
   ```bash
   python --version  # Should show Python 3.11.x
   ```

3. **Install dependencies** - All development tools and project dependencies
   ```bash
   uv sync --extra dev
   ```

4. **Verify environment** - Check that tools are available
   ```bash
   uv run pytest --version   # Test runner
   uv run ruff --version     # Linter and formatter
   ```

### Available Tools

After setup, the following tools are available via `uv run`:

| Tool | Command | Description |
|------|---------|-------------|
| **pytest** | `uv run pytest` | Test runner with all plugins |
| **ruff** | `uv run ruff` | Fast Python linter and formatter |
| **mypy** | `uv run mypy` | Static type checker |
| **deepwork** | `uv run deepwork` | DeepWork CLI (local source) |

### Running Commands

All Python tools must be executed via `uv run` to ensure they run in the virtual environment where dependencies are installed:

```bash
# ✅ Correct - runs in virtual environment
uv run pytest tests/
uv run ruff check src/
uv run mypy src/

# ❌ Incorrect - may not find installed packages
python -m pytest tests/
pytest tests/
```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_example.py -v

# Run with coverage
uv run pytest tests/ --cov=deepwork --cov-report=html
```

### Code Quality Checks

```bash
# Format code
uv run ruff format src/ tests/

# Check linting
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

### Working with DeepWork CLI

```bash
# Run deepwork commands
uv run deepwork --help
uv run deepwork install --platform claude
uv run deepwork sync
```

## Why Not Nix?

While Nix is the **preferred and recommended** development environment for human developers (see [`CONTRIBUTING.md`](../CONTRIBUTING.md)), it cannot be used in GitHub Copilot workflows because:

1. Nix installation causes Copilot agent Bash tool calls to silently hang
2. The `nix-develop` action interferes with interactive command execution
3. Workflow timeouts and failures occur with no useful error messages

The uv/Python setup provides a compatible alternative that:
- ✅ Works reliably in GitHub Actions with Copilot agents
- ✅ Provides all necessary development tools (pytest, ruff, mypy)
- ✅ Uses dependency caching for fast workflow execution
- ✅ Follows the same patterns as `release.yml` and `claude-code-test.yml`

## Additional Resources

- **Primary Agent Instructions**: [`AGENTS.md`](../AGENTS.md) - Complete context for AI agents
- **Human Developer Setup**: [`CONTRIBUTING.md`](../CONTRIBUTING.md) - Nix-based setup for local development
- **Workflow Definition**: [`.github/workflows/copilot-setup-steps.yml`](workflows/copilot-setup-steps.yml)
