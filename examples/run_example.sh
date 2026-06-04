#!/usr/bin/env bash
# ScaleCut — generate the Acme Studio example project via the CLI.
# Run from the repo root with the venv active:
#   source .venv/bin/activate
#   bash examples/run_example.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Generating Acme Studio / Lanzamiento Q4 2024..."

scalecut quick "$SCRIPT_DIR" \
  --client "Acme Studio" \
  --project "Lanzamiento Q4" \
  --type "Campaña publicitaria" \
  --date "2024-12-20" \
  --clips 4 \
  --platforms "Instagram Reels,TikTok,LinkedIn,YouTube" \
  --formats "9x16,1x1,16x9" \
  --version "01" \
  --language "ES" \
  --status "Not started"

echo ""
echo "Project created at: $SCRIPT_DIR/ACME_STUDIO_LANZAMIENTO_Q4_20241220/"
