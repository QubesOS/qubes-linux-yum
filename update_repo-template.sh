#!/bin/bash --
set -eu
[[ "${1-}" =~ ^r[1-9]([.-][0-9a-z]*)?$ ]] || {
    printf %s\\n "Usage: $0 RELEASE [ignored bogus repo names...]">&2
    exit 1
}
REPOS_TO_UPDATE="$1/templates-itl $1/templates-community"
script_basename=$(basename "$0")
# .sh suffix is optional
script_basename="${script_basename%.sh}"
if [ "$script_basename" != "update_repo-template" ]; then
    if ! [[ "$script_basename" =~ ^update_repo-templates-[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
        printf 'Invalid template repository name %q, sorry\n' "$script_basename"
    fi
    # get repository name from $0
    REPOS_TO_UPDATE="$1/${script_basename#update_repo-}"
    echo "$REPOS_TO_UPDATE" >&2
fi

dir=$(dirname -- "$0") || exit
. "$dir/update_repo.sh" "$1" $REPOS_TO_UPDATE

if [ "${AUTOMATIC_UPLOAD-}" = 1 ]; then
    "$dir/sync_qubes-os.org_repo.sh" "$1" $REPOS_TO_UPDATE
fi
