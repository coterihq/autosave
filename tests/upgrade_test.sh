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

# Learn: a reinstall must not touch learn state or the generated rules file, and must not duplicate hook entries.
H2="$T/home2"; mkdir -p "$H2/.claude/learn" "$H2/.claude/rules"
HOME="$H2" bash "$T/kit/install.sh" > "$T/out2.txt" 2>&1 || { echo "FAIL: first install"; cat "$T/out2.txt"; exit 1; }
printf '%s' '{"corrections":[],"rules":[{"id":1,"text":"Use tabs","created":"2026-11-01","state":"held","trial_start":"2026-11-01","receipts":[],"repeats":[]}],"active_days":[],"last_nudge":"","quarantined":0}' > "$H2/.claude/learn/learn.json"
printf '# Learned rules\n\n- Use tabs\n' > "$H2/.claude/rules/learned-rules.md"
cp "$H2/.claude/learn/learn.json" "$T/learn.before"; cp "$H2/.claude/rules/learned-rules.md" "$T/rules.before"
HOME="$H2" bash "$T/kit/install.sh" > "$T/out3.txt" 2>&1 || { echo "FAIL: reinstall"; cat "$T/out3.txt"; exit 1; }
cmp -s "$T/learn.before" "$H2/.claude/learn/learn.json" || { echo "FAIL: learn.json changed on reinstall"; exit 1; }
cmp -s "$T/rules.before" "$H2/.claude/rules/learned-rules.md" || { echo "FAIL: learned-rules.md changed on reinstall"; exit 1; }
python3 - "$H2/.claude/settings.json" <<'PY' || { echo "FAIL: learn.py hook entries"; exit 1; }
import json, sys
h = json.load(open(sys.argv[1]))["hooks"]
for ev in ("UserPromptSubmit", "Stop", "SessionStart"):
    n = sum("hooks/learn.py" in x["command"] for e in h[ev] for x in e["hooks"])
    assert n == 1, (ev, n)
PY
echo "upgrade_test: pass"
