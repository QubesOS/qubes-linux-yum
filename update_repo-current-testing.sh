#!/bin/bash --
dir=$(dirname -- "$0") || exit
pushd -- "$dir"
. ./upload-functions.sh "${0##*/}" "$@"
