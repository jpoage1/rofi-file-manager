#!/usr/bin/env bash
# set -x
projects=$(ls -d -1 /srv/projects/*)
dirs=("$0" "${projects[@]}")

source /srv/projects/editor-menu/editor.sh
run "${dirs[@]}"
