#!/bin/sh

REPOS_TO_UPDATE="current-release/security-testing/dom0/fc* current-release/security-testing/vm/*"

. `dirname $0`/update_repo.sh

if [ "$AUTOMATIC_UPLOAD" = 1 ]; then
    `dirname $0`/sync_qubes-os.org_repo.sh
fi
