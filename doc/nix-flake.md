# Using DeepWork with Nix Flakes

DeepWork provides a Nix flake for reproducible development environments and easy installation. This document covers how to use the flake in various scenarios.

## Prerequisites

- Nix with flakes support enabled
- Add to your `~/.config/nix/nix.conf`:
  ```
  experimental-features = nix-command flakes
  ```

## Development Environment

### Quick Start with direnv (Recommended)

direnv automatically activates the Nix environment when you enter the directory:

```bash
# Clone the repository
git clone https://github.com/Unsupervisedcom/deepwork.git
cd deepwork

# Allow direnv to load the environment
direnv allow

# Environment activates automatically!
```

The `.envrc` file is already configured with `use flake`, so you'll get:
- Python 3.11
- uv package manager
- All development dependencies (pytest, ruff, mypy)
- Automatic virtual environment activation
- Environment variables set (`PYTHONPATH`, `DEEPWORK_DEV=1`)

### Manual Activation

If you don't use direnv:

```bash
# Enter development shell
nix develop

# Or use the legacy command
nix-shell
```

### What's Included

The development environment provides:

- **Python 3.11** with pip and virtualenv
- **uv** - Fast Python package installer
- **Git** - Version control
- **jq** - JSON processing
- **Python packages**:
  - jinja2, pyyaml, gitpython
  - pytest, pytest-mock, pytest-cov
  - click, rich
- **Development tools**:
  - ruff - Python linter and formatter
  - mypy - Static type checker

## Installing DeepWork

### From the Flake

Install deepwork system-wide or in your user profile:

```bash
# Install to your user profile
nix profile install github:Unsupervisedcom/deepwork

# Verify installation
deepwork --help
```

### Running Without Installing

```bash
# Run deepwork directly
nix run github:Unsupervisedcom/deepwork -- --help

# Run a specific command
nix run github:Unsupervisedcom/deepwork -- install --platform claude
```

### Building the Package

```bash
# Build the package
nix build github:Unsupervisedcom/deepwork

# Result will be in ./result/
ls -la result/bin/deepwork
```

## Using in Your Project

DeepWork can be added to your existing Nix flake using a GitHub reference. This allows you to use DeepWork in your development environment or as a dependency for your projects.

### As a Development Dependency

Create a `flake.nix` in your project that references DeepWork via GitHub:

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # Add DeepWork via GitHub reference
    deepwork.url = "github:Unsupervisedcom/deepwork";
  };

  outputs = { self, nixpkgs, deepwork }:
    let
      system = "x86_64-linux"; # or your system
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          deepwork.packages.${system}.default
        ];
      };
    };
}
```

You can also pin to a specific version, tag, or commit:

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # Pin to a specific tag
    deepwork.url = "github:Unsupervisedcom/deepwork/0.3.0";
    # Or pin to a specific commit
    # deepwork.url = "github:Unsupervisedcom/deepwork/abc1234";
    # Or pin to a specific branch
    # deepwork.url = "github:Unsupervisedcom/deepwork/main";
  };

  outputs = { self, nixpkgs, deepwork }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          deepwork.packages.${system}.default
        ];
      };
    };
}
```

### As a Runtime Dependency

If you're building a Nix package that depends on DeepWork:

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # Add DeepWork as a dependency via GitHub reference
    deepwork.url = "github:Unsupervisedcom/deepwork";
  };

  outputs = { self, nixpkgs, deepwork }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in {
      packages.${system}.default = pkgs.stdenv.mkDerivation {
        name = "my-project";
        buildInputs = [
          deepwork.packages.${system}.default
        ];
      };
    };
}
```

### Using with flake-utils for Multi-System Support

For projects that need to support multiple systems (Linux, macOS, etc.):

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    # Add DeepWork via GitHub reference
    deepwork.url = "github:Unsupervisedcom/deepwork";
  };

  outputs = { self, nixpkgs, flake-utils, deepwork }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            deepwork.packages.${system}.default
          ];
        };
      }
    );
}
```

### Complete Example with direnv

Create a complete development environment with DeepWork and direnv:

**flake.nix:**
```nix
{
  description = "My project using DeepWork";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # Reference DeepWork from GitHub
    deepwork.url = "github:Unsupervisedcom/deepwork";
  };

  outputs = { self, nixpkgs, deepwork }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          # Include DeepWork in the development environment
          deepwork.packages.${system}.default
          # Add other dependencies
          pkgs.python311
          pkgs.git
        ];

        shellHook = ''
          echo "DeepWork is available!"
          deepwork --version
        '';
      };
    };
}
```

**.envrc:**
```bash
use flake
```

Then run:
```bash
direnv allow
# Environment with DeepWork loads automatically
```

## Flake Outputs

The flake provides several outputs:

### devShells.default

Development environment with all tools and dependencies.

```bash
nix develop
```

### packages.default / packages.deepwork

The deepwork Python package.

```bash
nix build
nix build .#deepwork
```

### apps.default

Runnable deepwork application.

```bash
nix run
nix run .#default -- --help
```

## Updating Dependencies

### Update nixpkgs

```bash
# Update the flake lock file
nix flake update

# Or update just nixpkgs
nix flake lock --update-input nixpkgs
```

### Update Python Dependencies

Python dependencies are managed by `uv` and `pyproject.toml`:

```bash
# Inside the development environment
nix develop
uv sync
```

## Troubleshooting

### Flakes Not Enabled

If you get an error about flakes not being recognized:

```bash
# Add to ~/.config/nix/nix.conf
echo "experimental-features = nix-command flakes" >> ~/.config/nix/nix.conf
```

### Hooks Working with Different Installation Methods

DeepWork hooks use the `deepwork hook` CLI command, which works consistently regardless of how deepwork was installed:

**Installation Methods Supported:**
- Nix flake (`nix profile install github:Unsupervisedcom/deepwork`)
- pipx (`pipx install deepwork`)
- uv (`uv tool install deepwork`)
- pip (`pip install deepwork`)

**How it Works:**

The hook wrapper scripts (`.deepwork/hooks/claude_hook.sh`, `.gemini/hooks/gemini_hook.sh`) call:
```bash
deepwork hook rules_check
```

Instead of the old approach:
```bash
python -m deepwork.hooks.rules_check  # ❌ Doesn't work with all install methods
```

**Requirements:**
1. The `deepwork` command must be in your PATH
2. For Nix flake users: Install with `nix profile install github:Unsupervisedcom/deepwork`
3. For pipx users: Install with `pipx install deepwork`
4. For uv users: Install with `uv tool install deepwork`

All these methods ensure `deepwork` is available globally, so hooks work correctly outside of development environments.

### direnv Not Working

1. Make sure direnv is installed:
   ```bash
   nix-env -i direnv
   ```

2. Add the hook to your shell rc file:
   ```bash
   # For bash (~/.bashrc)
   eval "$(direnv hook bash)"
   
   # For zsh (~/.zshrc)
   eval "$(direnv hook zsh)"
   ```

3. Allow the directory:
   ```bash
   direnv allow
   ```

### Environment Variables Not Set

If `PYTHONPATH` or `DEEPWORK_DEV` are not set:

```bash
# Manually source the hook
source .envrc
```

Or ensure you're in the Nix environment:

```bash
nix develop
```

## Additional Resources

- [Nix Flakes Documentation](https://nixos.wiki/wiki/Flakes)
- [direnv Documentation](https://direnv.net/)
- [DeepWork Contributing Guide](../CONTRIBUTING.md)
- [DeepWork Architecture](./architecture.md)
