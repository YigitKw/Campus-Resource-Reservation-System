#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
if command -v python3 &>/dev/null; then
    python3 "$DIR/main.py" "$@"
else
    python "$DIR/main.py" "$@"
fi
