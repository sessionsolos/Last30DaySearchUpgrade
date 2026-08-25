#!/usr/bin/env bash
# Package skill/ as a claude.ai-uploadable .skill bundle.
# Usage: bash scripts/build-skill.sh   (run from repo root)
#
# A .skill file is a zip containing exactly one top-level directory with
# SKILL.md at its root. claude.ai caps the archive at 200 files.
set -euo pipefail

cd "$(cd "$(dirname "$0")/.." && pwd)"

if [ ! -f skill/SKILL.md ]; then
  echo "error: run this from the repository root" >&2
  exit 1
fi

mkdir -p dist
OUT="dist/signal.skill"
rm -f "$OUT"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/signal"
cp -R skill/. "$STAGE/signal/"
find "$STAGE" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$STAGE" -name '.DS_Store' -delete 2>/dev/null || true

( cd "$STAGE" && zip -q -r "$OLDPWD/$OUT" signal )

COUNT=$(unzip -l "$OUT" | tail -1 | awk '{print $2}')
if [ "$COUNT" -gt 200 ]; then
  echo "error: $COUNT files, claude.ai caps at 200" >&2
  exit 1
fi
if [ "$(unzip -l "$OUT" | grep -c 'SKILL\.md$')" -ne 1 ]; then
  echo "error: expected exactly one SKILL.md" >&2
  exit 1
fi

echo "built $OUT ($COUNT files, $(du -h "$OUT" | cut -f1))"
echo "upload via claude.ai > Customize > Skills > + > Create skill > Upload a skill"
