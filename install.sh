#!/usr/bin/env bash
# Autosave installer. One command, idempotent, backs up before writing.
#   ./install.sh             install into ~/.claude (or $CLAUDE_DIR)
#   ./install.sh --dry-run   show what would change, write nothing
#   ./install.sh --no-settings   skip merging hooks into settings.json
# Every existing file that would change is copied to
#   ~/.claude/backups/autosave-<timestamp>/<same path>
# before it is touched. Re-running with no changes writes nothing.
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
DRY_RUN=0; DO_SETTINGS=1
for a in "$@"; do
  case "$a" in
    --dry-run) DRY_RUN=1 ;;
    --no-settings) DO_SETTINGS=0 ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "unknown option: $a" >&2; exit 1 ;;
  esac
done

command -v python3 >/dev/null || { echo "python3 is required (hooks are Python)." >&2; exit 1; }

CONFIG="$KIT_DIR/kit.conf"
if [[ ! -f "$CONFIG" ]]; then
  echo "note: no kit.conf found; using defaults from config.example (cp config.example kit.conf to customize)"
  CONFIG="$KIT_DIR/config.example"
fi
# shellcheck disable=SC1090
set -a; source "$CONFIG"; set +a

export KIT_DIR CLAUDE_DIR DRY_RUN DO_SETTINGS
export BACKUP_DIR="$CLAUDE_DIR/backups/autosave-$(date +%Y%m%d-%H%M%S)"

python3 - <<'PY'
import filecmp, json, os, re, shutil, subprocess, sys
from pathlib import Path

kit = Path(os.environ["KIT_DIR"]); dest = Path(os.environ["CLAUDE_DIR"])
dry = os.environ["DRY_RUN"] == "1"; backup = Path(os.environ["BACKUP_DIR"])
KEYS = ["USER_NAME", "APPROVER", "PROJECTS_DIR", "EVALS_DIR", "OUTPUT_DIR", "MONTHLY_BUDGET_USD",
        "CYCLE", "CYCLE_START_DAY", "CONTEXT_WARN_TOKENS", "FOOTER_MARKER", "FOOTER_DISABLE", "INVARIANTS"]
vals = {k: os.environ.get(k, "") for k in KEYS}
home = str(Path.home())
for k in ("PROJECTS_DIR", "EVALS_DIR", "OUTPUT_DIR"):  # show paths as ~/... in prose
    if vals[k].startswith(home):
        vals[k] = "~" + vals[k][len(home):]
stats = {"new": 0, "updated": 0, "same": 0, "kept": 0}

def render(text, as_json=False):
    for k, v in vals.items():
        text = text.replace("{{%s}}" % k, json.dumps(v)[1:-1] if as_json else v)
    return text

# Parse both settings files BEFORE writing anything, so a bad value or a hand-edited
# settings.json stops the install cleanly instead of leaving it half done.
sp = dest / "settings.json"
try:
    tpl = json.loads(render((kit / "settings.template.json").read_text(), as_json=True))
    cur = json.loads(sp.read_text()) if sp.exists() else {}
except ValueError as e:
    where = sp if sp.exists() else "the kit config"
    sys.exit(f"Stopped before writing anything: {where} is not valid JSON ({e}). "
             f"Fix it (a trailing comma is the usual cause) and rerun.")

# Files a previous run of this installer wrote. Those are the kit's own and get updated;
# any other file with the same name is the user's and is never replaced.
manifest = dest / ".autosave-manifest.json"
old_manifest = dest / ".starter-kit-manifest.json"  # name used by v1.0/v1.1, before the rename
src = manifest if manifest.exists() else old_manifest
owned = set(json.loads(src.read_text())) if src.exists() else set()
installed = set()

def backup_file(target):
    b = backup / target.relative_to(dest)
    if b.exists():
        return  # keep the first (original) copy
    if not dry:
        b.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, b)

def put(rel, content, mode=None, keep_existing=False):
    """Write dest/rel. Identical: skip. Different: back up, then replace
    (or, with keep_existing, leave it and write rel + '.kit-new' beside it)."""
    target = dest / rel
    if target.exists():
        if target.read_text(errors="replace") == content:
            stats["same"] += 1; return
        if keep_existing:
            side = target.with_name(target.name + ".kit-new")
            print(f"  kept   {rel} (yours differs; kit version at {side.name})")
            stats["kept"] += 1
            if not dry:
                side.write_text(content)
            return
        backup_file(target)
        print(f"  update {rel} (backed up)"); stats["updated"] += 1
    else:
        print(f"  new    {rel}"); stats["new"] += 1
    if not dry:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        if mode:
            os.chmod(target, mode)

print(f"Installing into {dest}{' (dry run)' if dry else ''}")
for sub in ("hooks", "commands", "skills", "rules"):
    for f in sorted((kit / sub).rglob("*")):
        if not f.is_file() or "__pycache__" in f.parts:
            continue
        rel = f.relative_to(kit)
        keep = str(rel) in ("rules/standing-rules.md", "rules/workflow.md") or \
            ((dest / rel).exists() and str(rel) not in owned)
        content = render(f.read_text())
        put(rel, content, mode=0o755 if f.suffix == ".py" else None, keep_existing=keep)
        if not dry and (dest / rel).read_text(errors="replace") == content:
            installed.add(str(rel))  # the file at this path is now the kit's

# CLAUDE.md: install the template if none exists; otherwise only add the marker block.
cm = dest / "CLAUDE.md"
BEGIN = "<!-- BEGIN STANDING-RULES (generated - edit the manifest, not this block) -->"
if not cm.exists():
    put("CLAUDE.md", render((kit / "CLAUDE.md.template").read_text()))
elif BEGIN not in cm.read_text():
    print("  update CLAUDE.md (append standing-rules block, backed up)"); stats["updated"] += 1
    if not dry:
        backup_file(cm)
        with cm.open("a") as fh:
            fh.write("\n\n## Standing rules (canonical: ~/.claude/rules/standing-rules.md)\n"
                     + BEGIN + "\n(filled from rules/standing-rules.md by check_rule_sync.py)\n<!-- END STANDING-RULES -->\n")
if not dry:
    r = subprocess.run([sys.executable, str(dest / "hooks/check_rule_sync.py")], capture_output=True, text=True)
    if r.returncode != 0:
        backup_file(cm)
        subprocess.run([sys.executable, str(dest / "hooks/check_rule_sync.py"), "--fix"], check=False)
        print("  synced standing rules into CLAUDE.md (backed up)")

# settings.json: merge, never replace. Adds missing env keys, hook entries, statusLine.
if os.environ["DO_SETTINGS"] == "1":
    new = json.loads(json.dumps(cur))
    env = new.setdefault("env", {})
    for k, v in tpl["env"].items():
        env.setdefault(k, v)
    def wired(ev, matcher, script):
        for e in new.get("hooks", {}).get(ev, []):
            if e.get("matcher", "") == matcher and any(".claude/hooks/" + script in (h.get("command") or "") for h in e.get("hooks", [])):
                return True
        return False
    for ev, entries in tpl["hooks"].items():
        for e in entries:
            script = re.search(r"hooks/(\w+\.py)", e["hooks"][0]["command"]).group(1)
            if wired(ev, e.get("matcher", ""), script):
                continue  # already wired for this event + matcher (any path spelling)
            new.setdefault("hooks", {}).setdefault(ev, []).append(e)
    if "statusLine" not in new:
        new["statusLine"] = tpl["statusLine"]
    if new != cur:
        print(f"  {'update' if sp.exists() else 'new   '} settings.json (merged hooks/env{', backed up' if sp.exists() else ''})")
        if not dry:
            if sp.exists():
                backup_file(sp)
            sp.write_text(json.dumps(new, indent=2) + "\n")
    else:
        stats["same"] += 1

if not dry:
    for d in ("handoffs", "state", "usage"):
        (dest / d).mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(sorted(owned | installed), indent=1) + "\n")
    if old_manifest.exists():
        old_manifest.unlink()  # its entries now live in the new manifest
print(f"\nDone: {stats['new']} new, {stats['updated']} updated, {stats['same']} unchanged, {stats['kept']} kept as yours.")
if (stats["updated"] or stats["kept"]) and not dry and backup.exists():
    print(f"Backups: {backup}")
PY

if [[ "$DRY_RUN" == "0" ]]; then
  echo
  echo "Self-test: guard hook"
  python3 "$CLAUDE_DIR/hooks/guard_tests.py" | tail -1
  echo "Restart Claude Code (or run /hooks) to load the hooks. See QUICKSTART.md."
fi
