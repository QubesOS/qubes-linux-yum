#!/bin/sh

REPOS_TO_UPDATE="$1/templates-itl $1/templates-community"

. `dirname $0`/update_repo.sh

if [ "$AUTOMATIC_UPLOAD" = 1 ]; then
    `dirname $0`/sync_qubes-os.org_repo-templates.sh "$1" "templates-itl" "templates-community"
fi
