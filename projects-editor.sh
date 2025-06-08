#!/usr/bin/env bash
# set -x
readarray -t projects < <(find /srv/projects -mindepth 1 -maxdepth 1 -type d)
dirs=("$0" "${projects[@]}")

source /srv/projects/editor-menu/editor.sh
# echo "${dirs[@]}"
run "${dirs[@]}"
