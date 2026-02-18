{
  description = "DeepWork - Framework for enabling AI agents to perform complex, multi-step work tasks";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    # Claude Code with pre-built native binaries (hourly updates)
    claude-code-nix.url = "github:sadjow/claude-code-nix";

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

  outputs = { self, nixpkgs, claude-code-nix, pyproject-nix, uv2nix, pyproject-build-systems, ... }:
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
              claude-code-nix.packages.${system}.default
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
                echo "  claude             Claude Code CLI"
                echo "  gh                 GitHub CLI"
                echo ""
              fi
            '';
          };
        }
      );

      # Package output - wrapped deepwork binary with isolated Python environment
      # When consumed as a dependency in other flakes, the consuming devShell may
      # include Python packages for a different version (e.g. python3.13 from
      # azure-cli, awscli2). These pollute PYTHONPATH and cause symbol errors
      # when deepwork's python3.11 tries to load python3.13 native extensions.
      # Wrapping with --unset PYTHONPATH isolates deepwork from the host environment.
      packages = forAllSystems (system:
        let
          pkgs = import nixpkgs {
            inherit system;
            config.allowUnfree = true;
          };
          venv = pythonSets.${system}.mkVirtualEnv "deepwork-env" workspace.deps.default;
          wrapped = pkgs.runCommand "deepwork-wrapped" {
            nativeBuildInputs = [ pkgs.makeWrapper ];
          } ''
            mkdir -p $out/bin
            makeWrapper ${venv}/bin/deepwork $out/bin/deepwork \
              --unset PYTHONPATH
          '';
        in {
          default = wrapped;
          deepwork = wrapped;  # Alias for backwards compatibility
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
