#!/usr/bin/env bash
# Update claude-code package to latest npm version
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Get versions
OLD_VERSION=$(grep 'version = "' package.nix | head -1 | sed 's/.*version = "\([^"]*\)".*/\1/')
VERSION=$(npm view @anthropic-ai/claude-code version 2>/dev/null)

if [[ "$VERSION" == "$OLD_VERSION" ]]; then
    echo "Already at latest version: $OLD_VERSION"
    exit 0
fi

echo "Updating claude-code: $OLD_VERSION -> $VERSION"

# Download tarball
TARBALL_URL="https://registry.npmjs.org/@anthropic-ai/claude-code/-/claude-code-${VERSION}.tgz"
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

curl -sL "$TARBALL_URL" -o "$TMPDIR/claude-code.tgz"

# Extract and compute source hash
mkdir -p "$TMPDIR/src"
tar -xzf "$TMPDIR/claude-code.tgz" -C "$TMPDIR/src" --strip-components=1
SRC_HASH=$(nix hash path "$TMPDIR/src")

# Get package-lock.json from tarball
if [[ -f "$TMPDIR/src/package-lock.json" ]]; then
    cp "$TMPDIR/src/package-lock.json" package-lock.json
else
    echo "Error: No package-lock.json in tarball"
    exit 1
fi

# Compute npmDepsHash using prefetch-npm-deps
NPM_DEPS_HASH=$(nix shell nixpkgs#prefetch-npm-deps -c prefetch-npm-deps package-lock.json 2>/dev/null)

# Update package.nix
sed -i "s/version = \"[^\"]*\"/version = \"$VERSION\"/" package.nix
sed -i "s|hash = \"sha256-[^\"]*\"|hash = \"$SRC_HASH\"|" package.nix
sed -i "s|npmDepsHash = \"sha256-[^\"]*\"|npmDepsHash = \"$NPM_DEPS_HASH\"|" package.nix

echo "Updated to version $VERSION"
echo "  Source hash: $SRC_HASH"
echo "  Deps hash: $NPM_DEPS_HASH"
