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
      forAllSystems = lib.genAttrs [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];

      # Load the uv workspace from uv.lock
      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      # Create overlay from uv.lock - prefer wheels for faster builds
      overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };

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
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.python311
              pkgs.uv
              pkgs.git
              pkgs.jq
              pkgs.gh
            ];

            env = {
              UV_PYTHON_DOWNLOADS = "never";
              DEEPWORK_DEV = "1";
            };

            shellHook = ''
              export REPO_ROOT=$(git rev-parse --show-toplevel)

              # Create project venv with deepwork + all dev deps (pytest, ruff, mypy, etc.)
              uv sync --extra dev --quiet 2>/dev/null || true
              export PATH="$REPO_ROOT/.venv/bin:$PATH"

              # Also register as a uv tool so `uvx deepwork serve` uses local source
              uv tool install -e "$REPO_ROOT" --quiet 2>/dev/null || true

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
                echo "  gh                 GitHub CLI"
                echo ""
              fi
            '';
          };
        }
      );

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
          deepwork = wrapped;
        }
      );

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/deepwork";
        };
      });
    };
}
