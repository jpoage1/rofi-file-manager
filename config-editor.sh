#!/usr/bin/env bash
set -x
dirs=(
    "$(which editor.sh)"
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
./menu4.py "/srv/projects/editor-menu/${dirs[@]}"
