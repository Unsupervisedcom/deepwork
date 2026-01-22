#!/usr/bin/env bash
# Update claude-code package to latest version
#
# Usage:
#   ./update.sh          # Sync from nixpkgs (recommended)
#   ./update.sh --manual # Manual update from npm

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

sync_from_nixpkgs() {
    echo "Syncing claude-code package from nixpkgs..."

    NIXPKGS_URL="https://raw.githubusercontent.com/NixOS/nixpkgs/master/pkgs/by-name/cl/claude-code"

    # Fetch package.nix
    echo "Fetching package.nix..."
    curl -sL "$NIXPKGS_URL/package.nix" -o package.nix.new

    # Fetch package-lock.json
    echo "Fetching package-lock.json..."
    curl -sL "$NIXPKGS_URL/package-lock.json" -o package-lock.json.new

    # Extract version from new package.nix
    NEW_VERSION=$(grep 'version = "' package.nix.new | head -1 | sed 's/.*version = "\([^"]*\)".*/\1/')
    OLD_VERSION=$(grep 'version = "' package.nix | head -1 | sed 's/.*version = "\([^"]*\)".*/\1/')

    if [[ "$NEW_VERSION" == "$OLD_VERSION" ]]; then
        echo "Already at latest version: $OLD_VERSION"
        rm -f package.nix.new package-lock.json.new
        exit 0
    fi

    echo "Updating from $OLD_VERSION -> $NEW_VERSION"

    # Replace files, keeping our local header comment
    {
        echo "# Claude Code package - locally maintained for version control"
        echo "# Based on nixpkgs: https://github.com/NixOS/nixpkgs/tree/master/pkgs/by-name/cl/claude-code"
        echo "#"
        echo "# To update: Run ./update.sh from this directory"
        # Skip the nixpkgs-specific comment at the top and keep the rest
        tail -n +7 package.nix.new | head -n -3  # Skip comment and maintainers
        echo "  meta = {"
        echo "    description = \"Agentic coding tool that lives in your terminal, understands your codebase, and helps you code faster\";"
        echo "    homepage = \"https://github.com/anthropics/claude-code\";"
        echo "    downloadPage = \"https://www.npmjs.com/package/@anthropic-ai/claude-code\";"
        echo "    license = lib.licenses.unfree;"
        echo "    mainProgram = \"claude\";"
        echo "  };"
        echo "})"
    } > package.nix

    mv package-lock.json.new package-lock.json
    rm -f package.nix.new

    echo "Updated to version $NEW_VERSION"
    echo ""
    echo "Next steps:"
    echo "  1. Test: nix develop (from repo root)"
    echo "  2. Verify: claude --version"
    echo "  3. Commit the changes"
}

manual_update() {
    echo "Manual update from npm..."

    # Get latest version from npm
    echo "Fetching latest version from npm..."
    VERSION=$(npm view @anthropic-ai/claude-code version 2>/dev/null)
    OLD_VERSION=$(grep 'version = "' package.nix | head -1 | sed 's/.*version = "\([^"]*\)".*/\1/')

    if [[ "$VERSION" == "$OLD_VERSION" ]]; then
        echo "Already at latest version: $OLD_VERSION"
        exit 0
    fi

    echo "Updating from $OLD_VERSION -> $VERSION"

    # Download and compute hash
    TARBALL_URL="https://registry.npmjs.org/@anthropic-ai/claude-code/-/claude-code-${VERSION}.tgz"
    TMPDIR=$(mktemp -d)
    trap "rm -rf $TMPDIR" EXIT

    echo "Downloading tarball..."
    curl -sL "$TARBALL_URL" -o "$TMPDIR/claude-code.tgz"

    echo "Computing source hash..."
    # Unpack and compute nix hash
    mkdir -p "$TMPDIR/src"
    tar -xzf "$TMPDIR/claude-code.tgz" -C "$TMPDIR/src" --strip-components=1
    SRC_HASH=$(nix hash path "$TMPDIR/src" 2>/dev/null || nix-hash --type sha256 --base32 "$TMPDIR/src")

    # Extract package-lock.json from tarball if it exists
    if [[ -f "$TMPDIR/src/package-lock.json" ]]; then
        cp "$TMPDIR/src/package-lock.json" package-lock.json
        echo "Updated package-lock.json from tarball"
    else
        echo "Warning: No package-lock.json in tarball, fetching from nixpkgs..."
        curl -sL "https://raw.githubusercontent.com/NixOS/nixpkgs/master/pkgs/by-name/cl/claude-code/package-lock.json" -o package-lock.json
    fi

    # Update version and hash in package.nix
    sed -i "s/version = \"[^\"]*\"/version = \"$VERSION\"/" package.nix
    sed -i "s|hash = \"sha256-[^\"]*\"|hash = \"$SRC_HASH\"|" package.nix

    echo ""
    echo "Updated to version $VERSION"
    echo "Source hash: $SRC_HASH"
    echo ""
    echo "NOTE: You may need to update npmDepsHash manually."
    echo "Run 'nix develop' - if it fails with hash mismatch, update npmDepsHash with the correct value from the error."
    echo ""
    echo "Next steps:"
    echo "  1. Test: nix develop (from repo root)"
    echo "  2. Verify: claude --version"
    echo "  3. Commit the changes"
}

# Parse arguments
case "${1:-}" in
    --manual)
        manual_update
        ;;
    --help|-h)
        echo "Usage: $0 [--manual]"
        echo ""
        echo "Options:"
        echo "  (default)  Sync package from nixpkgs (recommended)"
        echo "  --manual   Update directly from npm (requires computing hashes)"
        ;;
    *)
        sync_from_nixpkgs
        ;;
esac
