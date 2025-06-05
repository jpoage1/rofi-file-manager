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

#fzf_dir() {
#    set +e
#    file=$(rg --files -u "$@" | rofi -dmenu -multi-select)
#    set -e
#    if [ -z "$file" ]; then
#        menu "$@"
#        return
#    fi
#    xterm -fa 'DejaVu Sans Mono Book' -fs 12 -e "$EDITOR" "$file"
#}
fzf_dir() {
    set +e
    cwd_entries="$@"
    local raw_entries=()
    # Read the dirs and get the entries based on the mode
    mapfile -t raw_entries < <(get_entries "${cwd_entries[@]}")

    local filtered_entries=()
    # Filter the entries
    if [[ "$regex_mode" == "on" && -n "$regex_pattern" ]]; then
        for e in "${raw_entries[@]}"; do
            if [[ "$e" =~ $regex_pattern ]]; then
                filtered_entries+=("$e")
            fi
        done
    else
        filtered_entries=("${raw_entries[@]}")
    fi

    local entries=("${filtered_entries[@]}")

    # Add extended options before files
    local extended=(
        "[Toggle Search Options]"
        "[Change Mode: $current_mode]"
        "---"
    )

    local selection
    selection=$(printf "%s\n" "${extended[@]}" "${entries[@]}" | rofi -dmenu -multi-select -p "Select files or options")
    set -e

    if [ -z "$selection" ]; then
        menu "${entries[@]}"
        return
    fi

    # Handle extended selections first, must exactly match
    while IFS= read -r item; do
        case "$item" in
        "[Toggle Search Options]")
            toggle_menu
            fzf_dir "${entries[@]}"
            return
            ;;
        "[Change Mode:"*)
            mode_menu
            fzf_dir "${entries[@]}"
            return
            ;;
        esac
    done <<<"$selection"

    # Filter out extended options from selection to get files only
    local files=()
    for item in $selection; do
        [[ "$item" != \[* ]] && files+=("$item")
    done

    if [ "${#files[@]}" -eq 0 ]; then
        menu "${entries[@]}"
        return
    fi

    case "$current_mode" in
    "Traverse") ;;
    "Edit") xterm -fa 'DejaVu Sans Mono Book' -fs 12 -e "$EDITOR" "${files[@]}" ;;
    "Execute") for f in "${files[@]}"; do bash "$f"; done ;;
    "Clipboard")
        for f in "${files[@]}"; do
            clipboard_queue+=("$f")
        done
        clipboard_mode_menu
        fzf_dir "${cwd_entries[@]}"
        return
        ;;
    esac
}

build_query() {
    local query_args=()

    # Example toggle variables (could be set dynamically later)
    local use_gitignore=1
    local include_dotfiles=0
    local search_dirs_only=0
    local search_files_only=1

    [[ "$use_gitignore" -eq 1 ]] && query_args+=("--glob" "!$(git rev-parse --show-toplevel)/.gitignore")
    [[ "$include_dotfiles" -eq 0 ]] && query_args+=("--hidden" "--glob" "!.*/")
    [[ "$search_dirs_only" -eq 1 ]] && query_args+=("--type" "d")
    [[ "$search_files_only" -eq 1 ]] && query_args+=("--type" "f")

    # Always ignore .git unless overridden
    query_args+=("--glob" "!.git")

    printf "%s\n" "${query_args[@]}"
}

mode_menu() {
    local modes=("Edit" "Execute" "Clipboard")
    local choice
    choice=$(printf "%s\n" "${modes[@]}" | rofi -dmenu -p "Select Mode")

    [ -n "$choice" ] && current_mode="$choice"
}

toggle_menu() {
    while true; do
        local options=(
            "Use .gitignore: $use_gitignore"
            "Include dotfiles: $include_dotfiles"
            "Search dirs only: $search_dirs_only"
            "Search files only: $search_files_only"
            "Continue"
        )

        local choice
        choice=$(printf "%s\n" "${options[@]}" | rofi -dmenu -p "Toggle options")

        case "$choice" in
        "Use .gitignore: 1") use_gitignore=0 ;;
        "Use .gitignore: 0") use_gitignore=1 ;;
        "Include dotfiles: 1") include_dotfiles=0 ;;
        "Include dotfiles: 0") include_dotfiles=1 ;;
        "Search dirs only: 1") search_dirs_only=0 ;;
        "Search dirs only: 0") search_dirs_only=1 ;;
        "Search files only: 1") search_files_only=0 ;;
        "Search files only: 0") search_files_only=1 ;;
        "Continue") break ;;
        *) continue ;;
        esac
    done
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

menu "$@"
