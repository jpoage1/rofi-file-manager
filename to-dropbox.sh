#!/bin/bash
# files=($(ls -d ./*.py | grep -v main.py))
# cat "${files[@]}" ./*/*.py main.py >/nfs/jasonpoage.com/drop/workspace-manager.py

files=(
    plugins/*/*.py
    core/*.py
    filters/*.py
)
cat "${files[@]}" >/nfs/jasonpoage.com/drop/workspace-manager.py
