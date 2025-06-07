#set -x
export root_dir=/srv/projects/editor-menu
# export DISPLAY=:0
# export XAUTHORITY="/home/$USER/.Xauthority"
# export XDG_RUNTIME_DIR="/run/user/$(id -u)"

source "$root_dir/.venv/bin/activate"
run() {
    python "$root_dir/main.py" "$@"
}
