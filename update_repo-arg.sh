#!/bin/sh

REPOS_TO_UPDATE="$@"
SKIP_REPO_CHECK="1"

. `dirname $0`/update_repo.sh
