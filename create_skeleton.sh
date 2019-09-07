#!/bin/bash

print_usage() {
cat >&2 <<USAGE
Usage: $0 release package_set dist
Create Qubes repository skeleton
USAGE
}

if [ $# -lt 3 ] ; then
    print_usage
    exit 1
fi

release="$1"
package_set="$2"
dist="$3"

if [[ $release =~ r[1-9].[0-9] ]] && [[ $package_set =~ (dom0|vm) ]] && [[ $dist =~ (fc[1-9][0-9]|centos[1-9][0-9]*) ]]
then
    for repo in current current-testing security-testing unstable
    do
        mkdir -p "$release/$repo/$package_set/$dist/repodata"
        mkdir -p "$release/$repo/$package_set/$dist/rpm"

        touch "$release/$repo/$package_set/$dist/repodata/.gitignore"
        touch "$release/$repo/$package_set/$dist/rpm/.gitignore"

        ln -s "comps-${package_set}.xml" "$release/$repo/$package_set/$dist"
    done
fi