#!/usr/bin/env bash
#set -x
export root_dir=/srv/projects/editor-menu

source "$root_dir/.venv/bin/activate"
run() {
    python "$root_dir/main.py" "$@"
}

# echo "${dirs[@]}"

workspace_editor() {
    cd "$root_dir"
    readarray -t project < <(
        git ls-tree -r --name-only HEAD |
            xargs -I{} dirname "{}" |
            sort -u
    )
    dirs=("$0" "${project[@]}")
    run --cwd="$root_dir" --workspace-file=workspace.json -- "${dirs[@]}"
}

# Detect if script is sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then # Script is not sourced
    workspace_editor
fi
# Prevent workspace_editor from getting sourced
unset -f workspace_editor
