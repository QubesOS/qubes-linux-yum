#!/bin/sh

if [ -n "$1" ]; then
    current_release=$1
else
    current_release=current-release
fi

if [ -z "$REPOS_TO_UPDATE" ]; then
    REPOS_TO_UPDATE="r1/current/dom0-upgrade-r2"
    REPOS_TO_UPDATE="$REPOS_TO_UPDATE $current_release/current/dom0/fc* $current_release/current/vm/*"
    REPOS_TO_UPDATE="$REPOS_TO_UPDATE $current_release/current-testing/dom0/fc* $current_release/current-testing/vm/*"
fi

mkmetalink=$(which mkmetalink)
mirrors_list=$(realpath "$(dirname "$0")/mirrors.list")

# $1 -- path to rpm dir
check_repo()
{
    RPM_VERSION="$(rpm --version | awk '{print $3}')"

    if [ "$(printf '%s\n' "$RPM_VERSION" "4.14.0" | sort -V | head -n1)" == "4.14.0" ]; then
        PGP_NOTSIGNED='signatures OK'
    else
        PGP_NOTSIGNED='pgp'
    fi

    if [ "x$SKIP_REPO_CHECK" = "x1" ]; then
        return 0
    fi
    if rpm --checksig $1/*.rpm | grep -v "$PGP_NOTSIGNED" > /dev/null ; then
        echo "ERROR: There are unsigned RPM packages in $1 repo:"
        echo "---------------------------------------"
        rpm --checksig $1/*.rpm | grep -v "$PGP_NOTSIGNED"
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
    if [ -x "$mkmetalink" -a -r "$mirrors_list" ]; then
        $mkmetalink $mirrors_list "$1/repodata/repomd.xml" \
            > "$1/repodata/repomd.xml.metalink"
    fi
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
