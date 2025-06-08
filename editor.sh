#!/usr/bin/env bash
#set -x
export root_dir=/srv/projects/editor-menu

source "$root_dir/.venv/bin/activate"
run() {
    python "$root_dir/main.py" "$@"
}

# echo "${dirs[@]}"

# Detect if script is sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then # Script is not sourced
    cd "$root_dir"
    readarray -t projects < <(git ls-files)
    dirs=("$0" "${projects[@]}")
    run "${dirs[@]}"
fi
