#!/bin/sh

pushd `dirname $0`

#DRY="-n"
USERNAME=marmarek
HOST=yum.qubes-os.org
RELS_TO_SYNC="`readlink current-release|tr -d /`"
REPOS_TO_SYNC="unstable"

for rel in $RELS_TO_SYNC; do

    for repo in $REPOS_TO_SYNC; do
        echo
        echo "Syncing $rel/$repo..."
        rsync $DRY --partial --progress --exclude repodata -air $rel/$repo/* $USERNAME@$HOST:/var/www/yum.qubes-os.org/$rel/$repo/
        rsync $DRY update_repo.sh update_repo-arg.sh $USERNAME@$HOST:
        [ -z "$DRY" ] && ssh $USERNAME@$HOST ./update_repo-arg.sh "/var/www/yum.qubes-os.org/$rel/$repo/dom0/fc*" "/var/www/yum.qubes-os.org/$rel/$repo/vm/fc*"
    done

done

popd
