{
  description = "DeepWork - Framework for enabling AI agents to perform complex, multi-step work tasks";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    # Claude Code with pre-built native binaries (hourly updates)
    claude-code-nix.url = "github:sadjow/claude-code-nix";
  };

  outputs = { self, nixpkgs, claude-code-nix, ... }:
    let
      inherit (nixpkgs) lib;
      forAllSystems = lib.genAttrs [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
    in
    {
      devShells = forAllSystems (system:
        let
          pkgs = import nixpkgs {
            inherit system;
            config.allowUnfree = true;
          };
        in
        let
          claude-code = claude-code-nix.packages.${system}.default;
          # Wrapper that auto-loads project plugin dirs.
          # References the real binary by store path to avoid circular PATH lookup.
          claude-wrapper = pkgs.writeShellScriptBin "claude" ''
            exec ${claude-code}/bin/claude \
              --plugin-dir "$(git rev-parse --show-toplevel)/plugins/claude" \
              --plugin-dir "$(git rev-parse --show-toplevel)/learning_agents" \
              "$@"
          '';
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.python311
              pkgs.uv
              pkgs.git
              pkgs.jq
              claude-wrapper
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
                echo "  claude             Claude Code CLI"
                echo "  gh                 GitHub CLI"
                echo ""
              fi
            '';
          };
        }
      );
    };
}
