# Contributing to DeepWork

Thank you for your interest in contributing to DeepWork! This guide will help you set up your local development environment and understand the development workflow.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Installing DeepWork Locally](#installing-deepwork-locally)
- [Testing Your Local Installation](#testing-your-local-installation)
- [Running Tests](#running-tests)
- [Code Quality](#code-quality)
- [Development Workflow](#development-workflow)
- [Project Structure](#project-structure)
- [Submitting Changes](#submitting-changes)

## Prerequisites

- **Python 3.11 or higher** - Required for running DeepWork
- **Git** - For version control
- **Nix** (optional but recommended) - For reproducible development environment
  - Nix flakes enabled (add `experimental-features = nix-command flakes` to `~/.config/nix/nix.conf`)
- **direnv** (optional) - For automatic environment activation when using Nix flakes
- **uv** - Modern Python package installer (included in Nix environment)
- **Homebrew** (optional) - For easy installation on macOS/Linux via `brew install`
- **Signed CLA** - All contributors must sign the Contributor License Agreement (see below)

## Contributor License Agreement (CLA)

Before we can accept your contributions, you must sign our Contributor License Agreement (CLA). This is a one-time requirement for all contributors.

### Why We Require a CLA

The CLA ensures that:
- You have the legal right to contribute your code
- The project can safely use and distribute your contributions
- Your contributions comply with the Business Source License 1.1 under which DeepWork is licensed
- Both you and the project are legally protected

### How to Sign the CLA

**For First-Time Contributors:**

1. **Submit your pull request** - When you open your first PR, the CLA Assistant bot will automatically comment on it
2. **Read the CLA** - Review the [Contributor License Agreement (CLA)](CLA/version_1/CLA.md)
3. **Sign electronically** - Comment on your PR with: `I have read the CLA Document and I hereby sign the CLA`
4. **Verification** - The bot will verify your signature and update the PR status

The CLA Assistant will remember your signature for all future contributions.

**For Corporate Contributors:**

If you're contributing on behalf of your employer, your organization must sign a Corporate CLA. Please contact legal@unsupervised.com to obtain the Corporate CLA.

### CLA Details

Our CLA:
- Grants the project a license to use your contributions
- Confirms you have the right to contribute the code
- Acknowledges the Business Source License 1.1 restrictions
- Is based on the Apache Software Foundation's CLA with modifications for BSL 1.1

For the full text, see [CLA.md](CLA/version_1/CLA.md).

## Development Setup

### Setting Up direnv (Optional but Recommended)

direnv automatically loads the Nix environment when you `cd` into the project directory:

```bash
# Install direnv (if not already installed)
# On macOS with Homebrew:
brew install direnv

# On Linux (Debian/Ubuntu):
apt-get install direnv

# On NixOS or with Nix:
nix-env -i direnv

# Add direnv hook to your shell
# For bash, add to ~/.bashrc:
eval "$(direnv hook bash)"

# For zsh, add to ~/.zshrc:
eval "$(direnv hook zsh)"

# For fish, add to ~/.config/fish/config.fish:
direnv hook fish | source

# Restart your shell or source your rc file
source ~/.bashrc  # or ~/.zshrc
```

Once direnv is set up, the environment will activate automatically when you enter the directory.

### Option 1: Using Nix Flakes (Recommended)

The easiest way to get started is using Nix flakes, which provides a fully reproducible development environment with all dependencies pre-configured.

#### Quick Start with direnv (Recommended)

If you have direnv installed, the entire development environment activates automatically when you `cd` into the project:

```bash
# Clone the repository
git clone https://github.com/deepwork/deepwork.git
cd deepwork

# Allow direnv (first time only)
direnv allow

# That's it! Everything is ready:
deepwork --help    # CLI works
pytest             # Tests work
ruff check src/    # Linting works
```

The `.envrc` file contains `use flake`, which tells direnv to load the Nix flake's development shell. This automatically:

1. Creates `.venv/` if it doesn't exist
2. Installs all dependencies via `uv sync --all-extras`
3. Adds `.venv/bin` to your PATH
4. Sets `PYTHONPATH` and `DEEPWORK_DEV=1`

Every time you `cd` into the directory, the environment is ready instantly (venv is reused, deps are cached).

#### Manual Flake Usage

If you don't use direnv, you can manually enter the development environment:

```bash
# Clone the repository
git clone https://github.com/deepwork/deepwork.git
cd deepwork

# Enter the Nix development environment
nix develop
```

#### What's Included

The Nix environment provides:

| Tool | Description |
|------|-------------|
| `deepwork` | CLI using your local source code (editable install) |
| `claude` | Claude Code CLI (built from source for version control) |
| `pytest` | Test runner with all plugins |
| `ruff` | Fast Python linter and formatter |
| `mypy` | Static type checker |
| `uv` | Python package manager |
| `python` | Python 3.11 interpreter |
| `update` | Updates claude-code and flake inputs |

#### CI Usage

For CI pipelines or scripts, use `nix develop --command`:

```bash
nix develop --command pytest
nix develop --command ruff check src/
nix develop --command mypy src/
```

#### Updating Development Dependencies

The Nix environment includes Claude Code built from source to ensure version control (the nixpkgs version can lag behind npm releases). Use the `update` command to keep dependencies current:

```bash
# In the dev shell - updates claude-code and flake inputs
update
```

To manually update Claude Code:

```bash
./nix/claude-code/update.sh
```

This fetches the latest version from npm, computes the necessary hashes using `prefetch-npm-deps`, and updates `package.nix` automatically.

A GitHub Action automatically checks for new Claude Code versions daily and creates PRs when updates are available.

### Option 2: Manual Setup (Without Nix)

If you prefer not to use Nix:

```bash
# Clone the repository
git clone https://github.com/deepwork/deepwork.git
cd deepwork

# Install uv if you don't have it (see https://docs.astral.sh/uv/getting-started/installation/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install all dependencies (including dev tools)
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync --all-extras

# Set environment variables for development
export PYTHONPATH="$PWD/src:$PYTHONPATH"
export DEEPWORK_DEV=1
```

## Installing DeepWork Locally

The development version of DeepWork is installed automatically in **editable mode**, meaning changes to source code are reflected immediately without reinstalling.

### With Nix (Automatic)

If you're using the Nix development environment, DeepWork is already installed in editable mode. No additional steps needed.

### Without Nix (Manual)

If you set up manually, the `uv sync --all-extras` command installs DeepWork in editable mode automatically.

Alternatively, you can install explicitly:

```bash
# Using uv
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Check that the deepwork command is available
deepwork --help

# Verify you're using the local development version
which deepwork  # Should point to .venv/bin/deepwork

# Check version
deepwork --version
```

## Testing Your Local Installation

To test your local DeepWork installation in a real project:

### 1. Create a Test Project

```bash
# Outside the deepwork directory
mkdir ~/test-deepwork-project
cd ~/test-deepwork-project
git init
```

### 2. Install DeepWork in the Test Project

Since you installed DeepWork in editable mode, the `deepwork` command uses your local development version:

```bash
# Run the install command
deepwork install --platform claude

# Verify installation
ls -la .deepwork/
ls -la .claude/
```

### 3. Test Your Changes

Any changes you make to the DeepWork source code will be immediately reflected:

```bash
# Make changes in ~/deepwork/src/deepwork/...
# Then test in your test project
deepwork install --platform claude

# Or test the CLI directly
deepwork --help
```

### 4. Test with Claude Code

If you have Claude Code installed, you can test the generated skills:

```bash
# In your test project
claude  # Start Claude Code

# Try the generated skills
/deepwork.define
```

### 5. Test a Feature Branch with One-Off Nix Shell

You can test a feature branch directly from GitHub without cloning or modifying your local environment. This is useful for:
- Reviewing someone else's PR
- Testing a feature branch before merging
- Trying out experimental changes without affecting your setup

```bash
# Run DeepWork CLI directly from a feature branch
nix run github:Unsupervisedcom/deepwork/feature-branch-name -- --help

# Enter a development shell with a specific branch
nix develop github:Unsupervisedcom/deepwork/feature-branch-name

# Run a specific command from a feature branch
nix develop github:Unsupervisedcom/deepwork/feature-branch-name --command deepwork install --platform claude

# Test against a specific commit
nix run github:Unsupervisedcom/deepwork/abc1234 -- --version

# Test against a PR from a fork
nix run github:pr-author/deepwork/feature-name -- --help
# Or if the PR is from a branch in this repository:
nix run github:Unsupervisedcom/deepwork/feature-name -- --help
```

For example, to test a branch named `feat/new-parser`:

```bash
# Quick test of the CLI
nix run github:Unsupervisedcom/deepwork/feat/new-parser -- install --platform claude --dry-run

# Or enter a full development shell to run tests and run a specific test
nix develop github:Unsupervisedcom/deepwork/feat/new-parser --command pytest tests/unit/core/test_parser.py -v
```

**Note**: The first run will take longer as Nix fetches and builds the branch. Subsequent runs use the cached build.

## Running Tests

DeepWork has a comprehensive test suite with 568+ tests.

### Run All Tests

```bash
# In Nix environment (interactive or CI)
pytest

# Or using nix develop --command (CI-friendly, no interactive shell)
nix develop --command pytest

# Using uv run (without Nix)
uv run pytest
```

### Run Specific Test Types

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Run a specific test file
pytest tests/unit/core/test_parser.py -v

# Run a specific test function
pytest tests/unit/core/test_parser.py::test_parse_valid_job -v
```

### Test with Coverage

```bash
# Generate coverage report
uv run pytest tests/ --cov=deepwork --cov-report=html

# View coverage in browser
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

### Watch Mode (Continuous Testing)

```bash
# Install pytest-watch
uv pip install pytest-watch

# Run tests on file changes
ptw
```

## Code Quality

DeepWork maintains high code quality standards using automated tools.

### Linting

```bash
# Check for linting issues
ruff check src/

# Check specific files
ruff check src/deepwork/cli/main.py

# Auto-fix linting issues
ruff check --fix src/
```

### Formatting

```bash
# Format code
ruff format src/

# Check formatting without making changes
ruff format --check src/
```

### Type Checking

```bash
# Run mypy type checker
mypy src/

# Run mypy on specific module
mypy src/deepwork/core/
```

### Run All Quality Checks

```bash
# Before committing, run all checks
ruff check src/
ruff format --check src/
mypy src/
uv run pytest
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes

- Edit code in `src/deepwork/`
- Add tests in `tests/unit/` or `tests/integration/`
- Update documentation if needed

### 3. Test Your Changes

```bash
# Run relevant tests
uv run pytest tests/unit/core/test_yourmodule.py -v

# Run all tests
uv run pytest

# Check code quality
ruff check src/
mypy src/
```

### 4. Test in a Real Project

```bash
# Create or use a test project
cd ~/test-project/
deepwork install --platform claude

# Verify your changes work as expected
```

### 5. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature X"

# Or for bug fixes
git commit -m "fix: resolve issue with Y"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/) format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions or changes
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

## Project Structure

```
deepwork/
├── src/deepwork/          # Source code
│   ├── cli/              # CLI commands (install, etc.)
│   │   ├── main.py       # Main CLI entry point
│   │   └── commands/     # Command implementations
│   ├── core/             # Core functionality
│   │   ├── parser.py     # Job definition parsing
│   │   ├── registry.py   # Job registry management
│   │   ├── detector.py   # Platform detection
│   │   └── generator.py  # Skill file generation
│   ├── templates/        # Jinja2 templates for skill generation
│   │   ├── claude/       # Claude Code templates
│   │   ├── gemini/       # Gemini templates
│   │   └── copilot/      # Copilot templates
│   ├── schemas/          # JSON schemas for validation
│   └── utils/            # Utility modules
│       ├── fs.py         # File system operations
│       ├── yaml.py       # YAML operations
│       ├── git.py        # Git operations
│       └── validation.py # Validation utilities
├── tests/
│   ├── unit/             # Unit tests (147 tests)
│   ├── integration/      # Integration tests (19 tests)
│   └── fixtures/         # Test fixtures and sample data
├── doc/                  # Documentation
│   ├── architecture.md   # Comprehensive architecture doc
│   └── TEMPLATE_REVIEW.md
├── flake.nix             # Nix flake for development environment
├── pyproject.toml        # Python project configuration
├── CLAUDE.md             # Project context for Claude Code
└── README.md             # Project overview
```

## Submitting Changes

### Before Submitting a Pull Request

1. **Ensure all tests pass**:
   ```bash
   uv run pytest
   ```

2. **Ensure code quality checks pass**:
   ```bash
   ruff check src/
   ruff format --check src/
   mypy src/
   ```

3. **Add tests for new features**:
   - Unit tests in `tests/unit/`
   - Integration tests in `tests/integration/` if appropriate

4. **Update documentation**:
   - Update `README.md` if adding user-facing features
   - Update `doc/architecture.md` if changing core design
   - Add docstrings to new functions/classes

5. **Test in a real project**:
   - Create a test project
   - Run `deepwork install`
   - Verify the feature works end-to-end

### Creating a Pull Request

1. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create PR on GitHub**:
   - Go to https://github.com/deepwork/deepwork
   - Click "Pull requests" → "New pull request"
   - Select your branch
   - Fill in the PR template:
     - **Description**: What does this PR do?
     - **Motivation**: Why is this change needed?
     - **Testing**: How did you test this?
     - **Breaking Changes**: Any breaking changes?

3. **Respond to review feedback**:
   - Address reviewer comments
   - Push additional commits to your branch
   - Request re-review when ready

### Pull Request Guidelines

- **Keep PRs focused**: One feature/fix per PR
- **Write clear commit messages**: Follow conventional commits
- **Add tests**: All new code should have tests
- **Update docs**: Keep documentation in sync
- **Pass CI checks**: All automated checks must pass

## Getting Help

- **Documentation**: See `doc/architecture.md` for design details
- **Issues**: Check existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions
- **Code Style**: Follow existing code patterns

## Development Tips

### Quick Development Cycle

```bash
# In one terminal: Enter Nix development environment
nix develop

# In Nix environment: Watch tests
uv run pytest tests/unit/ --watch

# In another terminal: Make changes to src/deepwork/

# Tests automatically re-run on save
```

### Debugging

```bash
# Run tests with verbose output and stop on first failure
uv run pytest -vv -x

# Run tests with pdb debugger on failure
uv run pytest --pdb

# Add breakpoints in code
import pdb; pdb.set_trace()
```

### Performance Testing

```bash
# Time test execution
time uv run pytest tests/unit/

# Profile test execution
uv run pytest --profile
```

## Common Issues

### Issue: `deepwork` command not found
**With Nix**: Re-enter the development environment:
```bash
nix develop
# or if using direnv
direnv reload
```

**Without Nix**: Ensure venv is activated and dependencies synced:
```bash
source .venv/bin/activate
uv sync --all-extras
```

### Issue: Tests failing with import errors
**Solution**: This usually means dependencies aren't installed. Re-sync:
```bash
uv sync --all-extras
```

### Issue: Changes not reflected
**Solution**: Verify editable install with uv:
```bash
uv pip list | grep deepwork
# Should show: deepwork (editable) with path to your local directory
```

### Issue: Nix environment not loading
**Solution**: Ensure Nix is installed with flakes enabled:
```bash
nix --version
# Add to ~/.config/nix/nix.conf if not already there:
# experimental-features = nix-command flakes
```

### Issue: Old venv causing conflicts
**Solution**: Remove and let Nix recreate it:
```bash
rm -rf .venv
nix develop  # Will recreate .venv automatically
```

## License

By contributing to DeepWork, you agree that your contributions will be licensed under the project's current license. The licensor (Unsupervised.com, Inc.) reserves the right to change the project license at any time at its sole discretion.

You must sign the [Contributor License Agreement (CLA)](CLA/version_1/CLA.md) before your contributions can be accepted. See the CLA section above for details.

---

Thank you for contributing to DeepWork! Your efforts help make AI-powered workflows accessible to everyone.
