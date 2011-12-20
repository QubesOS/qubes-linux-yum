#!/bin/sh

DRY="-n"
HOST=yum.qubes-os.org
RELS_TO_SYNC="r1"
REPOS_TO_SYNC="current current-testing"

for rel in $RELS_TO_SYNC; do

    for repo in $REPOS_TO_SYNC; do
        echo
        echo "Syncing $rel/$repo..."
        rsync $DRY --delete --partial --progress -air $rel/$repo/* joanna@$HOST:/var/www/yum.qubes-os.org/$rel/$repo/
    done

done

