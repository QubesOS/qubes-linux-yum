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

        cat > "$release/$repo/$package_set/$dist/repodata/.gitignore" << EOF
*.xml
*.gz
*.bz2
*.metalink
EOF
        cat > "$release/$repo/$package_set/$dist/rpm/.gitignore" << EOF
*.rpm
EOF

        ln -sf "../../../comps-${package_set}.xml" "$release/$repo/$package_set/$dist/comps.xml"
    done
fi

if [[ $release =~ r[1-9].[0-9] ]]; then
    for repo in templates-itl templates-itl-testing templates-community templates-community-testing
    do
        mkdir -p "$release/$repo/repodata"
        mkdir -p "$release/$repo/rpm"

        cat > "$release/$repo/repodata/.gitignore" << EOF
*.xml
*.gz
*.bz2
*.metalink
EOF
        cat > "$release/$repo/rpm/.gitignore" << EOF
*.rpm
EOF
    done
fi