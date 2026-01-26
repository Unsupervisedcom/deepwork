{
  description = "DeepWork - Framework for enabling AI agents to perform complex, multi-step work tasks";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          # Allow unfree packages to support the Business Source License 1.1
          config.allowUnfree = true;
        };
        # Local claude-code package for version control (update via nix/claude-code/update.sh)
        claude-code = pkgs.callPackage ./nix/claude-code/package.nix { };
        # Read version from pyproject.toml to avoid duplication
        pyproject = builtins.fromTOML (builtins.readFile ./pyproject.toml);
        deepwork = pkgs.python311Packages.buildPythonPackage {
          pname = "deepwork";
          version = pyproject.project.version;
          src = ./.;
          format = "pyproject";
          nativeBuildInputs = [ pkgs.python311Packages.hatchling ];
          # Required for `nix build` - must match pyproject.toml dependencies
          propagatedBuildInputs = with pkgs.python311Packages; [
            click gitpython jinja2 jsonschema pyyaml rich rpds-py
          ];
          doCheck = false;
        };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Python 3.11 - base interpreter for uv
            python311

            # uv manages all Python packages (deps, dev tools, etc.)
            uv

            # Git for version control
            git

            # System tools
            jq  # For JSON processing

            # CLI tools (claude-code is locally built, see nix/claude-code/)
            claude-code
            gh           # GitHub CLI
          ];

          # Environment variables for uv integration with Nix
          env = {
            # Tell uv to use the Nix-provided Python interpreter
            UV_PYTHON = "${pkgs.python311}/bin/python";
            # Prevent uv from downloading Python binaries
            UV_PYTHON_DOWNLOADS = "never";
            # Development mode flag
            DEEPWORK_DEV = "1";
          };

          shellHook = ''
            # Create venv if it doesn't exist
            if [ ! -d .venv ]; then
              echo "Creating virtual environment..."
              uv venv .venv --quiet
            fi

            # Sync dependencies (including dev extras like pytest, ruff, mypy)
            # Run quietly - uv only outputs when changes are needed
            uv sync --all-extras --quiet 2>/dev/null || uv sync --all-extras

            # Activate venv by setting environment variables directly
            # This works reliably for both interactive shells and `nix develop --command`
            export VIRTUAL_ENV="$PWD/.venv"
            export PATH="$VIRTUAL_ENV/bin:$PATH"
            unset PYTHONHOME

            # Set PYTHONPATH for editable install access to src/
            export PYTHONPATH="$PWD/src:$PYTHONPATH"

            # Add nix/ scripts to PATH (for 'update' command)
            export PATH="$PWD/nix:$PATH"

            # Only show welcome message in interactive shells
            if [[ $- == *i* ]]; then
              echo ""
              echo "DeepWork Development Environment"
              echo "================================"
              echo ""
              echo "Python: $(python --version) | uv: $(uv --version)"
              echo ""
              echo "Commands:"
              echo "  deepwork --help    CLI (development version)"
              echo "  pytest             Run tests"
              echo "  ruff check src/    Lint code"
              echo "  mypy src/          Type check"
              echo "  claude-code        Claude Code CLI"
              echo "  gh                 GitHub CLI"
              echo "  update             Update claude-code and flake inputs"
              echo ""
            fi
          '';
        };

        # Make the package available as a flake output
        packages.default = deepwork;
        packages.deepwork = deepwork;

        # Make deepwork runnable with 'nix run'
        apps.default = {
          type = "app";
          program = "${deepwork}/bin/deepwork";
        };
      }
    );
}
