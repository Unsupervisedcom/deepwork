{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # Python 3.11 or later
    python311
    python311Packages.pip
    python311Packages.virtualenv

    # Modern Python tooling
    uv

    # Git for version control
    git

    # Additional tools
    jq  # For JSON processing

    # Python development dependencies
    python311Packages.jinja2
    python311Packages.pyyaml
    python311Packages.gitpython
    python311Packages.pytest
    python311Packages.pytest-mock
    python311Packages.pytest-cov
    python311Packages.click
    python311Packages.rich

    # Linting and type checking
    ruff
    mypy
  ];

  shellHook = ''
    # Set up environment variables
    export PYTHONPATH="$PWD/src:$PYTHONPATH"
    export DEEPWORK_DEV=1

    # Auto-sync dependencies and activate venv for direct deepwork access
    echo "Setting up DeepWork development environment..."
    uv sync --quiet 2>/dev/null || uv sync

    # Activate the virtual environment so 'deepwork' command is directly available
    if [ -f .venv/bin/activate ]; then
      source .venv/bin/activate
    fi

    echo ""
    echo "DeepWork Development Environment"
    echo "================================"
    echo ""
    echo "Python version: $(python --version)"
    echo "uv version: $(uv --version)"
    echo ""
    echo "Available tools:"
    echo "  - deepwork: CLI is ready (try 'deepwork --help')"
    echo "  - pytest: Testing framework"
    echo "  - ruff: Python linter and formatter"
    echo "  - mypy: Static type checker"
    echo ""
    echo "Quick start:"
    echo "  - 'deepwork --help' to see available commands"
    echo "  - 'pytest' to run tests"
    echo "  - Read doc/architecture.md for design details"
    echo ""
  '';
}
