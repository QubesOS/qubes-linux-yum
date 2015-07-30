#!/bin/sh

pushd `dirname $0`

#DRY="-n"
HOST=yum.qubes-os.org
HOST_BASEDIR=/pub/qubes/repo/yum
if [ -n "$1" ]; then
    RELS_TO_SYNC=`basename "$1"`
else
    RELS_TO_SYNC="`readlink current-release|tr -d /`"
fi
REPOS_TO_SYNC="unstable"

for rel in $RELS_TO_SYNC; do

    for repo in $REPOS_TO_SYNC; do
        echo
        echo "Syncing $rel/$repo..."
        rsync $DRY --partial --progress --exclude repodata -air $rel/$repo/* $HOST:/var/www/yum.qubes-os.org/$rel/$repo/
        rsync $DRY --partial --progress --exclude repodata -air $rel/$repo/* $HOST:$HOST_BASEDIR/$rel/$repo/
        rsync $DRY update_repo.sh update_repo-arg.sh $HOST:
        [ -z "$DRY" ] && ssh $HOST ./update_repo-arg.sh "$HOST_BASEDIR/$rel/$repo/dom0/fc*" "$HOST_BASEDIR/$rel/$repo/vm/fc*"
    done

done

popd
