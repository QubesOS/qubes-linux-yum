usage () {
    printf 'Usage: %q RELEASE REPOSITORIES\n' "$1">&2
    shift
    printf 'Arguments received:'>&2
    printf ' %q' "$@">&2
    echo>&2
    exit 1
}

set -eu
[[ "$#" -ge 2 ]] && [[ "$2" =~ ^r[1-9]([.-][0-9a-z]*)?$ ]] || usage "$@"

case $1 in
    (update_repo-*.sh) :;;
    (*) printf "Invalid script name: %q\\n">&2 "$1"; usage "$@";;
esac

name=${1:12:-3} release=$2
shift 2

for i; do
    if ! [[ "$i" =~ ^[A-Za-z][A-Za-z0-9/._-]*$ ]]; then
        echo "Invalid character in repository">&2
        usage "$@"
    fi
done

REPOS_TO_UPDATE=
for i; do REPOS_TO_UPDATE+=" $release/$name/$i"; done

. ./update_repo.sh "$release" $REPOS_TO_UPDATE

if [ "${AUTOMATIC_UPLOAD-}" = 1 ]; then
    ./sync_qubes-os.org_repo.sh "$release" $REPOS_TO_UPDATE
fi
