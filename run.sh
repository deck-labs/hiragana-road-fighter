#!/usr/bin/env bash
# ==============================================================================
# Launch Hiragana Road Fighter (Python Edition)
# ==============================================================================
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$DIR/python:${PYTHONPATH}"

if [ -x "/tmp/pygame_build_venv/bin/python" ]; then
    exec "/tmp/pygame_build_venv/bin/python" "$DIR/python/main.py" "$@"
else
    exec python3 "$DIR/python/main.py" "$@"
fi
