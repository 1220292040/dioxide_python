#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SETUP_PY="$REPO_ROOT/setup.py"

usage() {
    echo "Usage: $0 <tag>  (e.g. $0 v0.6)"
    exit 1
}

[[ $# -ne 1 ]] && usage

TAG="$1"

if [[ ! "$TAG" =~ ^v[0-9]+\.[0-9]+(\.[0-9]+)?$ ]]; then
    echo "Error: tag must match pattern v<major>.<minor>[.<patch>], e.g. v0.6 or v1.2.3"
    exit 1
fi

VERSION="${TAG#v}"

if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "Error: tag '$TAG' already exists"
    exit 1
fi

echo "Updating $SETUP_PY version to $VERSION ..."
sed -i "s/version=\"[^\"]*\"/version=\"$VERSION\"/" "$SETUP_PY"

cd "$REPO_ROOT"
git add setup.py
git commit -m "bump version to $VERSION"
git tag "$TAG"

echo "Done: setup.py updated to $VERSION, committed, and tagged $TAG"
