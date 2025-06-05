# libs.sh
edit_files() {
    xterm -fa 'DejaVu Sans Mono Book' -fs 12 -e "$EDITOR" "$@"
}
menu() {
    dirs=("$@")
    local entries=(
        "[All Files]"
        "${dirs[@]}"
    )

    path=$(printf "%s\n" "${entries[@]}" | rofi -dmenu -p "Edit target:")
    [ -z "$path" ] && return

    interpret_main_menu "$path" "${dirs[@]}"
}
interpret_main_menu() {
    local path=$1
    shift
    local dirs=("$@")

    if [ "$path" = "[All Files]" ]; then
        fzf_dir "${dirs[@]}"
    elif [ -f "$path" ]; then
        edit_files "$path"
    elif [ -d "$path" ]; then
        fzf_dir "$path"
    else
        echo "Not file or directory: $path"
    fi
}

get_entries() {
    local entries=("$@")
    case "$current_mode" in
    "Traverse")
        find "${entries[0]:-.}" -type d ! -path "${entries[0]:-.}" -printf '%P\n' | sort
        ;;
    "FilesOnly")
        find "${entries[0]:-.}" -maxdepth 1 -type f -printf '%f\n' | sort
        ;;
    "SearchAll")
        find "${entries[0]:-.}" -type f -printf '%P\n' | sort
        ;;
    "Edit")
        # List files and directories in the given path, non-recursive, showing relative names
        find "${entries[0]:-.}" -maxdepth 1 ! -path "${entries[0]:-.}" -printf '%f\n' | sort
        ;;
    *)
        printf '%s\n' "${entries[@]}"
        ;;
    esac
}
