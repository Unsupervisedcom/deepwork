# GitHub Copilot Development Environment

**Primary agent instructions**: See [`AGENTS.md`](../AGENTS.md) for complete repository context.

## Environment Setup

GitHub Copilot agents use uv/Python (not Nix) because Nix causes Bash tool calls to hang. Setup is handled by `.github/workflows/copilot-setup-steps.yml`:

```bash
uv sync --extra dev
```

## Available Tools

All tools must be run via `uv run`:

| Tool | Command |
|------|---------|
| **pytest** | `uv run pytest tests/ -v` |
| **ruff** | `uv run ruff check src/` |
| **mypy** | `uv run mypy src/` |
| **deepwork** | `uv run deepwork` |

## Running Tests

```bash
# All tests
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_example.py -v

# With coverage
uv run pytest tests/ --cov=deepwork --cov-report=html
```
