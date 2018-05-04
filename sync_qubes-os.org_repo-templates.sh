#!/bin/sh

pushd `dirname $0`

usage() {
    echo "Usage: $0 <RELEASE> <REPOS>"
    echo "<RELEASE>: r2, r3.0"
    echo "<REPOS>: templates-community, templates-itl"
    exit 1
}

#DRY="-n"
[ "x$HOST" == "x" ] && HOST=yum.qubes-os.org
[ "x$HOST_BASEDIR" == "x" ] && HOST_BASEDIR=/pub/qubes/repo/yum
if [ -n "$1" ]; then
    RELS_TO_SYNC=`basename "$1"`
    shift
else
    usage
fi
REPOS_TO_SYNC="$*"

if [ -z "$REPOS_TO_SYNC" ]; then
    usage
fi

for rel in $RELS_TO_SYNC; do

    rsync_args=
    for repo in $REPOS_TO_SYNC; do
        rsync_args="$rsync_args $rel/$repo"
    done
    echo "Syncing $rel..."
    rsync $DRY --partial --progress --hard-links --exclude repodata -air $rsync_args $HOST:$HOST_BASEDIR/$rel/
    rsync $DRY update_repo.sh update_repo-arg.sh mirrors.list $HOST:
    for repo in $REPOS_TO_SYNC; do
        [ -z "$DRY" ] && ssh $HOST sh -c "\"cd $HOST_BASEDIR; ~/update_repo-arg.sh $rel/$repo\""
    done

done

popd
