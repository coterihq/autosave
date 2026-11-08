#!/usr/bin/env python3
"""Nightly rule-sync check. Compares the canonical manifest
(~/.claude/rules/standing-rules.md) against the marker-delimited block in
~/.claude/CLAUDE.md. Drift -> writes ~/.claude/RULE_SYNC_DRIFT.md and exits 1.
--fix regenerates the CLAUDE.md block from the manifest.
Prints manifest sha256 (first 12) so another surface (e.g. claude.ai memory) can pin it."""
import hashlib, re, sys, os

CDIR = os.environ.get("CLAUDE_DIR") or os.path.expanduser("~/.claude")
MANIFEST = f"{CDIR}/rules/standing-rules.md"
CLAUDE = f"{CDIR}/CLAUDE.md"
FLAG = f"{CDIR}/RULE_SYNC_DRIFT.md"
BEGIN = "<!-- BEGIN STANDING-RULES (generated - edit the manifest, not this block) -->"
END = "<!-- END STANDING-RULES -->"

manifest = open(MANIFEST).read().strip()
doc = open(CLAUDE).read()
m = re.search(re.escape(BEGIN) + r"\n(.*?)\n" + re.escape(END), doc, re.S)
h = hashlib.sha256(manifest.encode()).hexdigest()[:12]

if "--fix" in sys.argv:
    if not m:
        sys.exit("no marker block in CLAUDE.md")
    doc = doc[:m.start(1)] + manifest + doc[m.end(1):]
    open(CLAUDE, "w").write(doc)
    if os.path.exists(FLAG):
        os.remove(FLAG)
    print(f"regenerated. manifest sha256:{h}")
    sys.exit(0)

if m and m.group(1).strip() == manifest:
    if os.path.exists(FLAG):
        os.remove(FLAG)
    print(f"in sync. manifest sha256:{h}")
    sys.exit(0)

open(FLAG, "w").write(
    f"# RULE SYNC DRIFT (detected by check_rule_sync.py)\n\n"
    f"Manifest sha256:{h} does not match the STANDING-RULES block in "
    f"CLAUDE.md (or block missing).\nResolve: decide which side is correct, "
    f"edit ~/.claude/rules/standing-rules.md, then run:\n"
    f"  python3 ~/.claude/hooks/check_rule_sync.py --fix\n"
    f"If another surface pins the hash, verify it still pins sha256:{h} "
    f"(or update the pin after fixing).\n")
print(f"DRIFT — flag written to {FLAG}. manifest sha256:{h}", file=sys.stderr)
sys.exit(1)
