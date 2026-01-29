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

# Create a temporary formula pointing to the local tarball
TEMP_FORMULA=$(mktemp)
trap "rm -f $TEMP_FORMULA" EXIT

sed -e "s|url \"https://.*\"|url \"file://$TARBALL_PATH\"|" \
    -e "s|sha256 \".*\"|sha256 \"$SHA256\"|" \
    "$HOMEBREW_TAP/Formula/deepwork.rb" > "$TEMP_FORMULA"

echo "==> Installing from local build..."
brew uninstall deepwork 2>/dev/null || true
brew install --verbose "$TEMP_FORMULA"

echo "==> Running brew test..."
brew test deepwork

echo "==> Verifying binary..."
deepwork --version
deepwork --help | head -5

echo "==> All tests passed for deepwork-$VERSION (local build)"
