#!/usr/bin/env bash
# ScaleCut launcher — activates the venv automatically.
# Usage: bash run.sh  (or ./run.sh after chmod +x run.sh)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV" ]; then
  echo "Virtual environment not found. Creating it..."
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -e "$SCRIPT_DIR" -q
fi

"$VENV/bin/python" "$SCRIPT_DIR/main.py" "$@"
