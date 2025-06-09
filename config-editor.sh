#!/usr/bin/env bash
# set -x

list_dirs() {
    find "$@" -type d
}
list_files() {
    find "$@" -type f
}

hide_dotfiles() {
    grep -v '/\.[^/]*'
}

list_git_files() {
    for dir in "$@"; do
        echo "Checking $dir"
        if [ -d "$dir" ] && [ -d "$dir/.git" ]; then
            echo "In $dir"
            cd "$dir" || continue
            git ls-files --cached --others --exclude-standard | grep -Ev '(^\.git|venv|\.git-crypt)(/|$)' | sed "s|^|$dir/|"
        else

            echo "Skipping $dir"
        fi
    done
}
dirs=(
    "$0"
    $(
        list_git_files \
            "$HOME/.config/i3" \
            "$HOME/.config/home-manager" \
            "/nix-config" \
            "$HOME/.config/tmux" \
            "$HOME/.config/fish" \
            "$HOME/.config/zsh" \
            "$HOME/.config/bash" \
            "$HOME/.config/posix" \
            "$HOME/.config/polybar" \
            "$HOME/.vim"
    )
)
dirs=(
    "$0"

    "$HOME/.config/i3"
    "$HOME/.config/home-manager"
    "/nix-config"
    "$HOME/.config/tmux"
    "$HOME/.config/fish"
    "$HOME/.config/zsh"
    "$HOME/.config/bash"
    "$HOME/.config/posix"
    "$HOME/.config/polybar"
    "$HOME/.vim"
)
dirs=(
    "$0"
    "/nix-config"
    "$HOME"/.config/{i3,home-manager,tmux,fish,zsh,bash,posix,polybar}
    "$HOME/.vim"
)
# echo "${dirs[@]}"
# dirs=($(list_git_files "$HOME/.config/i3" "$HOME/.config/home-manager" "/nix-config" \
#     "$HOME/.config/tmux" "$HOME/.config/fish" "$HOME/.config/zsh" \
#     "$HOME/.config/bash" "$HOME/.config/posix" "$HOME/.config/polybar" "$HOME/.vim"))

# echo "${dirs[@]}"
# # exit
# filtered_dirs=()
# for path in "${dirs[@]}"; do
#     [[ -d "$path" ]] && continue
#     filtered_dirs+=("$path")
# done
# dirs=("${filtered_dirs[@]}")
# printf "%s\n" "${dirs[@]}" | grep "$1"
source /srv/projects/editor-menu/editor.sh
run --cwd="$HOME" --interface=socket --frontend=rofi --workspace-file=".config/workspace.json" -- "${dirs[@]}"
