#!/bin/sh

pushd `dirname $0`

#DRY="-n"
USERNAME=joanna
HOST=yum.qubes-os.org
RELS_TO_SYNC="`readlink current-release|tr -d /`"
REPOS_TO_SYNC="current current-testing security-testing"

for rel in $RELS_TO_SYNC; do

    rsync_args=
    for repo in $REPOS_TO_SYNC; do
        rsync_args="$rsync_args $rel/$repo"
    done
    echo "Syncing $rel..."
    rsync $DRY --partial --progress --hard-links --exclude repodata -air $rsync_args $USERNAME@$HOST:/var/www/yum.qubes-os.org/$rel/
    rsync $DRY update_repo.sh update_repo-arg.sh $USERNAME@$HOST:
    for repo in $REPOS_TO_SYNC; do
        [ -z "$DRY" ] && ssh $USERNAME@$HOST ./update_repo-arg.sh "/var/www/yum.qubes-os.org/$rel/$repo/dom0/fc*" "/var/www/yum.qubes-os.org/$rel/$repo/vm/fc*"
    done

done

popd
