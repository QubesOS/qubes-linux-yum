#!/bin/bash --
set -eu
default_repos='current current-testing security-testing'
usage () {
    printf %s\\n "Usage: $0 RELEASE REPOS_TO_SYNC..." >&2
    exit 1
}

dir=$(dirname "$0")
pushd "$dir"

#DRY="-n"
if [ "x${DRY+q}" = xq ] && [ "x$DRY" != x-n ]; then
    echo 'Bad value for $DRY (must be -n or unset)'>&2
    usage
fi

: "${DRY=}"

[ "x${HOST-}" == "x" ] && HOST=yum.qubes-os.org
if [[ ${#HOST} -gt 253 ]] || ! [[ "$HOST" =~ ^[A-Za-z0-9][A-Za-z0-9.-]+$ ]]; then
    printf 'Invalid host %q\n' "$HOST">&2
    usage
fi
[ "x${HOST_BASEDIR-}" == "x" ] && HOST_BASEDIR=/pub/qubes/repo/yum
if ! [[ "$HOST_BASEDIR" =~ ^/[A-Za-z0-9/._-]+$ ]]; then
    printf 'Invalid HOST_BASEDIR: %q\n' "$HOST_BASEDIR">&2
    usage
elif [ -n "${1-}" ]; then
    rel=$(basename "$1")
    shift
else
    echo 'Release must be specified'>&2
    usage
fi
[[ "$rel" =~ ^r[1-9]([.-][0-9a-z]*)?$ ]] || {
    printf 'Bad release %q\n' "$rel">&2
    usage
}

for i; do
    if ! [[ "$i" =~ ^[A-Za-z][A-Za-z0-9/._-]*$ ]]; then
        echo "Invalid character in repository">&2
        usage
    fi
done

export PATH=/usr/bin:/bin

echo "Syncing $rel..."
ssh -- "$HOST" "cd -- '$HOST_BASEDIR' && exec mkdir -p -- $*"
for i; do
    rsync $DRY --partial --progress --hard-links -air -- "./$i" "$HOST:$HOST_BASEDIR/${i%/*}"
done
rsync $DRY -- update_repo.sh mirrors.list "$HOST:"
[ -z "$DRY" ] && ssh -- "$HOST" "cd -- '$HOST_BASEDIR' && for i in $*; do \
    mkmetalink -- ~/mirrors.list \"\$i/repodata/repomd.xml\" \
    > \"\$i/repodata/repomd.xml.metalink\"; done"
