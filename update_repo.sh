#!/bin/sh --

usage () {
    printf 'Usage: %q RELEASE REPOSITORIES\n' "$1">&2
    shift
    printf 'Arguments received:'>&2
    printf ' %q' "$@">&2
    echo>&2
    exit 1
}

set -eu

if [ $# -lt 2 ]; then
    echo 'update_repo.sh: must have at least 2 arguments'>&2
    usage "$0" "$@"
elif [ -z "$1" ]; then
    echo 'current-release must be specified'>&2
    usage "$0" "$@"
fi
current_release=$1
shift

[[ "$current_release" =~ ^r[1-9]([.-][0-9a-z]*)?$ ]] || {
    printf 'Bad release %q\n' "$current_release">&2
    usage "$0" "$@"
}

createrepo=$(which createrepo_c createrepo 2>/dev/null|head -n 1)

if [ -z "$createrepo" ]; then
    echo "ERROR: createrepo not found"
    exit 1
fi

RPM_OPTS=
if [ "x${NO_SIGN=0}" = x1 ]; then
    # If we are told not to sign anything, then unsigned RPMs are expected.
    SKIP_REPO_CHECK=1
elif [ "x${SKIP_REPO_CHECK=0}" != x1 ]; then
    if [ -d "$BUILDER_DIR/keyrings/rpmdb" ]; then
        RPM_OPTS="$RPM_OPTS --dbpath=$BUILDER_DIR/keyrings/rpmdb"
    fi
fi

# $1 -- path to rpm dir
check_repo()
{
    if [ "x$SKIP_REPO_CHECK" = "x1" ]; then
        return 0
    fi

    RPM_VERSION="$(rpm --version | awk '{print $3}')"

    if [ "$(printf '%s\n' "$RPM_VERSION" "4.14.0" | sort -V | head -n1)" = "4.14.0" ]; then
        PGP_NOTSIGNED='signatures OK'
    else
        PGP_NOTSIGNED='pgp'
    fi

    if rpm $RPM_OPTS --checksig $1/*.rpm | grep -v "$PGP_NOTSIGNED" > /dev/null ; then
        echo "ERROR: There are unsigned RPM packages in $1 repo:"
        echo "---------------------------------------"
        rpm $RPM_OPTS --checksig $1/*.rpm | grep -v "$PGP_NOTSIGNED"
        echo "---------------------------------------"
        echo "Sign them before proceeding."
        exit 1
    fi
}

update_repo()
{
    local OPTS= tosign sign_key

    # If we are told to not sign anything, we don’t bother generating metadata.
    # Unsigned metadata will be rejected anyway, so generating it is wasteful.
    # Furthermore, it risks clobbering signed metadata that already exists.
    if [ "x$NO_SIGN" != x1 ]; then
        if [ "x${SIGN_KEY+test}" = xtest ]; then
            sign_key=$SIGN_KEY
        else
            sign_key=$(rpm --eval '%{?_gpg_name:%_gpg_name}') || return
        fi
        if [ -n "$sign_key" ]; then
            if [ -z "${GNUPG-}" ]; then
                GNUPG=$(rpm --eval '%{?__gpg:%__gpg}') || return
            fi
            [ -r "$1/comps.xml" ] && OPTS="-g comps.xml"
            "$createrepo" $OPTS --update -x 'fc*/*' -o "$1" -- "$1" >/dev/null || return
            "$GNUPG" --detach-sign --output=- --armor "--local-user=$sign_key" \
            -- "$1/repodata/repomd.xml" > "$1/repodata/repomd.xml.asc" || return
        fi
    fi
}

is_repo_not_empty() {
    ls -- "$1/rpm"/*.rpm > /dev/null 2>&1
}

for repo; do
    printf '%c-> Processing repo: %q...\n' - "$repo"
    if is_repo_not_empty "$repo" ; then
        check_repo "$repo/rpm" || exit 1
    fi
    update_repo "$repo" || exit 1
done
echo Done.
