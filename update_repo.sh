#!/bin/sh

[ -z "$REPOS_TO_UPDATE" ] && REPOS_TO_UPDATE="current-release/current/dom0/fc* r1/current/dom0-upgrade-r2 current-release/current/vm/* current-release/current-testing/dom0/fc* current-release/current-testing/vm/*"

# $1 -- path to rpm dir
check_repo()
{
    if [ "x$SKIP_REPO_CHECK" = "x1" ]; then
        return 0
    fi
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
    OPTS=
    [ -r "$1/comps.xml" ] && OPTS="-g comps.xml"
    createrepo $OPTS --update -x 'fc*/*' -o $1 $1 >/dev/null
}

is_repo_empty() {
    ls $1/rpm/*.rpm > /dev/null 2>&1 || return 0
    return 1
}

for repo in $REPOS_TO_UPDATE ; do
    echo "--> Processing repo: $repo..."
    if ! is_repo_empty $repo ; then
        check_repo $repo/rpm || exit 1
    fi
    update_repo $repo || exit 1
done
echo Done.

#yum clean metadata
