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
- **uv** - Modern Python package installer (included in Nix environment)
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
2. **Read the CLA** - Review the [Contributor License Agreement (CLA)](CLA.md)
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

For the full text, see [CLA.md](CLA.md).

## Development Setup

### Option 1: Using Nix (Recommended)

The easiest way to get started is using Nix, which provides a fully reproducible development environment with all dependencies pre-configured.

```bash
# Clone the repository
git clone https://github.com/deepwork/deepwork.git
cd deepwork

# Enter the Nix development environment
nix-shell
```

When you enter `nix-shell`, you'll see a welcome message with available tools. The environment includes:
- Python 3.11
- uv (package manager)
- pytest, ruff, mypy
- All Python dependencies
- Environment variables (`PYTHONPATH`, `DEEPWORK_DEV=1`)

### Option 2: Manual Setup (Without Nix)

If you prefer not to use Nix:

```bash
# Clone the repository
git clone https://github.com/deepwork/deepwork.git
cd deepwork

# Create a virtual environment (optional but recommended)
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install uv if you don't have it
pip install uv

# Install dependencies
uv sync

# Set PYTHONPATH for development
export PYTHONPATH="$PWD/src:$PYTHONPATH"
export DEEPWORK_DEV=1
```

## Installing DeepWork Locally

To use your local development version of DeepWork, install it in **editable mode**. This allows you to make changes to the code and have them immediately reflected without reinstalling.

### Using uv (Recommended)

```bash
# Install in editable mode with development dependencies
uv pip install -e ".[dev]"

# Or if you're inside nix-shell
uv sync  # Automatically installs in editable mode
```

### Using pip

```bash
# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Check that the deepwork command is available
deepwork --help

# Verify you're using the local version
which deepwork  # Should point to your local environment

# Check version (should show 0.1.0 or current dev version)
python -c "import deepwork; print(deepwork.__version__)"
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

## Running Tests

DeepWork has a comprehensive test suite with unit and integration tests.

### Run All Tests

```bash
# Using uv (recommended)
uv run pytest

# Or with explicit paths
uv run pytest tests/ -v

# Using pytest directly (if in nix-shell or venv)
pytest
```

### Run Specific Test Types

```bash
# Unit tests only (147 tests)
uv run pytest tests/unit/ -v

# Integration tests only (19 tests)
uv run pytest tests/integration/ -v

# Run a specific test file
uv run pytest tests/unit/core/test_parser.py -v

# Run a specific test function
uv run pytest tests/unit/core/test_parser.py::test_parse_valid_job -v
```

### Test with Coverage

```bash
# Generate coverage report
uv run pytest --cov=deepwork --cov-report=html

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
├── shell.nix             # Nix development environment
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
# In one terminal: Enter nix-shell and keep it open
nix-shell

# In nix-shell: Watch tests
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
**Solution**: Make sure you've installed in editable mode:
```bash
uv pip install -e .
```

### Issue: Tests failing with import errors
**Solution**: Set PYTHONPATH:
```bash
export PYTHONPATH="$PWD/src:$PYTHONPATH"
```

### Issue: Changes not reflected in test project
**Solution**: Verify editable install:
```bash
pip list | grep deepwork
# Should show: deepwork 0.1.0 /path/to/your/local/deepwork/src
```

### Issue: Nix shell not loading
**Solution**: Make sure Nix is installed and `<nixpkgs>` is available:
```bash
nix-shell --version
echo $NIX_PATH
```

## License

By contributing to DeepWork, you agree that your contributions will be licensed under the project's current license. The licensor (Unsupervised.com, Inc.) reserves the right to change the project license at any time at its sole discretion.

You must sign the [Contributor License Agreement (CLA)](CLA.md) before your contributions can be accepted. See the CLA section above for details.

---

Thank you for contributing to DeepWork! Your efforts help make AI-powered workflows accessible to everyone.
