#!/usr/bin/env bash
source libs.sh
set -vexuo pipefail
EDITOR=nvim

# State
declare -A state=(
    [current_mode]="Edit"
    [use_gitignore]=1
    [include_dotfiles]=0
    [search_dirs_only]=0
    [search_files_only]=1
    [regex_mode]=0
    [regex_pattern]=""
    [root_dir]="."
)
declare -a clipboard_queue=()
declare -a state_stack=()

push_state() {
    state_stack+=("$(declare -p state)")
}
pop_state() {
    if ((${#state_stack[@]} > 0)); then
        eval "${state_stack[-1]}"
        unset 'state_stack[-1]'
    fi
}

fzf_dir() {
    local -n st="$1"
    set +e
    local raw_entries=()
    mapfile -t raw_entries < <(get_entries st)

    local filtered_entries=()
    if [[ "${st[regex_mode]}" -eq 1 && -n "${st[regex_pattern]}" ]]; then
        for e in "${raw_entries[@]}"; do
            [[ "$e" =~ ${st[regex_pattern]} ]] && filtered_entries+=("$e")
        done
    else
        filtered_entries=("${raw_entries[@]}")
    fi

    local entries=("${filtered_entries[@]}")
    local extended=(
        "[Toggle Search Options]"
        "[Change Mode: ${st[current_mode]}]"
        "---"
    )

    local selection
    selection=$(printf "%s\n" "${extended[@]}" "${entries[@]}" | rofi -dmenu -multi-select -p "Select files or options")
    set -e
    [[ -z "$selection" ]] && menu "${entries[@]}" && return

    while IFS= read -r item; do
        case "$item" in
        "[Toggle Search Options]")
            push_state
            toggle_menu st
            fzf_dir st
            return
            ;;
        "[Change Mode:"*)
            push_state
            mode_menu st
            fzf_dir st
            return
            ;;
        esac
    done <<<"$selection"

    local files=()
    for item in $selection; do
        [[ "$item" != \[* ]] && files+=("$item")
    done
    [[ "${#files[@]}" -eq 0 ]] && menu "${entries[@]}" && return

    case "${st[current_mode]}" in
    "Traverse") ;;
    "Edit") xterm -fa 'DejaVu Sans Mono Book' -fs 12 -e "$EDITOR" "${files[@]}" ;;
    "Execute") for f in "${files[@]}"; do bash "$f"; done ;;
    "Clipboard")
        for f in "${files[@]}"; do clipboard_queue+=("$f"); done
        clipboard_mode_menu
        fzf_dir st
        return
        ;;
    esac
}

get_entries() {
    local -n st="$1"
    local path="${st[root_dir]}"
    case "${st[current_mode]}" in
    "Traverse")
        find "$path" -type d ! -path "$path" -printf '%P\n' | sort
        ;;
    "FilesOnly")
        find "$path" -maxdepth 1 -type f -printf '%f\n' | sort
        ;;
    "SearchAll")
        find "$path" -type f -printf '%P\n' | sort
        ;;
    "Edit")
        find "$path" -maxdepth 1 ! -path "$path" -printf '%f\n' | sort
        ;;
    *)
        printf '%s\n' "$path"
        ;;
    esac
}
toggle_menu() {
    while true; do
        local options=(
            "Use .gitignore: ${state[use_gitignore]}"
            "Include dotfiles: ${state[include_dotfiles]}"
            "Search dirs only: ${state[search_dirs_only]}"
            "Search files only: ${state[search_files_only]}"
            "Continue"
        )

        local choice
        choice=$(printf "%s\n" "${options[@]}" | rofi -dmenu -p "Toggle options")

        case "$choice" in
        "Use .gitignore: 1") state[use_gitignore]=0 ;;
        "Use .gitignore: 0") state[use_gitignore]=1 ;;
        "Include dotfiles: 1") state[include_dotfiles]=0 ;;
        "Include dotfiles: 0") state[include_dotfiles]=1 ;;
        "Search dirs only: 1") state[search_dirs_only]=0 ;;
        "Search dirs only: 0") state[search_dirs_only]=1 ;;
        "Search files only: 1") state[search_files_only]=0 ;;
        "Search files only: 0") state[search_files_only]=1 ;;
        "Continue") break ;;
        *) continue ;;
        esac
    done
}

mode_menu() {
    local -n st="$1"
    local modes=("Edit" "Execute" "Clipboard")
    local choice
    choice=$(printf "%s\n" "${modes[@]}" | rofi -dmenu -p "Select Mode")
    [[ -n "$choice" ]] && st[current_mode]="$choice"
}

main_menu() {
    dirs=("$@")
    local entries=("[All Files]" "${dirs[@]}")
    local path
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

add_to_queue() {
    local files
    files=$(rg --files "$1" 2>/dev/null || echo "$1")
    for f in $files; do
        [[ ! " ${clipboard_queue[*]} " =~ " $f " ]] && clipboard_queue+=("$f")
    done
}

remove_from_queue() {
    local to_remove
    to_remove=$(printf "%s\n" "${clipboard_queue[@]}" | rofi -dmenu -multi-select -p "Remove files")
    [[ -z "$to_remove" ]] && return
    for r in $to_remove; do
        clipboard_queue=("${clipboard_queue[@]/$r/}")
    done
}

commit_queue() {
    local all_content
    all_content=$(cat "${clipboard_queue[@]}")
    printf "%s" "$all_content" | xclip -selection clipboard
}

clipboard_mode_menu() {
    while true; do
        local options=(
            "Add files by regex"
            "Remove files"
            "Show queue"
            "Commit and exit"
            "Cancel"
        )
        local choice
        choice=$(printf "%s\n" "${options[@]}" | rofi -dmenu -p "Clipboard mode")
        case "$choice" in
        "Add files by regex")
            local pattern
            pattern=$(rofi -dmenu -p "Enter regex pattern")
            [[ -n "$pattern" ]] && add_to_queue "$pattern"
            ;;
        "Remove files")
            remove_from_queue
            ;;
        "Show queue")
            printf "%s\n" "${clipboard_queue[@]}" | rofi -dmenu -p "Current clipboard queue" -mesg "Press ESC to continue"
            ;;
        "Commit and exit")
            commit_queue
            break
            ;;
        "Cancel")
            break
            ;;
        esac
    done
}

main_menu "$@"
