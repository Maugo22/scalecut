#!/usr/bin/env bash
# ScaleCut — launch the Streamlit web UI.
# Usage: bash run_app.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV" ]; then
  echo "Virtual environment not found. Creating it..."
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -e "$SCRIPT_DIR" -q
fi

echo "Launching ScaleCut UI at http://localhost:8501"
"$VENV/bin/streamlit" run "$SCRIPT_DIR/app.py" \
  --server.headless false \
  --browser.gatherUsageStats false
