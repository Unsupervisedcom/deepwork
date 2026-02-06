#!/usr/bin/env bash
set -euo pipefail

# Test the Homebrew formula against a local build of deepwork
# Usage: ./scripts/test-homebrew.sh [path-to-homebrew-tap]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
HOMEBREW_TAP="${1:-$REPO_DIR/../homebrew-deepwork}"

if [[ ! -f "$HOMEBREW_TAP/Formula/deepwork.rb" ]]; then
    echo "Error: homebrew-deepwork tap not found at $HOMEBREW_TAP"
    echo "Usage: $0 [path-to-homebrew-tap]"
    exit 1
fi

echo "==> Building deepwork from $REPO_DIR"
cd "$REPO_DIR"

# Clean previous builds
rm -rf dist/

# Build the sdist tarball
uv build --sdist

# Find the built tarball
TARBALL=$(ls dist/deepwork-*.tar.gz | head -1)
if [[ ! -f "$TARBALL" ]]; then
    echo "Error: No tarball found in dist/"
    exit 1
fi

VERSION=$(basename "$TARBALL" | sed 's/deepwork-\(.*\)\.tar\.gz/\1/')
SHA256=$(shasum -a 256 "$TARBALL" | awk '{print $1}')
TARBALL_PATH="$(cd "$(dirname "$TARBALL")" && pwd)/$(basename "$TARBALL")"

echo "==> Built deepwork-$VERSION"
echo "    Tarball: $TARBALL_PATH"
echo "    SHA256:  $SHA256"

# Set up a local tap with the modified formula
TAP_NAME="local/deepwork-test"
TAP_DIR="$(brew --repository)/Library/Taps/local/homebrew-deepwork-test"

echo "==> Cleaning up previous installation..."
brew uninstall deepwork 2>/dev/null || true

echo "==> Setting up local tap..."
brew untap "$TAP_NAME" 2>/dev/null || true
brew tap-new --no-git "$TAP_NAME"

sed -e "s|url \"https://.*\"|url \"file://$TARBALL_PATH\"|" \
    -e "s|sha256 \".*\"|sha256 \"$SHA256\"|" \
    "$HOMEBREW_TAP/Formula/deepwork.rb" > "$TAP_DIR/Formula/deepwork.rb"

echo "==> Installing from local build..."
brew install --verbose "$TAP_NAME/deepwork"

echo "==> Running brew test..."
brew test "$TAP_NAME/deepwork"

echo "==> Verifying binary..."
deepwork --version
deepwork --help | head -5

echo "==> All tests passed for deepwork-$VERSION (local build)"
