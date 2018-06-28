#!/bin/sh

REPOS_TO_UPDATE="$1/templates-itl $1/templates-community"
script_basename=$(basename "$0")
script_basename="${script_basename%.sh}"
if [ "$script_basename" != "update_repo-template" ]; then
    # get repository name from $0
    REPOS_TO_UPDATE="$1/${script_basename#update_repo-}"
    echo "$REPOS_TO_UPDATE" >&2
fi

. `dirname $0`/update_repo.sh

if [ "$AUTOMATIC_UPLOAD" = 1 ]; then
    `dirname $0`/sync_qubes-os.org_repo-templates.sh "$1" "templates-itl" "templates-community"
fi
