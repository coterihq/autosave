import json, os, subprocess, sys
GUARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guard.py")

# (expected exit, expected substring of the block reason or None, command)
# A guard's negative test passes only when it fails for the INTENDED reason, so blocks assert on
# the mechanism named in stderr, not just on the exit code.
cases = [
 # --- .env, live toggles, prod DB, rm -rf ---
 (2, ".env", 'echo X=1 >> .env.local'),
 (0, None, 'cat .env.example'),
 (2, "live-mode", 'DRY_RUN=false python3 bot.py'),
 (2, "prod", 'supabase db push'),
 (0, None, 'supabase db push --local'),
 (2, "root-level", 'rm -rf ~/'),
 # --- v1.0 audit: false positives that stopped normal work ---
 (0, None, 'cp config.example kit.conf'),
 (0, None, "grep -rn 'supabase db push' docs/"),
 (0, None, "git commit -m 'document the DRY_RUN=false toggle'"),
 (0, None, 'ng serve --live-reload'),
 (0, None, 'npm run db:migrate'),
 (0, None, 'rm -rf .claude'),
 (0, None, 'rm -rf ./build /tmp/x'),
 (2, "live-mode", 'python3 bot.py --live'),
 (0, None, "git commit -q -F - <<'EOF'\nguard: match the live flag as --live only\nEOF"),
 (2, "live-mode", "bash <<'EOF'\nDRY_RUN=false python3 bot.py\nEOF"),
 # --- v1.0 audit: catastrophic rm spellings that slipped past ---
 (2, "root-level", 'rm -rf ~/.claude/'),
 (2, "root-level", 'rm -rf /*'),
 (2, "root-level", 'rm -rf ~/*'),
 (2, "root-level", 'rm -rf $HOME'),
 (2, "root-level", 'rm -rf "$HOME"'),
 (2, "root-level", 'rm -rf ${HOME}/.claude'),
 (2, "root-level", 'rm --recursive --force /'),
 # --- zsh word splitting (zsh only; bash does split) ---
 (2, "word", 'set -- $files'),
 (0, None, 'set -- $files', "/bin/bash"),
 (0, None, 'for f in $(find . -name "*.py"); do wc -l $f; done'),
 (0, None, 'n=$(ls | wc -l); echo $n'),
 (2, "multiple values", 'files=$(ls *.md); wc -l $files'),

 # --- rule 5a: pgrep/pkill -f in a wait loop ---
 (2, "never exits", 'cd x && until [ a = b ]; do sleep 30; done; while pgrep -f deploy.sh >/dev/null; do sleep 20; done; npm run -s prod:deploy'),
 (2, "never exits", 'until ! pgrep -f "next build --webpack"; do sleep 5; done'),
 (0, None, 'pgrep -fl "next start -p 5555" | cut -c1-40'),
 (0, None, "while pgrep -f '[d]eploy-prod.sh' >/dev/null; do sleep 20; done"),
 (0, None, "python3 - x <<'EOF2'\nt='- **Wait loops must not match themselves.** `until ! pgrep -f \"X\"` also matches'\nEOF2\ndiff -rq a b"),

 # --- rule 5b: ps|grep in a wait loop ---
 # A real failure: pattern IS bracketed, but the wait message carries the bare
 # literal into the same argv, so the loop matched its own announcement and never fired the deploy.
 (2, "own announcement", "cat > /tmp/d.sh <<'SH'\nuntil [ \"$(ps -eo command | grep -c '[n]ext build')\" -eq 0 ]; do echo \"waiting: another next build is running\"; sleep 60; done\nnpm run prod:deploy\nSH\nbash /tmp/d.sh"),
 # Same shape without a heredoc, unbracketed: the plain case.
 (2, "never exits", 'until [ "$(ps -eo command | grep -c \'next build\')" -eq 0 ]; do sleep 60; done'),
 # Bracketed, bare literal nowhere else: this is the CORRECT form and must stay allowed.
 (0, None, "until [ \"$(ps -eo command | grep -c '[n]ext build')\" -eq 0 ]; do sleep 60; done"),
 # ps|grep with no loop at all — a one-shot inspection, always fine.
 (0, None, "ps -eo pid,command | grep 'next build' | cut -c1-120"),
 # A loop that polls an artefact instead of the process table — the recommended alternative.
 (0, None, 'until curl -sf http://127.0.0.1:5555/ >/dev/null; do sleep 5; done'),
 # Prose about the failure, quoted into a doc, with no execution of the heredoc.
 (0, None, "cat > notes.md <<'EOF2'\nuntil ps -eo command | grep -c 'next build'; the loop hangs\nEOF2"),
 # Regression: the first cut of 5b searched the WHOLE command, so an
 # unrelated `while read` cross-producted with an unrelated quoted `ps aux | grep` and blocked a
 # legitimate call. Scanning only the loop CONDITION fixed it; this case keeps it fixed.
 (0, None, 'while read -r l; do echo "$l"; done < f.txt; grep -rn "ps aux | grep foo" docs/'),
 # ps|grep in a loop BODY is not a wait condition and cannot hang on itself.
 (0, None, 'while true; do ps -eo command | grep foo; sleep 1; done'),
]

bad = 0
for want, reason, c, *shell in cases:
    env = dict(os.environ, SHELL=shell[0] if shell else "/bin/zsh")
    r = subprocess.run([sys.executable, GUARD],
                       input=json.dumps({"tool_name": "Bash", "tool_input": {"command": c}}),
                       capture_output=True, text=True, env=env)
    ok = r.returncode == want and (reason is None or reason in r.stderr)
    if not ok:
        bad += 1
    detail = "" if ok else f"  <- got {r.returncode} want {want}" + (f", reason missing {reason!r}" if reason and reason not in r.stderr else "")
    print(("OK  " if ok else "BAD ") + c[:66].replace("\n", " ") + detail)
print(f"\n{len(cases) - bad}/{len(cases)} pass")
raise SystemExit(1 if bad else 0)
