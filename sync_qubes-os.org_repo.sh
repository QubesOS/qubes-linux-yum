#!/bin/sh

pushd `dirname $0`

#DRY="-n"
[ "x$HOST" == "x" ] && HOST=yum.qubes-os.org
[ "x$HOST_BASEDIR" == "x" ] && HOST_BASEDIR=/pub/qubes/repo/yum
if [ -n "$1" ]; then
    RELS_TO_SYNC=`basename "$1"`
else
    RELS_TO_SYNC="`readlink current-release|tr -d /`"
fi
REPOS_TO_SYNC="current current-testing security-testing"

for rel in $RELS_TO_SYNC; do

    rsync_args=
    for repo in $REPOS_TO_SYNC; do
        rsync_args="$rsync_args $rel/$repo"
    done
    echo "Syncing $rel..."
    rsync $DRY --partial --progress --hard-links --exclude repodata -air $rsync_args $HOST:$HOST_BASEDIR/$rel/
    rsync $DRY update_repo.sh update_repo-arg.sh mirrors.list $HOST:
    for repo in $REPOS_TO_SYNC; do
        [ -z "$DRY" ] && ssh $HOST sh -c "\"cd $HOST_BASEDIR; ~/update_repo-arg.sh $rel/$repo/dom0/fc* $rel/$repo/vm/*\""
    done

done

popd
