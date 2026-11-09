#!/usr/bin/env python3
"""Every number and claim the README and rules make about the kit is checked here (stdlib only).
Run: python3 tests/claims_test.py. From an unpacked ZIP (no release/ or .git) the manifest
checks report SKIP; everything else still runs."""
import os, re, subprocess, sys, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hooks"))
MANIFEST = ROOT / "release" / "free-files.txt"
SKIP = "SKIP (no release/ or .git)"


def shipped():
    """Files that ship: the manifest when present, otherwise everything in this tree."""
    if MANIFEST.exists():
        return [n for n in MANIFEST.read_text().splitlines() if n]
    return [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and "__pycache__" not in p.parts]


def readme_number(pattern):
    m = re.search(pattern, (ROOT / "README.md").read_text())
    assert m, f"README has no match for {pattern!r}"
    return int(m.group(1))


def test_readme_skill_count():
    skills = [n for n in shipped() if re.fullmatch(r"skills/[^/]+/SKILL\.md", n)]
    assert readme_number(r"(\d+) evidence-first engineering skills") == len(skills), len(skills)


def test_readme_guard_case_count():
    import guard_tests
    assert readme_number(r"(\d+) regression cases") == len(guard_tests.cases), len(guard_tests.cases)


def test_no_retired_claims():
    # Built from parts so this file does not match itself.
    retired = ["migration" + "-auditor", "cannot " + "talk"]
    hits = []
    for n in shipped():
        if n.startswith("tests/") or n == "CHANGELOG.md":
            continue
        text = (ROOT / n).read_text(errors="ignore")
        hits += [f"{n}: {r}" for r in retired if r in text]
    assert not hits, hits


def test_manifest_complete():
    if not MANIFEST.exists() or not (ROOT / ".git").exists():
        return SKIP
    names = set(shipped())
    tracked = subprocess.run(["git", "ls-files", "skills", "hooks", "tests"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.split()
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "skills", "hooks", "tests"],
                               cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    missing = sorted(set(tracked + untracked) - names)
    absent = sorted(n for n in names if not (ROOT / n).is_file())
    assert not missing and not absent, {"not in manifest": missing, "listed but missing": absent}


def test_footer_marked_optional():
    assert "footer_check.py, off by default" in (ROOT / "rules" / "standing-rules.md").read_text()


if __name__ == "__main__":
    tests = [(n, f) for n, f in list(globals().items()) if n.startswith("test_") and callable(f)]
    bad = 0
    for n, f in tests:
        try:
            print(f"{SKIP:<4} {n}" if f() == SKIP else f"OK  {n}")
        except Exception as ex:
            bad += 1
            print(f"BAD {n}: {type(ex).__name__}: {ex}")
            if os.getenv("HOOKS_TEST_TRACE"):
                traceback.print_exc()
    print(f"\n{len(tests) - bad}/{len(tests)} pass")
    raise SystemExit(1 if bad else 0)
