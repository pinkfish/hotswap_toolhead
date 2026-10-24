#!/usr/bin/env bash
# Copies this project into the local GitHub folder and pushes it to GitHub.
#
#   Destination: /Volumes/ExternalDocs/Documents/GitHub/hotswap_toolhead
#   GitHub repo: hotswap_toolhead (private unless you pass --public)
#
# Safe to run more than once:
#   - creates the folder and git repo if they don't exist yet
#   - if the folder already has files, any file that would be overwritten and
#     differs is first backed up to .update-backups/<timestamp>/ (git-ignored)
#   - files you added yourself (e.g. the XT30 footprint) are never deleted
#   - an existing toolhead.kicad_pcb, toolhead.kicad_pro and fp-lib-table are
#     never replaced, so board layout work and KiCad settings are kept
#   - creates the GitHub repo only if it doesn't exist; otherwise just pushes
#
# Needs: git and the GitHub CLI logged in (`gh auth login`).
# Usage, from the unzipped hotswap_toolhead folder:
#   bash setup_repo.sh            # private repo
#   bash setup_repo.sh --public   # public repo
#   DEST=/some/other/path bash setup_repo.sh
set -euo pipefail

VIS="--private"; [ "${1:-}" = "--public" ] && VIS="--public"
DEST="${DEST:-/Volumes/ExternalDocs/Documents/GitHub/hotswap_toolhead}"
REPO="hotswap_toolhead"
SRC="$(cd "$(dirname "$0")" && pwd)"
TS="$(date +%Y%m%d-%H%M%S)"

say() { printf '\n==> %s\n' "$*"; }
die() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

command -v git   >/dev/null || die "git is not installed (run: xcode-select --install)"
command -v gh    >/dev/null || die "GitHub CLI is not installed: brew install gh  (or https://cli.github.com)"
gh auth status >/dev/null 2>&1 || die "Not logged in to GitHub. Run: gh auth login"

# The external drive must be mounted.
VOL="$(echo "$DEST" | awk -F/ '$2=="Volumes"{print "/Volumes/"$3}')"
if [ -n "$VOL" ] && [ ! -d "$VOL" ]; then
  die "$VOL is not mounted. Connect the drive and try again."
fi

# KiCad keeps the schematic in memory and will write the old one back on save.
if pgrep -i "kicad|eeschema|pcbnew" >/dev/null 2>&1; then
  die "KiCad is running. Close it (choose don't save), then run this again."
fi

mkdir -p "$DEST"
SRC_REAL="$(cd "$SRC" && pwd -P)"; DEST_REAL="$(cd "$DEST" && pwd -P)"

if [ "$SRC_REAL" != "$DEST_REAL" ]; then
  say "Copying files to $DEST"
  BK="$DEST/.update-backups/$TS"
  BACKED="$(mktemp)"; SKIPPED="$(mktemp)"
  (cd "$SRC" && find . -type f ! -path './.git/*' ! -path './.update-backups/*' \
        ! -path '*/__pycache__/*' ! -name '.DS_Store' -print) |
  while IFS= read -r f; do
    rel="${f#./}"; dst="$DEST/$rel"
    if [ -f "$dst" ] && cmp -s "$SRC/$rel" "$dst"; then continue; fi
    case "$rel" in                     # your layout and KiCad settings: never replace
      hardware/toolhead.kicad_pcb|hardware/toolhead.kicad_pro|hardware/fp-lib-table)
        if [ -f "$dst" ]; then echo "$rel" >> "$SKIPPED"; continue; fi ;;
    esac
    if [ -f "$dst" ]; then            # differs: back up the existing copy first
      mkdir -p "$(dirname "$BK/$rel")"; cp -p "$dst" "$BK/$rel"; echo "$rel" >> "$BACKED"
    fi
    mkdir -p "$(dirname "$dst")"; cp -p "$SRC/$rel" "$dst"
    echo "  $rel"
  done
  if [ -s "$BACKED" ]; then
    echo "Files that differed were backed up to: $BK"
  fi
  if [ -s "$SKIPPED" ]; then
    echo "Kept your existing copies of (not replaced):"; sed 's/^/  /' "$SKIPPED"
    echo "  Schematic changes reach the PCB with Tools > Update PCB from Schematic (F8)."
  fi
  rm -f "$BACKED" "$SKIPPED"
else
  say "Already running inside $DEST, nothing to copy"
fi

cd "$DEST"
grep -qx ".update-backups/" .gitignore 2>/dev/null || printf '\n# Backups made by setup_repo.sh\n.update-backups/\n' >> .gitignore

if [ ! -d .git ]; then
  say "Creating git repository"
  git init -q -b main
fi

say "Committing"
git add -A
if git diff --cached --quiet; then
  echo "No changes to commit."
else
  if git rev-parse --verify -q HEAD >/dev/null; then
    git commit -q -m "Update design: FET footprints, LMR16006 buck, XT30(2+2) library, docs"
  else
    git commit -q -m "Initial commit: 24 V CAN toolhead board design, KiCad project and generator"
  fi
  git log --oneline -1
fi

if git remote get-url origin >/dev/null 2>&1; then
  say "Pushing to $(git remote get-url origin)"
  git push -u origin HEAD
elif gh repo view "$REPO" >/dev/null 2>&1; then
  URL="$(gh repo view "$REPO" --json url -q .url)"
  say "GitHub repo already exists ($URL) - linking and pushing"
  git remote add origin "$URL.git"
  git push -u origin HEAD || die "Push was rejected - the GitHub repo already has commits this folder doesn't. Run: git pull --rebase origin main   then run this script again."
else
  say "Creating GitHub repo $REPO ($VIS) and pushing"
  gh repo create "$REPO" $VIS --source=. --remote=origin --push \
     --description "24 V CAN toolhead board: heater, fan, thermistor, USB debug (STM32G0B1, Klipper)"
fi

say "Done: $DEST"
gh repo view "$REPO" --json url -q .url 2>/dev/null || true
