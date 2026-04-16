#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYPROJECT="$REPO_ROOT/pyproject.toml"

usage() {
    echo "Usage: $0 <tag>  (e.g. $0 v0.6.0)"
    exit 1
}

[[ $# -ne 1 ]] && usage

TAG="$1"

if [[ ! "$TAG" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: tag must match pattern v<major>.<minor>.<patch>, e.g. v0.6.0 or v1.2.3"
    exit 1
fi

VERSION="${TAG#v}"
REMOTE="${REMOTE:-origin}"

require_clean_main() {
    local current_branch
    current_branch="$(git branch --show-current)"

    if [[ "$current_branch" != "main" ]]; then
        echo "Error: release must be run from the main branch"
        exit 1
    fi

    if [[ -n "$(git status --short)" ]]; then
        echo "Error: working tree must be clean before releasing"
        exit 1
    fi

    git fetch "$REMOTE" main >/dev/null 2>&1

    local local_head remote_head
    local_head="$(git rev-parse HEAD)"
    remote_head="$(git rev-parse "$REMOTE/main")"
    if [[ "$local_head" != "$remote_head" ]]; then
        echo "Error: local main must match $REMOTE/main before releasing"
        exit 1
    fi
}

confirm_tag_overwrite() {
    local existing_refs="$1"
    local answer

    echo "Warning: tag '$TAG' already exists in:"
    printf '%s\n' "$existing_refs"
    read -r -p "Overwrite tag '$TAG' locally and on $REMOTE? [y/N] " answer
    case "$answer" in
        y|Y|yes|YES)
            return 0
            ;;
        *)
            echo "Release cancelled"
            exit 1
            ;;
    esac
}

prepare_tag() {
    local existing_refs=()

    if git rev-parse --verify "refs/tags/$TAG" >/dev/null 2>&1; then
        existing_refs+=("local tag")
    fi

    if git ls-remote --exit-code --tags "$REMOTE" "refs/tags/$TAG" >/dev/null 2>&1; then
        existing_refs+=("remote tag on $REMOTE")
    fi

    if [[ ${#existing_refs[@]} -eq 0 ]]; then
        return 0
    fi

    confirm_tag_overwrite "$(printf '%s\n' "${existing_refs[@]}")"

    if git rev-parse --verify "refs/tags/$TAG" >/dev/null 2>&1; then
        git tag -d "$TAG" >/dev/null
    fi

    if git ls-remote --exit-code --tags "$REMOTE" "refs/tags/$TAG" >/dev/null 2>&1; then
        git push "$REMOTE" ":refs/tags/$TAG"
    fi
}

sed_inplace() {
    local expr="$1"
    local file="$2"

    if [[ "$(uname -s)" == "Darwin" ]]; then
        sed -i '' -e "$expr" "$file"
    else
        sed -i -e "$expr" "$file"
    fi
}

cd "$REPO_ROOT"
require_clean_main
prepare_tag

echo "Updating $PYPROJECT version to $VERSION ..."
sed_inplace "s/^version = \"[^\"]*\"/version = \"$VERSION\"/" "$PYPROJECT"

git add pyproject.toml
git commit -m "bump version to $VERSION"
git tag "$TAG"
git push "$REMOTE" main
git push "$REMOTE" "$TAG"

echo "Done: pyproject.toml updated to $VERSION, committed, tagged $TAG, and pushed to $REMOTE"
