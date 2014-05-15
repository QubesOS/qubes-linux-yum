#!/bin/sh

RELS_TO_UPDATE="`readlink current-release|tr -d /`"
MIN_AGE=7
#DRY=echo

if [ -z "$1" ]; then
    echo "Usage: $0 <path-to-current-testing-repo-snapshot> [<component list>]"
    exit 1
fi

repo_snapshot_dir="$1"
components="$2"

touch -t `date -d "$MIN_AGE days ago" +%Y%m%d%H%M` age-compare-file

# $1 - snapshot file
# $2 - source dir
# $3 - destination dir
process_snapshot_file() {
    if ! [ -r $1 ]; then
        if [ "$VERBOSE" -ge 1 ]; then
            echo "Not existing snapshot, ignoring: `basename $1`"
        fi
        return
    fi
    if [ $1 -nt age-compare-file ]; then
        echo "Packages wasn't in current-testing for at least $MIN_AGE days, ignoring: `basename $1`"
        continue
    fi
    for f in `cat $1`; do
        f=`basename $f`
        if ! [ -r $2/$f ]; then
            echo "Not existing package, ignoring: $2/$f"
            continue
        fi
        if rpm --checksig $2/$f | grep -v pgp > /dev/null; then
            echo "Not signed package: $2/$f"
            continue 
        fi
        $DRY ln -f $2/$f $3/
    done
}
        
for rel in $RELS_TO_UPDATE; do
    for pkg_set in dom0 vm; do
        for dist in `ls $rel/current/$pkg_set`; do
            if [ -n "$components" ]; then
                for component in $components; do
                    process_snapshot_file $repo_snapshot_dir/current-testing-$pkg_set-$dist-$component \
                        $rel/current-testing/$pkg_set/$dist/rpm \
                        $rel/current/$pkg_set/$dist/rpm
                done
            else
                for snapshot_file in $repo_snapshot_dir/current-testing-$pkg_set-$dist-*; do
                    process_snapshot_file $snapshot_file \
                        $rel/current-testing/$pkg_set/$dist/rpm \
                        $rel/current/$pkg_set/$dist/rpm
                done
            fi
        done
    done
done

rm -f age-compare-file

echo Done.
