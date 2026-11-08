#!/usr/bin/env bash
# Regression: a kit file installed by an earlier version (tracked in the old
# .starter-kit-manifest.json) must be UPDATED by a newer version, not kept as
# the user's own with a .kit-new copy beside it.
set -euo pipefail
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
mkdir -p "$T/home/.claude/commands" "$T/kit"
# Simulate a v1.1 install: one kit file, recorded in the old manifest name.
echo "old version" > "$T/home/.claude/commands/handoff.md"
echo '["commands/handoff.md"]' > "$T/home/.claude/.starter-kit-manifest.json"
cp -R "$KIT/." "$T/kit/"
HOME="$T/home" bash "$T/kit/install.sh" --no-settings > "$T/out.txt" 2>&1
if grep -q "kept   commands/handoff.md" "$T/out.txt" || [ -e "$T/home/.claude/commands/handoff.md.kit-new" ]; then
  echo "FAIL: kit file from the old manifest was kept as the user's"; cat "$T/out.txt"; exit 1
fi
cmp -s "$KIT/commands/handoff.md" "$T/home/.claude/commands/handoff.md" || { echo "FAIL: handoff.md not updated"; exit 1; }
[ -e "$T/home/.claude/.autosave-manifest.json" ] || { echo "FAIL: new manifest missing"; exit 1; }
[ ! -e "$T/home/.claude/.starter-kit-manifest.json" ] || { echo "FAIL: old manifest left behind"; exit 1; }
grep -q '"commands/handoff.md"' "$T/home/.claude/.autosave-manifest.json" || { echo "FAIL: entry not carried over"; exit 1; }
echo "upgrade_test: pass"
