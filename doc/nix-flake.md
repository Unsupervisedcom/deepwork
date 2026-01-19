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

### As a Development Dependency

Create a `flake.nix` in your project that uses DeepWork:

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
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

### As a Runtime Dependency

If you're building a Nix package that depends on DeepWork:

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
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

## Backward Compatibility

The `shell.nix` file is still maintained for users who prefer the traditional approach:

```bash
nix-shell
```

This provides the same environment as `nix develop`, just using the legacy interface.

## Additional Resources

- [Nix Flakes Documentation](https://nixos.wiki/wiki/Flakes)
- [direnv Documentation](https://direnv.net/)
- [DeepWork Contributing Guide](../CONTRIBUTING.md)
- [DeepWork Architecture](./architecture.md)
