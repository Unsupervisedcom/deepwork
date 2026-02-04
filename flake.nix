{
  description = "DeepWork - Framework for enabling AI agents to perform complex, multi-step work tasks";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, pyproject-nix, uv2nix, pyproject-build-systems, ... }:
    let
      inherit (nixpkgs) lib;

      # Systems to support
      forAllSystems = lib.genAttrs [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];

      # Load the uv workspace from uv.lock
      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      # Create overlay from uv.lock - prefer wheels for faster builds
      overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };

      # Editable overlay for development (live-reload from src/)
      editableOverlay = workspace.mkEditablePyprojectOverlay { root = "$REPO_ROOT"; };

      # Build Python package sets for each system
      pythonSets = forAllSystems (system:
        let
          pkgs = import nixpkgs {
            inherit system;
            config.allowUnfree = true;
          };
          python = pkgs.python311;
        in
        (pkgs.callPackage pyproject-nix.build.packages { inherit python; }).overrideScope
          (lib.composeManyExtensions [
            pyproject-build-systems.overlays.default
            overlay
          ])
      );

    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs {
            inherit system;
            config.allowUnfree = true;
          };

          # Local claude-code package (update via nix/claude-code/update.sh)
          claude-code = pkgs.callPackage ./nix/claude-code/package.nix { };

          # Python set with editable overlay for development
          pythonSet = pythonSets.${system}.overrideScope editableOverlay;

          # Virtual environment with all dependencies (including dev extras)
          virtualenv = pythonSet.mkVirtualEnv "deepwork-dev-env" workspace.deps.all;
        in
        {
          default = pkgs.mkShell {
            packages = [
              virtualenv
              pkgs.uv
              pkgs.git
              pkgs.jq
              claude-code
              pkgs.gh
            ];

            env = {
              # Prevent uv from managing packages (Nix handles it)
              UV_NO_SYNC = "1";
              UV_PYTHON = "${pythonSet.python}/bin/python";
              UV_PYTHON_DOWNLOADS = "never";
              DEEPWORK_DEV = "1";
            };

            shellHook = ''
              # Required for editable overlay
              unset PYTHONPATH
              export REPO_ROOT=$(git rev-parse --show-toplevel)

              # Add nix/ scripts to PATH (for 'update' command)
              export PATH="$PWD/nix:$PATH"

              # Only show welcome message in interactive shells
              if [[ $- == *i* ]]; then
                echo ""
                echo "DeepWork Development Environment (uv2nix)"
                echo "=========================================="
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
        }
      );

      # Package output - virtual environment with default deps only
      packages = forAllSystems (system:
        let
          pkg = pythonSets.${system}.mkVirtualEnv "deepwork-env" workspace.deps.default;
        in {
          default = pkg;
          deepwork = pkg;  # Alias for backwards compatibility
        }
      );

      # Make deepwork runnable with 'nix run'
      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/deepwork";
        };
      });
    };
}
