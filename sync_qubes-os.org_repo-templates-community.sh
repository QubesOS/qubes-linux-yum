#!/bin/sh

pushd `dirname $0`

#DRY="-n"
HOST=yum.qubes-os.org
if [ -n "$1" ]; then
    RELS_TO_SYNC=`basename "$1"`
else
    RELS_TO_SYNC="`readlink current-release|tr -d /`"
fi
REPOS_TO_SYNC="templates-community"

for rel in $RELS_TO_SYNC; do

    for repo in $REPOS_TO_SYNC; do
        echo
        echo "Syncing $rel/$repo..."
        rsync $DRY --partial --progress -air $rel/$repo/repodata $USERNAME@$HOST:/var/www/yum.qubes-os.org/$rel/$repo/
    done

done

popd
