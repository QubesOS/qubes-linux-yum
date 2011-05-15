#!/bin/sh

DRY="-n"
HOST=yum.qubes-os.org


echo "Syncing repos to remote host $HOST..."
rsync $DRY --delete --partial --progress -air r1-beta1/current/* joanna@$HOST:/var/www/yum.qubes-os.org/r1-beta1/current/
rsync $DRY --delete --partial --progress -air r1-beta1/current-testing/* joanna@$HOST:/var/www/yum.qubes-os.org/r1-beta1/current-testing/

