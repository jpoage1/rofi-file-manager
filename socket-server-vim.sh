#!/usr/bin/env bash
# set -x
readarray -t projects < <(find /srv/projects -mindepth 1 -maxdepth 1 -type d)
dirs=("$0" "${projects[@]}")

source /srv/projects/editor-menu/editor.sh
# echo "${dirs[@]}"

run --cwd=/srv/projects --interface=socket-server --port=12345 --workspace-file=workspace.json -- "${dirs[@]}"
SERVER_PID=$! # Get the PID of the background server

echo $SERVER_PID
