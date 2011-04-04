#!/bin/sh

DRY="-n"
HOST=yum.qubes-os.org


echo "Syncing repos to remote host $HOST..."
rsync $DRY --delete --partial --progress --exclude=*.sh -air * joanna@$HOST:/var/www/yum.qubes-os.org/

