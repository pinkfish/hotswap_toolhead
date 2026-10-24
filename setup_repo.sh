#!/usr/bin/env bash
# Creates ~/Documents/github/hotswap_toolhead and pushes it to a new GitHub repo.
# Needs: git, and the GitHub CLI (gh) logged in (`gh auth login`).
# Usage: run from the unzipped hotswap_toolhead folder:  bash setup_repo.sh [--public]
set -euo pipefail
VIS="--private"; [ "${1:-}" = "--public" ] && VIS="--public"
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="/Volumes/ExternalDocs/Documents/GitHub/hotswap_toolhead"
command -v git >/dev/null || { echo "git is not installed"; exit 1; }
command -v gh  >/dev/null || { echo "GitHub CLI (gh) is not installed: https://cli.github.com"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "Run 'gh auth login' first"; exit 1; }
if [ "$SRC" != "$DEST" ]; then
  [ -e "$DEST" ] && { echo "$DEST already exists - move or delete it first"; exit 1; }
  mkdir -p "$(dirname "$DEST")"
  cp -R "$SRC" "$DEST"
fi
cd "$DEST"
git init -q -b main
git add .
git commit -q -m "Initial commit: 24 V CAN toolhead board design, KiCad project and generator"
gh repo create hotswap_toolhead $VIS --source=. --remote=origin --push \
   --description "24 V CAN toolhead board: heater, fan, thermistor, USB debug (STM32G0B1, Klipper)"
echo "Done: $DEST"
gh repo view --web >/dev/null 2>&1 || true
