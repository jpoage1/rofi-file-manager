#!/usr/bin/env bash
# set -x
readarray -t projects < <(find /srv/projects -mindepth 1 -maxdepth 1 -type d)
dirs=("$0" "${projects[@]}")

source /srv/projects/editor-menu/editor.sh
# echo "${dirs[@]}"

# Launch the client in the foreground
run --cwd=/srv/projects --interface=socket-client --workspace-file=workspace.json -- "${dirs[@]}"

# After the client exits, clean up the server (optional, but good for testing)
kill $SERVER_PID
echo "Killed server process $SERVER_PID"
