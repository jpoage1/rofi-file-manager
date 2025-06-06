#!/usr/bin/env bash
set -x
projects=$(ls -d -1 /srv/projects/*)
dirs=("$0" "${projects[@]}")

./menu3.py "/srv/projects/editor-menu/${dirs[@]}"
