#!/bin/sh


# $1 -- path to rpm dir
check_repo()
{
    if rpm --checksig $1/*.rpm | grep -v pgp > /dev/null ; then
        echo "ERROR: There are unsigned RPM packages in $1 repo:"
        echo "---------------------------------------"
        rpm --checksig $1/*.rpm | grep -v pgp 
        echo "---------------------------------------"
        echo "Sign them before proceeding."
        exit 1
    fi
}


update_repo()
{
    createrepo --update $1
}


for repo in current-release/current/dom0 current-release/current/vm/* current-release/current-testing/dom0 current-release/current-testing/vm/* current-release/unstable/dom0 current-release/unstable/vm/*; do
    echo "--> Processing repo: $repo..."
    check_repo $repo/rpm -o $repo/repodata || exit 1
    update_repo $repo -o $repo/repodata || exit 1
done
echo Done.

#yum clean metadata
