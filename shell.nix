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
    echo "DeepWork Development Environment"
    echo "================================"
    echo ""
    echo "Python version: $(python --version)"
    echo "uv version: $(uv --version)"
    echo ""
    echo "Available tools:"
    echo "  - uv: Modern Python package installer"
    echo "  - pytest: Testing framework"
    echo "  - ruff: Python linter and formatter"
    echo "  - mypy: Static type checker"
    echo ""
    echo "To get started:"
    echo "  1. Run 'uv sync' to install project dependencies"
    echo "  2. Run 'uv run pytest' to run tests"
    echo "  3. Read doc/architecture.md for design details"
    echo ""

    # Set up environment variables
    export PYTHONPATH="$PWD/src:$PYTHONPATH"
    export DEEPWORK_DEV=1
  '';
}
